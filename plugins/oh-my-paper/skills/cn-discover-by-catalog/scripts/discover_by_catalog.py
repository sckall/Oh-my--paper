#!/usr/bin/env python3
"""Discover Chinese candidate journals by catalog labels and ncpssd subject recall."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path


PLUGIN_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(PLUGIN_ROOT))

from _shared.adapter_utils import candidate_journal, normalize_journal_name, source_evidence  # noqa: E402


DATA_DIR = Path(__file__).resolve().parents[1] / "data" / "catalogs"


def load_catalogs() -> list[dict]:
    path = DATA_DIR / "merged.json"
    if not path.exists():
        return []
    return json.loads(path.read_text(encoding="utf-8"))


def catalog_candidates(subject: str, limit: int) -> list[dict]:
    subject_key = normalize_journal_name(subject)
    results: list[dict] = []
    for item in load_catalogs():
        haystack = normalize_journal_name(" ".join(item.get("subjects") or []) + item.get("title_cn", ""))
        if subject_key and subject_key not in haystack:
            continue
        results.append(
            candidate_journal(
                item["title_cn"],
                issn=item.get("issn"),
                catalog_labels=item.get("catalog_labels") or [],
                fit_score=0.75,
                evidence=item.get("evidence") or [],
                trust_level="catalog-cn",
            )
        )
        if len(results) >= limit:
            break
    return results


def ncpssd_candidates(subject: str, limit: int) -> list[dict]:
    script = Path(__file__).with_name("ncpssd_subject_query.py")
    result = subprocess.run(
        [sys.executable, str(script), subject, "--limit", str(limit)],
        check=False,
        capture_output=True,
        text=True,
        timeout=45,
    )
    if result.returncode != 0:
        return []
    payload = json.loads(result.stdout)
    candidates = []
    for item in payload.get("candidates") or []:
        candidates.append(
            candidate_journal(
                item["title_cn"],
                issn=item.get("issn"),
                fit_score=item.get("fit_score"),
                evidence=[source_evidence("ncpssd-subject-query", None, "ncpssd-subject", tool_tier_used="2")],
                trust_level="catalog-cn",
            )
        )
    return candidates


def merge_candidates(primary: list[dict], secondary: list[dict], limit: int) -> list[dict]:
    seen: set[str] = set()
    merged: list[dict] = []
    for item in primary + secondary:
        title = item.get("identity", {}).get("title_cn") or ""
        key = normalize_journal_name(title)
        if not key or key in seen:
            continue
        seen.add(key)
        merged.append(item)
        if len(merged) >= limit:
            break
    return merged


def main() -> int:
    parser = argparse.ArgumentParser(description="Discover Chinese journals by subject/catalog.")
    parser.add_argument("subject")
    parser.add_argument("--limit", type=int, default=20)
    args = parser.parse_args()
    catalog = catalog_candidates(args.subject, args.limit)
    expanded = ncpssd_candidates(args.subject, args.limit)
    candidates = merge_candidates(catalog, expanded, args.limit)
    payload = {
        "query": args.subject,
        "status": "ok" if candidates else "empty",
        "candidate_count": len(candidates),
        "path": "A/catalog+ncpssd",
        "candidates": candidates,
    }
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0 if candidates else 1


if __name__ == "__main__":
    raise SystemExit(main())
