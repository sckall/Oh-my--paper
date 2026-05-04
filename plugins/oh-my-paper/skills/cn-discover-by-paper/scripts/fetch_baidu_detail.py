#!/usr/bin/env python3
"""Baidu Scholar detail fetcher copied from academic-suite on 2026-04-29.

This physical copy keeps journal-research-cn self-contained and avoids a
runtime dependency on plugins/academic-suite.
"""

import argparse
import json
import sys
import urllib.error
import urllib.parse
import urllib.request
from urllib.parse import parse_qs, urlparse


def extract_paper_id(url: str) -> str:
    parsed = urlparse(url)
    query = parse_qs(parsed.query)
    for key in ("paperid", "paperId"):
        values = query.get(key)
        if values:
            return values[0]
    raise ValueError("No paperId/paperid found in URL")


def fetch_detail(paper_id: str) -> dict:
    endpoint = (
        "https://xueshu.baidu.com/scholarai/paper/detail/info?paperId="
        + urllib.parse.quote(paper_id)
    )
    request = urllib.request.Request(
        endpoint,
        headers={
            "User-Agent": "Mozilla/5.0",
            "Accept": "application/json",
        },
    )
    with urllib.request.urlopen(request, timeout=20) as response:
        data = json.load(response)
    if not isinstance(data, dict):
        raise ValueError("Unexpected response shape from Baidu Scholar detail endpoint")
    return data.get("data", data)


def normalize(payload: dict, paper_id: str) -> dict:
    journal = ((payload.get("publish_info") or {}).get("journal") or {})
    authors = []
    for author in payload.get("authors") or []:
        name = (author or {}).get("name", "").strip()
        if name:
            authors.append(name)

    sources = []
    for source in payload.get("sources") or []:
        anchor = (source or {}).get("anchor", "").strip()
        url = (source or {}).get("url", "").strip()
        if url:
            sources.append({"anchor": anchor, "url": url})

    return {
        "paperId": paper_id,
        "title": payload.get("title", "").strip(),
        "authors": authors,
        "publishedYear": payload.get("published_year"),
        "journal": {
            "name": journal.get("journal_name", "").strip(),
            "volume": str(journal.get("journal_volume_no", "")).strip(),
            "issue": str(journal.get("journal_issue", "")).strip(),
            "pages": str(journal.get("journal_page_no", "")).strip(),
        },
        "doi": (payload.get("doi") or "").strip(),
        "sources": sources,
    }


def render_summary(detail: dict) -> str:
    journal = detail["journal"]
    parts = [
        f"title: {detail['title'] or '-'}",
        f"authors: {', '.join(detail['authors']) if detail['authors'] else '-'}",
        f"publishedYear: {detail['publishedYear'] or '-'}",
        f"journal: {journal['name'] or '-'}",
        f"volume: {journal['volume'] or '-'}",
        f"issue: {journal['issue'] or '-'}",
        f"pages: {journal['pages'] or '-'}",
        f"doi: {detail['doi'] or '-'}",
        "sources:",
    ]
    if detail["sources"]:
        for source in detail["sources"]:
            anchor = source["anchor"] or "source"
            parts.append(f"- {anchor}: {source['url']}")
    else:
        parts.append("- -")
    return "\n".join(parts)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Fetch Baidu Scholar detail metadata from a paperId or Baidu detail URL."
    )
    parser.add_argument("--paper-id", help="Baidu Scholar paperId")
    parser.add_argument("--url", help="Baidu Scholar detail page URL")
    parser.add_argument(
        "--format",
        choices=("summary", "json"),
        default="summary",
        help="Output format",
    )
    args = parser.parse_args()

    if not args.paper_id and not args.url:
        parser.error("Provide --paper-id or --url")

    try:
        paper_id = args.paper_id or extract_paper_id(args.url)
        detail = normalize(fetch_detail(paper_id), paper_id)
    except (ValueError, urllib.error.URLError, urllib.error.HTTPError, json.JSONDecodeError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    if args.format == "json":
        print(json.dumps(detail, ensure_ascii=False, indent=2))
    else:
        print(render_summary(detail))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
