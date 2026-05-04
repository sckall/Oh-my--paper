#!/usr/bin/env python3
"""Query ncpssd by subject and aggregate journal venues."""

from __future__ import annotations

import argparse
import base64
import html
import json
import re
import sys
import urllib.parse
import urllib.request
from collections import Counter
from pathlib import Path
from typing import Any


PLUGIN_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(PLUGIN_ROOT))

from _shared.adapter_utils import normalize_issn, normalize_journal_name, request_text, source_evidence  # noqa: E402


ENDPOINT = "https://www.ncpssd.cn/Literature/articlelist"
SEARCH_HANDLER = "https://www.ncpssd.cn/searchHandler/search"
JOURNAL_PATTERNS = [
    re.compile(r"(?:来源|刊名|期刊|source)[：:\s]*</?[^>]*>\s*([^<>\n]{2,80})", re.I),
    re.compile(r"《([^》]{2,60})》"),
]
ISSN_RE = re.compile(r"\b\d{4}-?\d{3}[\dXx]\b")


def build_search(subject: str) -> str:
    expr = f'(IKTE="{subject}" OR IKPYTE="{subject}" OR IKST="{subject}")'
    return base64.b64encode(expr.encode("gbk")).decode("ascii")


def build_expression(subject: str) -> str:
    return f'(IKTE="{subject}" OR IKPYTE="{subject}" OR IKST="{subject}")'


def extract_candidates(text: str, limit: int) -> list[dict[str, Any]]:
    clean = html.unescape(re.sub(r"\s+", " ", text))
    counter: Counter[str] = Counter()
    issns: dict[str, str] = {}
    for pattern in JOURNAL_PATTERNS:
        for match in pattern.findall(clean):
            title = normalize_journal_name(re.sub(r"<[^>]+>", "", match))
            if 2 <= len(title) <= 40:
                counter[title] += 1
    for title in list(counter):
        nearby = clean[max(clean.find(title) - 120, 0) : clean.find(title) + 160]
        issn_match = ISSN_RE.search(nearby)
        if issn_match:
            issns[title] = normalize_issn(issn_match.group(0)) or issn_match.group(0)
    return [
        {
            "title_cn": title,
            "issn": issns.get(title),
            "frequency": count,
            "fit_score": round(min(1.0, count / max(counter.values() or [1])), 3),
            "trust_level": "ncpssd-subject",
        }
        for title, count in counter.most_common(limit)
    ]


def fetch_search_rows(subject: str, limit: int) -> list[dict[str, Any]]:
    expression = build_expression(subject)
    body = urllib.parse.urlencode(
        {
            "search": expression,
            "pageNum": 1,
            "pageSize": max(limit, 10),
            "sort": "synUpdateType|DESC,date|DESC,ik_subject|DESC,id|DESC",
            "sType": 0,
        }
    ).encode("utf-8")
    request = urllib.request.Request(
        SEARCH_HANDLER,
        data=body,
        headers={
            "User-Agent": "journal-research-cn/0.1.0 Mozilla/5.0",
            "Referer": f"{ENDPOINT}?sType=0&search={build_search(subject)}",
            "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
            "X-Requested-With": "XMLHttpRequest",
            "Accept": "application/json",
        },
    )
    with urllib.request.urlopen(request, timeout=25) as response:
        payload = json.loads(response.read().decode("utf-8", errors="replace"))
    data = payload.get("data") if isinstance(payload, dict) else {}
    rows = data.get("rows") if isinstance(data, dict) else []
    return rows if isinstance(rows, list) else []


def extract_candidates_from_rows(rows: list[dict[str, Any]], limit: int) -> list[dict[str, Any]]:
    counter: Counter[str] = Counter()
    issns: dict[str, str] = {}
    for row in rows:
        title = normalize_journal_name(str(row.get("cbw_name") or row.get("source") or ""))
        if not (2 <= len(title) <= 40):
            continue
        counter[title] += 1
        issn = normalize_issn(str(row.get("issn") or ""))
        if issn:
            issns.setdefault(title, issn)
    max_count = max(counter.values() or [1])
    return [
        {
            "title_cn": title,
            "issn": issns.get(title),
            "frequency": count,
            "fit_score": round(min(1.0, count / max_count), 3),
            "trust_level": "ncpssd-subject",
        }
        for title, count in counter.most_common(limit)
    ]


def query_subject(subject: str, limit: int = 20) -> dict[str, Any]:
    search = build_search(subject)
    url = f"{ENDPOINT}?sType=0&search={search}"
    candidates: list[dict[str, Any]] = []
    html_text = request_text(
        ENDPOINT,
        params={"sType": 0, "search": search},
        headers={"Referer": "https://www.ncpssd.cn/journal/index?nav=1&langType=1"},
        timeout=25,
        retries=2,
    )
    candidates = extract_candidates(html_text, limit)
    if not candidates:
        rows = fetch_search_rows(subject, limit)
        candidates = extract_candidates_from_rows(rows, limit)
    return {
        "query": subject,
        "status": "ok" if candidates else "empty",
        "search_expression_gbk_base64": search,
        "search_expression": build_expression(subject),
        "candidate_count": len(candidates),
        "candidates": candidates,
        "evidence": [
            source_evidence("ncpssd-subject-query", url, "ncpssd-subject", tool_tier_used="2"),
            source_evidence("ncpssd-search-handler", SEARCH_HANDLER, "ncpssd-subject", tool_tier_used="2"),
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Query ncpssd subject tree/search for candidate journals.")
    parser.add_argument("subject", help="Subject name, e.g. 经济学")
    parser.add_argument("--limit", type=int, default=20)
    args = parser.parse_args()
    try:
        result = query_subject(args.subject, args.limit)
    except Exception as exc:
        print(json.dumps({"status": "error", "error": str(exc)}, ensure_ascii=False))
        return 1
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["candidate_count"] > 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
