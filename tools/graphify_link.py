"""Share the main checkout's graphify graph with its worktrees (TCK-20261011-GRAPHIFY-SHARED-GRAPH-FROM-WORKTREES).

`graphify-out/` is gitignored, so a new worktree has no graph and `graphify query` fails there. A worktree gets a
symlink `graphify-out -> <main checkout>/graphify-out` instead. It is read-only by convention: the PostToolUse
`graphify update .` hook skips a symlinked `graphify-out`, and `tools/graphify_prune.py` will not write through one.
Stdlib only; never raises, so launchers and hooks can call it unconditionally.
"""
from __future__ import annotations

import os
from pathlib import Path

try:
    from tools.handover_home import main_checkout_root
except ImportError:  # run as a script from tools/
    from handover_home import main_checkout_root  # type: ignore[no-redef]

NAME = "graphify-out"
LINKED, MAIN, HAS_OWN, NO_SHARED_GRAPH, UNKNOWN, FAILED = "linked", "main-checkout", "has-own", "no-shared-graph", "no-main-checkout", "failed"


def link_shared_graph(worktree: Path | str) -> str:
    """Link `<worktree>/graphify-out` to the main checkout's; returns a status string, never raises.

    Leaves anything already at that name alone: a real directory (`rpg-perf` keeps its own), a symlink of any
    target (host ubuntu's hand-made ones), even a broken one."""
    try:
        wt = Path(worktree).resolve()
        main = main_checkout_root(wt)
        if main is None:
            return UNKNOWN
        main = main.resolve()
        if wt == main:
            return MAIN
        target, link = main / NAME, wt / NAME
        if os.path.lexists(link):
            return HAS_OWN
        if not (target / "graph.json").is_file():
            return NO_SHARED_GRAPH
        link.symlink_to(target, target_is_directory=True)
        return LINKED
    except OSError:
        return FAILED
