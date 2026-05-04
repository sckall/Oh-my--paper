#!/usr/bin/env python3
"""
Journal Authority Check - DOAJ + SCImago verification

Usage:
    python3 authority_check.py "1673-5370"           # ISSN
    python3 authority_check.py "1673-5370" -o auth.json

Checks:
  1. DOAJ (Directory of Open Access Journals) - open access verification
  2. Crossref - metadata verification

All HTTP via urllib.request (stdlib, zero deps).
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path
from typing import Any

# Add _shared to path
_SCRIPT_DIR = Path(__file__).resolve().parent
_PLUGIN_DIR = _SCRIPT_DIR.parent.parent.parent
_SHARED_DIR = _PLUGIN_DIR / "_shared"
_JOURNAL_DIR = _SHARED_DIR / "journal"
for p in (_SHARED_DIR, _JOURNAL_DIR):
    sp = str(p)
    if sp not in sys.path:
        sys.path.insert(0, sp)

from adapter_utils import request_json, source_evidence, utc_now, normalize_issn, USER_AGENT

DOAJ_API = "https://api.doaj.org/api/v1/search/journals/"
CROSSREF_API = "https://api.crossref.org/journals/"


def check_doaj(issn: str) -> dict[str, Any]:
    """Check DOAJ for open access journal status."""
    try:
        url = f"{DOAJ_API}{issn.replace('-', '')}?api_key="
        data = request_json(url, headers={"User-Agent": USER_AGENT}, timeout=15)
        results = data.get("results", [])
        if results:
            journal = results[0]
            bib = journal.get("bibjson", {}) or journal.get("journal", {}) or {}
            return {
                "in_doaj": True,
                "journal_name": bib.get("title", ""),
                "publisher": bib.get("publisher", ""),
                "country": bib.get("country", ""),
                "language": bib.get("language", []),
                "license": bib.get("license", []),
                "apc": bib.get("apc", {}),
                "eissn": bib.get("eissn"),
                "pissn": bib.get("pissn"),
                "url": bib.get("link", ""),
            }
        return {"in_doaj": False, "reason": "not_found"}
    except Exception as e:
        return {"in_doaj": None, "error": str(e)}


def check_crossref(issn: str) -> dict[str, Any]:
    """Check Crossref for journal metadata."""
    try:
        url = f"{CROSSREF_API}{issn}"
        data = request_json(url, headers={"User-Agent": USER_AGENT}, timeout=15)
        message = data.get("message", {})
        return {
            "found": bool(message),
            "title": message.get("title", []),
            "publisher": message.get("publisher", ""),
            "issn": message.get("ISSN", []),
            "subjects": message.get("subjects", []),
        }
    except Exception as e:
        return {"found": None, "error": str(e)}


def main() -> None:
    parser = argparse.ArgumentParser(description="Journal Authority Check (DOAJ + Crossref)")
    parser.add_argument("issn", help="Journal ISSN (e.g. 1673-5370)")
    parser.add_argument("-o", "--output", help="Output JSON file path")
    args = parser.parse_args()

    issn = normalize_issn(args.issn)
    print(f"Checking authority for ISSN: {issn}", file=sys.stderr)

    # Check DOAJ
    print("  Checking DOAJ...", file=sys.stderr)
    doaj_result = check_doaj(issn)
    time.sleep(0.5)

    # Check Crossref
    print("  Checking Crossref...", file=sys.stderr)
    crossref_result = check_crossref(issn)

    result = {
        "issn": issn,
        "doaj": doaj_result,
        "crossref": crossref_result,
        "metadata": {
            "fetched_at": utc_now(),
            "tool_tier_used": "0",
            "trust_level": "authoritative-secondary",
            "skill_version": "0.4.0",
        },
    }

    text = json.dumps(result, ensure_ascii=False, indent=2)
    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(text + "\n")
        print(f"Written to {args.output}", file=sys.stderr)
    else:
        print(text)


if __name__ == "__main__":
    main()
