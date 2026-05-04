#!/usr/bin/env python3
"""Smoke test for crossref-validator."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


def main() -> int:
    identifier = sys.argv[1] if len(sys.argv) > 1 else "0028-0836"
    script = Path(__file__).with_name("crossref_validate.py")
    result = subprocess.run(
        [sys.executable, str(script), identifier],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=60,
    )
    if result.returncode != 0:
        print(result.stderr, file=sys.stderr)
        print(result.stdout, file=sys.stderr)
        return result.returncode
    payload = json.loads(result.stdout)
    identity = payload["candidate"]["identity"]
    title = (identity.get("title") or "").lower()
    issns = {identity.get("issn"), identity.get("eissn")}
    if "nature" not in title:
        print(f"expected Nature metadata, got title={identity.get('title')!r}", file=sys.stderr)
        return 1
    if "0028-0836" not in issns:
        print(f"expected ISSN 0028-0836 in {issns}", file=sys.stderr)
        return 1
    print(f"PASS crossref-validator: {identity.get('title')} {sorted(v for v in issns if v)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
