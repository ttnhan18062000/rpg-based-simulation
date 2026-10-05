---
status: active
layer: performance
authority: P2
audience: agent
ticket_id: TCK-20261005-PERF-M1-ZERO-CAPACITY-SIGNAL
phase: open
date: 2026-10-05
tags: [performance, determinism, testing, engine]
---

# TCK-20261005-PERF-M1-ZERO-CAPACITY-SIGNAL

## Title
PERF-M1-T01: zero-capacity worker and queue signals follow PERF-D1, with specification tests and a baseline disposition

## Status
OPEN

## Tier
standard

## Type
bug

## Priority
P2

## Request Summary
Released by the owner on 2026-10-05 (`performance_optimization_roadmap.md`, "Gate definition and
partial lift", item 5): the combat nondeterminism root cause was `id()`-keyed de-duplication in
`src/core/dirty.py`, the governor was in `NORMAL` throughout, so `governor.py` joins the partial
lift for this ticket.

PERF-D1 (`docs/architecture/performance_optimization_decisions.md`, "Zero-capacity semantics",
answering conflict C-03) fixes the contract:

- zero workers means synchronous execution: worker utilization does not apply and reports `0.0`
  (already true since `TCK-20260911-WORKER-UTILIZATION-ZERO-WORKERS-DEGRADED-MISTRIGGER`; PERF-D1
  ratifies it);
- zero queue depth with zero workers means no queue exists: queue utilization reports `0.0`;
- zero queue depth with one or more workers is a configuration error, rejected when the worker
  manager is built, not reported as permanent saturation;
- idle is `0.0`, saturated is `1.0`, and "unavailable" is never encoded as a utilization value.

Live code on 2026-10-05: `WorkerManager.get_stats()` (`src/engine/worker_manager.py`, about line
242) still returns queue utilization `1.0` when `max_queue_depth <= 0`, and `__init__` accepts any
value. `ResourceGovernor._get_indicated_mode()` (`src/engine/governor.py`, about line 99) reads
`>= 0.9` as DEGRADED. So a zero-queue manager forces DEGRADED from tick 1.

**Reachability, read by the planner (verify it):** the kernel builds its manager from
`RuntimeProfile.max_queue_depth`, which `src/config/profiles.py` declares `gt=0`. The other `src/`
constructions (`campaigns/runner.py`, `scenario_checkpoint.py`, `scenario_runtime.py`,
`observability/readiness/harness.py`) pass 500 or 1000. If that holds, the queue half is a latent
defect: no shipped run has hit it, and it affects no baseline. The worker half did affect runs: any
run with zero workers (for example `PERF_512MB_LOCAL`, the `*_local` baselines) taken before the
worker fix landed went DEGRADED from tick 1.

## Scope
1. `src/engine/worker_manager.py`:
   - reject `max_queue_depth <= 0` with `max_workers >= 1` at construction (a `ValueError` with a
     message naming both values);
   - report queue utilization `0.0` when no queue exists (`max_workers == 0` and
     `max_queue_depth <= 0`);
   - decide and test negative inputs (`max_workers < 0`, `max_queue_depth < 0`): reject, or treat
     as zero. Record the choice in the ticket. Do not silently clamp without a test.
2. "Unavailable": find whether any state exists in which the manager or its pool cannot report
   (for example after shutdown, or a broken process pool that falls back to local execution). If
   one exists, it must not be signalled through a utilization value; record how it is signalled
   instead (or that it is not signalled today, as a finding). Do not invent a new typed field
   unless the state exists and needs one.
3. Specification tests, written from PERF-D1, not from current output, one per state the M1 epic
   names: unavailable (if it exists), disabled (zero workers), local (work forced to local
   execution because the queue is at its limit), configured-zero (each of the zero combinations
   above, including the rejected one), idle (`0.0`), busy (between), saturated (`1.0`).
4. Governor tests in `tests/unit/resource/test_resource_governor_contract.py` (no `governor.py` edit expected):
   `get_stats()` output from the disabled and no-queue configurations does not move
   `ResourceGovernor` out of `NORMAL` on its own, and a saturated configuration still reaches
   DEGRADED. If an edit to `governor.py` turns out to be needed, stop and tell the planner first.
5. Baseline disposition: list every committed baseline whose run used zero workers or zero queue
   depth (start with `docs/observability/baselines/*_local.json`, `perf_baselines.json`, and
   anything `tools/perf/perf_baseline.py` writes), and give each one retain, rerun or incomparable,
   with the reason. Use the date the worker fix's code landed in git (not the ticket file's date)
   against each baseline's capture date. This list is an input to `PERF-M1-T05`; do not rerun any
   baseline here (measurements stay provisional under the gate).
