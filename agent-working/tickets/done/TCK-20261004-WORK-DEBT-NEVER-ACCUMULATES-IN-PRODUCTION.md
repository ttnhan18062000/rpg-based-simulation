---
status: historical
layer: performance
authority: P2
audience: agent
ticket_id: TCK-20261004-WORK-DEBT-NEVER-ACCUMULATES-IN-PRODUCTION
phase: done
date: 2026-10-04
tags: [performance, engine, bug]
---

# TCK-20261004-WORK-DEBT-NEVER-ACCUMULATES-IN-PRODUCTION

## Title
`AuthoritativeState.work_debt` has no production writer that increases it, so every debt-driven signal is permanently zero

## Status
DONE

## Tier
standard

## Type
bug

## Priority
P2

## Request Summary
Found by perf-planner on 2026-10-04 while reviewing `TCK-20261004-PERF-M1-DEBT-HARNESS-CORRECTNESS`,
at `origin/main` `9793aee08`. The ticket's implementer could not make debt accumulate through the
kernel and had to seed it. perf-planner traced every writer:

- `AuthoritativeState.work_debt: Dict[str, int]` (`src/core/state.py:1423`) changes only in
  `apply.py` (around line 323), as `max(0, prior + delta)` over `StateUpdate.work_debt_updates`.
- The kernel fills `work_debt_updates` only from `WorkerResult.work_debt_update`
  (`src/engine/kernel.py`, around line 647).
- The only producer of `work_debt_update` is the executor's `DRAIN_DEBT` branch
  (`src/engine/executor.py`, around lines 192 and 338). It sets it to
  `SimulationDomainLogic.drain_debt()`, which returns `-profile.max_worker_count`. That value is
  always negative or zero.
- The scheduler emits `DRAIN_DEBT` only for systems already in `state.work_debt`
  (`src/engine/scheduler.py`, around line 124).
- Dropped work is recorded in `RuntimeStatus` counters (`record_dropped_work`), not in
  `state.work_debt`.
- The only code that increases it is `src/certification/scenarios.py::inject_work_debt`, which is
  test and certification scaffolding.

So in ordinary play `work_debt` starts empty and stays empty. Everything derived from it is
constant zero:
- the governor's `work_debt_total` and its debt-based mode thresholds and recovery limit
  (`governor.py`, `phase_governor.py`);
- the kernel's `debt_ratio`;
- the work-debt term of `global_salience`.

This matters for `TCK-20261003-SALIENCE-WALL-CLOCK-PRICE-COUPLING`. That fix keeps the work-debt
term and removes the compute term, so after it lands `global_salience` is always 0 in production,
and the salience price multiplier is always 1.

PERF-D3 (closed) says capacity debt is the aggregate counter. The counter exists, but no production
path produces debt. Either a producer was lost or never built, or the dropped-work counter was
meant to be the debt.

## Scope
- Confirm the trace with a test: a long run of each non-combat perf scenario at a tight profile
  (dropped work recorded) ends with empty `state.work_debt`
- Find the intent: search git history and docs (`docs/engine/contracts/resource_governor_contract.md`,
  the Milestone C notes behind `drain_debt`) for where debt was meant to be produced
- Recommend one of:
  - wire a deterministic producer (PERF-D1 A1: no wall-clock input);
  - retire `work_debt` and the dead governor branches;
  - document it as certification-only.

  The recommendation goes to the owner as a decision, not an implementation

## Out of Scope
- Implementing the producer or the retirement. That needs an owner decision, and the files
  involved (`kernel.py`, `apply.py`, `governor.py`, `state.py`) are gated
- The salience fix itself (RPG-core track)

## Acceptance Criteria
1. A test shows `state.work_debt` stays empty across real runs in which dropped work is non-zero
2. The ticket lists every reader of `work_debt` and says which behaviour is dead because of it
3. A recommendation (producer, retire, or certification-only) with evidence is recorded in the ticket and sent to perf-planner for the owner; the decision itself is out of scope

