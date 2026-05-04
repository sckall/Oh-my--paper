#!/bin/bash
# Pipeline status watcher — monitors task completion changes in background
# Used by monitors/monitors.json pipeline-status monitor
set -e

WATCH_FILE=".pipeline/tasks/tasks.json"
CACHE_FILE="${CLAUDE_PLUGIN_DATA:-/tmp}/.pipeline-cache.json"

# Helper: check pipeline status (return one-line summary)
get_status() {
  if [ ! -f "$WATCH_FILE" ]; then
    echo "⏳ Pipeline not initialized"
    return
  fi

  if command -v python3 &>/dev/null; then
    python3 -c "
import json, os
d = json.load(open(os.path.expanduser('$WATCH_FILE')))
tasks = d.get('tasks', [])
total = len(tasks)
done = sum(1 for t in tasks if t.get('status') == 'done')
prog = sum(1 for t in tasks if t.get('status') == 'in_progress')
print(f'📊 {done}/{total} tasks done | {prog} in progress')
" 2>/dev/null || echo "📊 Pipeline running"
  else
    echo "📊 Pipeline: check with /omp:progress"
  fi
}

# Initial status
get_status

# Watch for changes (tail -F follows file renames/rotations)
if [ -f "$WATCH_FILE" ]; then
  tail -F "$WATCH_FILE" 2>/dev/null | while read -r line; do
    get_status
  done
fi
