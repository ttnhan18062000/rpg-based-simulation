---
status: historical
layer: architecture
authority: P2
audience: agent
ticket_id: TCK-20261018-VISUAL-ASSETS-ASEPRITE-JOB-TIMEOUT-UNDER-LOAD
phase: done
date: 2026-10-18
tags: [architecture, testing]
---

# TCK-20261018-VISUAL-ASSETS-ASEPRITE-JOB-TIMEOUT-UNDER-LOAD

## Title
Find why a sub-second Aseprite job hits the 30 s `JOB_TIMEOUT_S` under host load (flaky `tests/visual_assets/drawing/integration/test_ops.py`)

## Status
DONE

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
- [x] The investigation names the phase and the cause, with timings from failing runs.
- [x] REPLACED (scope change, agreed with asset-planner and lead-planner 2026-10-18; evidence commit `f20933f71`): ~~The fix passes N repeated runs under the same controlled load that failed before. N is set in test_plan.md.~~ The failure comes from the host (the whole guest stalls), so no code fix can pass this criterion. Replacement: each loaded failure maps to an external scheduling gap of the same length (N=3: runs 4, 5, 6, see `investigation.md`).
- [x] (not triggered: no change under `visual_assets/**`; the docs note is outside the guarded set) `visual_assets/drawing/**` is guarded (`docs/assets/store_contract.md`, local Aseprite proof record), so the change comes with a refreshed `docs/assets/aseprite_local_proof.json` from a real full `make visual-assets-aseprite-local` run. Any new or changed numeric bound gets a `docs/assets/budgets.md` row. Get lead-planner's OK for the heavy runs before starting.

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
- Root cause: a guest-wide stall (swap thrash and host contention on the VirtualBox guest), not a job phase. Details and numbers: `investigation.md`. Option A chosen by asset-planner (lead-planner agreed): no code change.
- Added a docs-only section "A sub-second job that "times out" under load is a host stall" to `docs/assets/drawing_tools.md` (symptom, how to confirm with `extsamp.py`, what to do: rerun when quiet, never raise the bound).

## Test Summary
N=3 loaded runs of `test_ops.py` with the external gap sampler (6 busy loops, MemoryMax=3G scope, own basetemp):
- Run 4: failing call 37.4 s; sampler gap 37.7 s.
- Run 5: slowest calls 20.0, 19.5 and 17.4 s; sampler gaps 18.0, 17.7 and 17.5 s.
- Run 6: slowest calls 39.1, 21.6 and 19.9 s; sampler gaps 37.8, 22.2 and 18.0 s (and 20.2 s).
Every slow call has a gap of nearly the same length; non-stalled calls took under 2.2 s. Runs 1-3 (before the external sampler) failed the same way and are in `investigation.md`. No code under test changed; no suite was run beyond these.

## Files Changed
- `docs/assets/drawing_tools.md` (new section)
- Ticket and staging artifacts (`plan.md`, `investigation.md`, `test_plan.md`, `evidence/`).

## Completion Summary
SCOPE CHANGE, not a pass: the acceptance criterion "the fix passes N repeated runs under the same load" was replaced, because the failure is a host stall that no code change can pass (stalls reached 172 s; the job itself needs about 0.2 s). The replacement criterion (each loaded failure maps to an external scheduling gap of the same length, N=3) is met. No code was changed, `JOB_TIMEOUT_S` is unchanged, no test was skipped or retried, and no proof refresh or budgets row was needed. Open items: whether u24desktop shows it is unknown; the host-side memory and swap pressure goes to lead-planner.
