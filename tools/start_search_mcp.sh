#!/usr/bin/env bash
# Portable launcher for search_mcp.py — works across machines with different venv paths.
# Tries known venv locations in priority order, then falls back to system python3.
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(dirname "$SCRIPT_DIR")"

for py in \
    "$REPO_ROOT/.venv/bin/python3" \
    "/home/vboxuser/Work/venv/bin/python3" \
    "$(command -v python3 2>/dev/null)"; do
    [ -x "$py" ] && exec "$py" "$SCRIPT_DIR/search_mcp.py" "$@"
done

echo "ERROR: no usable python3 found for search_mcp" >&2
exit 1
