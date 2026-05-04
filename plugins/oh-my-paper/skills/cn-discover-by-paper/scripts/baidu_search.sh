#!/bin/bash
#
# Copied from plugins/academic-suite/skills/scholar-search/scripts/baidu_search.sh
# for journal-research-cn on 2026-04-29. This copy is intentionally physical
# so the Chinese journal plugin has no runtime dependency on academic-suite.
#
# Usage: bash baidu_search.sh "keyword" [page_number] [include_abstract]
# Example: bash baidu_search.sh "配电网故障定位" 0 false

set -e

# Key lookup order: env BAIDU_API_KEY -> macOS Keychain service "baidu".
if [ -z "${BAIDU_API_KEY:-}" ]; then
    BAIDU_API_KEY="$(security find-generic-password -s baidu -w 2>/dev/null || true)"
fi

if [ -z "$BAIDU_API_KEY" ]; then
    echo '{"error": "BAIDU_API_KEY not set; set env or Keychain service baidu"}'
    exit 1
fi

# Get search keyword (required)
WD="$1"
if [ -z "$WD" ]; then
    echo '{"error": "Missing search keyword parameter"}'
    exit 1
fi

# Page number (default 0, i.e., first page)
pageNum="${2:-0}"

# Include abstract (default false, not included)
enable_abstract="${3:-false}"

encoded_wd="$(python3 -c 'import sys, urllib.parse; print(urllib.parse.quote(sys.argv[1]))' "$WD")"

# Send request
curl -s -X GET \
  -H "Authorization: Bearer $BAIDU_API_KEY" \
  -H "X-Appbuilder-From: openclaw" \
  "https://qianfan.baidubce.com/v2/tools/baidu_scholar/search?wd=$encoded_wd&pageNum=$pageNum&enable_abstract=$enable_abstract"
