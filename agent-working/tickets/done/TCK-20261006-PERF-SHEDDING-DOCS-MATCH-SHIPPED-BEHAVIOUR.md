---
status: historical
layer: performance
authority: P2
audience: agent
ticket_id: TCK-20261006-PERF-SHEDDING-DOCS-MATCH-SHIPPED-BEHAVIOUR
phase: done
date: 2026-10-06
tags: [performance, engine]
---

# TCK-20261006-PERF-SHEDDING-DOCS-MATCH-SHIPPED-BEHAVIOUR

## Title
Engine docs say what degradation really does: modes shed replay richness, traces, cadence, budgets and concurrency, not work; the periodic and opportunistic shedding path is documented as designed but unused

## Status
DONE

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
Docs only; each correction cites the code it rests on. Citations were re-checked against the tree on 2026-10-06
(`scheduler.py` 103 and 138-139, `kernel.py` 127 and the `set_concurrency_limit` call, `replay_manager.py` 90, 94 and 99,
`governor.py` `force_mode` with no caller).

| Doc (all P1) | What changed |
|---|---|
| `docs/engine/matrices/resource_governor_degradation_matrix.md` | Table cells now equal `GovernorPolicy.from_mode` (Opportunistic CONSTRAINED `Allowed`, no "Reduced 50%"); each non-acting cell is marked mechanism-only, flag-only or value-only; new "Shipped behaviour" section (what acts, notes 1-3 with the code lines); rule 1 and the waterfall get a one-sentence qualification |
| `docs/engine/runtime_profiles.md` §5 | CONSTRAINED and DEGRADED lines say what the levers really are (traces and cadence; replay richness, concurrency, cadence, budgets); one sentence pointing to the matrix |
| `docs/engine/architecture.md` Law 3 | law text kept; added what ships: traces and replay richness shed, fidelity via budgets and cadence, diagnostics step has no effect |
| `docs/engine/project_lawbook.md` Graceful Degradation | law text kept; added that the governor changes the mode and drops no work items |
| `docs/engine/matrices/scheduler_work_model_matrix.md` | PERIODIC and OPPORTUNISTIC rows and the OPPORTUNISTIC paragraph say no instance/producer ships; new "Designed but unused" section (the four items, the tests, retire step 2) |
| `docs/engine/matrices/observability_operational_controls_matrix.md` | `FORCE_DEGRADED` row corrected (see the correction below) |
| `docs/engine/matrices/worker_bounds_matrix.md` | Tick Budget row: mode change, no work shed, overrun is only reported (DEV-014); Local Fallback Triggers item 2: no mode forces local execution |

- **Correction to my own investigation.** `investigation.md` of `TCK-20261006-PERF-SCHEDULER-SHEDS-NOTHING-IN-SHIPPED-RUNS` rated the
  `FORCE_DEGRADED` row "partly true". On re-reading, no code in `src/` reads a `FORCE_DEGRADED` flag at all, so the row now says it
  is not implemented. `ResourceGovernor.force_mode` exists with no caller since the throttle became report-only.
- **Parity ledger (Scope 9):** no entry text repeats a corrected claim; no change.
- **No `src/` or `tests/` change.** The two misleading comments (`observability.py:32`, `governance.py:45`) stay for retire step 2.
- **`worker_bounds_matrix.md` "Local Fallback Triggers" item 2 (added at the planner's request, same claim class):** it said DEGRADED
  or SURVIVAL sets local execution. `force_local` (`worker_manager.py` lines 97 and 104) has no caller in `src/`, so no mode forces
  local execution; modes only lower `concurrency_limit` (`kernel.py`, `set_concurrency_limit`). The item now says so.
- **Not checked:** whether the other `FORCE_*` flags in `observability_operational_controls_matrix.md` (`FORCE_REPLAY_OFF`,
  `SELECT_PROFILE`, `FORCE_NORMAL`) are implemented. Left alone; the planner decides whether to file it.
- **Date:** the doc notes say 2026-10-06 (an earlier draft said 2026-10-07 in error; `date +%F` is 2026-10-06).

## Test Summary
- `tests/docs`: 69 passed, 2 skipped, 1 xfailed. Frontmatter validator: OK on all seven docs. `make knowledge-index-update`: ran (132 files re-embedded).
- No test added or changed (docs only).

## Files Changed
- The seven docs in the table above. Ticket and monitoring records.

## Completion Summary
Seven P1 engine docs now state what degradation does in shipped runs: a mode change reduces replay richness, traces, cadence, phase
budgets and concurrency, and drops no work items. The periodic and opportunistic shedding path is documented as designed but unused
(scheduler work model matrix), with removal folded into `TCK-20261004-WORK-DEBT-RETIRE-STEP2-CODE`. `FORCE_DEGRADED` is documented
as not implemented and no mode forces local execution. No `src/` or `tests/` file changed. Not checked: the other `FORCE_*` flags.
