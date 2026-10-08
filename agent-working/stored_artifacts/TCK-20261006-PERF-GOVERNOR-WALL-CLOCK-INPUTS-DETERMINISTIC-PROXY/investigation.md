---
status: historical
layer: performance
authority: P2
audience: agent
artifact_type: investigation
ticket_id: TCK-20261006-PERF-GOVERNOR-WALL-CLOCK-INPUTS-DETERMINISTIC-PROXY
date: 2026-10-06
tags: [performance, determinism, engine, testing]
---

# Investigation: TCK-20261006-PERF-GOVERNOR-WALL-CLOCK-INPUTS-DETERMINISTIC-PROXY

Design only. Tree: `origin/main` at `7f361ee73`. No `src/` or `tests/` file was edited. Line numbers are from that tree.
Evidence for the numbers in section 4 is in `probes/` (a script and its 180 rows).

## 1. What reaches the two governors

`docs/performance/wall_clock_inventory.md` was the starting point. `wall_clock_inventory --check` passes on this tree, so
its read list is current. It lists reads; this section traces each one to the decision it drives.

Signals are built twice per tick in `src/engine/kernel.py`: at the end of tick N (`_record_runtime_signals`, line 788, stored in
`RuntimeStatus.signal_history`) and at the start of tick N+1 (`_phase_init`, lines 515-565), which feeds
`ResourceGovernor.evaluate` (`governor.py`, called at `kernel.py:562`). So every decision uses the previous tick's measurement. That
one-tick lag is deterministic and is kept.

