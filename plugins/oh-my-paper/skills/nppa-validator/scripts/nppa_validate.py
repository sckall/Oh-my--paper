#!/usr/bin/env python3
"""Validate Chinese journal publication identity through NPPA public pages."""

from __future__ import annotations

import argparse
import html
import json
import re
import sys
from pathlib import Path
from typing import Any


PLUGIN_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(PLUGIN_ROOT))

from _shared.adapter_utils import request_text, source_evidence, utc_now  # noqa: E402


ENDPOINT = "https://www.nppa.gov.cn/bsfw/jggs/cbwzy/"
CAPTCHA_MARKERS = ("验证码", "安全验证", "滑块", "captcha", "访问过于频繁")


def strip_tags(text: str) -> str:
    text = re.sub(r"(?is)<script.*?</script>", " ", text)
    text = re.sub(r"(?is)<style.*?</style>", " ", text)
    text = re.sub(r"<[^>]+>", " ", text)
    return re.sub(r"\s+", " ", html.unescape(text)).strip()


def extract_fields(text: str, journal_name: str) -> dict[str, Any]:
    clean = strip_tags(text)
    if journal_name not in clean:
        return {}
    window_start = max(clean.find(journal_name) - 160, 0)
    window = clean[window_start : clean.find(journal_name) + 700]
    cn_match = re.search(r"CN\s*[\d]{2}-[\d]{3,5}/?[A-Z0-9]*", window, re.I)
    issn_match = re.search(r"\b\d{4}-?\d{3}[\dXx]\b", window)
    fields = {
        "title_cn": journal_name,
        "cn_number": cn_match.group(0).upper().replace(" ", "") if cn_match else None,
        "issn": issn_match.group(0).upper() if issn_match else None,
        "raw_window": window,
    }
    for label, key in (("主管单位", "supervising_org"), ("主办单位", "host_org"), ("出版单位", "publisher"), ("类别", "category")):
        match = re.search(label + r"\s*[:：]?\s*([^:：]{2,80})", window)
        if match:
            fields[key] = match.group(1).strip()
    return fields


def validate(journal_name: str) -> dict[str, Any]:
    url = ENDPOINT
    try:
        text = request_text(
            ENDPOINT,
            params={"word": journal_name},
            headers={"Referer": "https://www.nppa.gov.cn/"},
            timeout=25,
            retries=2,
        )
    except Exception as exc:
        return {
            "query": journal_name,
            "status": "captcha_required",
            "reason": f"official page could not be fetched automatically: {exc}",
            "manual_url": url,
            "fetched_at": utc_now(),
            "evidence": [source_evidence("nppa-publication-query", url, "official-cn", tool_tier_used="2")],
        }
    lowered = text.lower()
    if any(marker.lower() in lowered for marker in CAPTCHA_MARKERS):
        return {
            "query": journal_name,
            "status": "captcha_required",
            "manual_url": url,
            "fetched_at": utc_now(),
            "evidence": [source_evidence("nppa-publication-query", url, "official-cn", tool_tier_used="2")],
        }
    fields = extract_fields(text, journal_name)
    if fields:
        return {
            "query": journal_name,
            "status": "ok",
            "official_identity": fields,
            "manual_url": url,
            "fetched_at": utc_now(),
            "evidence": [source_evidence("nppa-publication-query", url, "official-cn", tool_tier_used="2")],
        }
    return {
        "query": journal_name,
        "status": "captcha_required",
        "reason": "NPPA page is reachable but no parseable result block was found; use manual official query.",
        "manual_url": url,
        "fetched_at": utc_now(),
        "evidence": [source_evidence("nppa-publication-query", url, "official-cn", tool_tier_used="2")],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate Chinese publication identity through NPPA.")
    parser.add_argument("journal_name")
    args = parser.parse_args()
    payload = validate(args.journal_name)
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0 if payload.get("status") in {"ok", "captcha_required"} else 1


if __name__ == "__main__":
    raise SystemExit(main())
