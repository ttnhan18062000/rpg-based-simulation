---
status: historical
layer: performance
authority: P2
audience: agent
ticket_id: TCK-20261005-PERF-M1-ZERO-CAPACITY-SIGNAL
phase: done
date: 2026-10-05
tags: [performance, determinism, testing, engine]
---

# TCK-20261005-PERF-M1-ZERO-CAPACITY-SIGNAL

## Title
PERF-M1-T01: zero-capacity worker and queue signals follow PERF-D1, with specification tests and a baseline disposition

## Status
DONE

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
- `agent-working/stored_artifacts/TCK-20261005-PERF-M1-ZERO-CAPACITY-SIGNAL/` (investigation, plan, test_plan)

## Related Code Areas
- `src/engine/worker_manager.py` (edit)
- `src/engine/governor.py` (read; tests only)
- `src/config/profiles.py`, `src/perf/profiles.py` (read)
- `tests/unit/core/test_signal_hardening.py`, `tests/unit/kernel/test_worker_bounds.py`

## Assumptions / Open Questions
- Assumed: no shipped configuration reaches zero queue depth (to verify, AC 5).
- Open: whether an "unavailable" state exists at all (Scope 2).

## Implementation Notes
- **Reachability verified.** The only `WorkerManager(` in `src/` is `src/engine/kernel.py:133`, built from
  `RuntimeProfile.max_worker_count` / `max_queue_depth` (`src/config/profiles.py:30`, `gt=0`; perf
  profiles default queue 1000, `src/perf/profiles.py`). The four other callers named above do not
  construct it; they reach it through the kernel. No test or tool constructs a zero or negative
  capacity. The queue half is latent: no shipped run and no baseline was affected by it.
- **Negative inputs:** rejected (`ValueError`), not clamped. `max_workers >= 1` with `max_queue_depth <= 0`
  is rejected naming both values. Zero workers with zero or positive queue stays valid.
- **"Unavailable":** no such state exists. After `shutdown()` the pool is `None`, `execute_batch` runs
  locally and `get_stats()` still returns numbers; the small-batch process-pool fallback is also local
  execution. Neither is signalled through a utilization value; no typed field added.
- **Finding and fix (planner decision 2026-10-05, in scope as the "local" state):** local fallback ran
  on the caller thread through `_wrap_work`, which counted it as an active worker. With workers=1,
  queue=1, 200 packets, `get_stats()` returned `worker_utilization` **2.0** (`peak_workers` 2); after
  `shutdown()` a 4-worker manager reported **0.25** for purely local work. PERF-D1 says saturated is
  1.0. Fix: `_wrap_work(..., pooled=True)`; `_execute_locally` passes `pooled=False`, so only pool
  threads count as active. Not a clamp. Now: the same run gives 1.0 (`peak_workers` 1), post-shutdown
  local work gives 0.0. The strict xfail became the passing
  `test_local_fallback_never_reports_more_than_saturated`.
- **Mode guard rail:** `test_overloaded_run_with_local_fallback_reaches_degraded` (governor contract
  tests) feeds the overloaded run's stats to `ResourceGovernor`: DEGRADED before the fix (utilization
  2.0) and after (1.0). `governor.py` is unchanged. `tests/perf/test_concurrency_parity.py` passes.
  No existing test changed its RuntimeMode sequence.
- **Not verified here:** `tests/regression/test_behavioral_5k.py` hits the 60 s conftest limit
  (`TimeoutError`, not an assertion) on this machine, like the known certification long-run gap; it was
  not run to completion, so its 5k mode sequence is unchecked locally. CI is the check for it.
- **Docs:** `docs/engine/runtime_profiles.md` and `docs/engine/deterministic_execution.md` state no
  zero-capacity or utilization-range semantics (only that the governor reads utilization), so nothing
  was wrong or missing to edit; PERF-D1 in the decisions doc remains the statement. Parity ledger:
  `INFRA-422`.

- **Known limitation (process-pool route):** `_process_chunk_wrapper` runs in the child process and never
  touches `_active_count`, so on the process-pool route `worker_utilization` stays 0.0 even when that
  pool is saturated. This change affects one case there: before it, a process manager with
  `max_workers=1` sent small batches (`< 10 * workers`) to local execution and reported 1.0 (a false
  DEGRADED); now it reports 0.0. Neither is reachable from the kernel: `src/engine/kernel.py:133`
  builds `WorkerManager(max_workers=..., max_queue_depth=...)` with threads (`use_processes` unset)
  and never passes `force_local`. No follow-up ticket unless a shipped path ever enables processes.

