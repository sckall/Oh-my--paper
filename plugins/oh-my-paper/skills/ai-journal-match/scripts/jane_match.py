#!/usr/bin/env python3
"""
JANE (Journal/Author Name Estimator) - AI Journal Matching

Usage:
    python3 jane_match.py "multimodal medical image segmentation"
    python3 jane_match.py "LLM RAG" --count 20
    python3 jane_match.py "deep learning" -o matches.json

JANE API: https://jane.biosemantics.org/
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
from urllib.parse import quote

# Add _shared to path
_SCRIPT_DIR = Path(__file__).resolve().parent
_PLUGIN_DIR = _SCRIPT_DIR.parent.parent.parent
_SHARED_DIR = _PLUGIN_DIR / "_shared"
_JOURNAL_DIR = _SHARED_DIR / "journal"
for p in (_SHARED_DIR, _JOURNAL_DIR):
    sp = str(p)
    if sp not in sys.path:
        sys.path.insert(0, sp)

from adapter_utils import request_text, source_evidence, utc_now

JANE_URL = "https://jane.biosemantics.org/jsearch/"
JANE_UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"


def search_jane(query: str, count: int = 10) -> dict[str, Any]:
    """Search JANE for journal matching."""
    params = {
        "query": query,
        "count": count,
    }
    encoded = "&".join(f"{k}={quote(str(v))}" for k, v in params.items())
    url = f"{JANE_URL}?{encoded}"

    html = request_text(url, headers={"User-Agent": JANE_UA}, timeout=30)

    # Parse JANE results
    results = []

    # JANE returns results in a table or list format
    # Extract journal names, scores, and confidence levels
    # Pattern: journal name + article count + confidence
    journal_pattern = re.compile(
        r'<a[^>]*href="[^"]*journal[^"]*"[^>]*>([^<]+)</a>',
        re.IGNORECASE,
    )
    names = journal_pattern.findall(html)

    # Also try to find confidence percentages
    conf_pattern = re.compile(r'(\d+(?:\.\d+)?)\s*%')

    # Try to find a structured results table
    rows = re.findall(r'<tr[^>]*>(.*?)</tr>', html, re.DOTALL)
    for row in rows[1:count + 1]:  # Skip header
        cells = re.findall(r'<t[dh][^>]*>(.*?)</t[dh]>', row, re.DOTALL)
        clean_cells = [re.sub(r'<[^>]+>', '', c).strip() for c in cells]
        clean_cells = [c for c in clean_cells if c]

        if len(clean_cells) >= 2:
            journal_name = clean_cells[0]
            # Skip non-journal rows
            if any(kw in journal_name.lower() for kw in ['result', 'search', 'jane', 'total']):
                continue
            result = {"name": journal_name}
            if len(clean_cells) >= 2:
                result["articles"] = clean_cells[1]
            if len(clean_cells) >= 3:
                result["confidence"] = clean_cells[2]
            results.append(result)

    # Fallback: if no table parsed, use the link list
    if not results and names:
        confs = conf_pattern.findall(html[:len(html) // 2])
        for i, name in enumerate(names[:count]):
            result = {"name": name.strip()}
            if i < len(confs):
                result["confidence"] = confs[i] + "%"
            results.append(result)

    return {
        "source": "jane",
        "query": query,
        "total_returned": len(results),
        "results": results,
        "metadata": {
            "fetched_at": utc_now(),
            "tool_tier_used": "0",
            "source_url": url,
            "trust_level": "ai-suggestion",
            "skill_version": "0.4.0",
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="JANE AI Journal Matching")
    parser.add_argument("query", help="Research topic or paper abstract text")
    parser.add_argument("--count", type=int, default=10, help="Number of results (default: 10)")
    parser.add_argument("-o", "--output", help="Output JSON file path")
    args = parser.parse_args()

    print(f"Searching JANE for: {args.query}", file=sys.stderr)
    data = search_jane(args.query, args.count)

    text = json.dumps(data, ensure_ascii=False, indent=2)
    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(text + "\n")
        print(f"Written to {args.output}", file=sys.stderr)
    else:
        print(text)


if __name__ == "__main__":
    main()
