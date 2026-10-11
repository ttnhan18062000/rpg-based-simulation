---
status: historical
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20261011-KNOWLEDGE-TORCH-CPU-INDEX-IN-LOCK
phase: done
date: 2026-10-11
tags: [knowledge-store]
---

# TCK-20261011-KNOWLEDGE-TORCH-CPU-INDEX-IN-LOCK

## Title
The knowledge extra's comments and the Makefile tell the truth about torch and the knowledge venv path (option 2; lock unchanged)

## Status
DONE

## Tier
hotfix

## Type
chore

## Priority
P2

## Request Summary
Closes #514. `pyproject.toml`'s `knowledge` extra comment implies a CPU torch the lock does not give (uv.lock resolves torch from PyPI, the CUDA build), and the Makefile's `PYTHON_KNOWLEDGE` hard-codes a `/home/u24desktop/...` path. Lead chose option 2 over putting a CPU index into the lock, because `download.pytorch.org` is blocked on u24desktop (`docs/guidelines/agent_working_environment.md`, "Why the knowledge stack is stuck on 3.12").

Unstaffed-seat exception: `tests/tools/**`, `tools/**` and the issue belong to agent-working, whose seat is unstaffed; codebase takes this on lead-planner's request with the owner's confirmation (batch brief `docs/plans/codebase_health/knowledge_lock_transit_test_brief.md`). `pyproject.toml`, `uv.lock`, `Makefile` are lead-owned; lead approved the edit and reviews by PR comment.

## Scope
- `pyproject.toml` `knowledge` extra: comment states the lock resolves PyPI torch; `.venv-knowledge` is built by the manual CPU-wheel step, is NOT lock-reproducible; do not `uv sync --extra knowledge` expecting CPU.
- `Makefile` `PYTHON_KNOWLEDGE`: drop the u24desktop literal; order `KNOWLEDGE_PYTHON` override, main checkout's `.venv-knowledge` (git common dir), repo-relative `.venv-knowledge`, `python3`.
- `tools/start_headroom_mcp.sh`: same swap only if a pure path swap; otherwise an agent-working follow-up noted here.
- Doc mentions of the path; `make knowledge-index-update`.

## Out of Scope
- Any change to `uv.lock` or a CPU index (option 1).
- Behaviour of the headroom launcher beyond a path swap.

## Acceptance Criteria
1. `uv.lock` unchanged; `uv lock --check` passes.
2. `PYTHON_KNOWLEDGE` resolves on this VM with and without `KNOWLEDGE_PYTHON`.
3. `tests/tools/test_mcp_launcher_hardening.py` green, no ordering check weakened.
4. #514 closing comment carries the revisit trigger: option 1 becomes viable once download.pytorch.org is reachable from every working host (the owner's call).

## Related Tickets
- TCK-20261011-HANDOVER-TRANSIT-TEST-HOME-ISOLATION (same batch)

## Related Docs
- docs/guidelines/agent_working_environment.md
- docs/plans/codebase_health/knowledge_lock_transit_test_brief.md

## Related Stored Artifacts
None (hotfix).

## Related Code Areas
- pyproject.toml
- Makefile
- tools/start_headroom_mcp.sh

## Assumptions / Open Questions
- Headroom launcher scope decided after reading it.

## Implementation Notes
See brief.

## Test Summary
`uv.lock` unchanged and `uv lock --check` passes (127 packages resolved). `make` PYTHON_KNOWLEDGE resolves to the main checkout's `.venv-knowledge` by default, `KNOWLEDGE_PYTHON=/x/py` env and `make KNOWLEDGE_PYTHON=/y/py` both used verbatim. `bash -n tools/start_headroom_mcp.sh` ok. `tests/static`, `test_mcp_launcher_hardening.py`, `test_handover_transit.py`: 159 passed, no ordering assertion changed. CI's Tools f-z lane then failed `tests/tools/test_makefile_interpreter_selection.py` on the first multi-statement form of PYTHON_KNOWLEDGE (the test extracts a one-line `for py in` loop); fixed in the Makefile (git-common-dir lookup moved to `KNOWLEDGE_MAIN_ROOT`), test file untouched and as strict as before. Whole `tests/tools` run locally: 4782 passed, 29 skipped, 1 xfailed.

## Files Changed
- Makefile
- pyproject.toml (comment only)
- requirements-knowledge.txt (comment only)
- tools/start_headroom_mcp.sh
- docs/guidelines/agent_working_environment.md
- docs/plans/codebase_health/knowledge_lock_transit_test_brief.md

## Completion Summary
Option 2 (lead's decision): the lock is untouched and the comments now say it resolves PyPI torch and that .venv-knowledge is not lock-reproducible. Makefile PYTHON_KNOWLEDGE has no host path: KNOWLEDGE_PYTHON, main-checkout venv via git common dir, repo-relative venv, python3. Headroom launcher: u24desktop candidate dropped (the generic main-root candidate covers it) and KNOWLEDGE_PYTHON honoured first. Follow-ups for agent-working (not done here): `tools/start_headroom_mcp.sh` still sets HEADROOM_WORKSPACE_DIR to the u24desktop path (a behaviour change, not a path swap); `tools/start_search_mcp.sh` still lists the u24desktop candidate. Revisit trigger for the #514 closing comment: option 1 (CPU index in the lock) becomes viable once download.pytorch.org is reachable from every working host (the owner's call). Unstaffed-seat exception; lead reviews pyproject/uv.lock/Makefile by PR comment.
