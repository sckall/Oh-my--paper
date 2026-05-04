#!/usr/bin/env python3
"""Smoke test for openalex-explore."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


def main() -> int:
    query = sys.argv[1] if len(sys.argv) > 1 else "quantum computing"
    script = Path(__file__).with_name("openalex_search.py")
    result = subprocess.run(
        [sys.executable, str(script), query, "--per-page", "10"],
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
    candidates = payload.get("candidates", [])
    if len(candidates) < 5:
        print(f"expected >=5 candidates, got {len(candidates)}", file=sys.stderr)
        return 1
    bad = [
        c
        for c in candidates
        if (c.get("authority_metrics") or {}).get("source_type") in {"repository", "preprint server"}
    ]
    if bad:
        print(f"unexpected non-journal candidates: {bad[:2]}", file=sys.stderr)
        return 1
    print(f"PASS openalex-explore: {len(candidates)} candidates for {query!r}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
