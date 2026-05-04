#!/usr/bin/env python3
"""Explore likely publication venues from arXiv preprints."""

from __future__ import annotations

import argparse
import re
import sys
import time
import xml.etree.ElementTree as ET
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

for parent in Path(__file__).resolve().parents:
    if (parent / "_shared").is_dir() and (parent / "skills").is_dir():
        sys.path.insert(0, str(parent))
        break

from _shared.api_utils import (  # noqa: E402
    DEFAULT_USER_AGENT,
    openalex_entity_id,
    openalex_params,
    print_payload,
    request_json,
    source_to_candidate,
)


ARXIV_API = "https://export.arxiv.org/api/query"
OPENALEX_API = "https://api.openalex.org"
ATOM = {"atom": "http://www.w3.org/2005/Atom", "arxiv": "http://arxiv.org/schemas/atom"}
CATEGORY_QUERY_MAP = {
    "cs.lg": "machine learning",
    "cs.ai": "artificial intelligence",
    "cs.cv": "computer vision",
    "cs.cl": "natural language processing",
    "stat.ml": "machine learning statistics",
    "math": "mathematics",
    "physics": "physics",
    "quant-ph": "quantum computing",
}


def arxiv_search_query(value: str) -> str:
    clean = value.strip()
    if re.match(r"^[a-z-]+\.[A-Z]{2}$", clean, re.I) or clean.lower() in CATEGORY_QUERY_MAP:
        return f"cat:{clean}"
    if clean.startswith("au:") or clean.startswith("cat:") or clean.startswith("all:"):
        return clean
    return f"all:{clean}"


def parse_arxiv_id(entry_id: str) -> str:
    value = entry_id.rstrip("/").split("/")[-1]
    return value.replace("arXiv:", "").split("v")[0]


def fetch_arxiv_entries(query: str, max_results: int) -> tuple[list[dict[str, Any]], list[str]]:
    warnings: list[str] = []
    import requests

    params = {
        "search_query": arxiv_search_query(query),
        "start": 0,
        "max_results": max_results,
        "sortBy": "submittedDate",
        "sortOrder": "descending",
    }
    response = requests.get(ARXIV_API, params=params, timeout=45, headers={"User-Agent": DEFAULT_USER_AGENT})
    if response.status_code == 429:
        warnings.append("arXiv API returned 429; falling back to OpenAlex topic aggregation")
        return [], warnings
    response.raise_for_status()
    root = ET.fromstring(response.text)
    entries = []
    for entry in root.findall("atom:entry", ATOM):
        entry_id = entry.findtext("atom:id", default="", namespaces=ATOM)
        title = " ".join(entry.findtext("atom:title", default="", namespaces=ATOM).split())
        entries.append({"arxiv_id": parse_arxiv_id(entry_id), "title": title, "url": entry_id})
    return entries, warnings


def source_from_openalex_work(work: dict[str, Any]) -> dict[str, Any] | None:
    candidates = []
    primary = (work.get("primary_location") or {}).get("source")
    if primary:
        candidates.append(primary)
    for location in work.get("locations") or []:
        source = location.get("source")
        if source:
            candidates.append(source)
    for source in candidates:
        source_type = source.get("type")
        display_name = source.get("display_name")
        if display_name and source_type not in {"repository", "preprint server"}:
            return source
    return None


def openalex_work_for_arxiv_id(arxiv_id: str) -> tuple[dict[str, Any] | None, str | None]:
    try:
        data = request_json("GET", f"{OPENALEX_API}/works/arxiv:{arxiv_id}", retries=1)
        return data, "direct"
    except Exception:
        return None, None


def openalex_work_for_title(title: str) -> tuple[dict[str, Any] | None, str | None]:
    params, _ = openalex_params({"search": title, "per-page": 3, "select": "id,title,primary_location,locations"})
    data = request_json("GET", f"{OPENALEX_API}/works", params=params, retries=3)
    for work in data.get("results") or []:
        source = source_from_openalex_work(work)
        if source:
            return work, "title-search"
    return None, None


def fetch_source(source_id: str) -> dict[str, Any] | None:
    entity_id = openalex_entity_id(source_id)
    if not entity_id:
        return None
    params, _ = openalex_params({})
    return request_json("GET", f"{OPENALEX_API}/sources/{entity_id}", params=params, retries=3)