## Related Tickets
- `TCK-20261004-PERF-M1-DEBT-HARNESS-CORRECTNESS` (where it was found)
- `TCK-20261003-SALIENCE-WALL-CLOCK-PRICE-COUPLING` (its remaining salience term is this zero)
- `TCK-20261004-PERF-M1-TIED-WORKER-RESULT-VERIFICATION` (the kernel's `work_debt_updates[...] =` is last-writer-wins for tied system results)

## Related Docs
- `docs/architecture/performance_optimization_decisions.md` (PERF-D3, PERF-D1)
- `docs/engine/contracts/resource_governor_contract.md`

## Related Stored Artifacts
- none

## Related Code Areas
- `src/core/state.py`, `src/engine/apply.py`, `src/engine/kernel.py`, `src/engine/executor.py`,
  `src/engine/scheduler.py`, `src/engine/domain_logic.py`, `src/engine/governor.py`,
  `src/engine/phase_governor.py`, `src/certification/scenarios.py`

## Assumptions / Open Questions
- **Owner decision 2026-10-04: investigate first.** This ticket now runs as investigation only, under the partial lift: the confirming test (AC1), the reader list (AC2), and a history/doc search for the intended producer. No `src/` edit at all. AC3 becomes: a written recommendation (producer / retire / certification-only), with evidence, put to the owner. The chosen change is a separate ticket that waits for the gate if it touches gated files
- This trace is a code read plus a keyword search, not a proof. The confirming test is AC1

## Implementation Notes
Investigation only: no `src/` file was edited. Findings, then the recommendation.

### Writers (confirmed, AC1 trace)
| Where | What it does | Can it raise debt? |
|---|---|---|
| `src/engine/apply.py:322-324` | `max(0, prior + delta)` over `StateUpdate.work_debt_updates` | only if a delta is positive |
| `src/engine/kernel.py:647-648` | `work_debt_updates[subsystem_id] = res.work_debt_update` (last-writer-wins) | only passes a delta through |
| `src/engine/executor.py:206, 350` | the only producer of `work_debt_update`: `SimulationDomainLogic.drain_debt()` = `-profile.max_worker_count` | no: always <= 0 |
| `src/engine/scheduler.py:124` | emits a `DRAIN_DEBT` item only for a system already in `state.work_debt` with debt > 0 | no: needs existing debt |
| `src/certification/scenarios.py:33` `PressureInjector.inject_work_debt` | adds to a state's debt | yes, but it has **no caller** in `src/`, `tests/` or `tools/` |
Nothing else assigns `work_debt`. Dropped work is counted in `RuntimeStatus.total_dropped_work` and never written to `state.work_debt`.

### Readers of `work_debt` / `work_debt_total`, and what is dead because of it (AC2)
Because `state.work_debt` is always `{}`, every `work_debt_total` is 0, so each condition below is constantly false:
| Reader | Use | Consequence in production |
|---|---|---|
| `governor.py:76` | `work_debt_total >= max_work_debt` -> SURVIVAL | dead branch |
| `governor.py:84` | `>= max_work_debt * 0.5` -> DEGRADED | dead branch |
| `governor.py:145, 154` | recovery limit: debt must be under half the maximum | always satisfied, never gates recovery |
| `phase_governor.py:138-139` | `work_debt_total > max_debt * 0.7` (an OR with the compute term) | debt half never fires; only compute can |
| `kernel.py:665` | `debt_ratio = work_debt_total / max_work_debt` | always 0.0 |
| `kernel.py:667` | `global_salience = min(2.0, debt_ratio + compute_ratio)` | equals `compute_ratio`, a wall-clock quantity |
| `economy.py:26-27` | reads `global_salience` (price pressure) | price pressure follows wall-clock compute only; after `TCK-20261003-SALIENCE-WALL-CLOCK-PRICE-COUPLING` removes the compute term it is constant 0 and the price multiplier is constant 1 |
| `kernel.py:543, 559, 811`, `observability.py:25,120,128`, `runtime_status.py:58`, `governance.py:32` | build the `work_debt_total` pressure signal | constant 0 |
| `scheduler.py:124` and `executor.py` DRAIN_DEBT branch, `domain_logic.drain_debt`, `apply.py:322` clamp, `ProtocolValidator` per-subsystem rule (PERF-M1 hotfix), T04 tied-result analysis | the consumer half | unreachable in production (never see a positive debt) |
| `api/engine_manager.py:205`, `observability/live/snapshot_provider.py:136`, `prometheus_collector.py:63-66` (`sim_work_debt_total`), `certification/harness.py:154`, `certification/models.py:69,84` | reporting | always report 0 |
| `observability/understanding/rootcause/rules.py:255` `GovernorPressureFromObservabilityOrWorkDebt` | root-cause hypothesis | its debt half never fires |
| `checkpoint.py:126` (`CanonicalStateHasher`) | hashes `work_debt` | hashes an empty dict |
| `src/config/profiles.py`, `src/perf/profiles.py` `max_work_debt` | the threshold field | its only readers are the dead branches above |
Not dead: the `dropped_work_delta` signal is stored but nothing in the governors reads it (`git grep` shows only copies into status and reporting), so shedding work does not itself raise any pressure signal.

### Confirming test (AC1)
`tests/integration/kernel/test_work_debt_stays_empty_in_production.py` (5 tests, 7.5 s): for idle, movement, resource and strategic at 120 entities, 12 ticks, the smallest accepted tick budget (1.0 ms) and `audit_mode` off, the governor leaves NORMAL (DEGRADED and SURVIVAL), `total_dropped_work` is about 70 000, and `state.work_debt` is `{}` after every tick with the governor's debt signal 0 on every tick. A control test seeds debt through `PressureInjector.inject_work_debt` and shows the same recorder sees it (`[{"SYS_A": 5}] * 4`, signal 5), so the empty result is not a blind spot.
Caveat on "dropped work": the roughly 70 000 is dominated by a literal `record_dropped_work(9999)` per tick after tick 5 in `kernel.py:463` (7 ticks x 9999 plus a few real counts). It is a sentinel for a watchdog overrun, not a measure of shed items. The real shedding is the mid-tick throttle in `_phase_resolution` and the scheduler's non-authoritative periodic drops. The test needs only that something was shed, not how much.

### Intent: where debt was meant to be produced (history and docs)
- Design (Milestone 4): `docs/engine/matrices/scheduler_work_model_matrix.md` defines DEFERRED as "Accumulated when prior-tick work overflowed. Drained in order on the next tick. Bounded by profile capacity: overflow is rejected, never silently discarded." The M4 stored plan (`TCK-20260418-RESOURCE-KERNEL-M4`) specified a `BoundedBuffer` with a `REJECT` policy and tests `test_debt_limit_reject` / `test_debt_overflow_reject`. `resource_governor_contract.md` defines `work_debt` as "total count of postponed authoritative items".
- Built: the consumer half (scheduler DEFERRED emission, `DRAIN_DEBT`, apply, governor thresholds, signal, reporting).
- Never built: the producer half, "overflowed work becomes debt". The history has 363 commits since the initial commit on 2026-02-08. Across every commit that touches `work_debt`, `work_debt_updates` or `drain_debt`, no added line increases debt: the only debt-changing additions are the generic clamp in `apply.py` and `work_debt_update=drain` (a negative drain). The other "debt" matches are unrelated (`sleep_debt`, social `OLD_DEBT_COLLECTED`). The tests that exist (`tests/unit/core/test_deferred_work_debt.py`) seed debt by hand.
- The overflow tests the matrices name (`test_debt_limit_reject`, `test_debt_overflow_reject`) are not in `tests/`. A `BoundedBuffer` with a REJECT overflow policy exists (`src/core/retention.py`), but it is used only by the replay buffer (`src/engine/replay_buffer.py`), never for work debt: debt is an integer counter per system with no capacity check beyond the governor's `max_work_debt` threshold.
- Design tension: the engine does not keep a work backlog. Each tick the scheduler re-derives what is due from state (readiness, cadence, `periodic_due_ticks`), so a postponed item is already represented in state. A separate debt counter would duplicate that. PERF-D3 (closed) already decided no semantic deferred-work queue and "capacity debt is the aggregate counter"; its own evidence line says the counter is only ever written through `work_debt_updates`, which matches this finding.
- Limit of this search: a keyword search (`git log -S`/`-G` for `work_debt`, `work_debt_updates`, `drain_debt`, and a scan of the added lines of every commit that touches them) of this repository's 363 commits, not a proof. A producer that used other names (for example a queue-length counter written under a different field) would not match.

### Recommendation (AC3): retire, in two steps; do not build a producer now. **Status: pending owner decision.** **Owner decision 2026-10-04: RETIRE, in two steps, as recommended.** Step 1 (docs): `TCK-20261004-WORK-DEBT-RETIRE-STEP1-DOCS`; step 2 (code, gated): `TCK-20261004-WORK-DEBT-RETIRE-STEP2-CODE`.
1. **Now, ungated, docs and tests only (NOT done in this ticket; perf-planner files it separately if the owner chooses it):** state the truth. Label `work_debt` as certification/injection-only in `resource_governor_contract.md` and the scheduler matrix (they currently say it counts postponed authoritative items), and keep the new test as the guard that production debt is empty.
2. **When the gate lifts, with an owner decision:** retire `work_debt` and its dead branches (governor 76/84/145/154, phase_governor, `debt_ratio`, the salience debt term, the `DRAIN_DEBT` path, the validator rule, the telemetry gauge and the `max_work_debt` profile field). That edits `state.py`, `apply.py`, `kernel.py`, `governor.py`, so it is gated and is a separate ticket.
Why not a producer: a producer needs a definition of "overflowed work" that is deterministic. Today's shedding signals are wall-clock-driven (the mid-tick throttle, the 9999 watchdog sentinel, and the governor mode itself outside `audit_mode`), so feeding them into `work_debt` would put wall-clock time into `global_salience` and prices, which PERF-D1 amendment A1 forbids. A deterministic overflow count would need a new feature contract (PERF-D3's own revisit condition) and a real backlog the engine does not have.
Why not certification-only as the end state: nothing, not even certification, uses the injector; keeping dead production branches only for a scenario that never injects debt is cost without a user.
Decision criteria for the owner: choose **producer** only if a debt-driven pressure or pricing feature is wanted (then write its feature contract first); choose **retire** if the governor should react to compute and memory only; choose **certification-only** if the governor's debt branches should stay as stress-test hooks (then wire `inject_work_debt` into the `WORK_DEBT_BUILDUP` scenario so something exercises them).
Effect on the salience ticket: `TCK-20261003-SALIENCE-WALL-CLOCK-PRICE-COUPLING` keeps the debt term, so after it lands `global_salience` is a constant 0 unless a producer exists. If the owner picks retire, that ticket should drop the salience term entirely instead of keeping a zero.

## Test Summary
- `tests/integration/kernel/test_work_debt_stays_empty_in_production.py`: 5 passed in 7.5 s (4 non-combat scenarios under a tight budget with `audit_mode` off, plus the seeded-debt control). Run with `-m "not slow and not extra_slow"` under a 3 GB cap.
- Not marked `slow`. The runs measure counters, not timings, so they are not flaky on counters; the precondition (`total_dropped_work > 0` and the governor leaving NORMAL) is asserted in each test so a machine fast enough to avoid shedding would fail loudly, not pass vacuously.

## Files Changed
- `tests/integration/kernel/test_work_debt_stays_empty_in_production.py` (new)
- No `src/` file. `docs/REGISTRY.yaml` regenerated at close.

## Completion Summary
The investigation is complete and edits no `src/` file. `state.work_debt` is confirmed empty in ordinary runs even while work is dropped (5 tests), every reader is listed with what is dead because of it, and a recommendation (retire in two steps, no producer) is recorded as pending owner decision and sent to perf-planner. The chosen change is a separate ticket.
