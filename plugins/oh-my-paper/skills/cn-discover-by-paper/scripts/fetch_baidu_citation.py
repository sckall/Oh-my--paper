#!/usr/bin/env python3
"""Baidu Scholar citation fetcher copied from academic-suite on 2026-04-29.

This physical copy keeps journal-research-cn self-contained and avoids a
runtime dependency on plugins/academic-suite.
"""

import argparse
import json
import re
import sys
import urllib.error
import urllib.parse
import urllib.request

from fetch_baidu_detail import extract_paper_id


STYLE_ALIASES = {
    "gbt": "sc_GBT7714",
    "gbt7714": "sc_GBT7714",
    "apa": "sc_APA",
    "mla": "sc_MLA",
}


def fetch_citation_payload(paper_id: str) -> dict:
    endpoint = (
        "https://xueshu.baidu.com/u/citation?paperid="
        + urllib.parse.quote(paper_id)
        + "&type=cite"
    )
    request = urllib.request.Request(
        endpoint,
        headers={
            "User-Agent": "Mozilla/5.0",
            "Accept": "application/json",
        },
    )
    with urllib.request.urlopen(request, timeout=20) as response:
        payload = json.load(response)
    if not isinstance(payload, dict):
        raise ValueError("Unexpected response shape from Baidu Scholar citation endpoint")
    if payload.get("status") != 0:
        raise ValueError(payload.get("msg") or "Baidu Scholar citation request failed")
    data = payload.get("data")
    if not isinstance(data, dict):
        raise ValueError("Missing citation data in Baidu Scholar response")
    return data


def clean_citation_text(value: str) -> str:
    text = value or ""
    text = re.sub(r"#i\{([^}]*)\}", r"\1", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def normalize_citations(paper_id: str, payload: dict) -> dict:
    citations = {}
    for style, key in STYLE_ALIASES.items():
        citations[style] = clean_citation_text(str(payload.get(key, "")))
    return {
        "paperId": paper_id,
        "citations": citations,
    }


def format_all(result: dict) -> str:
    lines = [f"paperId: {result['paperId']}"]
    for style in ("gbt7714", "apa", "mla"):
        lines.append(f"{style}: {result['citations'][style] or '-'}")
    return "\n".join(lines)


def strip_index(text: str) -> str:
    return re.sub(r"^\[\d+\]\s*", "", text).strip()


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Fetch Baidu Scholar citation-modal data from a paperId or detail URL."
    )
    parser.add_argument("--paper-id", help="Baidu Scholar paperId")
    parser.add_argument("--url", help="Baidu Scholar detail page URL")
    parser.add_argument(
        "--format",
        choices=("gbt", "gbt7714", "apa", "mla", "all", "json"),
        default="gbt7714",
        help="Output format",
    )
    parser.add_argument(
        "--strip-index",
        action="store_true",
        help="Remove the leading [1] style index from rendered citation text",
    )
    args = parser.parse_args()

    if not args.paper_id and not args.url:
        parser.error("Provide --paper-id or --url")

    try:
        paper_id = args.paper_id or extract_paper_id(args.url)
        result = normalize_citations(paper_id, fetch_citation_payload(paper_id))
    except (ValueError, urllib.error.URLError, urllib.error.HTTPError, json.JSONDecodeError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    if args.strip_index:
        for key, value in result["citations"].items():
            result["citations"][key] = strip_index(value)

    if args.format == "json":
        print(json.dumps(result, ensure_ascii=False, indent=2))
    elif args.format == "all":
        print(format_all(result))
    else:
        style = "gbt7714" if args.format in ("gbt", "gbt7714") else args.format
        print(result["citations"][style])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
