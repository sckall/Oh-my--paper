#!/usr/bin/env python3
"""Explore CS venues through dblp and enrich through OpenAlex."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any

for parent in Path(__file__).resolve().parents:
    if (parent / "_shared").is_dir() and (parent / "skills").is_dir():
        sys.path.insert(0, str(parent))
        break

from _shared.api_utils import openalex_params, print_payload, request_json, source_to_candidate  # noqa: E402


DBLP_API = "https://dblp.org/search/venue/api"
OPENALEX_API = "https://api.openalex.org"


def as_list(value: Any) -> list[Any]:
    if value is None:
        return []
    return value if isinstance(value, list) else [value]


def search_openalex_source(name: str) -> tuple[dict[str, Any] | None, list[str]]:
    params, warnings = openalex_params({"search": name, "per-page": 1})
    data = request_json("GET", f"{OPENALEX_API}/sources", params=params, retries=3)
    results = data.get("results") or []
    return (results[0] if results else None), warnings


def explore(query: str, *, limit: int = 10, include_conference: bool = False) -> dict[str, Any]:
    data = request_json("GET", DBLP_API, params={"q": query, "format": "json"}, retries=3)
    hits = as_list(((data.get("result") or {}).get("hits") or {}).get("hit"))
    candidates: list[dict[str, Any]] = []
    warnings: list[str] = []

    for hit in hits:
        info = hit.get("info") or {}
        venue_type = info.get("type")
        if venue_type != "Journal" and not include_conference:
            continue
        venue_name = info.get("venue")
        if not venue_name:
            continue
        source, source_warnings = search_openalex_source(venue_name)
        warnings.extend(source_warnings)
        fit_score = None
        try:
            fit_score = float(hit.get("@score")) if hit.get("@score") is not None else None
        except ValueError:
            pass
        if source:
            candidate = source_to_candidate(
                source,
                fit_score=fit_score,
                evidence_source="dblp-venue-search",
                evidence_url=info.get("url"),
                trust_level="dblp-cs-explore",
                extra_metrics={
                    "dblp_venue": venue_name,
                    "dblp_type": venue_type,
                    "dblp_url": info.get("url"),
                    "dblp_acronym": info.get("acronym"),
                },
                warnings=source_warnings,
            )
        else:
            warnings.append(f"OpenAlex source lookup missed dblp venue: {venue_name}")
            candidate = source_to_candidate(
                {"display_name": venue_name, "type": venue_type, "id": f"dblp:{info.get('url')}"},
                fit_score=fit_score,
                evidence_source="dblp-venue-search",
                evidence_url=info.get("url"),
                trust_level="dblp-cs-explore",
                extra_metrics={"dblp_type": venue_type, "dblp_url": info.get("url"), "dblp_acronym": info.get("acronym")},
            )
        candidates.append(candidate)
        if len(candidates) >= limit:
            break

    return {
        "adapter": "dblp-cs-explore",
        "query": query,
        "count": len(candidates),
        "candidates": candidates,
        "warnings": warnings,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="dblp CS venue explorer")
    parser.add_argument("query")
    parser.add_argument("--limit", type=int, default=10)
    parser.add_argument("--include-conference", action="store_true")
    args = parser.parse_args()
    payload = explore(args.query, limit=args.limit, include_conference=args.include_conference)
    print_payload(payload)
    return 0 if payload["count"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
