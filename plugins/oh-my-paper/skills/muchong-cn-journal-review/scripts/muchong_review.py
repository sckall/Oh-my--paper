#!/usr/bin/env python3
"""
Muchong (小木虫) Chinese Journal Review Fetcher

Usage:
    python3 muchong_review.py "1000-4018"           # ISSN (recommended)
    python3 muchong_review.py "生物学教学"            # journal name
    python3 muchong_review.py "1000-4018" -o review.json

All HTTP via urllib.request (stdlib, zero deps).
GBK encoding handled automatically.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import time
from pathlib import Path
from typing import Any

# Add _shared to path: scripts/ → skill/ → skills/ → plugin/
_SCRIPT_DIR = Path(__file__).resolve().parent
_PLUGIN_DIR = _SCRIPT_DIR.parent.parent.parent
_SHARED_DIR = _PLUGIN_DIR / "_shared"
_JOURNAL_DIR = _SHARED_DIR / "journal"
for p in (_SHARED_DIR, _JOURNAL_DIR):
    sp = str(p)
    if sp not in sys.path:
        sys.path.insert(0, sp)

from adapter_utils import request_bytes, source_evidence, utc_now, normalize_issn

MUCHONG_UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
BASE_URL = "https://muchong.com/bbs/journal.php"


def decode_gbk(data: bytes) -> str:
    """Decode GBK/GB2312/GB18030 encoded bytes."""
    for enc in ("gb18030", "gbk", "gb2312"):
        try:
            return data.decode(enc)
        except (UnicodeDecodeError, LookupError):
            continue
    return data.decode("utf-8", errors="replace")


def fetch_journal_page(issn: str) -> tuple[str, str]:
    """Fetch muchong journal page by ISSN. Returns (url, html)."""
    url = f"{BASE_URL}?id={issn}"
    raw = request_bytes(url, headers={"User-Agent": MUCHONG_UA}, timeout=15)
    html = decode_gbk(raw)
    return url, html


def search_journal(name: str) -> list[dict[str, str]]:
    """Search muchong by journal name. Returns list of {issn, name}."""
    # Muchong doesn't have a clean search API; use Google-like approach
    # Try fetching the journal page directly with URL-encoded name
    from urllib.parse import quote
    url = f"{BASE_URL}?id={quote(name)}"
    raw = request_bytes(url, headers={"User-Agent": MUCHONG_UA}, timeout=15)
    html = decode_gbk(raw)

    # Try to extract ISSN from the page
    issn_match = re.search(r'(\d{{4}}-\d{{3}}[\dXx])', html)
    if issn_match:
        return [{"issn": issn_match.group(1), "name": name}]

    # Check if we got a valid journal page
    if "投稿经验" in html or "审稿周期" in html:
        return [{"issn": name, "name": name, "note": "ISSN not found on page"}]

    return []


def extract_reviews(html: str) -> dict[str, Any]:
    """Extract review data from muchong journal page."""
    result: dict[str, Any] = {
        "basic_info": {},
        "review_intel": {},
        "reviews": [],
    }

    # Basic info
    # Journal name
    title_match = re.search(r'<title>([^<]+)</title>', html)
    if title_match:
        result["basic_info"]["page_title"] = title_match.group(1).strip()

    # ISSN
    issn_match = re.search(r'(\d{4}-\d{3}[\dXx])', html)
    if issn_match:
        result["basic_info"]["issn"] = normalize_issn(issn_match.group(1))

    # Review speed / 审稿周期
    speed_patterns = [
        r'审稿周期[：:\s]*([^\s<]{2,30})',
        r'审稿速度[：:\s]*([^\s<]{2,30})',
        r'平均审稿[时间周期]*[：:\s]*([^\s<]{2,30})',
    ]
    for pat in speed_patterns:
        m = re.search(pat, html)
        if m:
            val = m.group(1).strip()
            if len(val) > 2 and not val.startswith(('if', '$', '//', '{', '<')):
                result["review_intel"]["review_speed_note"] = val
                break

    # Acceptance rate / 录用率
    accept_match = re.search(r'录用[率情况]*[：:\s]*([^\s<]{2,20}?)', html)
    if accept_match:
        val = accept_match.group(1).strip()
        if len(val) > 1:
            result["review_intel"]["acceptance_note"] = val

    # Page charges / 版面费
    charge_match = re.search(r'版面费[：:\s]*([^\s<]{2,30})', html)
    if charge_match:
        val = charge_match.group(1).strip()
        if len(val) > 1:
            result["review_intel"]["page_charge_note"] = val

    # Review count
    count_match = re.search(r'(\d+)\s*篇投稿经验', html)
    if count_match:
        result["review_intel"]["total_reviews"] = int(count_match.group(1))

    # Extract individual reviews
    # Pattern: review blocks with date, direction, cycle
    review_blocks = re.findall(
        r'<div[^>]*class="[^"]*review[^"]*"[^>]*>(.*?)</div>',
        html, re.DOTALL | re.IGNORECASE
    )
    if not review_blocks:
        # Alternative: look for table rows or list items
        review_blocks = re.findall(
            r'<tr[^>]*>(.*?)</tr>',
            html, re.DOTALL
        )

    extracted_count = 0
    for block in review_blocks[:10]:
        review: dict[str, str] = {}

        # Date
        date_match = re.search(r'(\d{4}[-/]\d{1,2}[-/]\d{1,2})', block)
        if date_match:
            review["date"] = date_match.group(1)

        # Research direction
        dir_match = re.search(r'研究方向[：:\s]*([^\s<]{2,50})', block)
        if dir_match:
            review["research_dir"] = dir_match.group(1).strip()

        # Review cycle
        cycle_match = re.search(r'(\d+\.?\d*)\s*个月', block)
        if cycle_match:
            review["cycle_months"] = float(cycle_match.group(1))

        # Decision
        for kw, key in [("录用", "decision"), ("退稿", "decision"), ("修改", "decision")]:
            if kw in block:
                review["decision"] = kw
                break

        if review.get("date") or review.get("cycle_months"):
            result["reviews"].append(review)
            extracted_count += 1

    return result


def main() -> None:
    parser = argparse.ArgumentParser(description="Muchong Chinese Journal Review Fetcher")
    parser.add_argument("query", help="ISSN or journal name")
    parser.add_argument("-o", "--output", help="Output JSON file path")
    parser.add_argument("--raw", action="store_true", help="Output raw HTML")
    args = parser.parse_args()

    # Determine if input is ISSN
    is_issn = bool(re.match(r'^\d{4}-?\d{3}[\dXx]$', args.query.replace("-", "").strip()))
    normalized = normalize_issn(args.query) if is_issn else args.query.strip()

    if is_issn:
        print(f"Fetching muchong page for ISSN: {normalized}", file=sys.stderr)
        url, html = fetch_journal_page(normalized)
    else:
        print(f"Searching muchong for: {args.query}", file=sys.stderr)
        matches = search_journal(args.query)
        if not matches:
            print(json.dumps({"error": "no_match", "query": args.query}, ensure_ascii=False))
            sys.exit(1)

        normalized = normalize_issn(matches[0].get("issn", args.query))
        url, html = fetch_journal_page(normalized)

    if args.raw:
        print(html)
        sys.exit(0)

    # Check if page is valid
    if len(html) < 1000 or "404" in html[:500]:
        print(json.dumps({"error": "page_not_found", "issn": normalized, "url": url}, ensure_ascii=False))
        sys.exit(1)

    # Extract
    data = extract_reviews(html)
    data["metadata"] = {
        "fetched_at": utc_now(),
        "tool_tier_used": "0",
        "source_url": url,
        "issn": normalized,
        "query": args.query,
        "trust_level": "community",
        "skill_version": "0.4.0",
    }

    # Output
    text = json.dumps(data, ensure_ascii=False, indent=2)
    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(text + "\n")
        print(f"Written to {args.output}", file=sys.stderr)
    else:
        print(text)


if __name__ == "__main__":
    main()
