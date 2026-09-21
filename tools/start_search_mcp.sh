#!/usr/bin/env bash
# Portable launcher for search_mcp.py — works across machines with different venv paths.
# Tries known venv locations in priority order, then falls back to system python3.
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(dirname "$SCRIPT_DIR")"

# The u24desktop shared venv lives at the main checkout root, not per-worktree -- $REPO_ROOT
# resolves to whatever worktree this script's own copy is running from (each worktree has its
# own tools/start_search_mcp.sh), so a git-worktree session's $REPO_ROOT/.venv-knowledge never has
# the knowledge deps installed. Checking the absolute shared path first makes every worktree's MCP
# launch resolve to the one real venv instead of silently falling through to bare python3.
# TCK-20260914-VENV-NAMING-CI-PARITY-SWAP: the knowledge-stack venv is `.venv-knowledge` (Python
# 3.12), not `.venv` -- `.venv` is now the CI-matching 3.13 env and does not have these deps.
#
# Hardened after that same ticket's own rename, per real-world evidence: picking the first
# candidate that merely *exists* (`[ -x "$py" ]`) is exactly what made `origin/main`'s copy of this
# script pick the newly-renamed `.venv` (3.13, no `sentence_transformers`) the moment the rename
# landed on this machine -- a real, live breakage, not a hypothetical. Now probes that the
# candidate can actually import the search stack's real heavy dependency before selecting it, so a
# future rename or a stale/incomplete venv falls through to a working candidate instead of
# launching a broken server silently. Every failed probe stays quiet (stdout+stderr suppressed);
# only the final "nothing worked" message is visible.
for py in \
    "/home/u24desktop/Working/rpg-based-simulation/.venv-knowledge/bin/python3" \
    "$REPO_ROOT/.venv-knowledge/bin/python3" \
    "/home/vboxuser/Work/venv/bin/python3" \
    "$(command -v python3 2>/dev/null)"; do
    [ -x "$py" ] || continue
    "$py" -c "import sentence_transformers" >/dev/null 2>&1 || continue
    exec "$py" "$SCRIPT_DIR/search_mcp.py" "$@"
done

echo "ERROR: no usable python3 with sentence_transformers found for search_mcp" >&2
exit 1
