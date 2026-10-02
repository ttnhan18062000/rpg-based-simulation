#!/usr/bin/env bash
# Launcher for the drawing-tools MCP server (python -m visual_assets.drawing.server).
# Portable across machines and git worktrees: picks the first interpreter that can actually locate
# the `mcp` package (a probe, not a bare existence check), changes to the repo root so the
# `visual_assets` package is importable, and execs the module. Failed probes stay quiet; only the
# final "nothing worked" message is visible. Same shape as tools/start_search_mcp.sh.
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(dirname "$SCRIPT_DIR")"

# A git worktree has no venv of its own; the main checkout's venv is checked by absolute path.
for py in \
    "$REPO_ROOT/.venv/bin/python3" \
    "/home/vboxuser/Work/rpg-based-simulation/.venv/bin/python3" \
    "$(command -v python3 2>/dev/null)"; do
    [ -x "$py" ] || continue
    "$py" -c "import importlib.util, sys; sys.exit(0 if importlib.util.find_spec('mcp') else 1)" >/dev/null 2>&1 || continue
    cd "$REPO_ROOT" || exit 1
    exec "$py" -m visual_assets.drawing.server "$@"
done

echo "ERROR: no usable python3 with the 'mcp' package found for visual_assets drawing server" >&2
exit 1
