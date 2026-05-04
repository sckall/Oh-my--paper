#!/usr/bin/env python3
"""Smoke test for easyScholar rank adapter."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


SCRIPT = Path(__file__).with_name("easyscholar_rank.py")


def main() -> int:
    journal_name = sys.argv[1] if len(sys.argv) > 1 else "经济研究"
    result = subprocess.run(
        [sys.executable, str(SCRIPT), journal_name],
        check=False,
        capture_output=True,
        text=True,
        timeout=30,
    )
    print(result.stdout.strip())
    if result.returncode != 0:
        if result.stderr:
            print(result.stderr, file=sys.stderr)
        return result.returncode
    payload = json.loads(result.stdout)
    rank_profile = payload.get("rank_profile") or {}
    official_rank = rank_profile.get("officialRank") or {}
    haystack = json.dumps(official_rank, ensure_ascii=False).lower()
    missing = [name for name in ("cssci", "pku") if name not in haystack]
    if missing:
        print(f"missing expected fields in officialRank.all/select: {', '.join(missing)}", file=sys.stderr)
        return 1
    print("PASS: easyScholar code=200 and officialRank contains cssci+pku")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
