#!/usr/bin/env python3
"""Explore candidate journals through OpenAlex Works/Sources."""

from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path
from typing import Any

PLUGIN_ROOT = None
for parent in Path(__file__).resolve().parents:
    if (parent / "_shared").is_dir() and (parent / "skills").is_dir():
        PLUGIN_ROOT = parent
        sys.path.insert(0, str(parent))
        break
if PLUGIN_ROOT is None:
    raise RuntimeError("could not locate journal-research-en root")

from _shared.api_utils import (  # noqa: E402
    openalex_entity_id,
    openalex_params,
    print_payload,
    request_json,
    source_to_candidate,
)


OPENALEX_API = "https://api.openalex.org"


def fetch_source(source_id: str, *, mailto: str | None = None) -> tuple[dict[str, Any], list[str]]:
    entity_id = openalex_entity_id(source_id)
    params, warnings = openalex_params({}, mailto=mailto)
    data = request_json("GET", f"{OPENALEX_API}/sources/{entity_id}", params=params, retries=3)
    return data, warnings


def explore(query: str, *, per_page: int = 10, mailto: str | None = None, oa_only: bool = False) -> dict[str, Any]:
    filter_parts = ["primary_location.source.type:journal"]
    if oa_only:
        filter_parts.append("is_oa:true")
    params, warnings = openalex_params(
        {
            "search": query,
            "per-page": per_page,
            "group_by": "primary_location.source.id",
            "filter": ",".join(filter_parts),
        },
        mailto=mailto,
    )
    grouped = request_json("GET", f"{OPENALEX_API}/works", params=params, retries=3)
    groups = grouped.get("group_by") or []
    max_count = max([int(g.get("count", 0)) for g in groups] or [1])

    candidates: list[dict[str, Any]] = []
    for group in groups[:per_page]:
        source_id = group.get("key")
        if not source_id:
            continue
        try:
            source, source_warnings = fetch_source(source_id, mailto=mailto)
        except Exception as exc:
            warnings.append(f"source lookup failed for {source_id}: {exc}")
            continue
        time.sleep(0.1)
        source_type = source.get("type")
        if source_type and source_type != "journal":
            warnings.append(f"skipped non-journal OpenAlex source {source_id} type={source_type}")
            continue
        count = int(group.get("count", 0))
        fit_score = round(count / max_count, 4) if max_count else None
        candidates.append(
            source_to_candidate(
                source,
                fit_score=fit_score,
                evidence_source="openalex-grouped-works",
                evidence_url=source_id,
                trust_level="openalex-explore",
                extra_metrics={"group_count": count, "query": query},
                warnings=source_warnings,
            )
        )

    return {
        "adapter": "openalex-explore",
        "query": query,
        "count": len(candidates),
        "candidates": candidates,
        "warnings": warnings,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="OpenAlex journal source explorer")
    parser.add_argument("query")
    parser.add_argument("--per-page", type=int, default=10)
    parser.add_argument("--mailto")
    parser.add_argument("--oa-only", action="store_true")
    args = parser.parse_args()

    payload = explore(args.query, per_page=args.per_page, mailto=args.mailto, oa_only=args.oa_only)
    print_payload(payload)
    return 0 if payload["count"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
