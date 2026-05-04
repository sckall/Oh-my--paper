#!/usr/bin/env python3
"""Explore OA journal candidates through B!SON."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any

for parent in Path(__file__).resolve().parents:
    if (parent / "_shared").is_dir() and (parent / "skills").is_dir():
        sys.path.insert(0, str(parent))
        break

from _shared.api_utils import now_iso, print_payload, request_json  # noqa: E402


BISON_API = "https://service.tib.eu/bison/api/public/v1/search"
DEFAULT_ABSTRACT = (
    "A scholarly manuscript seeking a suitable open access journal based on topical fit, "
    "publishing model, review process, and indexing signals."
)


def score_value(score: Any) -> float | None:
    if isinstance(score, dict):
        value = score.get("value") or score.get("semantic_score")
    else:
        value = score
    try:
        return float(value) if value is not None else None
    except (TypeError, ValueError):
        return None


def journal_to_candidate(journal: dict[str, Any]) -> dict[str, Any]:
    licenses = journal.get("licenses") or []
    subjects = journal.get("subjects") or []
    return {
        "identity": {
            "title": journal.get("title"),
            "issn": journal.get("pissn"),
            "eissn": journal.get("eissn"),
            "publisher": journal.get("publisher_name"),
            "country": journal.get("publisher_country"),
            "language": ",".join(journal.get("languages") or []) or None,
            "official_site": journal.get("ref_journal"),
            "submission_site": journal.get("ref_author_instructions"),
            "wos_categories": [],
            "scie_status": None,
            "ssci_status": None,
        },
        "fit_score": score_value(journal.get("score")),
        "authority_metrics": {
            "bison_id": journal.get("id") or journal.get("idx"),
            "plan_s_compliance": journal.get("plan_s_compliance"),
            "doaj_seal": journal.get("doaj_seal"),
            "subjects": subjects,
            "licenses": licenses,
            "has_pid_scheme": journal.get("has_pid_scheme"),
            "doi_pid_scheme": journal.get("doi_pid_scheme"),
        },
        "cas_legacy": None,
        "cas_letpub": None,
        "review_intel": {
            "editorial_review_process": journal.get("editorial_review_process") or [],
        },
        "speed_intel": {
            "publication_time_weeks": journal.get("publication_time_weeks"),
        },
        "cost_intel": {
            "has_apc": journal.get("has_apc"),
            "apc_max": journal.get("apc_max"),
            "has_other_charges": journal.get("has_other_charges"),
        },
        "risk_flags": [],
        "evidence": [
            {
                "source": "bison-public-api",
                "url": BISON_API,
                "access_level": "public",
                "trust_level": "oa-bison",
                "fetched_at": now_iso(),
                "raw_snippet_path": None,
                "tool_tier_used": "script",
                "notes": [],
            }
        ],
    }


def explore(title: str, *, abstract: str | None = None, keywords: list[str] | None = None, limit: int = 10) -> dict[str, Any]:
    body = {
        "title": title,
        "abstract": abstract or DEFAULT_ABSTRACT,
        "keywords": keywords or [],
    }
    data = request_json("POST", BISON_API, json_body=body, timeout=45, retries=3)
    journals = data.get("journals") or data.get("results") or []
    candidates = [journal_to_candidate(journal) for journal in journals[:limit]]
    return {
        "adapter": "bison-oa-explore",
        "query": {"title": title, "abstract": body["abstract"], "keywords": body["keywords"]},
        "count": len(candidates),
        "candidates": candidates,
        "warnings": [],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="B!SON OA journal explorer")
    parser.add_argument("title")
    parser.add_argument("abstract", nargs="?")
    parser.add_argument("--keyword", action="append", default=[])
    parser.add_argument("--limit", type=int, default=10)
    args = parser.parse_args()
    payload = explore(args.title, abstract=args.abstract, keywords=args.keyword, limit=args.limit)
    print_payload(payload)
    return 0 if payload["count"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
