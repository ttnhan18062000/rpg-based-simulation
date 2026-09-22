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
# candidate can actually locate the search stack's real heavy dependency before selecting it, so a
# future rename or a stale/incomplete venv falls through to a working candidate instead of
# launching a broken server silently. Every failed probe stays quiet (stdout+stderr suppressed);
# only the final "nothing worked" message is visible.
#
# TCK-20260921-INTERPRETER-SELECTION-PROBES-INCONSISTENT: probe uses `importlib.util.find_spec`
# (locates the module without executing its `__init__.py`), not a full `import
# sentence_transformers` -- the exec'd server below (search_mcp.py -> knowledge_search.py) imports
# the same module for real moments later anyway, so a full import here paid the same ~5.66s torch
# cost twice per cold start for no benefit. Measured before/after on this same machine
# (`--test`, one real query, cold): before 10.9s, after 6.2s/7.2s over two separate runs -- a real
# ~35-45% cut, smaller than the ticket's own ~5s estimate (that estimate assumed only the probe's
# own cost would drop; the exec'd server's own single remaining sentence_transformers import,
# ~6-7s here, was never itself measured before this ticket, only assumed roughly equal to the
# probe's own ~5.66s). Weaker guarantee, accepted deliberately:
# find_spec confirms the module's spec is locatable, not that `__init__.py` executes cleanly -- a
# corrupted install or missing native `.so` extension would pass this probe and only fail when the
# exec'd server actually imports it. Acceptable because that failure now surfaces immediately and
# loudly in the exec'd process's own startup (an ImportError, not a silent hang), the same as any
# other cold-start import error already would; the probe's job is catching the *wrong-venv*
# fallthrough case (proven fixed), not guaranteeing a flawless install.
for py in \
    "/home/u24desktop/Working/rpg-based-simulation/.venv-knowledge/bin/python3" \
    "$REPO_ROOT/.venv-knowledge/bin/python3" \
    "/home/vboxuser/Work/venv/bin/python3" \
    "$(command -v python3 2>/dev/null)"; do
    [ -x "$py" ] || continue
    "$py" -c "import importlib.util, sys; sys.exit(0 if importlib.util.find_spec('sentence_transformers') else 1)" >/dev/null 2>&1 || continue
    exec "$py" "$SCRIPT_DIR/search_mcp.py" "$@"
done

echo "ERROR: no usable python3 with sentence_transformers found for search_mcp" >&2
exit 1
