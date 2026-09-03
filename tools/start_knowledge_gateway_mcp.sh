#!/usr/bin/env bash
# Portable launcher for knowledge_gateway_mcp.py — works across machines with different venv paths.
# Tries known venv locations in priority order, then falls back to system python3.
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(dirname "$SCRIPT_DIR")"

# The u24desktop shared venv lives at the main checkout root, not per-worktree -- $REPO_ROOT
# resolves to whatever worktree this script's own copy is running from (each worktree has its
# own tools/start_knowledge_gateway_mcp.sh), so a git-worktree session's $REPO_ROOT/.venv never
# has the knowledge deps installed. Checking the absolute shared path first makes every
# worktree's MCP launch resolve to the one real venv instead of silently falling through to bare
# python3.
for py in \
    "/home/u24desktop/Working/rpg-based-simulation/.venv/bin/python3" \
    "$REPO_ROOT/.venv/bin/python3" \
    "/home/vboxuser/Work/venv/bin/python3" \
    "$(command -v python3 2>/dev/null)"; do
    [ -x "$py" ] && exec "$py" "$SCRIPT_DIR/knowledge_gateway_mcp.py" "$@"
done

echo "ERROR: no usable python3 found for knowledge_gateway_mcp" >&2
exit 1
