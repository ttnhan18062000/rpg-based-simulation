---
status: active
layer: architecture
authority: P2
audience: agent
ticket_id: TCK-20261018-VISUAL-ASSETS-ASEPRITE-JOB-TIMEOUT-UNDER-LOAD
phase: open
date: 2026-10-18
tags: [architecture, testing]
---

# TCK-20261018-VISUAL-ASSETS-ASEPRITE-JOB-TIMEOUT-UNDER-LOAD

## Title
Find why a sub-second Aseprite job hits the 30 s `JOB_TIMEOUT_S` under host load (flaky `tests/visual_assets/drawing/integration/test_ops.py`)

## Status
INPROGRESS

## Tier
standard

## Type
bug

## Priority
P3

## Request Summary
Backlog, filed by asset-planner on 2026-10-18 with lead-planner's OK. Not scheduled: it waits for a quieter week on the shared machine. `tests/visual_assets/drawing/integration/test_ops.py` sometimes fails on the Aseprite job timeout when the host is loaded, and passes when run alone. The bound is `JOB_TIMEOUT_S = 30` (`visual_assets/drawing/config.py:35`). Its budgets row (`docs/assets/budgets.md`, APPROVED 2026-10-04) measured the slowest Aseprite job at 0.258 s, more than 100x below the bound. So host load alone (a slowdown of over 100x) is an unlikely cause. A hang, or a wait on something other than CPU, is more likely: the sandbox start (bwrap), the display or socket, a lock, or the pipe drain in `visual_assets/drawing/backend/sandbox.py`.

## Scope
- Investigate first: reproduce under controlled load (stress at a fixed level, under the MemoryMax cap). Record the wall time of each phase (sandbox start, Aseprite start, script run, drain) for passing and failing runs. Name the phase that eats the 30 s.
- Then fix the cause. Raise the bound only if the investigation shows real slow work, and then only with a new budgets row and the owner's approval of the new value.

## Out of Scope
- Raising `JOB_TIMEOUT_S` without a measured cause.
- Marking the test flaky or skipping it under load. A skip hides the failure; see the CLAUDE.md gate rule.

## Acceptance Criteria
- [ ] The investigation names the phase and the cause, with timings from failing runs.
- [ ] The fix passes N repeated runs under the same controlled load that failed before. N is set in test_plan.md.
- [ ] `visual_assets/drawing/**` is guarded (`docs/assets/store_contract.md`, local Aseprite proof record), so the change comes with a refreshed `docs/assets/aseprite_local_proof.json` from a real full `make visual-assets-aseprite-local` run. Any new or changed numeric bound gets a `docs/assets/budgets.md` row. Get lead-planner's OK for the heavy runs before starting.

## Related Tickets
- `TCK-20261015-VISUAL-ASSETS-SANDBOX-BWRAP-USERNS-ERROR` (#555, last sandbox change)
- `TCK-20261010-VISUAL-ASSETS-ASEPRITE-LOCAL-PROOF-RECORD`

## Related Docs
- `docs/assets/budgets.md` (JOB_TIMEOUT_S row), `docs/assets/store_contract.md` (Local Aseprite proof record)

## Related Stored Artifacts
- None (the #555 hotfix has no staging artifacts; its ticket is `agent-working/tickets/done/TCK-20261015-VISUAL-ASSETS-SANDBOX-BWRAP-USERNS-ERROR.md`).

## Related Code Areas
- `visual_assets/drawing/config.py`, `visual_assets/drawing/backend/sandbox.py`, `tests/visual_assets/drawing/integration/test_ops.py`

## Assumptions / Open Questions
- Unknown: whether the failure happens on u24desktop too. Ask the owner, or check that machine's runs, during the investigation.

## Implementation Notes

## Test Summary

## Files Changed

## Completion Summary
