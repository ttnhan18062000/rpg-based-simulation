---
status: active
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20261018-MAKE-AGENT-MONITORING-INDEX-WORKS-WITHOUT-LOCAL-VENV
phase: open
date: 2026-10-18
tags: [ai, agent-monitoring, setup]
---

# TCK-20261018-MAKE-AGENT-MONITORING-INDEX-WORKS-WITHOUT-LOCAL-VENV

## Title
`make agent-monitoring-index` works in a worktree that has no `.venv` of its own

## Status
OPEN

## Tier
hotfix

## Type
bug

## Priority
P2

## Request Summary
Owner decision 2026-10-18 (via lead-planner), from the RETRO-2026-W42 final note.
- In a worktree without `.venv`, `make agent-monitoring-index` fails with "tools/agent-monitoring/build_index.py: Permission denied", error 127.
- The recipe picks its interpreter with `$(shell for py in .venv/bin/python3 python3; do [ -x "$$py" ] && echo "$$py" && break; done)`. `[ -x python3 ]` tests a file literally named `python3` in the cwd, so nothing is echoed, and make then tries to exec the `.py` file itself.
- The Makefile already has `PYTHON3` (L51), which tries `.venv`, then the main checkout's `.venv` via `KNOWLEDGE_MAIN_ROOT`, then `python3`, using `command -v` plus an import probe.

## Scope
- `Makefile`: the `agent-monitoring-index` recipe uses `$(PYTHON3)`, not the inline loop.
- Check the other inline `for py in .venv/bin/python3 python3` uses (`PYTHON :=` at ~L583, and any other `[ -x "$$py" ]` loop) for the same bug. Fix only ones that actually break without a local `.venv`, and list each in the ticket.
- **The Makefile is lead-owned (route: domain lead):** keep the diff to these recipe lines. Lead-planner reviews it as part of the batch.
- Test: in `tests/tools/`, next to the existing Makefile tests (find them with `grep -rl Makefile tests/tools`), assert that the `agent-monitoring-index` recipe has no `[ -x "$$py" ]` interpreter loop and uses `$(PYTHON3)`. Or use a `make -n agent-monitoring-index` dry run in a tmp copy with no `.venv` that resolves to a real interpreter path, whichever matches existing Makefile-test patterns.
- Per the memory rule for Makefile edits, run all of `tests/tools` once before the PR, through a lead heavy slot.

## Out of Scope
- Changing `PYTHON3`'s resolution order.

## Acceptance Criteria
- `make agent-monitoring-index` in a worktree with no `.venv` builds the index with a real interpreter.
- The test fails on the old recipe and passes on the new one.

## Related Tickets
- TCK-20261010-SEARCH-MCP-WORKTREE-VENV-RESOLUTION (same class of worktree-venv bug)

## Related Docs
- docs/guides/agent_monitoring.md (index section)

## Related Stored Artifacts
- none

## Related Code Areas
- Makefile (`agent-monitoring-index`, `PYTHON3`, `PYTHON`), tools/agent-monitoring/build_index.py

## Assumptions / Open Questions
- none

## Implementation Notes
## Test Summary
## Files Changed
## Completion Summary
