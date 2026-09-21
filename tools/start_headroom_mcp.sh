#!/usr/bin/env bash
# Worktree-safe launcher for the Headroom MCP server (TCK-20260916-HEADROOM-TRIAL-ISOLATION-AND-REVERT).
# Modeled on tools/start_search_mcp.sh's own launcher pattern -- same trap, same fix.
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(dirname "$SCRIPT_DIR")"

# The agent-tooling venv lives at the main checkout root, not per-worktree -- $REPO_ROOT resolves
# to whatever worktree this script's own copy is running from (each worktree has its own copy of
# this file), so a git-worktree session's $REPO_ROOT/.venv-knowledge never has headroom-ai
# installed. Checking the absolute shared path first makes every worktree's MCP launch resolve to
# the one real venv instead of silently falling through to bare python3 (which would fail with
# "headroom: command not found" rather than a clear error).
# TCK-20260914-VENV-NAMING-CI-PARITY-SWAP: headroom-ai was installed into `.venv` (the pre-rename
# 3.12 knowledge env, now named `.venv-knowledge`) -- `.venv` is now the CI-matching 3.13 env and
# does not have it. Found during that ticket's own implementation, not in its original Scope list.
for bin in \
    "/home/u24desktop/Working/rpg-based-simulation/.venv-knowledge/bin/headroom" \
    "$REPO_ROOT/.venv-knowledge/bin/headroom" \
    "/home/vboxuser/Work/venv/bin/headroom"; do
    if [ -x "$bin" ]; then
        # Isolation, not the default machine-wide ~/.headroom -- config_dir() derives from
        # HEADROOM_WORKSPACE_DIR/config automatically when only the workspace root is set
        # (headroom/paths.py's own documented precedence), so one env var covers both roots.
        # Shared across worktrees of this repo (same absolute path regardless of which
        # worktree's copy of this script is running), never shared with any other repo or
        # with ~/.headroom.
        export HEADROOM_WORKSPACE_DIR="/home/u24desktop/Working/rpg-based-simulation/.headroom-workspace"
        exec "$bin" mcp serve "$@"
    fi
done

echo "ERROR: no usable venv with headroom-ai installed found for start_headroom_mcp.sh" >&2
exit 1
