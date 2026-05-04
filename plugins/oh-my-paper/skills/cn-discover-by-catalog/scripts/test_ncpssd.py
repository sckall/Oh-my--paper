#!/usr/bin/env python3
"""Smoke test for ncpssd subject query."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


SCRIPT = Path(__file__).with_name("ncpssd_subject_query.py")


def main() -> int:
    subject = sys.argv[1] if len(sys.argv) > 1 else "经济学"
    result = subprocess.run(
        [sys.executable, str(SCRIPT), subject, "--limit", "10"],
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
    if not payload.get("candidates"):
        print("ncpssd returned no candidate journals", file=sys.stderr)
        return 1
    print(f"PASS: ncpssd returned {len(payload['candidates'])} candidate journals")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
