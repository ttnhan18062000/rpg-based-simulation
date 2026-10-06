---
status: active
layer: performance
authority: P2
audience: agent
ticket_id: TCK-20261006-PERF-SHEDDING-DOCS-MATCH-SHIPPED-BEHAVIOUR
phase: open
date: 2026-10-06
tags: [performance, engine]
---

# TCK-20261006-PERF-SHEDDING-DOCS-MATCH-SHIPPED-BEHAVIOUR

## Title
Engine docs say what degradation really does: modes shed replay richness, traces, cadence, budgets and concurrency, not work; the periodic and opportunistic shedding path is documented as designed but unused

## Status
OPEN

## Tier
hotfix

## Type
chore

## Priority
P2

## Request Summary
**Owner decision 2026-10-06: option (c)** from `TCK-20261006-PERF-SCHEDULER-SHEDS-NOTHING-IN-SHIPPED-RUNS`
(done; evidence in its stored `investigation.md`, the "Promises" table). Keep the code. Document the
periodic and opportunistic shedding path as designed but never wired, and correct the docs that
promise otherwise. Removing the dead code (and the hashed `periodic_due_ticks`) is folded into
`TCK-20261004-WORK-DEBT-RETIRE-STEP2-CODE`, which already needs a PERF-D5 hash-scheme bump.

The owner approved the correction in principle when choosing (c). Every target doc is P1, so the edits
only correct statements of fact against the cited code, and the PR shows the owner the exact wording.

## Scope
Correct each statement the investigation marked false or partly true. Cite the code the correction rests
on (from the investigation), and change nothing else in these docs.
1. `docs/engine/matrices/resource_governor_degradation_matrix.md`: lines about 17-19, 26, 29-32 (periodic
   rows, opportunistic row, "authoritative never shed / work debt", the waterfall). Also note that the
   table disagrees with `src/engine/policy.py` (the opportunistic flag per mode, and no "reduced 50%").
   Make the table match `policy.py`, and say no shipped task exists to shed.
2. `docs/engine/runtime_profiles.md` about 42-43: replay richness and traces change; diagnostics and
   metrics detail have no reader.
3. `docs/engine/architecture.md` about 72 (Law of Progressive Degradation): traces yes, diagnostics no,
   fidelity through `PhaseBudgetGovernor` and cadence yes.
4. `docs/engine/project_lawbook.md` about 28 (shedding order).
5. `docs/engine/matrices/scheduler_work_model_matrix.md` about 18 and 29 (OPPORTUNISTIC: no producer in
   shipped runs).
6. `docs/engine/matrices/observability_operational_controls_matrix.md` about 27 (`FORCE_DEGRADED`
   changes the mode; it sheds no work).
7. `docs/engine/matrices/worker_bounds_matrix.md` about 19 (the governor changes the mode; it does not
   shed work).
8. Add one short "Designed but unused" note in the doc that best owns the scheduler (the scheduler work
   model matrix, or `kernel.md` if it describes scheduling). Cover: `PeriodicDefinition` is never
   registered in `src/`, `allow_opportunistic` has an empty branch, `diagnostic_verbosity` and
   `metrics_detail` have no reader, and `periodic_updates` has no producer. Point to retire step 2 for
   the removal.
9. If a parity-ledger entry text repeats a corrected claim, align its text. The investigation found none
   claiming shedding as `verified`, so expect no status change.

## Out of Scope
- Any `src/` edit, including the two misleading comments (`src/engine/observability.py:32`,
  `src/core/governance.py:45`). They move to retire step 2, which edits that code anyway.
- Removing code or `periodic_due_ticks` (retire step 2).
- Test changes. The six mechanism tests stay valid as specs.

## Acceptance Criteria
1. Every row in the investigation's "Promises" table marked false or partly true is corrected or
   explicitly qualified, and each correction cites code.
2. The "Designed but unused" note exists and links retire step 2.
3. No `src/` or `tests/` file changes.
4. `tests/docs` and the frontmatter validators pass, and `make knowledge-index-update` runs.
5. The PR body lists each P1 doc changed, so the owner can review the wording.

## Related Tickets
- `TCK-20261006-PERF-SCHEDULER-SHEDS-NOTHING-IN-SHIPPED-RUNS` (done; the evidence)
- `TCK-20261004-WORK-DEBT-RETIRE-STEP2-CODE` (gets the removal and the two comments)
- `TCK-20261006-PERF-TICK-BUDGET-THROTTLE-REPORT-ONLY` (done; DEV-014)

## Related Docs
- the seven docs in Scope; `docs/guidelines/intentional_divergences.md` (DEV-014)

## Related Stored Artifacts
- `agent-working/stored_artifacts/TCK-20261006-PERF-SCHEDULER-SHEDS-NOTHING-IN-SHIPPED-RUNS/investigation.md`

## Related Code Areas
- (read only) `src/engine/scheduler.py`, `src/engine/policy.py`, `src/engine/replay_manager.py`,
  `src/engine/phase_governor.py`

## Assumptions / Open Questions
- none

## Implementation Notes

## Test Summary

## Files Changed

## Completion Summary
