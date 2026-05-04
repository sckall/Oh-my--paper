#!/usr/bin/env python3
"""Smoke test for bison-oa-explore."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


def main() -> int:
    title = sys.argv[1] if len(sys.argv) > 1 else "transformer attention is all you need"
    abstract = sys.argv[2] if len(sys.argv) > 2 else "A new simple network architecture based solely on attention mechanisms for sequence transduction tasks."
    script = Path(__file__).with_name("bison_search.py")
    result = subprocess.run(
        [sys.executable, str(script), title, abstract, "--limit", "10"],
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
    if len(candidates) < 3:
        print(f"expected >=3 OA candidates, got {len(candidates)}", file=sys.stderr)
        return 1
    print(f"PASS bison-oa-explore: {len(candidates)} candidates for {title!r}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
