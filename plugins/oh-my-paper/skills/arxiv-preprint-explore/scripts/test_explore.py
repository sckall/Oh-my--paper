#!/usr/bin/env python3
"""Smoke test for arxiv-preprint-explore."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


def main() -> int:
    query = sys.argv[1] if len(sys.argv) > 1 else "cs.LG"
    max_results = sys.argv[2] if len(sys.argv) > 2 else "5"
    script = Path(__file__).with_name("arxiv_explore.py")
    result = subprocess.run(
        [sys.executable, str(script), query, max_results],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=120,
    )
    if result.returncode != 0:
        print(result.stderr, file=sys.stderr)
        print(result.stdout, file=sys.stderr)
        return result.returncode
    payload = json.loads(result.stdout)
    candidates = payload.get("candidates", [])
    if len(candidates) < 3:
        print(f"expected >=3 candidates, got {len(candidates)}", file=sys.stderr)
        return 1
    print(f"PASS arxiv-preprint-explore: {len(candidates)} candidates for {query!r}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