| # | Signal | Measured where | Read where | Decision it drives |
|---|---|---|---|---|
| 1 | `tick_compute_ms` | `kernel.py:463` `_final_compute_ms = sum(self._phase_costs.values())`, a sum of `perf_counter_ns` deltas (`:398-461`); recorded at `:793`; copied into the next tick's signals at `:544-546` (capped to half the budget for ticks <= 5) | `governor.py:78` (SURVIVAL at 1.5x budget), `:95` (DEGRADED at 1.0x), `:103` (CONSTRAINED at 0.7x); recovery `governor.py:146` via the rolling average `RuntimeStatus.record_signals` (`runtime_status.py:45-62`); `phase_governor.py:139` (compaction level at 0.8x); `kernel.py:647` `compute_ratio` (salience, PERF-D1 input 4, RPG Lane A, out of scope) | `RuntimeMode`, then cadence, scan policy, concurrency, replay richness, phase budgets |
| 2 | `phase_costs_ms["locomotion"]`, `["final_integrity"]` | `pipeline.py:300` and `:466`, `perf_counter_ns` deltas of two cost buckets inside `refine`; merged into `_phase_costs` at `kernel.py:672` | `phase_governor.py:112-124` (locomotion), `:127-135` (final integrity): absolute thresholds 15.0 / 10.0 ms or 0.5 / 0.3 of the tick budget | scan policy (to EXACT_DIRTY), `movement_budget` (100 / 400), `strategic_budget` (8 / 20), `background_sweep_interval` (8 / 4), in every mode |
| 3 | `memory_estimate_mb` (RSS) | `observability.py:69` `psutil.Process.memory_info`, every `sampling_interval_ticks`, cached (`:64-93`); `kernel.py:552,796` | `governor.py:80` (SURVIVAL at the profile RAM ceiling), `:107` (CONSTRAINED at 85%), recovery `:150` | `RuntimeMode` |
| 4 | `replay_backlog_kb` | `replay_buffer.py:58` `len(buffer) * 0.25`, drained by a background flush thread (`replay_manager.py:352`); `kernel.py:553,797` | `governor.py:99` (DEGRADED at 90% of `max_replay_buffer_kb`). Not read by recovery. | `RuntimeMode` |
| 5 | `worker_utilization`, `queue_utilization` | `worker_manager.py` `get_stats()`: peak active pool threads and peak queued chunks (thread timing); `kernel.py:550-551,794-795` | `governor.py:97,105` (DEGRADED at 0.9, CONSTRAINED at 0.7), recovery `:148`. Zero workers report 0.0 (PERF-D1, PR #352) | `RuntimeMode` |
| 6 | `work_debt_total` | deterministic: always 0 (`TCK-20261004-WORK-DEBT-NEVER-ACCUMULATES-IN-PRODUCTION`) | `governor.py:76,84,152`, `phase_governor.py:139`, `kernel.py:646` | none in practice. Retire step 2 removes it. |
| 7 | `dropped_work_delta` | scheduler (always 0, DEV-014) | telemetry only | none |

Not inputs: frame pacing (`kernel.py:446-456` sleeps, but `_final_compute_ms` is a sum of phase costs and excludes the sleep), and
the report-only overrun check (DEV-014).

Other places where a mode or the flag decides what is computed, found while reading: `audit_mode` is read at `kernel.py:83` and
used for per-phase fingerprint checks (`:403-428`), the overrun report (`:468`, `:620`), zeroed signals (`:530-541`), and forcing the
per-tick digest (`:1164`); it is also passed to `ApplyPath` (`:768`, `:822`). Four harnesses set it: `certification/harness.py:88,173,301`,
`perf/long_run_harness.py:316`, `domains/campaigns/runner.py:89`; 25 test files use it.

## 2. What `audit_mode` is today

Under `audit_mode` the kernel builds `PressureSignals` with every timing and resource field at zero (`kernel.py:530-541`), so
nothing ever leaves `NORMAL`. It is a degenerate Canonical contract: deterministic because the pressure inputs are deleted, not
replaced. The consequence: no deterministic run, certification scenario or SimQ calibration ever exercises degradation, and the
governor path is never covered by a determinism claim. The `PhaseBudgetGovernor` divergence found in PR #379 happens only outside
`audit_mode`.

## 3. Facts from the other work this design builds on
- The scheduler sheds nothing in shipped runs (`TCK-20261006-PERF-SCHEDULER-SHEDS-NOTHING-IN-SHIPPED-RUNS`, owner chose (c)). So
  a mode change today controls only cadence, phase budgets, concurrency, replay richness and traces
  (`resource_governor_degradation_matrix.md`, "Shipped behaviour"). That is the whole effect a proxy has to reproduce.
- The kernel's budget checks are report-only (DEV-014), so the remaining wall-clock-to-outcome paths are rows 1 to 5 above plus
  the salience coupling (Lane A).
- Work debt is always 0 and is retired in the same window; the design therefore does not use it as a proxy.
- The `PhaseBudgetGovernor` divergence is real: a non-audit hash-equality test diverged in 1 of 3 runs at tick index 2 (`TCK-20261006-PERF-TICK-BUDGET-THROTTLE-REPORT-ONLY`).

## 4. Measurements (read-only probe; script and rows in `probes/`)

180 ticks: four scenario families (`idle`, `movement`, `resource`, `strategic`) at 60, 150 and 300 entities, 15 measured ticks each
(3 warm-up ticks dropped), `max_worker_count=0`, a budget large enough to stay in `NORMAL`. Per tick: measured total and bucket
costs, and candidate deterministic counters. This VM, one run of each.

- **Wall-clock noise is large.** Within one configuration the coefficient of variation of `tick_ms` was 4% to 11% for `idle` and
  26% to 28% for `strategic`. A threshold on measured ms therefore flips on noise alone near a boundary.
- **Absolute cost is host-specific.** A tick took 60 ms (60 idle entities) to 4,260 ms (300 strategic entities) here. Ms thresholds
  mean different things on different hosts, which is exactly the Canonical claim's problem.
- **No single counter works across scenario families.** Pearson r with `tick_ms`: movement candidates 0.89, leads 0.89, entities
  0.51, compacted updates 0.74. Milliseconds per resolved result ranged from 13 (`movement`) to 92 (`strategic`), a factor of 7.
- **A small fixed model fits reasonably.** `tick_ms ~ 1.10*entities + 4.79*movement_candidates + 7.80*leads` has R^2 0.87 pooled,
  but the per-family ratio of actual to predicted ran 0.48 to 1.30, a factor of 2.7. It is a usable approximation, not an accurate one.
- **`locomotion` has a good counter, `final_integrity` has none.** Locomotion cost vs movement candidates: r 0.93, R^2 0.79.
  `final_integrity` cost vs every counter tried (entities, results, compacted updates, movement candidates, leads): r <= 0.54, R^2 <= 0.24.
  The dirty-set size, the obvious candidate, could not be read after the tick (`_current_update` is cleared at advancement), so it was
  not measured. That is a first step for the implementation, with a fallback in `plan.md`.
- Limits: one machine, one run, `max_worker_count=0`, four synthetic scenarios, no combat scenario. The numbers say which counters
  are worth calibrating on a real matrix; they do not set weights.

## 5. Tests that drive a mode through time or a seam
| Test | How it gets a mode |
|---|---|
| `tests/integration/kernel/test_milestone_b_closure.py` | patched `time.perf_counter_ns` with a tick-keyed fake clock (#373) |
| `tests/integration/world/test_camp_raid_targeting.py` | `_DegradedGovernor._get_indicated_mode` override |
| `tests/integration/kernel/test_tick_budget_report_only.py` | `_NormalOnlyGovernor` override |
| `tests/integration/campaigns/test_catalog_entity_spawn_wiring.py` | `_PinnedNormalGovernor` override |
| `tests/integration/kernel/test_work_debt_stays_empty_in_production.py` | real 1 ms budget, real time, custom scheduler |
| `tests/unit/resource/test_resource_governor_contract.py`, `tests/unit/strategic/test_anti_thrashing.py`, `tests/unit/domains/optimization/test_phase_budget_governor.py`, `tests/unit/core/test_signal_truth.py`, `tests/integration/pipeline/test_governance_isolation.py` | construct `PressureSignals(tick_compute_ms=...)` directly |
| `tests/certification/test_resilience_recovery.py` | patches `ResourceGovernor.evaluate` |
| `tests/integration/world/test_long_run_stability.py`, `tests/certification/test_cert_long_run_stability.py:106` | CI-skipped because of the old throttle (`test-architecture-reviewer` decides) |
What happens to each is in `plan.md`.
