---
status: historical
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20261010-SEARCH-MCP-WORKTREE-VENV-RESOLUTION
phase: done
date: 2026-10-10
tags: [mcp]
---

# TCK-20261010-SEARCH-MCP-WORKTREE-VENV-RESOLUTION

## Title
search_docs works from every git worktree on any host: the launcher finds the main checkout's venv, and the server finds the main checkout's index

## Status
DONE

## Tier
hotfix

## Type
bug

## Priority
P1

## Request Summary
codebase-planner reported (2026-10-10) that the knowledge-search MCP server fails to start in every worktree session on host ubuntu, so no worktree seat has `search_docs`, the step CLAUDE.md requires first. The owner told lead-planner to fix it.

## Scope
- `tools/start_search_mcp.sh`: add a main-checkout candidate resolved through `git rev-parse --git-common-dir` (before the worktree's own `$REPO_ROOT`), and make the probe require `mcp` as well as `sentence_transformers`.
- `tools/start_headroom_mcp.sh`: the same main-checkout candidate (same flaw).
- `tools/search_mcp.py`: when this checkout has no knowledge index, query the main checkout's index (read-only).
- Static launcher tests and unit tests for the index fallback; one sentence in `docs/guidelines/agent_working_environment.md`.

## Out of Scope
- `HEADROOM_WORKSPACE_DIR` in `start_headroom_mcp.sh` is still the hardcoded u24desktop path; it is not part of this outage and is left as is.
- `visual_assets/start_mcp.sh` (asset domain) was not changed.
- `make knowledge-index` still builds into the checkout it runs in; no change to index building.

## Acceptance Criteria
- From a fresh worktree with no `.venv-knowledge` and no index, `bash tools/start_search_mcp.sh --test` selects the main checkout's `.venv-knowledge` and a real query returns ranked results. Verified: the "damage formula" query returned `mechanics/02_combat_laws#1-the-damage-formula-001`.
- An interpreter that lacks `mcp` is never selected. Verified: the old script selected `/usr/bin/python3` in the same worktree; the new one does not.
- The worktree's own index wins when present; the main checkout's index is used only when the worktree's own is missing.
- Scoped tests pass.

## Related Tickets
- TCK-20260903-HOTFIX-KGMCP-SHARED-VENV-RESOLUTION (same outage class, fixed only for the u24desktop path)
- TCK-20260914-VENV-NAMING-CI-PARITY-SWAP, TCK-20260921-INTERPRETER-SELECTION-PROBES-INCONSISTENT (launcher probe history)

## Related Docs
- docs/guidelines/agent_working_environment.md

## Related Stored Artifacts
None (hotfix).

## Related Code Areas
- tools/start_search_mcp.sh, tools/start_headroom_mcp.sh, tools/search_mcp.py

## Assumptions / Open Questions
- Querying the main checkout's index from a worktree can return results that are a little behind the worktree's own docs. The existing staleness report covers this, since it compares against the worktree's corpus.
- `tools/**` is agent-working's domain. The owner directed lead-planner to fix it directly because no agent-working seat is live on host ubuntu.

## Implementation Notes
Cause, verified: the launcher tried the u24desktop absolute path, then `$REPO_ROOT/.venv-knowledge` (a worktree has none), then `/home/vboxuser/Work/venv` (absent), then system `python3`. On ubuntu, system python3 3.13.7 has `sentence_transformers` but no `mcp`, so it passed the probe and `search_mcp.py` exited with "mcp package not installed" (CONNECTION_CLOSED). Even with a working interpreter, a worktree has no `agent-working/.index/knowledge-index/` (gitignored), so every query answered "index not found".

Immediate relief, applied outside git: the main checkout's `.venv-knowledge` is symlinked into each existing worktree on this host. Each worktree runs the launcher copy from its own branch, so this fix reaches a worktree only after it picks up main.

## Test Summary
`pytest tests/tools/test_search_mcp.py tests/tools/test_mcp_launcher_hardening.py tests/tools/test_mcp_json_registration.py`: 51 passed. Live: the `--test` query from a venv-less, index-less worktree returned results. `bash -x` confirmed the new script selects the main venv, and the old one selected `/usr/bin/python3`. The headroom launcher also selects the main venv.

## Files Changed
- tools/start_search_mcp.sh
- tools/start_headroom_mcp.sh
- tools/search_mcp.py
- tests/tools/test_mcp_launcher_hardening.py
- tests/tools/test_search_mcp.py
- docs/guidelines/agent_working_environment.md

## Completion Summary
search_docs now works from any worktree on any host. The launcher resolves the main checkout's `.venv-knowledge` through git's common dir and requires `mcp` to be present, and the server falls back to the main checkout's knowledge index when the worktree has none.
