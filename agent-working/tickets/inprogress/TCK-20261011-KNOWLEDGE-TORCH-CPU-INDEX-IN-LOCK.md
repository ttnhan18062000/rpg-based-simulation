---
status: active
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20261011-KNOWLEDGE-TORCH-CPU-INDEX-IN-LOCK
phase: open
date: 2026-10-11
tags: [knowledge-store]
---

# TCK-20261011-KNOWLEDGE-TORCH-CPU-INDEX-IN-LOCK

## Title
The knowledge extra's comments and the Makefile tell the truth about torch and the knowledge venv path (option 2; lock unchanged)

## Status
INPROGRESS

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
TBD

## Files Changed
TBD

## Completion Summary
TBD
