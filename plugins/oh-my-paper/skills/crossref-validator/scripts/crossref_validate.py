#!/usr/bin/env python3
"""Validate ISSN/DOI metadata through Crossref."""

from __future__ import annotations

import argparse
import os
import re
import sys
from pathlib import Path
from typing import Any
from urllib.parse import quote

for parent in Path(__file__).resolve().parents:
    if (parent / "_shared").is_dir() and (parent / "skills").is_dir():
        sys.path.insert(0, str(parent))
        break

from _shared.api_utils import DEFAULT_MAILTO, print_payload, request_json, source_to_candidate  # noqa: E402


CROSSREF_API = "https://api.crossref.org"
ISSN_RE = re.compile(r"^\d{4}-?\d{3}[\dXx]$")


def identifier_type(identifier: str) -> str:
    value = identifier.strip()
    if ISSN_RE.match(value):
        return "issn"
    if value.startswith("10.") or "doi.org/10." in value:
        return "doi"
    raise ValueError(f"unsupported identifier, expected ISSN or DOI: {identifier}")


def issn_candidate(message: dict[str, Any], identifier: str) -> dict[str, Any]:
    issns = message.get("ISSN") or []
    source = {
        "display_name": message.get("title"),
        "issn": issns,
        "publisher": message.get("publisher"),
        "type": "journal",
        "id": f"crossref:journal:{identifier}",
    }
    return source_to_candidate(
        source,
        fit_score=None,
        evidence_source="crossref-journal",
        evidence_url=f"https://api.crossref.org/journals/{identifier}",
        trust_level="crossref-validator",
        extra_metrics={
            "crossref_counts": message.get("counts"),
            "coverage": message.get("coverage"),
            "breakdowns": message.get("breakdowns"),
        },
    )


def doi_candidate(message: dict[str, Any], doi: str) -> dict[str, Any]:
    issns = message.get("ISSN") or []
    container_title = (message.get("container-title") or [None])[0]
    source = {
        "display_name": container_title,
        "issn": issns,
        "publisher": message.get("publisher"),
        "type": message.get("type"),
        "id": f"crossref:work:{doi}",
    }
    candidate = source_to_candidate(
        source,
        fit_score=None,
        evidence_source="crossref-work",
        evidence_url=f"https://doi.org/{doi}",
        trust_level="crossref-validator",
        extra_metrics={
            "doi": doi,
            "work_title": (message.get("title") or [None])[0],
            "published": message.get("published") or message.get("published-print") or message.get("published-online"),
        },
    )
    return candidate


def validate(identifier: str, *, mailto: str | None = None) -> dict[str, Any]:
    clean = identifier.strip()
    mailto = mailto or os.environ.get("CROSSREF_MAILTO") or os.environ.get("JOURNAL_RESEARCH_MAILTO") or DEFAULT_MAILTO
    kind = identifier_type(clean)
    if kind == "issn":
        endpoint = f"{CROSSREF_API}/journals/{clean}"
    else:
        clean = clean.replace("https://doi.org/", "").replace("http://doi.org/", "").replace("doi:", "")
        endpoint = f"{CROSSREF_API}/works/{quote(clean, safe='')}"
    params = {"mailto": mailto} if mailto else None
    data = request_json("GET", endpoint, params=params, retries=3)
    message = data.get("message") or {}
    candidate = issn_candidate(message, clean) if kind == "issn" else doi_candidate(message, clean)
    return {
        "adapter": "crossref-validator",
        "identifier": clean,
        "identifier_type": kind,
        "candidate": candidate,
        "work": message if kind == "doi" else None,
        "warnings": [],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Crossref ISSN/DOI validator")
    parser.add_argument("identifier")
    parser.add_argument("--mailto")
    args = parser.parse_args()
    payload = validate(args.identifier, mailto=args.mailto)
    print_payload(payload)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