6. Docs and parity: update `docs/engine/deterministic_execution.md` or `docs/engine/runtime_profiles.md`
   wherever they state utilization semantics (check both; edit only where a statement exists or is
   now wrong), and add or update the parity-ledger entry in `docs/parity_ledger/infrastructure.yaml`
   with `test_path` pointing at the new specification tests.

## Out of Scope
- Any edit to `src/core/state.py`, `src/engine/apply.py`, `src/engine/pipeline.py`,
  `src/engine/kernel.py` (still gated).
- Changing governor thresholds, hysteresis or recovery logic.
- The salience coupling (`TCK-20261003-SALIENCE-WALL-CLOCK-PRICE-COUPLING`, RPG-core track).
- Rerunning or promoting baselines; `PERF-M1-T05` consolidates the ledger.
- `RuntimeProfile` validation changes in `src/config/profiles.py` (already `gt=0`).

## Acceptance Criteria
1. Constructing `WorkerManager(max_workers>=1, max_queue_depth<=0)` raises, and a test proves it.
2. `get_stats()` reports queue utilization `0.0` for zero workers with zero queue depth, and worker
   utilization `0.0` for zero workers; tests prove both.
3. One specification test per epic state (unavailable recorded as found or not found), each citing
   PERF-D1 in its docstring; none asserts parity with the old `1.0` output.
4. Governor tests show disabled and no-queue configurations alone keep `NORMAL`, and saturation
   still reaches DEGRADED. `governor.py` is unchanged, or the planner approved the edit.
5. The reachability claim in the Request Summary is verified or corrected in Implementation Notes,
   with every `WorkerManager(` construction in `src/` listed.
6. The baseline disposition list exists in this ticket, one row per affected baseline.
7. Parity ledger updated; any doc that states utilization semantics matches PERF-D1.
8. Existing worker and governor tests pass: `tests/unit/core/test_signal_hardening.py`,
   `tests/unit/core/test_fallback_hardening.py`, `tests/unit/kernel/test_worker_*.py`,
   `tests/unit/kernel/test_executor_parity.py`, `tests/unit/resource/test_resource_governor_contract.py`, and
   `tests/perf/test_concurrency_parity.py`.
9. `make code-health` and `make typecheck-py` report no new or worse finding for the touched files.

## Related Tickets
- `TCK-20260911-WORKER-UTILIZATION-ZERO-WORKERS-DEGRADED-MISTRIGGER` (worker half, done)
- `TCK-20261003-COMBAT-TACTICAL-PATH-NONDETERMINISM-SURVIVES-AUDIT-MODE`,
  `TCK-20261005-DIRTY-SET-DEDUPES-UPDATES-BY-ID-SO-RECYCLED-ADDRESSES-DROP-WORK` (released the governor)
- `TCK-20261004-PERF-M1-TIED-WORKER-RESULT-VERIFICATION` (T04, done; same test surfaces)
- `TCK-20260908-DEGRADED-POLICY-NONURGENT-MOVEMENT-STARVATION` (gameplay consequence of false DEGRADED)
- `PERF-M1-T05` (unfiled; consumes item 5's list)

## Related Docs
- `docs/architecture/performance_optimization_decisions.md` (PERF-D1, zero-capacity semantics; C-03 row)
- `docs/plans/design_enhancement/performance_optimization/performance_m1_correctness_prerequisites_epic.md`
- `docs/plans/design_enhancement/performance_optimization/performance_optimization_roadmap.md` (gate, item 5)
- `docs/plans/design_enhancement/performance_optimization/performance_optimization_conflict_approval_review.md` (C-03)
- `docs/engine/deterministic_execution.md`, `docs/engine/runtime_profiles.md`

## Related Stored Artifacts
- None yet.

## Related Code Areas
- `src/engine/worker_manager.py` (edit)
- `src/engine/governor.py` (read; tests only)
- `src/config/profiles.py`, `src/perf/profiles.py` (read)
- `tests/unit/core/test_signal_hardening.py`, `tests/unit/kernel/test_worker_bounds.py`

## Assumptions / Open Questions
- Assumed: no shipped configuration reaches zero queue depth (to verify, AC 5).
- Open: whether an "unavailable" state exists at all (Scope 2).

## Implementation Notes

## Test Summary

## Files Changed

## Completion Summary
