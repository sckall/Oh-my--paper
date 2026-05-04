#!/usr/bin/env python3
"""Fetch easyScholar publication rank data for a Chinese journal."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


PLUGIN_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(PLUGIN_ROOT))

from _shared.adapter_utils import (  # noqa: E402
    TokenBucket,
    read_key,
    request_json,
    source_evidence,
    utc_now,
)


ENDPOINT = "https://www.easyscholar.cc/open/getPublicationRank"
BUCKET = TokenBucket(rate_per_second=2.0, capacity=2)


FIELD_ALIASES = {
    "pku": ["pku", "北大核心", "北京大学核心"],
    "cssci": ["cssci", "南大核心", "南京大学核心"],
    "cscd": ["cscd", "中国科学引文数据库"],
    "cstpcd": ["cstpcd", "中国科技核心", "科技核心"],
    "ami": ["ami", "人大复印", "a刊"],
    "fms": ["fms", "管理科学高质量期刊"],
}


def flatten_keys(value: Any, prefix: str = "") -> dict[str, Any]:
    flat: dict[str, Any] = {}
    if isinstance(value, dict):
        for key, item in value.items():
            child = f"{prefix}.{key}" if prefix else str(key)
            flat[child] = item
            flat.update(flatten_keys(item, child))
    elif isinstance(value, list):
        for index, item in enumerate(value):
            child = f"{prefix}[{index}]"
            flat[child] = item
            flat.update(flatten_keys(item, child))
    return flat


def collect_labels(official_rank: dict[str, Any]) -> dict[str, Any]:
    flat = flatten_keys(official_rank)
    labels: dict[str, Any] = {}
    joined = json.dumps(official_rank, ensure_ascii=False).lower()
    for canonical, aliases in FIELD_ALIASES.items():
        labels[canonical] = any(alias.lower() in joined for alias in aliases)
    return {
        "field_count": len(flat),
        "labels": labels,
        "flat_keys": sorted(flat.keys())[:120],
    }


def fetch_rank(publication_name: str, secret_key: str) -> dict[str, Any]:
    BUCKET.wait()
    return request_json(
        ENDPOINT,
        params={
            "secretKey": secret_key,
            "publicationName": publication_name,
        },
        headers={"Accept": "application/json"},
        timeout=20,
        retries=2,
    )


def normalize_response(publication_name: str, payload: dict[str, Any]) -> dict[str, Any]:
    data = payload.get("data") if isinstance(payload.get("data"), dict) else {}
    official_rank = data.get("officialRank") if isinstance(data.get("officialRank"), dict) else {}
    custom_rank = data.get("customRank") if isinstance(data.get("customRank"), dict) else data.get("customRank")
    diagnostics = collect_labels(official_rank)
    return {
        "query": publication_name,
        "status": "ok" if payload.get("code") == 200 else "error",
        "code": payload.get("code"),
        "msg": payload.get("msg"),
        "fetched_at": utc_now(),
        "rank_profile": {
            "customRank": custom_rank,
            "officialRank": official_rank,
            "field_count": diagnostics["field_count"],
            "catalog_labels_detected": diagnostics["labels"],
        },
        "diagnostics": {
            "official_rank_flat_keys_sample": diagnostics["flat_keys"],
        },
        "raw": payload,
        "evidence": [
            source_evidence(
                "easyscholar-open-api",
                ENDPOINT,
                "rank-cn",
                tool_tier_used="2",
            )
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Fetch easyScholar rank profile by journal name.")
    parser.add_argument("publication_name", help="Chinese or English journal name")
    parser.add_argument("--raw", action="store_true", help="Print raw API payload only")
    args = parser.parse_args()

    key = read_key("EASYSCHOLAR_SECRET_KEY", "easyscholar")
    if not key:
        print(
            json.dumps(
                {
                    "status": "blocked",
                    "error": "missing EASYSCHOLAR_SECRET_KEY; set env or Keychain service easyscholar",
                },
                ensure_ascii=False,
            )
        )
        return 2

    try:
        payload = fetch_rank(args.publication_name, key)
    except Exception as exc:
        print(json.dumps({"status": "error", "error": str(exc)}, ensure_ascii=False))
        return 1

    if args.raw:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        print(json.dumps(normalize_response(args.publication_name, payload), ensure_ascii=False, indent=2))
    return 0 if payload.get("code") == 200 else 1


if __name__ == "__main__":
    raise SystemExit(main())
