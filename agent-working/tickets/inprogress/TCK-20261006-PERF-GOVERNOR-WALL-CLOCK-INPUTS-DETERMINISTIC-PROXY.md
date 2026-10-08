---
status: active
layer: performance
authority: P2
audience: agent
ticket_id: TCK-20261006-PERF-GOVERNOR-WALL-CLOCK-INPUTS-DETERMINISTIC-PROXY
phase: inprogress
date: 2026-10-06
tags: [performance, determinism, engine]
---

# TCK-20261006-PERF-GOVERNOR-WALL-CLOCK-INPUTS-DETERMINISTIC-PROXY

## Title
Design (then implement) the Canonical contract's deterministic proxy for the governor's wall-clock inputs: ResourceGovernor's tick_compute_ms (PERF-D1 input 1) and PhaseBudgetGovernor's per-phase costs

## Status
INPROGRESS

## Tier
standard

## Type
feature

## Priority
P2

## Request Summary
After PR #379 (`33588b966`), the kernel's own budget checks (PERF-D1 inputs 2 and 3) are report-only,
and the salience coupling (input 4) is the RPG-core salience fix. Two wall-clock inputs still change
what a run computes when `audit_mode` is off:

1. **`ResourceGovernor._get_indicated_mode`** (`src/engine/governor.py`, about lines 78-105) picks
   `RuntimeMode` from measured `tick_compute_ms`. The mode then sets cadence, LOD, scan policy and
   concurrency.
2. **`PhaseBudgetGovernor.evaluate`** (`src/engine/phase_governor.py`, called from `governor.py` line
   62) reads `signals.phase_costs_ms` (about line 109) and `tick_compute_ms` (about line 139), and sets
   scan policy and the candidate, strategic and movement budgets. It is already listed as a remaining
   input in `deterministic_execution.md` ("Inputs the Canonical proxy set must replace").
   During #379 it broke a non-audit hash-equality test in 1 of 3 runs (diverging at tick index 2),
   which is why that test was removed.

Both signals are measured in `src/engine/kernel.py` (`_record_runtime_signals` and the pressure-signal
build in `_phase_init`). So the fix needs `kernel.py`, which is gated again since #379 merged. By the
owner's decision of 2026-10-06 (roadmap gate item 6.4), this half waits for the **full no-touch
window**.

PERF-D1 (approved 2026-10-03) fixes the target, so this ticket designs and implements to it:
- **Canonical contract:** pressure signals are deterministic proxies, such as work-unit counts or queue
  depth against a fixed ceiling. No wall-clock or host-resource reading may influence authoritative
  state. Same build, configuration, seed and initial state give the same canonical hash at every tick.
- **Live bounded contract:** real signals are allowed, but every decision that changes what is computed
  goes into a versioned control trace (the Live half may be a separate ticket; see Scope 4).

The memory, replay-backlog and utilization inputs are also on the Canonical proxy list. Include them in
the design (Scope 1); whether they are implemented here or split out is the design's call.