def aggregate_sources_from_entries(entries: list[dict[str, Any]], warnings: list[str]) -> tuple[Counter[str], dict[str, dict[str, Any]], dict[str, list[str]]]:
    counts: Counter[str] = Counter()
    source_details: dict[str, dict[str, Any]] = {}
    arxiv_ids_by_source: dict[str, list[str]] = defaultdict(list)

    for entry in entries:
        work, resolver = openalex_work_for_arxiv_id(entry["arxiv_id"])
        if not work:
            warnings.append(f"OpenAlex /works/arxiv:{entry['arxiv_id']} unavailable; using title search fallback")
            work, resolver = openalex_work_for_title(entry["title"])
        if not work:
            warnings.append(f"OpenAlex missed arXiv entry {entry['arxiv_id']}: {entry['title']}")
            continue
        source = source_from_openalex_work(work)
        if not source:
            continue
        source_id = source.get("id") or source.get("display_name")
        if not source_id:
            continue
        detailed = fetch_source(source_id) if source.get("id") else None
        source_details[source_id] = detailed or source
        source_details[source_id]["_resolver"] = resolver
        counts[source_id] += 1
        arxiv_ids_by_source[source_id].append(entry["arxiv_id"])
        time.sleep(0.1)
    return counts, source_details, arxiv_ids_by_source


def fallback_openalex_topic(query: str, limit: int, warnings: list[str]) -> tuple[Counter[str], dict[str, dict[str, Any]], dict[str, list[str]]]:
    mapped = CATEGORY_QUERY_MAP.get(query.lower(), query)
    warnings.append(f"using OpenAlex topic fallback query={mapped!r}")
    params, _ = openalex_params({"search": mapped, "per-page": limit, "group_by": "primary_location.source.id"})
    data = request_json("GET", f"{OPENALEX_API}/works", params=params, retries=3)
    counts: Counter[str] = Counter()
    details: dict[str, dict[str, Any]] = {}
    ids: dict[str, list[str]] = defaultdict(list)
    for group in data.get("group_by") or []:
        source_id = group.get("key")
        if not source_id:
            continue
        try:
            source = fetch_source(source_id)
        except Exception as exc:
            warnings.append(f"OpenAlex source fallback lookup failed for {source_id}: {exc}")
            continue
        if not source or source.get("type") in {"repository", "preprint server"}:
            continue
        counts[source_id] = int(group.get("count", 0))
        details[source_id] = source
        ids[source_id] = []
        if len(counts) >= limit:
            break
    return counts, details, ids


def explore(query: str, *, max_results: int = 5) -> dict[str, Any]:
    entries, warnings = fetch_arxiv_entries(query, max_results)
    counts, details, arxiv_ids = aggregate_sources_from_entries(entries, warnings) if entries else (Counter(), {}, defaultdict(list))
    if len(counts) < 3:
        f_counts, f_details, f_ids = fallback_openalex_topic(query, max_results, warnings)
        counts.update(f_counts)
        details.update(f_details)
        arxiv_ids.update(f_ids)

    max_count = max(counts.values() or [1])
    candidates = []
    for source_id, count in counts.most_common(max_results):
        source = details[source_id]
        resolver = source.get("_resolver", "topic-fallback")
        candidates.append(
            source_to_candidate(
                source,
                fit_score=round(count / max_count, 4),
                evidence_source="arxiv-openalex-resolver" if resolver != "topic-fallback" else "arxiv-openalex-fallback",
                evidence_url=source.get("id"),
                trust_level="arxiv-preprint-explore",
                extra_metrics={
                    "preprint_count": count,
                    "arxiv_ids": arxiv_ids.get(source_id, []),
                    "resolver": resolver,
                    "query": query,
                },
                warnings=warnings,
            )
        )
    return {
        "adapter": "arxiv-preprint-explore",
        "query": query,
        "arxiv_entries": entries,
        "count": len(candidates),
        "candidates": candidates,
        "warnings": warnings,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="arXiv preprint venue explorer")
    parser.add_argument("query")
    parser.add_argument("max_results", nargs="?", type=int, default=5)
    args = parser.parse_args()
    payload = explore(args.query, max_results=args.max_results)
    print_payload(payload)
    return 0 if payload["count"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
