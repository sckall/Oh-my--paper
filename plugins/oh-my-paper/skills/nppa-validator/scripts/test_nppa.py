#!/usr/bin/env python3
"""Smoke test for NPPA validator."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


SCRIPT = Path(__file__).with_name("nppa_validate.py")


def main() -> int:
    journal_name = sys.argv[1] if len(sys.argv) > 1 else "经济研究"
    result = subprocess.run(
        [sys.executable, str(SCRIPT), journal_name],
        check=False,
        capture_output=True,
        text=True,
        timeout=40,
    )
    print(result.stdout.strip())
    if result.returncode != 0:
        if result.stderr:
            print(result.stderr, file=sys.stderr)
        return result.returncode
    payload = json.loads(result.stdout)
    if payload.get("status") not in {"ok", "captcha_required"}:
        print(f"unexpected NPPA status: {payload.get('status')}", file=sys.stderr)
        return 1
    print(f"PASS: nppa status={payload['status']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
