#!/usr/bin/env python3
"""Google Scholar venue-frequency wrapper with OpenAlex enrichment."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import tempfile
from collections import Counter
from pathlib import Path
from typing import Any

for parent in Path(__file__).resolve().parents:
    if (parent / "_shared").is_dir() and (parent / "skills").is_dir():
        sys.path.insert(0, str(parent))
        break

from _shared.api_utils import openalex_params, print_payload, request_json, source_to_candidate  # noqa: E402


OPENALEX_API = "https://api.openalex.org"


def run_google_scholar(query: str, limit: int) -> tuple[list[dict[str, Any]], list[str]]:
    warnings: list[str] = []
    script = Path(__file__).with_name("search_google_scholar.py")
    with tempfile.NamedTemporaryFile("r+", suffix=".json", delete=True) as handle:
        result = subprocess.run(
            [sys.executable, str(script), query, "--limit", str(limit), "--output", handle.name],
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=max(90, limit * 8),
        )
        if result.returncode != 0:
            warnings.append(f"Google Scholar script failed: {result.stderr.strip() or result.stdout.strip()}")
            return [], warnings
        handle.seek(0)
        data = json.load(handle)
    return data.get("results") or [], warnings


def source_for_venue(venue: str) -> tuple[dict[str, Any] | None, list[str]]:
    params, warnings = openalex_params({"search": venue, "per-page": 1})
    data = request_json("GET", f"{OPENALEX_API}/sources", params=params, retries=3)
    results = data.get("results") or []
    return (results[0] if results else None), warnings


def openalex_fallback(query: str, limit: int, warnings: list[str]) -> tuple[Counter[str], dict[str, dict[str, Any]], bool]:
    warnings.append("using OpenAlex fallback because Google Scholar results were unavailable")
    params, _ = openalex_params({"search": query, "per-page": limit, "group_by": "primary_location.source.id"})
    data = request_json("GET", f"{OPENALEX_API}/works", params=params, retries=3)
    counts: Counter[str] = Counter()
    details: dict[str, dict[str, Any]] = {}
    for group in data.get("group_by") or []:
        source_id = group.get("key")
        if not source_id:
            continue
        try:
            source = request_json("GET", f"{OPENALEX_API}/sources/{source_id.rstrip('/').split('/')[-1]}", params=openalex_params({})[0], retries=3)
        except Exception as exc:
            warnings.append(f"OpenAlex fallback source lookup failed for {source_id}: {exc}")
            continue
        if source.get("type") in {"repository", "preprint server"}:
            continue
        counts[source_id] = int(group.get("count", 0))
        details[source_id] = source
        if len(counts) >= limit:
            break
    return counts, details, True


def explore(query: str, *, limit: int = 30, top: int = 10) -> dict[str, Any]:
    results, warnings = run_google_scholar(query, limit)
    venue_counts: Counter[str] = Counter()
    for item in results:
        venue = (item.get("venue") or "").strip()
        if venue:
            venue_counts[venue] += 1

    source_details: dict[str, dict[str, Any]] = {}
    fallback_used = False
    source_counts: Counter[str] = Counter()
    if venue_counts:
        for venue, count in venue_counts.most_common(top):
            source, source_warnings = source_for_venue(venue)
            warnings.extend(source_warnings)
            if source:
                source_id = source.get("id") or venue
                source_counts[source_id] += count
                source_details[source_id] = source
                source_details[source_id]["_venue"] = venue
    else:
        source_counts, source_details, fallback_used = openalex_fallback(query, top, warnings)

    max_count = max(source_counts.values() or [1])
    candidates = []
    for source_id, count in source_counts.most_common(top):
        source = source_details[source_id]
        candidates.append(
            source_to_candidate(
                source,
                fit_score=round(count / max_count, 4),
                evidence_source="google-scholar-openalex-fallback" if fallback_used else "google-scholar-venue-frequency",
                evidence_url=source.get("id"),
                trust_level="google-scholar-explore",
                extra_metrics={
                    "venue_count": count,
                    "google_scholar_fallback": fallback_used,
                    "scholar_venue": source.get("_venue"),
                    "query": query,
                },
                warnings=warnings,
            )
        )
    return {
        "adapter": "google-scholar-explore",
        "query": query,
        "scholar_result_count": len(results),
        "count": len(candidates),
        "candidates": candidates,
        "warnings": warnings,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Google Scholar venue-frequency explorer")
    parser.add_argument("query")
    parser.add_argument("--limit", type=int, default=30)
    parser.add_argument("--top", type=int, default=10)
    args = parser.parse_args()
    payload = explore(args.query, limit=args.limit, top=args.top)
    print_payload(payload)
    return 0 if payload["count"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
