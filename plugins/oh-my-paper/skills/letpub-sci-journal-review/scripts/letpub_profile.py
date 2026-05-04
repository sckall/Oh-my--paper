#!/usr/bin/env python3
"""
LetPub SCI Journal Profile Fetcher

Usage:
    python3 letpub_profile.py "Biology Teaching"
    python3 letpub_profile.py "1000-4018"              # ISSN
    python3 letpub_profile.py --id 8411                 # direct journalid
    python3 letpub_profile.py "生物学教学" --raw          # output raw HTML
    python3 letpub_profile.py "生物学教学" -o result.json

Claude Code agent should call this script instead of WebFetch/curl.
All HTTP via urllib.request (stdlib, zero deps).
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

from adapter_utils import request_text, source_evidence, utc_now, USER_AGENT

BASE_SEARCH = "https://letpub.com.cn/index.php?page=journalapp&view=search"
BASE_DETAIL = "https://letpub.com.cn/index.php?page=journalapp&view=detail"

LETPUB_UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"


def search_journal_id(name_or_issn: str) -> list[dict[str, str]]:
    """Search LetPub for journal ID(s) matching name or ISSN."""
    from urllib.parse import quote
    encoded = quote(name_or_issn, safe="")
    url = f"{BASE_SEARCH}&searchname={encoded}"
    html = request_text(url, headers={"User-Agent": LETPUB_UA}, timeout=15)

    # Extract journal entries: <a href="...&journalid=XXXXX">
    results = []
    # Pattern 1: detail link with journalid
    pattern = re.compile(
        r'<a[^>]*href="[^"]*journalid=(\d+)"[^>]*>([^<]+)</a>',
        re.IGNORECASE,
    )
    seen_ids = set()
    for match in pattern.finditer(html):
        jid = match.group(1)
        name = match.group(2).strip()
        if jid not in seen_ids and name:
            seen_ids.add(jid)
            results.append({"journalid": jid, "name": name})

    # Pattern 2: table rows with journal links
    if not results:
        row_pattern = re.compile(
            r'<tr[^>]*>.*?<a[^>]*href="[^"]*journalid=(\d+)"[^>]*>([^<]+)</a>.*?</tr>',
            re.DOTALL | re.IGNORECASE,
        )
        for match in row_pattern.finditer(html):
            jid = match.group(1)
            name = match.group(2).strip()
            if jid not in seen_ids and name:
                seen_ids.add(jid)
                results.append({"journalid": jid, "name": name})

    return results


def fetch_detail(journal_id: str) -> str:
    """Fetch LetPub detail page HTML."""
    url = f"{BASE_DETAIL}&journalid={journal_id}"
    return request_text(url, headers={"User-Agent": LETPUB_UA}, timeout=20)


def extract_fields(html: str) -> dict[str, Any]:
    """Extract structured fields from LetPub detail page HTML."""
    profile: dict[str, Any] = {
        "metadata": {},
        "identity": {},
        "authoritative": {},
        "cas_legacy": None,
        "cas_letpub": None,
        "community": {},
        "risk": {},
    }

    # --- Identity ---
    # Journal name from <title> tag (most reliable)
    title_match = re.search(r'<title>\s*【LetPub】\s*([A-Z][^<]+?)\s*影响因子', html)
    if title_match:
        profile["identity"]["journal_name"] = title_match.group(1).strip()
    else:
        # Fallback: second <h1> tag (first is hidden branding)
        h1_matches = re.findall(r'<h1[^>]*>([^<]+)</h1>', html)
        for h1_text in h1_matches:
            text = h1_text.strip()
            if len(text) > 5 and not re.search(r'hidden|display:none|ACCDON|哇咔', text, re.IGNORECASE):
                profile["identity"]["journal_name"] = text
                break

    # ISSN / eISSN
    for label, key in [("ISSN", "issn"), ("eISSN", "eissn")]:
        m = re.search(rf'{label}\s*[：:]\s*([0-9{{4}}]-[0-9{{3}}][0-9Xx])', html)
        if m:
            profile["identity"][key] = m.group(1)

    # --- Authoritative metrics ---
    # Impact Factor
    for pattern in [
        r'JCR[^<]*?IF[^<]*?(\d+\.\d+)',
        r'影响因子[^<]*?(\d+\.\d+)',
        r'Impact\s*Factor[^<]*?(\d+\.\d+)',
    ]:
        m = re.search(pattern, html, re.IGNORECASE)
        if m:
            profile["authoritative"]["impact_factor"] = float(m.group(1))
            break

    # 5-year IF
    m = re.search(r'5[年y]ear[^<]*?IF[^<]*?(\d+\.\d+)', html, re.IGNORECASE)
    if m:
        profile["authoritative"]["impact_factor_5yr"] = float(m.group(1))

    # JCR Quartile (WOS)
    m = re.search(r'(JCR[^\s]*?分区[^\s]*?)([Qq][1-4])', html)
    if m:
        profile["authoritative"]["wos_quartile"] = m.group(2).upper()

    # CiteScore
    m = re.search(r'CiteScore\s*[：:]*\s*(\d+\.\d+)', html, re.IGNORECASE)
    if m:
        profile["authoritative"]["citescore"] = float(m.group(1))

    # SJR
    m = re.search(r'SJR\s*[：:]*\s*(\d+\.\d+)', html, re.IGNORECASE)
    if m:
        profile["authoritative"]["sjr"] = float(m.group(1))

    # SNIP
    m = re.search(r'SNIP\s*[：:]*\s*(\d+\.\d+)', html, re.IGNORECASE)
    if m:
        profile["authoritative"]["snip"] = float(m.group(1))

    # h-index
    m = re.search(r'[Hh][- ]?[Ii]ndex\s*[：:]*\s*(\d+)', html)
    if m:
        profile["authoritative"]["h_index"] = int(m.group(1))

    # Open Access
    if re.search(r'Open\s*Access.*?Yes', html, re.IGNORECASE):
        profile["authoritative"]["open_access"] = "Yes"
    elif re.search(r'Open\s*Access.*?Hybrid', html, re.IGNORECASE):
        profile["authoritative"]["open_access"] = "Hybrid"
    elif re.search(r'Open\s*Access', html, re.IGNORECASE):
        profile["authoritative"]["open_access"] = "Yes"
    else:
        profile["authoritative"]["open_access"] = "No"

    # APC
    apc_match = re.search(r'APC\s*[：:]*\s*\$?([\d,]+\.?\d*)', html, re.IGNORECASE)
    if apc_match:
        profile["authoritative"]["apc"] = {"USD": float(apc_match.group(1).replace(",", ""))}

    # Publication frequency
    freq_match = re.search(r'出版频率[：:]*\s*([^<\s]+)', html)
    if freq_match:
        profile["authoritative"]["publication_freq"] = freq_match.group(1).strip()

    # Year first published
    year_match = re.search(r'创刊[年：:]*\s*(\d{4})', html)
    if year_match:
        profile["authoritative"]["year_first_pub"] = int(year_match.group(1))

    # Articles per year
    arts_match = re.search(r'年发文量[：:]*\s*(\d+)', html)
    if arts_match:
        profile["authoritative"]["articles_per_year"] = int(arts_match.group(1))

    # --- CAS partition ---
    # New锐 (LetPub) partition
    letpub_partition = re.search(r'《新锐期刊分区表》[》)]*[^\d]*?(\d{4})[^\d]*?([^\s<]{1,2}区)', html)
    if letpub_partition:
        profile["cas_letpub"] = {
            "release_year": letpub_partition.group(1),
            "partition": letpub_partition.group(2),
            "source": "LetPub 新锐期刊分区表",
        }

    # Legacy CAS partition
    legacy_match = re.search(r'期刊分区表[^\d]*?(\d{4})[^\d]*?[^\s<]{1,2}区', html)
    if legacy_match:
        profile["cas_legacy"] = {
            "frozen_year": legacy_match.group(1),
            "partition": legacy_match.group(2),
            "source": "中科院分区表（已冻结）",
        }

    # --- Community / user reviews ---
    # Review speed (from structured table data, not JS)
    speed_match = re.search(r'(?:审稿周期|平均审稿)[：:\s]*([^\s<]{3,30}?月?)(?:<|$)', html)
    if speed_match:
        val = speed_match.group(1).strip()
        if not val.startswith(('if', '$', '//', '{', 'function')):
            profile["community"]["review_speed_note"] = val

    # Acceptance rate
    accept_match = re.search(r'录用率[：:]*\s*([\d.]+)', html)
    if accept_match:
        profile["community"]["acceptance_rate_note"] = accept_match.group(1).strip()

    # LetPub score
    score_match = re.search(r'LetPub评分[：:]*\s*([\d.]+)', html)
    if score_match:
        profile["community"]["letpub_score"] = float(score_match.group(1))

    # User review count
    review_count_match = re.search(r'投稿经验[：:]*\s*(\d+)', html)
    if review_count_match:
        profile["community"]["user_review_count"] = int(review_count_match.group(1))

    # --- Risk / Warning ---
    if re.search(r'预警名单|warning\s*list', html, re.IGNORECASE):
        profile["risk"]["in_warning_list"] = True

    # SCI index status
    if re.search(r'SCIE.*?Active|检索状态.*?正常', html, re.IGNORECASE):
        profile["risk"]["sci_index_status"] = "Active"
    elif re.search(r'Under\s*Review', html, re.IGNORECASE):
        profile["risk"]["sci_index_status"] = "Under Review"
    elif re.search(r'Discontinued|已撤稿|停止检索', html, re.IGNORECASE):
        profile["risk"]["sci_index_status"] = "Discontinued"

    return profile


def main() -> None:
    parser = argparse.ArgumentParser(description="LetPub SCI Journal Profile Fetcher")
    parser.add_argument("query", nargs="?", default=None, help="Journal name or ISSN (optional with --id)")
    parser.add_argument("--id", dest="journal_id", help="Direct LetPub journal ID (skip search)")
    parser.add_argument("--raw", action="store_true", help="Output raw HTML instead of JSON")
    parser.add_argument("-o", "--output", help="Output JSON file path")
    parser.add_argument("--search-only", action="store_true", help="Only search, show matching journals")
    args = parser.parse_args()

    if args.journal_id:
        journal_id = args.journal_id
    else:
        # Step 1: Search
        print(f"Searching LetPub for: {args.query}", file=sys.stderr)
        matches = search_journal_id(args.query)

        if not matches:
            print(json.dumps({"error": "no_match", "query": args.query}, ensure_ascii=False))
            sys.exit(1)

        if args.search_only:
            print(json.dumps({"matches": matches}, ensure_ascii=False, indent=2))
            sys.exit(0)

        if len(matches) > 1:
            print(f"Found {len(matches)} matches, using first:", file=sys.stderr)
            for m in matches[:5]:
                print(f"  [{m['journalid']}] {m['name']}", file=sys.stderr)

        journal_id = matches[0]["journalid"]

    # Step 2: Fetch detail
    print(f"Fetching journal {journal_id}...", file=sys.stderr)
    html = fetch_detail(journal_id)

    if args.raw:
        print(html)
        sys.exit(0)

    # Step 3: Extract
    profile = extract_fields(html)
    profile["metadata"] = {
        "fetched_at": utc_now(),
        "tool_tier_used": "0",
        "source_url": f"{BASE_DETAIL}&journalid={journal_id}",
        "letpub_id": journal_id,
        "query": args.query,
    }
    profile["identity"]["letpub_id"] = journal_id
    profile["metadata"]["error_log"] = []
    profile["metadata"]["skill_version"] = "0.4.0"

    # Output
    text = json.dumps(profile, ensure_ascii=False, indent=2)
    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(text + "\n")
        print(f"Written to {args.output}", file=sys.stderr)
    else:
        print(text)


if __name__ == "__main__":
    main()
