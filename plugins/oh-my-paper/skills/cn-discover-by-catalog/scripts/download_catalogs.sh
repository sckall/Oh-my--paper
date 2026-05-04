#!/usr/bin/env bash
# Download public Chinese journal catalog PDFs used by cn-discover-by-catalog.

set -uo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DATA_DIR="$(cd "$SCRIPT_DIR/.." && pwd)/data/catalogs"
REF_DIR="$(cd "$SCRIPT_DIR/.." && pwd)/references"
mkdir -p "$DATA_DIR" "$REF_DIR"

UA="journal-research-cn/0.1.0 Mozilla/5.0"

download_pdf() {
  local name="$1"
  local url="$2"
  local out="$DATA_DIR/$name.pdf"
  echo "download: $name"
  if curl -fL --retry 2 --connect-timeout 15 --max-time 180 -A "$UA" "$url" -o "$out"; then
    local magic
    magic="$(file -b "$out" 2>/dev/null || true)"
    if echo "$magic" | grep -qi "PDF document"; then
      echo "PASS: $name -> $out ($magic)"
      return 0
    fi
    echo "WARN: $name downloaded but file magic is not PDF: $magic" >&2
    rm -f "$out"
    return 1
  fi
  echo "WARN: failed to download $name from $url" >&2
  rm -f "$out"
  return 1
}

download_cstpcd() {
  local page="https://kyc.gdhsc.edu.cn/info/1012/2962.htm"
  local html="$DATA_DIR/cstpcd-source.html"
  local discovered="$DATA_DIR/cstpcd-url.txt"
  local url=""
  echo "discover: cstpcd source page"
  if curl -fL --retry 2 --connect-timeout 15 --max-time 60 -A "$UA" "$page" -o "$html"; then
    python3 - "$html" "$page" > "$discovered" <<'PY'
import re
import sys
from urllib.parse import urljoin

html_path, base = sys.argv[1], sys.argv[2]
text = open(html_path, "rb").read().decode("utf-8", errors="ignore")
matches = re.findall(r'href=["\']([^"\']+\.pdf[^"\']*)["\']', text, re.I)
for match in matches:
    print(urljoin(base, match))
    break
PY
    url="$(head -n 1 "$discovered" 2>/dev/null || true)"
  fi
  if [ -n "$url" ]; then
    download_pdf "cstpcd-2024" "$url" && return 0
  fi
  cat > "$REF_DIR/cstpcd-mirrors.md" <<'EOF'
# CSTPCD Mirrors

Primary discovery page:

- https://kyc.gdhsc.edu.cn/info/1012/2962.htm

The CSTPCD PDF is less stable than PKU / CSSCI / CSCD public mirrors. PLAN-3 treats this table as best-effort: if the page stops exposing a direct PDF link, use easyScholar field `zhongguokejihexin` / `cstpcd` as the P0 fallback and schedule a P1 mirror patrol.
EOF
  echo "WARN: CSTPCD direct PDF not discovered. Wrote references/cstpcd-mirrors.md" >&2
  return 0
}

failures=0

download_pdf "pku-core-2023" "https://lib.hrbmu.edu.cn/zhongwenhexinqikanyaomuzonglan2023.pdf" || failures=$((failures + 1))
download_pdf "cssci-2023-2024" "https://statics.scnu.edu.cn/pics/lib/2025/1031/1761900032548492.pdf" || failures=$((failures + 1))
download_pdf "cscd-2023-2024" "https://lib.bjut.edu.cn/fj/hexinqikandaohang/CSCDlist2023-2024.pdf" || failures=$((failures + 1))
download_cstpcd || true

if [ "$failures" -gt 0 ]; then
  echo "WARN: $failures mandatory catalog download(s) failed. Re-run later or use local PDF mirrors." >&2
  exit 1
fi

echo "PASS: mandatory catalog downloads completed; CSTPCD is best-effort."