### Baseline disposition (input to PERF-M1-T05; nothing rerun)
Worker fix landed in git 2026-09-13 (`bc00caa1a`, PR #175). Queue half never affected any run.
No committed baseline stores a utilization value (checked the metric keys), so none could have
recorded a value above 1.0 from the local-fallback miscount: that part changes nothing.

| Baseline | Profile (workers) | Captured | Disposition | Reason |
|---|---|---|---|---|
| `tests/perf/baselines/*_local.json` (idle, movement, resource, combat, strategic, mixed) | `PERF_*_LOCAL` (0) | 2026-05-15 | rerun | Captured before the worker fix: DEGRADED from tick 1, so timings reflect DEGRADED-mode cadence |
| `docs/observability/baselines/*_local.json`, `test_perf_idle_baseline.json` | `PERF_*_LOCAL` (0) | 2026-05-19 | rerun | Same |
| `docs/observability/baselines/matrix_full.json` (local rows) | `PERF_*_LOCAL` (0) | 2026-05-26 | rerun | Same; concurrent rows retain |
| `docs/observability/baselines/latest.json` IDLE_100..IDLE_5000, MOVEMENT_1000, RESOURCE_1000, COMBAT_100, STRATEGIC_500 | `PERF_*_LOCAL` (0) | 2026-05-26 | rerun | Same |
| `*_concurrent.json` in both dirs, `latest.json` MIXED_1000, `matrix_full.json` concurrent rows | `PERF_*_CONC` (4, queue 1000) | 2026-05-15 / 05-19 / 05-26 | retain | Workers > 0, queue > 0: neither half applies. Local-fallback miscount touches no stored value |
| `tests/perf/baselines/simq_corpus_*.json` | `PERF_512MB_LOCAL` (0) | 2026-08-07 | rerun | Zero workers; captured before 2026-09-13 |
| `perf_baselines.json` | none | n/a | retain | Zero entries |

Caveat: the `*_local` rows are `rerun`, not `incomparable`, because a rerun on current code is
possible; whether T05 reruns or retires them is the planner's call. Capture dates read from file
timestamps (epoch 1778820924 = 2026-05-15, 1779190619 = 2026-05-19, 1786131441 = 2026-08-07) and
`git log` for the matrix and latest files.

## Test Summary
- New: `tests/unit/kernel/test_worker_capacity_semantics.py` (15 pass). Governor: 3 new tests in
  `tests/unit/resource/test_resource_governor_contract.py`.
- AC 8 set plus the new governor tests: 62 passed (includes `tests/perf/test_concurrency_parity.py`).
  Kernel milestone A/B/D closure, `test_signal_truth`, `test_metric_window_recorder`: pass.
- `tests/regression/test_behavioral_5k.py` was NOT run to completion locally: it hits the 60 s conftest
  time limit (`TimeoutError`, not an assertion). CI is the check; perf-planner reads that job on the PR.
- `make code-health` / `make typecheck-py`: no finding in `src/engine/worker_manager.py`. The branch
  shows 1 new / 26 worse code-health findings and 3 unbaselined mypy errors in files this ticket does
  not touch (main over its ceilings; forwarded to codebase-planner by perf-planner).

## Files Changed
- `src/engine/worker_manager.py`
- `tests/unit/kernel/test_worker_capacity_semantics.py` (new)
- `tests/unit/resource/test_resource_governor_contract.py`
- `docs/parity_ledger/infrastructure.yaml` (INFRA-422)
- `agent-working/staging_artifacts/TCK-20261005-PERF-M1-ZERO-CAPACITY-SIGNAL/` (investigation, plan, test_plan)

## Completion Summary
WorkerManager now follows PERF-D1: construction rejects negative capacities and workers>=1 with queue<=0;
queue utilization is 0.0 when no queue exists; local fallback is no longer counted as an active worker
(worker utilization was 2.0 under fallback, now 1.0). Specification tests, governor guard rail (DEGRADED
before and after), parity ledger INFRA-422 and the baseline disposition list are in. `governor.py` is
unchanged. Not verified locally: `test_behavioral_5k` (60 s conftest limit); CI is the check. Known
limitation: process-pool route never counts active workers (unreachable from the kernel).
