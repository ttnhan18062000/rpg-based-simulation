---
status: active
layer: performance
authority: P2
audience: agent
ticket_id: TCK-20261004-WORK-DEBT-RETIRE-STEP1-DOCS
phase: open
date: 2026-10-04
tags: [performance, engine]
---

# TCK-20261004-WORK-DEBT-RETIRE-STEP1-DOCS

## Title
Work-debt retirement step 1: correct the P1 contracts that say work debt counts postponed items

## Status
OPEN

## Tier
hotfix

## Type
repair

## Priority
P2

## Request Summary
`TCK-20261004-WORK-DEBT-NEVER-ACCUMULATES-IN-PRODUCTION` confirmed that nothing ever produces
`state.work_debt`. Its test `tests/integration/kernel/test_work_debt_stays_empty_in_production.py`
guards this. In 363 commits, only the drain half of the Milestone 4 design was built. The owner chose
**retire, in two steps** on 2026-10-04. This is step 1: docs only, ungated. Step 2, removing the code,
is `TCK-20261004-WORK-DEBT-RETIRE-STEP2-CODE` and waits for the gate.

The P1 docs still describe a producer that does not exist:
- `docs/engine/contracts/resource_governor_contract.md:31`: "`work_debt`: Total count of postponed
  authoritative items."
- `docs/engine/matrices/scheduler_work_model_matrix.md`: the `DEFERRED` / "Work debt" row and its
  section say the debt accumulates when work overflows.

## Scope
- Correct both P1 docs to state current behaviour. `work_debt` is never increased in production:
  only `DRAIN_DEBT` consumes it, and `PressureInjector.inject_work_debt` has no caller. Every reader
  therefore sees 0. The field is scheduled for retirement (owner decision 2026-10-04; step 2 ticket).
  Cite the guard test
- PERF-D3 in `docs/architecture/performance_optimization_decisions.md`: add a dated note. The
  aggregate counter it ratified has no producer, and the owner chose retirement
- `docs/guidelines/intentional_divergences.md`: not needed, because no behaviour changes in this step
- Parity ledger: if an entry claims debt accumulation (search `work_debt` in
  `docs/parity_ledger/*.yaml`), set it to the true status with the guard test as evidence
- `make knowledge-index-update`; regenerate the registry

## Out of Scope
- Any `src/` edit (step 2, gated)
- The archived matrix under `docs/archive/` (historical)

## Acceptance Criteria
1. No active P1 doc says that work debt counts postponed or overflowed work
2. Each corrected statement cites the guard test and the step 2 ticket
3. The parity ledger is consistent (schema check: 0 rose)

## Related Tickets
- `TCK-20261004-WORK-DEBT-NEVER-ACCUMULATES-IN-PRODUCTION` (evidence)
- `TCK-20261004-WORK-DEBT-RETIRE-STEP2-CODE`
- `TCK-20261003-SALIENCE-WALL-CLOCK-PRICE-COUPLING`

## Related Docs
- `docs/engine/contracts/resource_governor_contract.md`, `docs/engine/matrices/scheduler_work_model_matrix.md`
- `docs/architecture/performance_optimization_decisions.md` (PERF-D3, PERF-D1 A1)

## Related Stored Artifacts
- `agent-working/stored_artifacts/TCK-20261004-WORK-DEBT-NEVER-ACCUMULATES-IN-PRODUCTION/`

## Related Code Areas
- none edited

## Assumptions / Open Questions
- The owner approved the retirement on 2026-10-04, and these P1 edits only make the docs state
  current behaviour

## Implementation Notes

## Test Summary

## Files Changed

## Completion Summary
