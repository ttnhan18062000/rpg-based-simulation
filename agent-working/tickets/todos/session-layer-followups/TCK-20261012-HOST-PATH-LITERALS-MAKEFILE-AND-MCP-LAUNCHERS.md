---
status: active
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20261012-HOST-PATH-LITERALS-MAKEFILE-AND-MCP-LAUNCHERS
phase: open
date: 2026-10-12
tags: [ai, mcp, process-improvement]
---

# TCK-20261012-HOST-PATH-LITERALS-MAKEFILE-AND-MCP-LAUNCHERS

## Title
Remove the remaining host-specific absolute paths from Makefile PYTHON3 and the MCP launch scripts

## Status
OPEN

## Tier
hotfix

## Type
chore

## Priority
P2

## Request Summary
GitHub issue #517 (finding from lead-planner), the follow-up to PR #518 (knowledge-lock-transit-test), which
removed the u24desktop literal from `PYTHON_KNOWLEDGE` and from `start_headroom_mcp.sh`'s interpreter list.
These literals remain on main at e0f88c5f0:

| where | literal |
|---|---|
| `Makefile` line 48 `PYTHON3` | `/home/u24desktop/Working/rpg-based-simulation/.venv/bin/python3` and `/home/vboxuser/Work/venv/bin/python3` |
| `tools/start_headroom_mcp.sh` | `HEADROOM_WORKSPACE_DIR="/home/u24desktop/Working/rpg-based-simulation/.headroom-workspace"` |
| `tools/start_headroom_mcp.sh` | `/home/vboxuser/Work/venv/bin/python3` candidate |
| `tools/start_search_mcp.sh` | `/home/u24desktop/Working/rpg-based-simulation/.venv-knowledge/bin/python3` (first candidate) and `/home/vboxuser/Work/venv/bin/python3` |

Fact checked by the planner on u24desktop: `/home/u24desktop/Working` is a symlink to `/mnt/data/Working`, and
the main checkout is `/mnt/data/Working/rpg-based-simulation`. So on this host the git-common-dir main root
resolves to the same venvs as the literals, which makes them redundant here.

## Scope
1. `Makefile` `PYTHON3`: replace the two literals with the main-root pattern `PYTHON_KNOWLEDGE` already uses
   (`$(KNOWLEDGE_MAIN_ROOT)/.venv/bin/python3`; reuse that variable, do not compute the root twice). Keep
   `.venv/bin/python3` and bare `python3`, and keep the capability probe (`find_spec('pydantic')`) and the
   fall-through to the next candidate when a probe fails.
2. `tools/start_headroom_mcp.sh`: derive `HEADROOM_WORKSPACE_DIR` from `$MAIN_ROOT` (fall back to `$REPO_ROOT`
   when git cannot resolve it), so all worktrees of one checkout still share one workspace and no other repo
   shares it. Respect an already-set `HEADROOM_WORKSPACE_DIR`. Drop the vboxuser candidate.
3. `tools/start_search_mcp.sh`: drop the u24desktop and vboxuser literals. Put `${KNOWLEDGE_PYTHON:-}` first, as
   `start_headroom_mcp.sh` does, so a host whose venv lives elsewhere has an explicit override. Update the
   comment that says the u24desktop literal is deliberate, and the matching line in
   `docs/guidelines/agent_working_environment.md`.
4. Verify on u24desktop, from the main checkout and from a worktree:
   - `make -pn | grep '^PYTHON3 :='` (or `make -s print-PYTHON3` style) shows the main checkout's `.venv` python
     from both;
   - `bash tools/start_search_mcp.sh --test` (or the script's own health mode) and
     `bash tools/start_headroom_mcp.sh --help` start with the shared venvs from both;
   - the headroom workspace resolves to `/mnt/data/Working/rpg-based-simulation/.headroom-workspace` (the same
     directory as today, through the symlink), so no headroom state is orphaned.
   Record the commands and output in the ticket.
5. Tests: extend `tests/tools/test_makefile_interpreter_selection.py` for `PYTHON3` (main-root candidate picked
   from a worktree; a broken candidate falls through). Add a check that none of `Makefile`,
   `tools/start_*_mcp.sh` contains `/home/` (a small static test in `tests/tools/`).

## Out of Scope
- `.mcp.json` (lead-owned; no change needed).
- The search MCP behaviour (TCK-20261012-SEARCH-MCP-SHARED-SERVER-AND-IDLE-UNLOAD, same batch; that ticket
  edits `search_mcp.py`/`search_server.py`, this one edits the launch scripts, so they do not collide).
- `visual_assets/start_mcp.sh` (asset domain).
- Any other `/home/` literal outside the files named here (report it in the ticket if found; do not fix it).

## Acceptance Criteria
- AC1: `Makefile`, `tools/start_headroom_mcp.sh` and `tools/start_search_mcp.sh` contain no `/home/` path
  (static test).
- AC2: On u24desktop, `PYTHON3` resolves to the main checkout's `.venv` python from the main checkout and from a
  worktree (recorded output).
- AC3: Both MCP launchers start from a worktree on u24desktop with the shared venv (recorded output).
- AC4: The headroom workspace on u24desktop is the same directory as before.
- AC5: `pytest tests/tools/test_makefile_interpreter_selection.py` and the new static test pass.
- AC6: lead-planner has reviewed the Makefile diff (comment on the batch PR).

## Related Tickets
- GitHub issue #517 (source); PR #518 (TCK-20261011-KNOWLEDGE-TORCH-CPU-INDEX-IN-LOCK, the pattern reused here).
- TCK-20261010-SEARCH-MCP-WORKTREE-VENV-RESOLUTION; TCK-20260916-HEADROOM-TRIAL-ISOLATION-AND-REVERT.

## Related Docs
- docs/guidelines/agent_working_environment.md

## Related Stored Artifacts

## Related Code Areas
- Makefile (lead-owned: lead reviews), tools/start_headroom_mcp.sh, tools/start_search_mcp.sh
- tests/tools/test_makefile_interpreter_selection.py

## Assumptions / Open Questions
- Must be implemented and verified on u24desktop (the issue asks for it). agent-working-implementer runs on this host.

## Implementation Notes

## Test Summary

## Files Changed

## Completion Summary