## Scope
1. **Design first** (`plan.md`, perf-planner reviews it before any code). Cover:
   - the proxy for each input: tick cost becomes a work-unit count (what is counted: entities processed,
     results resolved, candidates scanned?), per-phase cost becomes per-phase work units, plus memory,
     replay backlog and utilization;
   - how a profile's thresholds (`max_tick_budget_ms` and the governor's ratios) map to work-unit
     thresholds, and whether `RuntimeProfile` needs a new field;
   - how the contract is selected (Canonical vs Live): a profile or kernel flag. And what `audit_mode`
     becomes (does Canonical replace it?);
   - what this does to existing tests that patch `time.perf_counter_ns` to drive the mode
     (`test_milestone_b_closure.py` uses a tick-keyed fake clock since #373, and others);
   - the PERF-D6 phase-catalog link, if the catalog defines per-phase work units.
2. **Implement the Canonical half** once the design is approved and the full window is open: the
   governor and `PhaseBudgetGovernor` read only proxies under Canonical. `kernel.py` computes them.
3. **Proof:** a non-audit, Canonical-mode hash-equality test over a scenario that crosses mode
   thresholds (the test #379 had to remove) passes reliably. Run it at least 10 times in CI-like
   conditions and record the results.
4. **Live half:** state in the design whether it is in this ticket or a follow-up. If it is a follow-up,
   file it.
5. Docs: `deterministic_execution.md` ("What runs today", "Inputs the Canonical proxy set must
   replace"), `runtime_profiles.md` §4, the PERF-D1 status, the parity ledger, and an
   intentional-divergence entry if gameplay under load changes.

## Out of Scope
- The salience coupling (RPG-core salience fix).
- Work-unit budgets for the kernel's report-only checks (only if a measurement shows the need).
- What shedding does in production (`TCK-20261006-PERF-SCHEDULER-SHEDS-NOTHING-IN-SHIPPED-RUNS`
  answers that first, and this design should use its answer).

## Acceptance Criteria
1. `plan.md` covers every item in Scope 1 and is approved by perf-planner, and by the owner where a
   PERF decision is touched, before any `src/` edit.
2. No `src/` edit before the full no-touch window opens (or a new owner partial lift naming
   `kernel.py`), recorded in the ticket.
3. Under Canonical, neither governor reads a wall-clock or host-resource value. A test enforces it,
   for example by patching `time.perf_counter_ns` to vary and asserting the same mode and budgets.
4. The Scope 3 hash-equality test passes 10 of 10 runs.
5. Docs and parity ledger updated. `wall_clock_inventory --check` passes after regeneration with the
   tool.
6. `uv run make code-health` and `uv run make typecheck-py` report no new or worse finding.

## Related Tickets
- `TCK-20261006-PERF-TICK-BUDGET-THROTTLE-REPORT-ONLY` (done; inputs 2 and 3)
- `TCK-20261003-SALIENCE-WALL-CLOCK-PRICE-COUPLING` (input 4, RPG-core Lane A)
- `TCK-20261006-PERF-SCHEDULER-SHEDS-NOTHING-IN-SHIPPED-RUNS` (answer this first)
- `TCK-20261004-WORK-DEBT-RETIRE-STEP2-CODE` (same window; `work_debt_total` is one of
  `PhaseBudgetGovernor`'s inputs)
- PERF-M1-T05

## Related Docs
- `docs/architecture/performance_optimization_decisions.md` (PERF-D1, amendment A1, PERF-D6)
- `docs/engine/deterministic_execution.md`, `docs/engine/runtime_profiles.md`
- `docs/performance/wall_clock_inventory.md`
- `docs/plans/design_enhancement/performance_optimization/performance_optimization_roadmap.md` (gate item 6)

## Related Stored Artifacts
- `agent-working/stored_artifacts/TCK-20261006-PERF-TICK-BUDGET-THROTTLE-REPORT-ONLY/` (the removed
  hash test and its 1-in-3 divergence)
- `agent-working/staging_artifacts/TCK-20261006-PERF-GOVERNOR-WALL-CLOCK-INPUTS-DETERMINISTIC-PROXY/` (design: investigation, plan, test_plan, probes; moves to stored when the ticket closes)

## Related Code Areas
- `src/engine/governor.py`, `src/engine/phase_governor.py`, `src/engine/kernel.py`
  (`_record_runtime_signals`, signal build), `src/core/governance.py` (`PressureSignals`),
  `src/config/profiles.py`

## Assumptions / Open Questions
- Is a work-unit count stable across executors (sequential, thread, process)? It must be, for
  Canonical. The design must show it.
- Does Canonical replace `audit_mode`, or do both stay? This is an owner-facing choice. Put it in the
  plan as a question.

## Implementation Notes
- **2026-10-06, design written (Scope 1, AC 1 draft):** `investigation.md` (inventory of every signal that reaches the two governors, with
  the decision each drives, verified against the tree and `wall_clock_inventory --check`; a read-only probe), `plan.md` (a proxy for each
  input, threshold mapping, contract selection as an OWNER QUESTION with three options and a recommendation, the Live half as a follow-up,
  fate of the tests that drive modes, per-file size estimate) and `test_plan.md` (the Canonical hash-equality test, 10 of 10; the test that
  varies `perf_counter_ns`). No `src/` or `tests/` file was touched. The ticket stays INPROGRESS: AC 1 needs perf-planner's approval and
  the owner's answers, and the code waits for the full no-touch window (AC 2).
- **Owner decisions 2026-10-06 (recorded by perf-planner in `performance_optimization_decisions.md`, PERF-D1 "Update 2026-10-06"):**
  Option 1 (`signal_contract` on `RuntimeProfile`, default `LIVE`, `audit_mode` unchanged); Q-A accepted (memory and replay backlog are not inputs
  under Canonical); Q-B accepted (thresholds keep their ms meaning as reference-host ms). The Live half is a separate ticket,
  `TCK-20261006-PERF-LIVE-CONTROL-TRACE`. Design commit `8fc5e711a`; `plan.md` section 3 carries the decision line. The ticket stays INPROGRESS:
  the code waits for the full no-touch window (AC 2) and `plan.md` step 1 (calibration) comes first.
- **rpg-planner review of PR #384, four points accepted (mirrored from `plan.md`):** (1) step 1 calibration has preconditions: the two RPG-core bench
  defects (`TCK-20261006-COOPERATION-PENDING-OFFER-SCAN-IS-QUADRATIC-PER-TICK`, `TCK-20261006-COMBAT-ENGAGEMENT-HOSTILITY-PROJECTION-COST-STEP`)
  merged first, or the `cooperation` and `combat_engagement` buckets excluded from the fit; the artifact records the RPG-core base commit; re-check the
  error band after the salience fix, Lane B's spawn-faction batch and CONFLICT-03; a risk line says the probe's x2.7 error may partly come from the
  quadratic. (2) step 2 rebases on the salience fix (same `_phase_init` region), re-measure `kernel.py` headroom, no parallel work. (3) if Option 2 ever
  makes CANONICAL the default for tests, `test_catalog_entity_spawn_wiring` (#367) must set `signal_contract=LIVE` explicitly, as must any other
  governor-pinned test that relies on the default.
- **2026-10-08, Phase A (core window, owner gate item 7):** step 1 calibration `0985734d4` (WORK_MODEL_V1 0.68 / 7.42 reference-ms, PROVISIONAL, pooled R^2 0.874,
  per-family 0.58 to 1.35, executors 0.92 / 0.83; `report.md` in the staging artifacts); the kernel double-count fix found there is its own ticket
  (`TCK-20261008-PERF-KERNEL-RESOLUTION-OVERHEAD-DOUBLE-COUNTS-SUB-PHASES`, `df2f34f43`); step 2 `36af39b3f` (signal source split, `work_units.py`, `PressureSignals`
  optional fields, `RuntimeProfile.signal_contract`; Live bit-identical per a golden fixture recorded from the pre-move code; `src/config/loader.py` typing-only edit);
  step 3 (Canonical source, governors read the effective cost, proof tests).
- **Changed in step 3, with the reason (plan.md section 2):** (1) queue and worker proxies use `entities_active`, not `_current_work_items`: scheduled items are post-policy and
  would break the cost-is-demand rule; (2) Canonical counts demand from the state about to be processed, so it has no one-tick lag; (3) `tick_budget` stays unset under Canonical
  (owner decision Q-B). The per-phase rules of `PhaseBudgetGovernor` are dropped under Canonical by giving the source an empty `phase_cost` (no contract branch in the governor).
- **Limit of the anti-thrash proof:** it is synthetic (the real governor and `RuntimeStatus` driven with flip-flopping modelled-cost sequences), because no kernel scenario changes its
  modelled cost mid-run. The run-level proofs (10 of 10 identical mode, budgets and hashes) use a constant modelled cost just over a threshold. Not filed as a follow-up: an honest limit.

## Test Summary

## Files Changed

## Completion Summary
