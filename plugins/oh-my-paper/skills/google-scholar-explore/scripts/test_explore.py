#!/usr/bin/env python3
"""Smoke test for google-scholar-explore."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


def main() -> int:
    query = sys.argv[1] if len(sys.argv) > 1 else "diffusion model image generation"
    script = Path(__file__).with_name("gs_explore.py")
    result = subprocess.run(
        [sys.executable, str(script), query, "--limit", "10", "--top", "5"],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=150,
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
    print(f"PASS google-scholar-explore: {len(candidates)} candidates for {query!r}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
