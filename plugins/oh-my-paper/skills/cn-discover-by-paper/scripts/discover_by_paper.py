#!/usr/bin/env python3
"""Discover candidate Chinese journals from Baidu Scholar paper search results."""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
import time
from collections import Counter
from pathlib import Path
from typing import Any


PLUGIN_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(PLUGIN_ROOT))

from _shared.adapter_utils import candidate_journal, normalize_journal_name, source_evidence  # noqa: E402


SCRIPT_DIR = Path(__file__).resolve().parent
BAIDU_SEARCH = SCRIPT_DIR / "baidu_search.sh"
BAIDU_DETAIL = SCRIPT_DIR / "fetch_baidu_detail.py"
EASYSCHOLAR = PLUGIN_ROOT / "skills" / "easyscholar-rank" / "scripts" / "easyscholar_rank.py"


def extract_paper_ids(payload: Any, limit: int) -> list[str]:
    text = json.dumps(payload, ensure_ascii=False)
    ids: list[str] = []
    for key in ("paperId", "paperid", "paper_id"):
        for match in re.findall(rf'"{key}"\s*:\s*"([^"]+)"', text):
            if match not in ids:
                ids.append(match)
            if len(ids) >= limit:
                return ids
    for match in re.findall(r"[?&]paperid=([A-Za-z0-9_-]+)", text, re.I):
        if match not in ids:
            ids.append(match)
        if len(ids) >= limit:
            return ids
    return ids


def search_papers(query: str, limit: int) -> tuple[list[str], dict[str, Any]]:
    result = subprocess.run(
        ["bash", str(BAIDU_SEARCH), query, "0", "false"],
        check=False,
        capture_output=True,
        text=True,
        timeout=45,
    )
    if result.returncode != 0:
        raise RuntimeError(result.stdout.strip() or result.stderr.strip() or "baidu_search failed")
    try:
        payload = json.loads(result.stdout)
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"Baidu Scholar search returned invalid JSON: {result.stdout[:300]}") from exc
    return extract_paper_ids(payload, limit), payload


def fetch_detail(paper_id: str) -> dict[str, Any] | None:
    result = subprocess.run(
        [sys.executable, str(BAIDU_DETAIL), "--paper-id", paper_id, "--format", "json"],
        check=False,
        capture_output=True,
        text=True,
        timeout=35,
    )
    if result.returncode != 0:
        return None
    try:
        return json.loads(result.stdout)
    except json.JSONDecodeError:
        return None


def venue_from_detail(detail: dict[str, Any]) -> str | None:
    journal = (detail.get("journal") or {}).get("name")
    if journal:
        return normalize_journal_name(journal)
    for source in detail.get("sources") or []:
        anchor = normalize_journal_name((source or {}).get("anchor"))
        if 2 <= len(anchor) <= 40 and not anchor.startswith("http"):
            return anchor
    return None


def rank_profile(title_cn: str) -> dict[str, Any]:
    result = subprocess.run(
        [sys.executable, str(EASYSCHOLAR), title_cn],
        check=False,
        capture_output=True,
        text=True,
        timeout=35,
    )
    if result.returncode != 0:
        return {"status": "unavailable", "error": result.stdout.strip() or result.stderr.strip()}
    try:
        payload = json.loads(result.stdout)
    except json.JSONDecodeError:
        return {"status": "unavailable", "error": "invalid easyScholar JSON"}
    return payload.get("rank_profile") or {}


def discover(query: str, *, limit: int, paper_limit: int) -> dict[str, Any]:
    paper_ids, search_payload = search_papers(query, paper_limit)
    counter: Counter[str] = Counter()
    paper_evidence: dict[str, list[str]] = {}
    for paper_id in paper_ids:
        detail = fetch_detail(paper_id)
        time.sleep(1.0)
        if not detail:
            continue
        venue = venue_from_detail(detail)
        if not venue:
            continue
        counter[venue] += 1
        paper_evidence.setdefault(venue, []).append(paper_id)
    candidates = []
    for title, count in counter.most_common(limit):
        profile = rank_profile(title)
        candidates.append(
            candidate_journal(
                title,
                fit_score=round(min(1.0, count / max(counter.values() or [1])), 3),
                rank_profile=profile,
                evidence=[
                    source_evidence("baidu-scholar-search", None, "baidu-scholar", tool_tier_used="2"),
                    source_evidence("baidu-scholar-detail", None, "baidu-scholar", tool_tier_used="2"),
                ],
                trust_level="paper-reverse-cn",
            )
        )
        candidates[-1]["supporting_paper_ids"] = paper_evidence.get(title, [])
    return {
        "query": query,
        "status": "ok" if candidates else "empty",
        "path": "B/baidu-paper-reverse",
        "searched_paper_count": len(paper_ids),
        "candidate_count": len(candidates),
        "candidates": candidates,
        "raw_search_keys": sorted(search_payload.keys()) if isinstance(search_payload, dict) else [],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Discover Chinese journals by Baidu Scholar paper reverse lookup.")
    parser.add_argument("query", help="Research direction or topic")
    parser.add_argument("--limit", type=int, default=10)
    parser.add_argument("--paper-limit", type=int, default=30)
    args = parser.parse_args()
    try:
        payload = discover(args.query, limit=args.limit, paper_limit=args.paper_limit)
    except Exception as exc:
        print(json.dumps({"status": "error", "error": str(exc)}, ensure_ascii=False))
        return 1
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0 if payload.get("candidate_count") else 1


if __name__ == "__main__":
    raise SystemExit(main())
