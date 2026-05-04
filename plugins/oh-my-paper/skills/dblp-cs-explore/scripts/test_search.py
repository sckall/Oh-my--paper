#!/usr/bin/env python3
"""Smoke test for dblp-cs-explore."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


def main() -> int:
    query = sys.argv[1] if len(sys.argv) > 1 else "transactions pattern analysis"
    script = Path(__file__).with_name("dblp_search.py")
    result = subprocess.run(
        [sys.executable, str(script), query],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=90,
    )
    if result.returncode != 0:
        print(result.stderr, file=sys.stderr)
        print(result.stdout, file=sys.stderr)
        return result.returncode
    payload = json.loads(result.stdout)
    titles = [(c["identity"].get("title") or "").lower() for c in payload.get("candidates", [])]
    if not any("pattern analysis" in title or "tpami" in title for title in titles):
        print(f"expected TPAMI/PAMI candidate, got {titles}", file=sys.stderr)
        return 1
    print(f"PASS dblp-cs-explore: {payload['count']} candidates for {query!r}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
