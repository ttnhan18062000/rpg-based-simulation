---
status: active
layer: performance
authority: P2
audience: agent
ticket_id: TCK-20261006-PERF-SCHEDULER-SHEDS-NOTHING-IN-SHIPPED-RUNS
phase: implement
date: 2026-10-06
tags: [performance, engine]
---

# TCK-20261006-PERF-SCHEDULER-SHEDS-NOTHING-IN-SHIPPED-RUNS

## Title
No shipped run registers a sheddable periodic task, so the governor's DEGRADED and SURVIVAL work shedding is a no-op: investigate and give the owner a decision

## Status
INPROGRESS

## Tier
standard

## Type
chore

## Priority
P2

## Request Summary
Found by perf-implementer during `TCK-20261006-PERF-TICK-BUDGET-THROTTLE-REPORT-ONLY` (PR #379) and
recorded in `intentional_divergences.md` DEV-014: `DeterministicScheduler()` is built with no
`PeriodicDefinition`, and nothing in `src/` registers one (`grep "PeriodicDefinition(" src` is empty on
`main` at `33588b966`). `_phase_scheduling` calls `self._scheduler.select_work(state, policy)` and
records what it sheds, so with no periodic task it never sheds. Before PR #379, the wall-clock throttle and its `9999`
sentinel were the only sources of `dropped_work`. Now `total_dropped_work` is 0 in shipped runs.

So the governor's modes reduce scan policy, cadence and budgets (through `PhaseBudgetGovernor`), but
the "shed non-authoritative work" half of DEGRADED and SURVIVAL does nothing in production. The engine
docs and the governance contract may promise otherwise. `test_work_debt_stays_empty_in_production.py`
now registers a test-only periodic task to get real shedding.

This matters for perf in three ways:
- the capacity run (M2) needs to know what degradation actually does;
- PERF-M1-T05 (the invalidation ledger) needs to know whether any baseline's `dropped_work` number
  ever meant anything (the old values were the throttle's drops or `9999`);
- the governor-half design (`TCK-20261006-PERF-GOVERNOR-WALL-CLOCK-INPUTS-DETERMINISTIC-PROXY`) needs
  to know what a mode change controls.

This ticket is **investigation and decision only**: read-only, no `src/` edit, so the gate does not
block it.

## Scope
1. Find every place that defines, documents or tests periodic or sheddable work: `src/engine/scheduler.py`,
   the governor's policies (`concurrency_limit`, any `shed_*` field), `PhaseBudgetGovernor`, the engine
   docs (`docs/engine/kernel.md`, `runtime_profiles.md`, `governance_logic.md`) and the parity ledger.
   For each, say what it promises about shedding under DEGRADED and SURVIVAL.
2. Git history: was a `PeriodicDefinition` ever registered in `src/`? If so, when and why was it
   removed? If not, was the mechanism ever wired?
3. List what a mode change actually changes in a shipped run today (scan policy, budgets, cadence,
   concurrency, replay richness), with code citations.
4. Baselines: list committed baselines or reports that record `dropped_work` or
   `total_dropped_work`, and say what those numbers actually counted. This is an input to PERF-M1-T05.
5. Options for the owner, with costs:
   (a) register real non-authoritative periodic tasks (name candidates, if any exist);
   (b) remove the dead periodic-shedding path and correct the docs;
   (c) keep the code, document it as unused, and mark any parity entry that claims shedding as
       `unsupported`.
   Recommend one.

## Out of Scope
- Implementing any option (a follow-up ticket after the owner decides).
- Governor thresholds and the wall-clock inputs (the governor-half ticket).

## Acceptance Criteria
1. `investigation.md` holds Scope 1-4 with file and line citations for each claim.
2. The options in Scope 5 are written down, with one recommendation, and put to the owner.
3. Every doc or parity entry that promises shedding is listed as true, false or partly true.
4. No `src/` file is edited.

## Related Tickets
- `TCK-20261006-PERF-TICK-BUDGET-THROTTLE-REPORT-ONLY` (done; where this was found)
- `TCK-20261006-PERF-GOVERNOR-WALL-CLOCK-INPUTS-DETERMINISTIC-PROXY`
- `TCK-20261004-WORK-DEBT-NEVER-ACCUMULATES-IN-PRODUCTION` (same pattern: a counter with no producer)
- PERF-M1-T05 (consumes Scope 4)

## Related Docs
- `docs/guidelines/intentional_divergences.md` (DEV-014)
- `docs/engine/governance_logic.md`, `docs/engine/runtime_profiles.md`, `docs/engine/kernel.md`
- `docs/architecture/performance_optimization_decisions.md` (PERF-D1, PERF-D3)

## Related Stored Artifacts
- `agent-working/stored_artifacts/TCK-20261006-PERF-TICK-BUDGET-THROTTLE-REPORT-ONLY/`
- `agent-working/stored_artifacts/TCK-20261006-PERF-SCHEDULER-SHEDS-NOTHING-IN-SHIPPED-RUNS/` (investigation with the citations, plan, test_plan)

## Related Code Areas
- `src/engine/scheduler.py`, `src/engine/kernel.py` (`_phase_scheduling`), `src/engine/governor.py`,
  `src/engine/policy.py`, `src/engine/phase_governor.py`

## Assumptions / Open Questions
- The planner assumes no shipped code path registers periodic work dynamically (for example from world
  content). Verify this; a dynamic registration would change the finding.

## Implementation Notes
Full evidence with file:line citations is in `investigation.md`. Summary:
- **Confirmed and wider.** `select_work` can shed nothing in shipped runs: `kernel.py:127` builds the scheduler with no
  `PeriodicDefinition`, and `scheduler.py:31` is the only place `_periodic_defs` is ever assigned. Three of the four rungs of
  the documented shedding waterfall (diagnostic verbosity, opportunistic work, non-authoritative periodic work) have no
  effect: `diagnostic_verbosity` and `metrics_detail` have no reader, `allow_opportunistic` is read only by an empty branch
  (`scheduler.py:138-139`). Degradation still works through phase budgets, cadence, concurrency, replay richness and traces.
- **Planner's assumption holds:** nothing registers periodic work dynamically; no `scheduler=` is passed to `Kernel(`, no
  mutator exists, and no code loads definitions from world content.
- **History:** `PeriodicDefinition(` was never instantiated outside tests on any branch (only `tests_v2`, `tests_legacy`, `tests`).
  The mechanism was added in `562116889` (2026-05-18) with no registration. It was designed and never wired, not removed.
- **Second dead path found:** `periodic_updates` has no producer, so `periodic_due_ticks` (in the canonical hash) never advances,
  and the executor has no branch for periodic work kinds, so even a registered task would do nothing.
- **Promises:** 12 doc/code statements classified true/false/partly in `investigation.md` (matrix, runtime_profiles, architecture,
  lawbook, scheduler matrix, observability matrix, worker bounds, two code comments). No parity-ledger entry claims scheduler
  shedding as verified. The unit tests are valid specs of the mechanism with test-registered definitions only.
- **Baselines (input to PERF-M1-T05):** no committed baseline file carries `dropped_work`. Before #379 the live value summed throttle
  drops and a `9999` sentinel per overrun; since #379 it is 0. Any externally stored series from before 2026-10-06 is
  incomparable and must not be read as a degradation measure.
- **Options and recommendation:** (a) register real non-authoritative tasks (no candidate exists; needs executor branch,
  `periodic_updates` producer and gated state edits); (b) remove the dead path (touches the canonical hash scheme and gated files);
  (c) keep, document as unused, correct the docs. **Recommendation: (c) now, and fold the removal part of (b) into work-debt retire
  step 2**, which already needs a PERF-D5 scheme bump for the hashed `work_debt` field; `periodic_due_ticks` can ride the same bump.
- **Decision:** the owner's. **PENDING.** Nothing was implemented.

## Test Summary
No tests added or changed (read-only). The read-only checks run are listed in `test_plan.md`.

## Files Changed
- No `src/` file. Ticket, staging artifacts (moved to stored on close), working log and monitoring records only.

## Completion Summary
