---
status: active
layer: performance
authority: P2
audience: agent
tags: [performance, determinism, engine]
---

# Wall-Clock and Host-Resource Read Inventory

Evidence for PERF-D1 (`docs/architecture/performance_optimization_decisions.md`), from
`TCK-20261003-PERF-WALL-CLOCK-READ-INVENTORY`. It was written on 2026-10-03 against the tree at the
commit named in the generated block. It measures nothing (no kernel run, no timing), proposes no policy,
and edits none of the documents or code it describes. PERF-D1's classification table and the P1 text are
for the planner and `PERF-M0-T09`; the findings that bear on them are in §1 and §3.

How to read it: §1 is the answer in short, including the answer to PERF-D1's revisit condition. §2 is the
scanner's generated tables. §3 traces every read in a module the kernel imports, grouped by value flow.
§4 lists each fourth-input candidate with its path. §5 groups the reads outside the tick path, one line
per module. §6 says how the scan was checked and what it cannot see.

## 1. Summary

- **Resolved 2026-10-06 (`TCK-20261003-SALIENCE-WALL-CLOCK-PRICE-COUPLING`): the salience path below no longer exists.** The kernel computes and writes no `pressure_signals`, and the buy price reads no state, so the file and line references in this finding and in §3 row 6-7 and §4.1 describe the code as inventoried (commit `8fcdc4fec`), not as it is now. The generated tables are regenerated from the fixed tree.
- **PERF-D1's revisit condition is met: there is a fourth input that reaches authoritative state.**
  `Kernel._phase_resolution` derives `compute_ratio` from the previous tick's wall-clock
  `tick_compute_ms` (`src/engine/kernel.py:666`), folds it into `global_salience` (`:667`), and writes it
  into the tick's `StateUpdate` as `pressure_signals_set` (`:678`). `ApplyPath` stores it in
  `AuthoritativeState.pressure_signals` (`src/engine/apply.py:335`, `:510`). `DynamicPriceService.calculate_buy_price`
  reads `global_salience` (`src/systems/economy_systems/economy.py:27`) and multiplies the shop price by
  `1 + salience`. `ShopService.buy_item` uses that price for the gold check and cost
  (`src/town/shop.py:36-41`), and `buy_item` is called from the action-intent path
  (`src/engine/intent/action_intent.py:246`). This path changes no `RuntimeMode`, so none of PERF-D1's
  three named inputs describes it, and the PERF-D1 control-input table has no row for it. `audit_mode`
  neutralizes it, because `audit_mode` zeroes `tick_compute_ms` in the signals (`kernel.py:541-553`).
  Details in §4.1. `AuthoritativeState.pressure_signals` is not in the proof digest
  (`src/engine/checkpoint.py::to_canonical_data` has no such key), so a salience difference is invisible to
  the flat hash until a purchase changes gold or inventory. This is evidence for PERF-D5 coverage.
- **Two more wall-clock or host-timing inputs reach control decisions and are not among PERF-D1's three
  named inputs.** Neither reaches authoritative state by a path other than the decisions PERF-D1 already
  classifies:
  - the replay buffer backlog (`replay_backlog_kb`) is one of `ResourceGovernor._get_indicated_mode`'s
    DEGRADED triggers (`src/engine/governor.py:101-102`). The backlog depends on how fast a background
    flush thread drains the buffer. PERF-D1's text names `tick_compute_ms`, RSS and worker and queue
    utilization, not the replay backlog (§4.2);
  - `PhaseBudgetGovernor.evaluate` lowers scan policy, movement and strategic budgets, sweep interval and
    compaction level directly from the previous tick's per-phase wall-clock costs and `tick_compute_ms`
    (`src/engine/phase_governor.py:108-141`), independent of the current mode (§4.3). PERF-D1's table has a
    row for this (`Phase budgets emitted from measured sub-phase cost`), but the decision's list of three
    inputs does not name it.
- **Everything else on the tick path is a log, metric, artifact or outward event.** §3 traces 17 groups of reads
  in modules the kernel imports. The values go into artifact manifests, alert and event envelopes,
  stream and warehouse timestamps, `metric_counters`, `compute_time_ns` on worker results, and a shutdown
  report. No read of those was found to feed an `AuthoritativeState` field, an update record that
  `ApplyPath` stores, an id, a seed, or a sort key. Run ids and event ids use wall-clock time and
  `uuid.uuid4`, and they go only to artifact paths and observability records (§3, groups T3, T12, T13).
- **No RNG is seeded from time or host entropy.** `DeterministicRNG.get_int` and its siblings are stateless
  functions of `(base_seed, domain, tick, entity_id, sub_id)` (`src/platform/rng.py:90-98`). The run-id
  suffix draw at `kernel.py:142` does not advance any stream. No module-level `random.<fn>` call and no
  `secrets` use exists in `src/`. `random.seed` and `random.SystemRandom` appear nowhere in `src/`.
- **Environment variables are a host input of a different kind.** 73 reads of `os.environ`. Three groups
  matter for determinism rather than operations: `RPG_<FIELD>` overrides of every `RuntimeProfile` field
  and `BROKER_DISABLED` (`src/config/loader.py:54-80`, outside the kernel's import closure; they set
  `max_tick_budget_ms`, `max_worker_count` and the other governor inputs before the kernel is built);
  `ObservabilityConfig` mode and flags (§3, group T13); and the `QUALITY_*` family (group T14). They are
  configuration identity (PERF-D2), not clock reads.
- **Counts.** 363 reads and 10 unresolved candidates (§2). 159 reads are in modules the kernel imports
  (transitively, over-approximate), 204 are not. 235 are wall-clock reads, 73 environment, 34 entropy
  (all `uuid.uuid4`), 10 CPU or host topology, 9 memory, 2 CPU time.

## 2. Scanner output

<!-- BEGIN GENERATED: tools/perf/wall_clock_inventory.py -->

Generated from commit `999c1ad5cc869caf4fedb2ecf5b1a318a20df3b6` by `tools/perf/wall_clock_inventory.py`. Regenerate this block with:

```
python3 tools/perf/wall_clock_inventory.py --update-doc docs/performance/wall_clock_inventory.md
python3 tools/perf/wall_clock_inventory.py --format json > docs/performance/wall_clock_inventory.json
python3 tools/perf/wall_clock_inventory.py --check docs/performance/wall_clock_inventory.json
```

Reads found: 364 (159 in modules reachable from `src.engine.kernel` through the import graph, 205 elsewhere). Modules reachable from the kernel: 436.

### G1. Reads in modules reachable from the kernel (guards are the conditions inside the enclosing function, as written)

| # | File | Line | Enclosing function | Source | Kind | Env var | Guards in the function |
|---|---|---|---|---|---|---|---|
| 39 | `src/domains/cooperation/phase.py` | 88 | `CooperationPhase.execute` | time.perf_counter_ns | wall-clock | - | none in this function |
| 40 | `src/domains/cooperation/phase.py` | 256 | `CooperationPhase.execute` | time.perf_counter_ns | wall-clock | - | none in this function |
| 41 | `src/domains/world_emergence/phase.py` | 35 | `WorldEmergencePhase.execute` | time.perf_counter_ns | wall-clock | - | none in this function |
| 42 | `src/domains/world_emergence/phase.py` | 128 | `WorldEmergencePhase.execute` | time.perf_counter_ns | wall-clock | - | none in this function |
| 43 | `src/engine/kernel.py` | 144 | `Kernel.__init__` | time.time | wall-clock | - | if self._run_id is None |
| 44 | `src/engine/kernel.py` | 164 | `Kernel.__init__` | datetime.datetime.now | wall-clock | - | if obs_mode != ObservabilityMode.OFF |
| 45 | `src/engine/kernel.py` | 216 | `Kernel.__init__` | time.perf_counter_ns | wall-clock | - | none in this function |
| 46 | `src/engine/kernel.py` | 245 | `Kernel.__init__` | os.environ.get | environment | QUALITY_PROFILE | try; if not isinstance(_feed, BrokerQualityFeed); if _feed is not None; if obs_mode != ObservabilityMode.OFF |
| 47 | `src/engine/kernel.py` | 414 | `Kernel._tick_once_inner` | time.perf_counter_ns | wall-clock | - | none in this function |
| 48 | `src/engine/kernel.py` | 419 | `Kernel._tick_once_inner` | time.perf_counter_ns | wall-clock | - | none in this function |
| 49 | `src/engine/kernel.py` | 434 | `Kernel._tick_once_inner` | time.perf_counter_ns | wall-clock | - | none in this function |
| 50 | `src/engine/kernel.py` | 443 | `Kernel._tick_once_inner` | time.perf_counter_ns | wall-clock | - | none in this function |
| 51 | `src/engine/kernel.py` | 452 | `Kernel._tick_once_inner` | time.perf_counter_ns | wall-clock | - | none in this function |
| 52 | `src/engine/kernel.py` | 459 | `Kernel._tick_once_inner` | time.perf_counter_ns | wall-clock | - | none in this function |
| 53 | `src/engine/kernel.py` | 463 | `Kernel._tick_once_inner` | time.perf_counter_ns | wall-clock | - | none in this function |
| 54 | `src/engine/kernel.py` | 468 | `Kernel._tick_once_inner` | time.perf_counter_ns | wall-clock | - | if target_ms > 0 and (not self._no_frame_pacing) |
| 55 | `src/engine/kernel.py` | 472 | `Kernel._tick_once_inner` | time.perf_counter_ns | wall-clock | - | if sleep_ms > 5.0; if target_ms > 0 and (not self._no_frame_pacing) |
| 56 | `src/engine/kernel.py` | 480 | `Kernel._tick_once_inner` | time.perf_counter_ns | wall-clock | - | none in this function |
| 57 | `src/engine/kernel.py` | 482 | `Kernel._tick_once_inner` | time.perf_counter_ns | wall-clock | - | none in this function |
| 58 | `src/engine/kernel.py` | 616 | `Kernel._phase_resolution` | time.perf_counter_ns | wall-clock | - | if not overrun_reported and i % 10 == 0 and (not self._audit_mode) |
| 59 | `src/engine/kernel.py` | 769 | `Kernel._phase_cleanup` | time.perf_counter_ns | wall-clock | - | none in this function |
| 60 | `src/engine/kernel.py` | 1234 | `Kernel.shutdown` | psutil.Process | CPU/host topology | - | try |
| 61 | `src/engine/kernel.py` | 1263 | `Kernel.shutdown` | datetime.datetime.now | wall-clock | - | if hasattr(self, '_artifact_repo') and self._artifact_repo and self._run_id |
| 62 | `src/engine/observability.py` | 47 | `SignalCollector.__init__` | psutil.Process | CPU/host topology | - | none in this function |
| 63 | `src/engine/observability.py` | 48 | `SignalCollector.__init__` | time.perf_counter | wall-clock | - | none in this function |
| 64 | `src/engine/observability.py` | 69 | `SignalCollector.collect_platform_signals` | psutil.Process.memory_info | memory | - | try; if tick % interval == 0 |
| 65 | `src/engine/observability.py` | 136 | `SignalCollector.get_snapshot` | time.perf_counter | wall-clock | - | none in this function |
| 66 | `src/engine/pipeline.py` | 95 | `AuthoritativeApplyPipeline.refine` | time.perf_counter_ns | wall-clock | - | none in this function |
| 67 | `src/engine/pipeline.py` | 138 | `AuthoritativeApplyPipeline.refine` | time.perf_counter_ns | wall-clock | - | none in this function |
| 68 | `src/engine/pipeline.py` | 145 | `AuthoritativeApplyPipeline.refine` | time.perf_counter_ns | wall-clock | - | none in this function |
| 69 | `src/engine/pipeline.py` | 159 | `AuthoritativeApplyPipeline.refine` | time.perf_counter_ns | wall-clock | - | none in this function |
| 70 | `src/engine/pipeline.py` | 167 | `AuthoritativeApplyPipeline.refine` | time.perf_counter_ns | wall-clock | - | none in this function |
| 71 | `src/engine/pipeline.py` | 174 | `AuthoritativeApplyPipeline.refine` | time.perf_counter_ns | wall-clock | - | none in this function |
| 72 | `src/engine/pipeline.py` | 180 | `AuthoritativeApplyPipeline.refine` | time.perf_counter_ns | wall-clock | - | none in this function |
| 73 | `src/engine/pipeline.py` | 187 | `AuthoritativeApplyPipeline.refine` | time.perf_counter_ns | wall-clock | - | none in this function |
| 74 | `src/engine/pipeline.py` | 190 | `AuthoritativeApplyPipeline.refine` | time.perf_counter_ns | wall-clock | - | none in this function |
| 75 | `src/engine/pipeline.py` | 193 | `AuthoritativeApplyPipeline.refine` | time.perf_counter_ns | wall-clock | - | none in this function |
| 76 | `src/engine/pipeline.py` | 196 | `AuthoritativeApplyPipeline.refine` | time.perf_counter_ns | wall-clock | - | none in this function |
| 77 | `src/engine/pipeline.py` | 202 | `AuthoritativeApplyPipeline.refine` | time.perf_counter_ns | wall-clock | - | none in this function |
| 78 | `src/engine/pipeline.py` | 205 | `AuthoritativeApplyPipeline.refine` | time.perf_counter_ns | wall-clock | - | none in this function |
| 79 | `src/engine/pipeline.py` | 212 | `AuthoritativeApplyPipeline.refine` | time.perf_counter_ns | wall-clock | - | none in this function |
| 80 | `src/engine/pipeline.py` | 215 | `AuthoritativeApplyPipeline.refine` | time.perf_counter_ns | wall-clock | - | none in this function |
| 81 | `src/engine/pipeline.py` | 218 | `AuthoritativeApplyPipeline.refine` | time.perf_counter_ns | wall-clock | - | none in this function |
| 82 | `src/engine/pipeline.py` | 221 | `AuthoritativeApplyPipeline.refine` | time.perf_counter_ns | wall-clock | - | none in this function |
| 83 | `src/engine/pipeline.py` | 224 | `AuthoritativeApplyPipeline.refine` | time.perf_counter_ns | wall-clock | - | none in this function |
| 84 | `src/engine/pipeline.py` | 228 | `AuthoritativeApplyPipeline.refine` | time.perf_counter_ns | wall-clock | - | none in this function |
| 85 | `src/engine/pipeline.py` | 231 | `AuthoritativeApplyPipeline.refine` | time.perf_counter_ns | wall-clock | - | none in this function |
| 86 | `src/engine/pipeline.py` | 235 | `AuthoritativeApplyPipeline.refine` | time.perf_counter_ns | wall-clock | - | none in this function |
| 87 | `src/engine/pipeline.py` | 242 | `AuthoritativeApplyPipeline.refine` | time.perf_counter_ns | wall-clock | - | none in this function |
| 88 | `src/engine/pipeline.py` | 245 | `AuthoritativeApplyPipeline.refine` | time.perf_counter_ns | wall-clock | - | none in this function |
| 89 | `src/engine/pipeline.py` | 253 | `AuthoritativeApplyPipeline.refine` | time.perf_counter_ns | wall-clock | - | none in this function |
| 90 | `src/engine/pipeline.py` | 256 | `AuthoritativeApplyPipeline.refine` | time.perf_counter_ns | wall-clock | - | none in this function |
| 91 | `src/engine/pipeline.py` | 283 | `AuthoritativeApplyPipeline.refine` | time.perf_counter_ns | wall-clock | - | none in this function |
| 92 | `src/engine/pipeline.py` | 286 | `AuthoritativeApplyPipeline.refine` | time.perf_counter_ns | wall-clock | - | none in this function |
| 93 | `src/engine/pipeline.py` | 293 | `AuthoritativeApplyPipeline.refine` | time.perf_counter_ns | wall-clock | - | none in this function |
| 94 | `src/engine/pipeline.py` | 296 | `AuthoritativeApplyPipeline.refine` | time.perf_counter_ns | wall-clock | - | none in this function |
| 95 | `src/engine/pipeline.py` | 300 | `AuthoritativeApplyPipeline.refine` | time.perf_counter_ns | wall-clock | - | none in this function |
| 96 | `src/engine/pipeline.py` | 303 | `AuthoritativeApplyPipeline.refine` | time.perf_counter_ns | wall-clock | - | none in this function |
| 97 | `src/engine/pipeline.py` | 321 | `AuthoritativeApplyPipeline.refine` | time.perf_counter_ns | wall-clock | - | none in this function |
| 98 | `src/engine/pipeline.py` | 324 | `AuthoritativeApplyPipeline.refine` | time.perf_counter_ns | wall-clock | - | none in this function |
| 99 | `src/engine/pipeline.py` | 335 | `AuthoritativeApplyPipeline.refine` | time.perf_counter_ns | wall-clock | - | none in this function |
| 100 | `src/engine/pipeline.py` | 338 | `AuthoritativeApplyPipeline.refine` | time.perf_counter_ns | wall-clock | - | none in this function |
| 101 | `src/engine/pipeline.py` | 349 | `AuthoritativeApplyPipeline.refine` | time.perf_counter_ns | wall-clock | - | none in this function |
| 102 | `src/engine/pipeline.py` | 352 | `AuthoritativeApplyPipeline.refine` | time.perf_counter_ns | wall-clock | - | none in this function |
| 103 | `src/engine/pipeline.py` | 356 | `AuthoritativeApplyPipeline.refine` | time.perf_counter_ns | wall-clock | - | none in this function |
| 104 | `src/engine/pipeline.py` | 360 | `AuthoritativeApplyPipeline.refine` | time.perf_counter_ns | wall-clock | - | none in this function |
| 105 | `src/engine/pipeline.py` | 382 | `AuthoritativeApplyPipeline.refine` | time.perf_counter_ns | wall-clock | - | none in this function |
| 106 | `src/engine/pipeline.py` | 385 | `AuthoritativeApplyPipeline.refine` | time.perf_counter_ns | wall-clock | - | none in this function |
| 107 | `src/engine/pipeline.py` | 388 | `AuthoritativeApplyPipeline.refine` | time.perf_counter_ns | wall-clock | - | none in this function |
| 108 | `src/engine/pipeline.py` | 391 | `AuthoritativeApplyPipeline.refine` | time.perf_counter_ns | wall-clock | - | none in this function |
| 109 | `src/engine/pipeline.py` | 393 | `AuthoritativeApplyPipeline.refine` | time.perf_counter_ns | wall-clock | - | none in this function |
| 110 | `src/engine/pipeline.py` | 396 | `AuthoritativeApplyPipeline.refine` | time.perf_counter_ns | wall-clock | - | none in this function |
| 111 | `src/engine/pipeline.py` | 399 | `AuthoritativeApplyPipeline.refine` | time.perf_counter_ns | wall-clock | - | none in this function |
| 112 | `src/engine/pipeline.py` | 411 | `AuthoritativeApplyPipeline.refine` | time.perf_counter_ns | wall-clock | - | none in this function |
| 113 | `src/engine/pipeline.py` | 413 | `AuthoritativeApplyPipeline.refine` | time.perf_counter_ns | wall-clock | - | none in this function |
| 114 | `src/engine/pipeline.py` | 415 | `AuthoritativeApplyPipeline.refine` | time.perf_counter_ns | wall-clock | - | none in this function |
| 115 | `src/engine/pipeline.py` | 417 | `AuthoritativeApplyPipeline.refine` | time.perf_counter_ns | wall-clock | - | none in this function |
| 116 | `src/engine/pipeline.py` | 428 | `AuthoritativeApplyPipeline.refine` | time.perf_counter_ns | wall-clock | - | none in this function |
| 117 | `src/engine/pipeline.py` | 436 | `AuthoritativeApplyPipeline.refine` | time.perf_counter_ns | wall-clock | - | none in this function |
| 118 | `src/engine/pipeline.py` | 445 | `AuthoritativeApplyPipeline.refine` | time.perf_counter_ns | wall-clock | - | none in this function |
| 119 | `src/engine/pipeline.py` | 465 | `AuthoritativeApplyPipeline.refine` | time.perf_counter_ns | wall-clock | - | none in this function |
| 120 | `src/engine/replay_manager.py` | 62 | `ReplayManager.__init__` | time.time | wall-clock | - | none in this function |
| 121 | `src/engine/replay_manager.py` | 131 | `ReplayManager.finalize` | time.perf_counter | wall-clock | - | none in this function |
| 122 | `src/engine/replay_manager.py` | 144 | `ReplayManager.finalize` | time.perf_counter | wall-clock | - | try |
| 123 | `src/engine/replay_manager.py` | 158 | `ReplayManager.finalize` | time.perf_counter | wall-clock | - | try |
| 124 | `src/engine/replay_manager.py` | 167 | `ReplayManager.finalize` | time.time | wall-clock | - | none in this function |
| 125 | `src/engine/worker_manager.py` | 27 | `_process_chunk_wrapper` | time.perf_counter_ns | wall-clock | - | none in this function |
| 126 | `src/engine/worker_manager.py` | 30 | `_process_chunk_wrapper` | time.perf_counter_ns | wall-clock | - | try |
| 127 | `src/engine/worker_manager.py` | 215 | `WorkerManager._wrap_work` | time.perf_counter_ns | wall-clock | - | none in this function |
| 128 | `src/engine/worker_manager.py` | 218 | `WorkerManager._wrap_work` | time.perf_counter_ns | wall-clock | - | try |
| 153 | `src/observability/alerts/deduplicator.py` | 22 | `AlertDeduplicator.should_suppress` | time.time | wall-clock | - | if current_time is None |
| 154 | `src/observability/alerts/deduplicator.py` | 40 | `AlertDeduplicator.prune` | time.time | wall-clock | - | if current_time is None |
| 155 | `src/observability/alerts/manager.py` | 22 | `AlertsManager.get_router` | os.environ.get | environment | SIM_ALERTS_SEVERITY_THRESHOLD | if cls._router is None |
| 156 | `src/observability/alerts/manager.py` | 22 | `AlertsManager.get_router` | os.environ.get | environment | RPG_ALERTS_SEVERITY_THRESHOLD | unless: os.environ.get('SIM_ALERTS_SEVERITY_THRESHOLD'); if cls._router is None |
| 157 | `src/observability/alerts/manager.py` | 24 | `AlertsManager.get_router` | os.environ.get | environment | SIM_ALERTS_DEDUP_WINDOW_SECONDS | if cls._router is None |
| 158 | `src/observability/alerts/manager.py` | 24 | `AlertsManager.get_router` | os.environ.get | environment | RPG_ALERTS_DEDUP_WINDOW_SECONDS | unless: os.environ.get('SIM_ALERTS_DEDUP_WINDOW_SECONDS'); if cls._router is None |
| 159 | `src/observability/alerts/manager.py` | 30 | `AlertsManager.get_router` | os.environ.get | environment | SIM_ALERTS_WEBHOOK_URL | if cls._router is None |
| 160 | `src/observability/alerts/manager.py` | 30 | `AlertsManager.get_router` | os.environ.get | environment | RPG_ALERTS_WEBHOOK_URL | unless: os.environ.get('SIM_ALERTS_WEBHOOK_URL'); if cls._router is None |
| 161 | `src/observability/alerts/manager.py` | 31 | `AlertsManager.get_router` | os.environ.get | environment | SIM_ALERTS_WEBHOOK_ENABLED | if cls._router is None |
| 162 | `src/observability/alerts/manager.py` | 31 | `AlertsManager.get_router` | os.environ.get | environment | RPG_ALERTS_WEBHOOK_ENABLED | unless: os.environ.get('SIM_ALERTS_WEBHOOK_ENABLED'); if cls._router is None |
| 163 | `src/observability/alerts/manager.py` | 36 | `AlertsManager.get_router` | os.environ.get | environment | SIM_ALERTS_WEBHOOK_TIMEOUT | if cls._router is None |
| 164 | `src/observability/alerts/manager.py` | 36 | `AlertsManager.get_router` | os.environ.get | environment | RPG_ALERTS_WEBHOOK_TIMEOUT | unless: os.environ.get('SIM_ALERTS_WEBHOOK_TIMEOUT'); if cls._router is None |
| 165 | `src/observability/alerts/manager.py` | 42 | `AlertsManager.get_router` | os.environ.get | environment | SIM_ALERTS_WEBHOOK_RETRIES | if cls._router is None |
| 166 | `src/observability/alerts/manager.py` | 42 | `AlertsManager.get_router` | os.environ.get | environment | RPG_ALERTS_WEBHOOK_RETRIES | unless: os.environ.get('SIM_ALERTS_WEBHOOK_RETRIES'); if cls._router is None |
| 167 | `src/observability/alerts/models.py` | 14 | `AlertEvent` | uuid.uuid4 | entropy | - | none in this function |
| 168 | `src/observability/alerts/models.py` | 17 | `AlertEvent` | datetime.datetime.now | wall-clock | - | none in this function |
| 169 | `src/observability/alerts/sinks.py` | 89 | `WebhookAlertSink._circuit_allows_dispatch` | time.time | wall-clock | - | if self._circuit_state == 'open' |
| 170 | `src/observability/alerts/sinks.py` | 107 | `WebhookAlertSink._record_outcome` | time.time | wall-clock | - | if self._circuit_state == 'half_open' |
| 171 | `src/observability/alerts/sinks.py` | 110 | `WebhookAlertSink._record_outcome` | time.time | wall-clock | - | if self._circuit_state == 'closed' and self._consecutive_failures >= self.CIRCUIT_BREAKER_FAILURE_THRESHOLD; else of: if self._circuit_state == 'half_open' |
| 201 | `src/observability/config.py` | 218 | `ObservabilityConfig.get_flag` | os.environ.get | environment | - | none in this function |
| 202 | `src/observability/config.py` | 291 | `ObservabilityConfig.get_mode` | os.environ.get | environment | SIM_OBS_MODE | none in this function |
| 203 | `src/observability/config.py` | 291 | `ObservabilityConfig.get_mode` | os.environ.get | environment | RPG_OBS_MODE | unless: os.environ.get('SIM_OBS_MODE') |
| 204 | `src/observability/config.py` | 303 | `ObservabilityConfig.get_deployment_profile` | os.environ.get | environment | SIM_DEPLOYMENT_PROFILE | none in this function |
| 205 | `src/observability/config.py` | 303 | `ObservabilityConfig.get_deployment_profile` | os.environ.get | environment | RPG_DEPLOYMENT_PROFILE | unless: os.environ.get('SIM_DEPLOYMENT_PROFILE') |
| 206 | `src/observability/config.py` | 308 | `ObservabilityConfig.get_stream_backend` | os.environ.get | environment | SIM_STREAM_BACKEND | none in this function |
| 207 | `src/observability/config.py` | 308 | `ObservabilityConfig.get_stream_backend` | os.environ.get | environment | RPG_STREAM_BACKEND | unless: os.environ.get('SIM_STREAM_BACKEND') |
| 208 | `src/observability/config.py` | 321 | `ObservabilityConfig.get_redis_url` | os.environ.get | environment | SIM_REDIS_URL | none in this function |
| 209 | `src/observability/config.py` | 321 | `ObservabilityConfig.get_redis_url` | os.environ.get | environment | RPG_REDIS_URL | unless: os.environ.get('SIM_REDIS_URL') |
| 210 | `src/observability/config.py` | 326 | `ObservabilityConfig.get_stream_name` | os.environ.get | environment | SIM_STREAM_NAME | none in this function |
| 211 | `src/observability/config.py` | 326 | `ObservabilityConfig.get_stream_name` | os.environ.get | environment | RPG_STREAM_NAME | unless: os.environ.get('SIM_STREAM_NAME') |
| 212 | `src/observability/config.py` | 331 | `ObservabilityConfig.get_max_queue_size` | os.environ.get | environment | SIM_MAX_QUEUE_SIZE | none in this function |
| 213 | `src/observability/config.py` | 331 | `ObservabilityConfig.get_max_queue_size` | os.environ.get | environment | RPG_MAX_QUEUE_SIZE | unless: os.environ.get('SIM_MAX_QUEUE_SIZE') |
| 214 | `src/observability/config.py` | 347 | `ObservabilityConfig.get_warehouse_backend` | os.environ.get | environment | SIM_WAREHOUSE_BACKEND | none in this function |
| 215 | `src/observability/config.py` | 347 | `ObservabilityConfig.get_warehouse_backend` | os.environ.get | environment | RPG_WAREHOUSE_BACKEND | unless: os.environ.get('SIM_WAREHOUSE_BACKEND') |
| 216 | `src/observability/config.py` | 358 | `ObservabilityConfig.get_clickhouse_host` | os.environ.get | environment | SIM_WAREHOUSE_CLICKHOUSE_HOST | none in this function |
| 217 | `src/observability/config.py` | 358 | `ObservabilityConfig.get_clickhouse_host` | os.environ.get | environment | RPG_WAREHOUSE_CLICKHOUSE_HOST | unless: os.environ.get('SIM_WAREHOUSE_CLICKHOUSE_HOST') |
| 218 | `src/observability/config.py` | 363 | `ObservabilityConfig.get_clickhouse_port` | os.environ.get | environment | SIM_WAREHOUSE_CLICKHOUSE_PORT | none in this function |
| 219 | `src/observability/config.py` | 363 | `ObservabilityConfig.get_clickhouse_port` | os.environ.get | environment | RPG_WAREHOUSE_CLICKHOUSE_PORT | unless: os.environ.get('SIM_WAREHOUSE_CLICKHOUSE_PORT') |
| 220 | `src/observability/config.py` | 374 | `ObservabilityConfig.get_clickhouse_database` | os.environ.get | environment | SIM_WAREHOUSE_CLICKHOUSE_DATABASE | none in this function |
| 221 | `src/observability/config.py` | 374 | `ObservabilityConfig.get_clickhouse_database` | os.environ.get | environment | RPG_WAREHOUSE_CLICKHOUSE_DATABASE | unless: os.environ.get('SIM_WAREHOUSE_CLICKHOUSE_DATABASE') |
| 222 | `src/observability/config.py` | 379 | `ObservabilityConfig.get_clickhouse_username` | os.environ.get | environment | SIM_WAREHOUSE_CLICKHOUSE_USERNAME | none in this function |
| 223 | `src/observability/config.py` | 379 | `ObservabilityConfig.get_clickhouse_username` | os.environ.get | environment | RPG_WAREHOUSE_CLICKHOUSE_USERNAME | unless: os.environ.get('SIM_WAREHOUSE_CLICKHOUSE_USERNAME') |
| 224 | `src/observability/config.py` | 384 | `ObservabilityConfig.get_clickhouse_password` | os.environ.get | environment | SIM_WAREHOUSE_CLICKHOUSE_PASSWORD | none in this function |
| 225 | `src/observability/config.py` | 384 | `ObservabilityConfig.get_clickhouse_password` | os.environ.get | environment | RPG_WAREHOUSE_CLICKHOUSE_PASSWORD | unless: os.environ.get('SIM_WAREHOUSE_CLICKHOUSE_PASSWORD') |
| 226 | `src/observability/config.py` | 389 | `ObservabilityConfig.get_clickhouse_secure` | os.environ.get | environment | SIM_WAREHOUSE_CLICKHOUSE_SECURE | none in this function |
| 227 | `src/observability/config.py` | 389 | `ObservabilityConfig.get_clickhouse_secure` | os.environ.get | environment | RPG_WAREHOUSE_CLICKHOUSE_SECURE | unless: os.environ.get('SIM_WAREHOUSE_CLICKHOUSE_SECURE') |
| 228 | `src/observability/config.py` | 397 | `ObservabilityConfig.get_clickhouse_batch_size` | os.environ.get | environment | SIM_WAREHOUSE_CLICKHOUSE_BATCH_SIZE | none in this function |
| 229 | `src/observability/config.py` | 397 | `ObservabilityConfig.get_clickhouse_batch_size` | os.environ.get | environment | RPG_WAREHOUSE_CLICKHOUSE_BATCH_SIZE | unless: os.environ.get('SIM_WAREHOUSE_CLICKHOUSE_BATCH_SIZE') |
| 230 | `src/observability/event_extractor.py` | 167 | `EventExtractor.extract` | time.time | wall-clock | - | none in this function |
| 231 | `src/observability/event_shapers.py` | 133 | `CombatShaper.shape` | time.time | wall-clock | - | none in this function |
| 232 | `src/observability/event_shapers.py` | 1723 | `NarrativeShaper.shape` | time.time | wall-clock | - | none in this function |
| 233 | `src/observability/events.py` | 56 | `SimulationEvent` | uuid.uuid4 | entropy | - | none in this function |
| 268 | `src/observability/stream/adapters.py` | 148 | `RedisStreamAdapter._connect` | datetime.datetime.now | wall-clock | - | try |
| 269 | `src/observability/stream/adapters.py` | 200 | `RedisStreamAdapter._send_to_redis` | datetime.datetime.now | wall-clock | - | try |
| 270 | `src/observability/stream/adapters.py` | 284 | `RedisStreamAdapter.flush` | time.perf_counter | wall-clock | - | none in this function |
| 271 | `src/observability/stream/adapters.py` | 285 | `RedisStreamAdapter.flush` | time.perf_counter | wall-clock | - | none in this function |
| 272 | `src/observability/stream/consumer.py` | 83 | `RedisStreamConsumer._send_to_dlq` | datetime.datetime.now | wall-clock | - | try |
| 337 | `src/simulation_quality/feed.py` | 129 | `build_feed_from_env` | os.environ.get | environment | QUALITY_SCORING_DISABLED | none in this function |
| 338 | `src/simulation_quality/feed.py` | 131 | `build_feed_from_env` | os.environ.get | environment | QUALITY_FEED_MODE | none in this function |
| 339 | `src/simulation_quality/feed.py` | 136 | `build_feed_from_env` | os.environ.get | environment | QUALITY_BROKER_URL | if mode == 'broker' |
| 340 | `src/simulation_quality/feed.py` | 137 | `build_feed_from_env` | os.environ.get | environment | QUALITY_STREAM_NAME | if mode == 'broker' |
| 341 | `src/simulation_quality/feed.py` | 138 | `build_feed_from_env` | os.environ.get | environment | QUALITY_CONSUMER_GROUP | if mode == 'broker' |
| 342 | `src/simulation_quality/quality_hub.py` | 117 | `QualityHub.__init__` | os.environ.get | environment | QUALITY_SCORING_DISABLED | none in this function |
| 343 | `src/simulation_quality/quality_report.py` | 130 | `QualityReportBuilder.build` | datetime.datetime.now | wall-clock | - | none in this function |
| 358 | `src/worldbuilding/compiler.py` | 371 | `WorldCompiler.compile` | time.perf_counter | wall-clock | - | none in this function |
| 359 | `src/worldbuilding/compiler.py` | 839 | `WorldCompiler.compile` | time.perf_counter | wall-clock | - | none in this function |
| 360 | `src/worldbuilding/repository.py` | 209 | `WorldRepository._update_index_entry` | datetime.datetime.now | wall-clock | - | none in this function |
| 361 | `src/worldbuilding/repository.py` | 281 | `WorldRepository.rebuild_index` | datetime.datetime.now | wall-clock | - | try; if yaml_file.is_file(); if path.is_dir(); if self.worlds_dir.is_dir() |
| 362 | `src/worldbuilding/repository.py` | 297 | `WorldRepository.rebuild_index` | datetime.datetime.now | wall-clock | - | if yaml_file.is_file(); if path.is_dir(); if self.worlds_dir.is_dir() |

### G2. Reads in modules not reachable from the kernel

| # | File | Line | Enclosing function | Source | Kind | Env var | Guards in the function |
|---|---|---|---|---|---|---|---|
| 1 | `src/api/admission_control.py` | 190 | `_check_admission` | time.time | wall-clock | - | if current_time is None |
| 2 | `src/api/agent_ops_dashboard/ingest.py` | 558 | `DashboardCache._maybe_rebuild` | datetime.datetime.now | wall-clock | - | unless: now |
| 3 | `src/api/agent_ops_dashboard/ingest.py` | 857 | `DashboardCache.get_agent_monitoring_stats` | datetime.datetime.now | wall-clock | - | if days; else of: if all_time |
| 4 | `src/api/engine_manager.py` | 266 | `V2EngineManager.start` | time.time | wall-clock | - | none in this function |
| 5 | `src/api/engine_manager.py` | 322 | `V2EngineManager._run_loop` | time.time | wall-clock | - | try; while not self._stop_requested.is_set() |
| 6 | `src/api/engine_manager.py` | 387 | `V2EngineManager.last_tick_age_seconds` | time.time | wall-clock | - | none in this function |
| 7 | `src/api/engine_manager.py` | 397 | `V2EngineManager.get_health_status` | time.time | wall-clock | - | none in this function |
| 8 | `src/api/ws/stream.py` | 275 | `stream_live_events_ws.heartbeat_loop` | time.time | wall-clock | - | while True; try |
| 9 | `src/certification/hardware.py` | 21 | `HardwareClassifier.detect_class` | psutil.cpu_count | CPU/host topology | - | none in this function |
| 10 | `src/certification/hardware.py` | 22 | `HardwareClassifier.detect_class` | psutil.virtual_memory | memory | - | none in this function |
| 11 | `src/certification/hardware.py` | 38 | `HardwareClassifier.get_detailed_telemetry` | psutil.cpu_count | CPU/host topology | - | none in this function |
| 12 | `src/certification/hardware.py` | 39 | `HardwareClassifier.get_detailed_telemetry` | psutil.cpu_count | CPU/host topology | - | none in this function |
| 13 | `src/certification/hardware.py` | 40 | `HardwareClassifier.get_detailed_telemetry` | psutil.virtual_memory | memory | - | none in this function |
| 14 | `src/certification/hardware.py` | 41 | `HardwareClassifier.get_detailed_telemetry` | psutil.cpu_freq | CPU/host topology | - | none in this function |
| 15 | `src/certification/hardware.py` | 41 | `HardwareClassifier.get_detailed_telemetry` | psutil.cpu_freq | CPU/host topology | - | if psutil.cpu_freq() (conditional expression) |
| 16 | `src/certification/harness.py` | 74 | `CertificationHarness.run_scenario` | uuid.uuid4 | entropy | - | none in this function |
| 17 | `src/certification/harness.py` | 75 | `CertificationHarness.run_scenario` | time.time | wall-clock | - | none in this function |
| 18 | `src/certification/harness.py` | 83 | `CertificationHarness.run_scenario` | time.time | wall-clock | - | none in this function |
| 19 | `src/certification/harness.py` | 110 | `CertificationHarness.run_scenario` | time.perf_counter_ns | wall-clock | - | none in this function |
| 20 | `src/certification/harness.py` | 129 | `CertificationHarness.run_scenario` | time.perf_counter_ns | wall-clock | - | none in this function |
| 21 | `src/cli/entry.py` | 248 | `_run_cli` | time.time | wall-clock | - | none in this function |
| 22 | `src/cli/entry.py` | 262 | `_run_cli` | time.time | wall-clock | - | none in this function |
| 23 | `src/config/loader.py` | 56 | `ConfigLoader.load_profile` | os.environ (whole mapping) | environment | - | none in this function |
| 24 | `src/config/loader.py` | 57 | `ConfigLoader.load_profile` | os.environ[...] | environment | - | if env_key in os.environ |
| 25 | `src/config/loader.py` | 73 | `ConfigLoader.load_profile` | os.environ.get | environment | BROKER_DISABLED | none in this function |
| 26 | `src/config/loader.py` | 78 | `ConfigLoader.load_profile` | os.environ.get | environment | TELEMETRY_DISABLED | none in this function |
| 27 | `src/core/certification_reporter.py` | 48 | `CertificationReporter.generate_report` | datetime.datetime.utcnow | wall-clock | - | none in this function |
| 28 | `src/core/certification_reporter.py` | 59 | `CertificationReporter.generate_report` | datetime.datetime.utcnow | wall-clock | - | none in this function |
| 29 | `src/domains/campaigns/runner.py` | 45 | `SimulationAnalysisRunner.run` | time.perf_counter_ns | wall-clock | - | none in this function |
| 30 | `src/domains/campaigns/runner.py` | 100 | `SimulationAnalysisRunner.run` | time.perf_counter_ns | wall-clock | - | none in this function |
| 31 | `src/domains/campaigns/runner.py` | 104 | `SimulationAnalysisRunner.run` | time.perf_counter_ns | wall-clock | - | none in this function |
| 32 | `src/domains/campaigns/runner.py` | 109 | `SimulationAnalysisRunner.run` | time.perf_counter_ns | wall-clock | - | none in this function |
| 33 | `src/domains/campaigns/runner.py` | 125 | `SimulationAnalysisRunner.run` | time.perf_counter_ns | wall-clock | - | none in this function |
| 34 | `src/domains/campaigns/runner.py` | 133 | `SimulationAnalysisRunner.run` | time.perf_counter_ns | wall-clock | - | none in this function |
| 35 | `src/domains/campaigns/runner.py` | 141 | `SimulationAnalysisRunner.run` | time.perf_counter_ns | wall-clock | - | none in this function |
| 36 | `src/domains/campaigns/runner.py` | 151 | `SimulationAnalysisRunner.run` | time.perf_counter_ns | wall-clock | - | none in this function |
| 37 | `src/domains/campaigns/runner.py` | 157 | `SimulationAnalysisRunner.run` | time.perf_counter_ns | wall-clock | - | none in this function |
| 38 | `src/domains/campaigns/runner.py` | 170 | `SimulationAnalysisRunner.run` | time.perf_counter_ns | wall-clock | - | none in this function |
| 129 | `src/lab/audit.py` | 79 | `LabApprovalGate.record_approval` | datetime.datetime.now | wall-clock | - | none in this function |
| 130 | `src/lab/audit.py` | 129 | `LabAuditTrail.log_event` | datetime.datetime.now | wall-clock | - | none in this function |
| 131 | `src/lab/cli.py` | 156 | `main` | datetime.datetime.now | wall-clock | - | if not lab_run_id; if parsed.command == 'run'; else of: if parsed.command == 'validate-experiment'; else of: if parsed.command == 'validate-scenario'; else of: if parsed.command == 'validate-world'; try |
| 132 | `src/lab/cli.py` | 277 | `main` | datetime.datetime.now | wall-clock | - | if not mutation_lab_id; if parsed.command == 'run-mutation'; else of: if parsed.command == 'preview-mutation'; else of: if parsed.command == 'validate-mutation'; else of: if parsed.command == 'inspect'; else of: if parsed.command == 'list'; else of: if parsed.command == 'report'; else of: if parsed.command == 'status'; else of: if parsed.command == 'run'; else of: if parsed.command == 'validate-experiment'; else of: if parsed.command == 'validate-scenario'; else of: if parsed.command == 'validate-world'; try |
| 133 | `src/lab/mutation_orchestrator.py` | 79 | `MutationLabOrchestrator.run_mutation_lab` | time.time | wall-clock | - | none in this function |
| 134 | `src/lab/mutation_orchestrator.py` | 80 | `MutationLabOrchestrator.run_mutation_lab` | datetime.datetime.now | wall-clock | - | none in this function |
| 135 | `src/lab/mutation_orchestrator.py` | 337 | `MutationLabOrchestrator.run_mutation_lab` | datetime.datetime.now | wall-clock | - | none in this function |
| 136 | `src/lab/mutation_orchestrator.py` | 338 | `MutationLabOrchestrator.run_mutation_lab` | time.time | wall-clock | - | none in this function |
| 137 | `src/lab/mutation_orchestrator.py` | 358 | `MutationLabOrchestrator.run_mutation_lab` | time.time | wall-clock | - | none in this function |
| 138 | `src/lab/orchestrator.py` | 135 | `ScenarioLabOrchestrator.run_lab` | datetime.datetime.now | wall-clock | - | none in this function |
| 139 | `src/lab/orchestrator.py` | 350 | `ScenarioLabOrchestrator.run_lab` | datetime.datetime.now | wall-clock | - | try |
| 140 | `src/lab/repository.py` | 119 | `ScenarioRepository.rebuild_index` | datetime.datetime.now | wall-clock | - | if spec |
| 141 | `src/lab/repository.py` | 130 | `ScenarioRepository.rebuild_index` | datetime.datetime.now | wall-clock | - | else of: if spec |
| 142 | `src/lab/repository.py` | 256 | `ExperimentRepository.rebuild_index` | datetime.datetime.now | wall-clock | - | if spec |
| 143 | `src/lab/repository.py` | 267 | `ExperimentRepository.rebuild_index` | datetime.datetime.now | wall-clock | - | else of: if spec |
| 144 | `src/lab/repository.py` | 450 | `LabRunRepository.rebuild_index` | datetime.datetime.now | wall-clock | - | try |
| 145 | `src/lab/repository.py` | 465 | `LabRunRepository.rebuild_index` | datetime.datetime.now | wall-clock | - | none in this function |
| 146 | `src/lab/repository.py` | 592 | `MutationRepository.rebuild_index` | datetime.datetime.now | wall-clock | - | if spec |
| 147 | `src/lab/repository.py` | 603 | `MutationRepository.rebuild_index` | datetime.datetime.now | wall-clock | - | else of: if spec |
| 148 | `src/lab/session.py` | 104 | `LabSessionStore.create_session` | datetime.datetime.now | wall-clock | - | none in this function |
| 149 | `src/lab/session.py` | 145 | `LabSessionStore.save_session` | datetime.datetime.now | wall-clock | - | none in this function |
| 150 | `src/lab/workflows/update_simulation_knowledge.py` | 148 | `UpdateSimulationKnowledgeWorkflow.run` | datetime.datetime.now | wall-clock | - | none in this function |
| 151 | `src/lab/workflows/update_simulation_knowledge.py` | 203 | `UpdateSimulationKnowledgeWorkflow.run` | datetime.datetime.now | wall-clock | - | none in this function |
| 152 | `src/logging/formatter.py` | 34 | `JsonFormatter.format` | datetime.datetime.utcnow | wall-clock | - | none in this function |
| 172 | `src/observability/analytics/dataset.py` | 46 | `AnalyticsDatasetBuilder.build_dataset` | uuid.uuid4 | entropy | - | if not dataset_id |
| 173 | `src/observability/analytics/exporter.py` | 17 | `ExportJob` | uuid.uuid4 | entropy | - | none in this function |
| 174 | `src/observability/anomaly/rules.py` | 9 | `Anomaly` | uuid.uuid4 | entropy | - | none in this function |
| 175 | `src/observability/anomaly/rules_engine.py` | 22 | `AnomalyRecord` | uuid.uuid4 | entropy | - | none in this function |
| 176 | `src/observability/anomaly/triage.py` | 216 | `TriageEngine.cluster_anomalies` | uuid.uuid4 | entropy | - | if not merged |
| 177 | `src/observability/anomaly/worker.py` | 43 | `WorkerStatus` | datetime.datetime.now | wall-clock | - | none in this function |
| 178 | `src/observability/anomaly/worker.py` | 56 | `ExternalAnomalyWorker.__init__` | uuid.uuid4 | entropy | - | unless: worker_id |
| 179 | `src/observability/anomaly/worker.py` | 79 | `ExternalAnomalyWorker.update_status` | datetime.datetime.now | wall-clock | - | none in this function |
| 180 | `src/observability/anomaly/worker.py` | 140 | `LiveWorkerConfig` | uuid.uuid4 | entropy | - | none in this function |
| 181 | `src/observability/anomaly/worker.py` | 282 | `LiveAnomalyWorker._run_loop` | time.time | wall-clock | - | while not self._stop_event.is_set() |
| 182 | `src/observability/anomaly/worker.py` | 358 | `LiveAnomalyWorker.flush_diagnostics` | psutil.Process | CPU/host topology | - | try |
| 183 | `src/observability/anomaly/worker.py` | 359 | `LiveAnomalyWorker.flush_diagnostics` | psutil.Process.memory_info | memory | - | try |
| 184 | `src/observability/anomaly/worker.py` | 367 | `LiveAnomalyWorker.flush_diagnostics` | datetime.datetime.now | wall-clock | - | none in this function |
| 185 | `src/observability/anomaly/worker.py` | 399 | `LiveAnomalyWorker.update_status` | datetime.datetime.now | wall-clock | - | none in this function |
| 186 | `src/observability/anomaly/worker.py` | 413 | `<module>` | os.environ.get | environment | LOG_LEVEL | if __name__ == '__main__' |
| 187 | `src/observability/anomaly/worker.py` | 417 | `<module>` | os.environ.get | environment | SIM_STREAM_BACKEND | if __name__ == '__main__' |
| 188 | `src/observability/anomaly/worker.py` | 418 | `<module>` | os.environ.get | environment | SIM_STREAM_NAME | if __name__ == '__main__' |
| 189 | `src/observability/anomaly/worker.py` | 419 | `<module>` | os.environ.get | environment | SIM_REDIS_URL | if __name__ == '__main__' |
| 190 | `src/observability/anomaly/worker.py` | 420 | `<module>` | os.environ.get | environment | SIM_CONSUMER_GROUP | if __name__ == '__main__' |
| 191 | `src/observability/behavior/episode_detector.py` | 58 | `EpisodeDetector.detect` | uuid.uuid4 | entropy | - | if active_combat_start is not None and (ev.behavior_category == 'combat' and ev.behavior_family in ('kill_or_defeat', 'defeat') or (ev.behavior_category == 'recovery' and ev.behavior_family == 'recover')); else of: if ev.behavior_category == 'combat' and ev.behavior_family == 'engage' |
| 192 | `src/observability/behavior/episode_detector.py` | 83 | `EpisodeDetector.detect` | uuid.uuid4 | entropy | - | if ev.behavior_family == 'complete'; if active_quest_start is not None and ev.behavior_category == 'quest' and (ev.target_id == active_quest_id); else of: if ev.behavior_category == 'quest' and ev.behavior_family == 'accept' |
| 193 | `src/observability/behavior/episode_detector.py` | 100 | `EpisodeDetector.detect` | uuid.uuid4 | entropy | - | if active_quest_start is not None and ev.behavior_category == 'failure_response' and (ev.behavior_family == 'quest_failure'); else of: if active_quest_start is not None and ev.behavior_category == 'quest' and (ev.target_id == active_quest_id); else of: if ev.behavior_category == 'quest' and ev.behavior_family == 'accept' |
| 194 | `src/observability/behavior/episode_detector.py` | 123 | `EpisodeDetector.detect` | uuid.uuid4 | entropy | - | if active_info_start is not None and ev.behavior_category == 'information_seeking' and (ev.behavior_family == 'learned'); else of: if ev.behavior_category == 'information_seeking' and ev.behavior_family == 'query' |
| 195 | `src/observability/behavior/episode_detector.py` | 146 | `EpisodeDetector.detect` | uuid.uuid4 | entropy | - | if active_fail_start is not None and ev.behavior_category == 'movement' and (ev.behavior_family == 'travel') and (ev.outcome == 'success'); else of: if ev.behavior_category == 'failure_response' and ev.behavior_family == 'blocked_route' |
| 196 | `src/observability/behavior/episode_detector.py` | 163 | `EpisodeDetector.detect` | uuid.uuid4 | entropy | - | if active_combat_start is not None |
| 197 | `src/observability/behavior/episode_detector.py` | 178 | `EpisodeDetector.detect` | uuid.uuid4 | entropy | - | if active_quest_start is not None |
| 198 | `src/observability/behavior/pattern_detectors.py` | 27 | `RepeatedFailureLoopDetector.detect` | uuid.uuid4 | entropy | - | if len(failure_episodes) >= 3 |
| 199 | `src/observability/behavior/pattern_detectors.py` | 54 | `BehaviorChangeProofDetector.detect` | uuid.uuid4 | entropy | - | none in this function |
| 200 | `src/observability/behavior/pattern_detectors.py` | 82 | `HiddenKnowledgeSuspicionDetector.detect` | uuid.uuid4 | entropy | - | if len(avoidances) >= 3 and len(queries) == 0 |
| 234 | `src/observability/live/snapshot_provider.py` | 66 | `LiveSnapshotProvider.get_status` | time.time | wall-clock | - | if manager.is_running or manager.is_paused; if manager.started_at is not None |
| 235 | `src/observability/mining/auditor.py` | 89 | `DataCompletenessAuditor.audit_completeness` | datetime.datetime.now | wall-clock | - | none in this function |
| 236 | `src/observability/mining/auditor.py` | 216 | `DeterminismAuditor.audit_determinism` | datetime.datetime.now | wall-clock | - | none in this function |
| 237 | `src/observability/mining/controller.py` | 143 | `MiningExperimentController.execute_experiment` | time.time | wall-clock | - | if not experiment_id |
| 238 | `src/observability/mining/controller.py` | 143 | `MiningExperimentController.execute_experiment` | uuid.uuid4 | entropy | - | if not experiment_id |
| 239 | `src/observability/mining/controller.py` | 153 | `MiningExperimentController.execute_experiment` | datetime.datetime.now | wall-clock | - | none in this function |
| 240 | `src/observability/mining/controller.py` | 276 | `MiningExperimentController.execute_experiment` | datetime.datetime.now | wall-clock | - | try |
| 241 | `src/observability/mining/controller.py` | 308 | `MiningExperimentController._write_status` | datetime.datetime.now | wall-clock | - | none in this function |
| 242 | `src/observability/mining/dataset.py` | 348 | `MiningDatasetBuilder.build_dataset` | datetime.datetime.now | wall-clock | - | none in this function |
| 243 | `src/observability/mining/evidence.py` | 346 | `EvidencePackBuilder.build_evidence_pack` | datetime.datetime.now | wall-clock | - | none in this function |
| 244 | `src/observability/mining/evidence.py` | 364 | `EvidencePackBuilder.build_evidence_pack` | datetime.datetime.now | wall-clock | - | none in this function |
| 245 | `src/observability/mining/orchestrator.py` | 121 | `AIAgentInvestigationRunner.run_investigation` | uuid.uuid4 | entropy | - | none in this function |
| 246 | `src/observability/mining/orchestrator.py` | 131 | `AIAgentInvestigationRunner.run_investigation` | datetime.datetime.now | wall-clock | - | none in this function |
| 247 | `src/observability/mining/orchestrator.py` | 173 | `AIAgentInvestigationRunner._write_markdown_finding` | datetime.datetime.now | wall-clock | - | none in this function |
| 248 | `src/observability/mining/patterns.py` | 103 | `PatternMiningEngine.mine_patterns` | datetime.datetime.now | wall-clock | - | none in this function |
| 249 | `src/observability/mining/priority.py` | 131 | `EngineeringBacklogGenerator.generate_backlog` | datetime.datetime.now | wall-clock | - | none in this function |
| 250 | `src/observability/mining/recommender.py` | 108 | `NextExperimentRecommender.recommend_next` | datetime.datetime.now | wall-clock | - | none in this function |
| 251 | `src/observability/mining/workflow.py` | 41 | `MiningReviewWorkflow.apply_review_label` | datetime.datetime.now | wall-clock | - | if item['candidate_id'] == candidate_id |
| 252 | `src/observability/mining/workflow.py` | 137 | `MiningQualityGate.evaluate_gate` | datetime.datetime.now | wall-clock | - | none in this function |
| 253 | `src/observability/performance/profiler.py` | 38 | `PhaseProfileScope.__enter__` | time.perf_counter_ns | wall-clock | - | if self.enabled |
| 254 | `src/observability/performance/profiler.py` | 45 | `PhaseProfileScope.__exit__` | time.perf_counter_ns | wall-clock | - | none in this function |
| 255 | `src/observability/readiness/harness.py` | 62 | `ReadinessResults.finalize` | datetime.datetime.now | wall-clock | - | none in this function |
| 256 | `src/observability/readiness/harness.py` | 117 | `ProductionReadinessHarness.run_overhead_scenario` | time.perf_counter_ns | wall-clock | - | try |
| 257 | `src/observability/readiness/harness.py` | 119 | `ProductionReadinessHarness.run_overhead_scenario` | time.perf_counter_ns | wall-clock | - | try |
| 258 | `src/observability/readiness/harness.py` | 129 | `ProductionReadinessHarness.run_overhead_scenario` | time.perf_counter_ns | wall-clock | - | try |
| 259 | `src/observability/readiness/harness.py` | 131 | `ProductionReadinessHarness.run_overhead_scenario` | time.perf_counter_ns | wall-clock | - | try |
| 260 | `src/observability/readiness/harness.py` | 411 | `ProductionReadinessHarness.run_all` | time.perf_counter | wall-clock | - | none in this function |
| 261 | `src/observability/readiness/harness.py` | 414 | `ProductionReadinessHarness.run_all` | time.perf_counter | wall-clock | - | try |
| 262 | `src/observability/readiness/harness.py` | 419 | `ProductionReadinessHarness.run_all` | time.perf_counter | wall-clock | - | none in this function |
| 263 | `src/observability/reporting/baseline_generator.py` | 255 | `BaselineGenerator.generate_baseline` | datetime.datetime.now | wall-clock | - | none in this function |
| 264 | `src/observability/reporting/retention.py` | 80 | `RetentionManager.generate_cleanup_plan` | datetime.datetime.now | wall-clock | - | none in this function |
| 265 | `src/observability/reporting/retention.py` | 208 | `RetentionManager.execute_cleanup` | datetime.datetime.now | wall-clock | - | if os.path.exists(manifest_path); else of: if 'full directory' in details['reason'] or details['reason'].startswith('Evaluation error'); try |
| 266 | `src/observability/reporting/retention.py` | 221 | `RetentionManager.execute_cleanup` | datetime.datetime.now | wall-clock | - | none in this function |
| 267 | `src/observability/reporting/run_report.py` | 108 | `RunReportGenerator.generate` | time.time | wall-clock | - | none in this function |
| 273 | `src/observability/sweeper.py` | 110 | `ScenarioSweeper.run_sweep` | time.time | wall-clock | - | if not sweep_id |
| 274 | `src/observability/sweeper.py` | 110 | `ScenarioSweeper.run_sweep` | uuid.uuid4 | entropy | - | if not sweep_id |
| 275 | `src/observability/sweeper.py` | 120 | `ScenarioSweeper.run_sweep` | datetime.datetime.now | wall-clock | - | none in this function |
| 276 | `src/observability/sweeper.py` | 259 | `ScenarioSweeper.run_sweep` | datetime.datetime.now | wall-clock | - | try |
| 277 | `src/observability/understanding/balance/models.py` | 18 | `BalanceFinding` | uuid.uuid4 | entropy | - | none in this function |
| 278 | `src/observability/understanding/domain/base.py` | 44 | `DomainFinding` | uuid.uuid4 | entropy | - | none in this function |
| 279 | `src/observability/understanding/domain/base.py` | 172 | `DomainAnalyzerRegistry.run_all` | time.perf_counter_ns | wall-clock | - | none in this function |
| 280 | `src/observability/understanding/domain/base.py` | 175 | `DomainAnalyzerRegistry.run_all` | time.perf_counter_ns | wall-clock | - | try |
| 281 | `src/observability/understanding/domain/base.py` | 177 | `DomainAnalyzerRegistry.run_all` | time.perf_counter_ns | wall-clock | - | none in this function |
| 282 | `src/observability/understanding/pipeline.py` | 118 | `UnderstandingPipeline.run` | time.perf_counter_ns | wall-clock | - | none in this function |
| 283 | `src/observability/understanding/pipeline.py` | 188 | `UnderstandingPipeline.run` | time.perf_counter_ns | wall-clock | - | none in this function |
| 284 | `src/observability/understanding/quality/baseline_evolution.py` | 106 | `BaselinePromotionWorkflow.promote` | datetime.datetime.now | wall-clock | - | none in this function |
| 285 | `src/observability/understanding/quality/quality_report.py` | 87 | `AnalyzerQualityReporter.compute` | datetime.datetime.now | wall-clock | - | none in this function |
| 286 | `src/observability/understanding/review/models.py` | 25 | `FindingReview` | uuid.uuid4 | entropy | - | none in this function |
| 287 | `src/observability/understanding/review/models.py` | 29 | `FindingReview` | datetime.datetime.now | wall-clock | - | none in this function |
| 288 | `src/observability/understanding/rootcause/models.py` | 34 | `RootCauseHypothesis` | uuid.uuid4 | entropy | - | none in this function |
| 289 | `src/observability/understanding/stories/models.py` | 11 | `StoryCandidate` | uuid.uuid4 | entropy | - | none in this function |
| 290 | `src/observability/warehouse/adapters.py` | 40 | `NullWarehouseAdapter.ingest_run` | uuid.uuid4 | entropy | - | none in this function |
| 291 | `src/observability/warehouse/adapters.py` | 49 | `NullWarehouseAdapter.ingest_sweep` | uuid.uuid4 | entropy | - | none in this function |
| 292 | `src/observability/warehouse/adapters.py` | 121 | `LocalWarehouseAdapter.ingest_run` | time.perf_counter | wall-clock | - | none in this function |
| 293 | `src/observability/warehouse/adapters.py` | 122 | `LocalWarehouseAdapter.ingest_run` | uuid.uuid4 | entropy | - | none in this function |
| 294 | `src/observability/warehouse/adapters.py` | 181 | `LocalWarehouseAdapter.ingest_run` | datetime.datetime.utcnow | wall-clock | - | unless: event_dict.get('timestamp'); if os.path.exists(events_path); try |
| 295 | `src/observability/warehouse/adapters.py` | 269 | `LocalWarehouseAdapter.ingest_run` | time.perf_counter | wall-clock | - | none in this function |
| 296 | `src/observability/warehouse/adapters.py` | 280 | `LocalWarehouseAdapter.ingest_sweep` | time.perf_counter | wall-clock | - | none in this function |
| 297 | `src/observability/warehouse/adapters.py` | 281 | `LocalWarehouseAdapter.ingest_sweep` | uuid.uuid4 | entropy | - | none in this function |
| 298 | `src/observability/warehouse/adapters.py` | 314 | `LocalWarehouseAdapter.ingest_sweep` | datetime.datetime.utcnow | wall-clock | - | try |
| 299 | `src/observability/warehouse/adapters.py` | 335 | `LocalWarehouseAdapter.ingest_sweep` | time.perf_counter | wall-clock | - | none in this function |
| 300 | `src/observability/warehouse/adapters.py` | 443 | `LocalWarehouseAdapter.query_events` | datetime.datetime.utcnow | wall-clock | - | unless: event_dict.get('timestamp'); try |
| 301 | `src/observability/warehouse/clickhouse.py` | 235 | `ClickHouseWarehouseAdapter.health` | time.perf_counter | wall-clock | - | none in this function |
| 302 | `src/observability/warehouse/clickhouse.py` | 238 | `ClickHouseWarehouseAdapter.health` | time.perf_counter | wall-clock | - | try |
| 303 | `src/observability/warehouse/clickhouse.py` | 297 | `ClickHouseWarehouseAdapter.ingest_run` | time.perf_counter | wall-clock | - | none in this function |
| 304 | `src/observability/warehouse/clickhouse.py` | 298 | `ClickHouseWarehouseAdapter.ingest_run` | uuid.uuid4 | entropy | - | none in this function |
| 305 | `src/observability/warehouse/clickhouse.py` | 330 | `ClickHouseWarehouseAdapter.ingest_run` | time.perf_counter | wall-clock | - | if existing_checksum == checksum; if existing; if not dry_run; try |
| 306 | `src/observability/warehouse/clickhouse.py` | 425 | `ClickHouseWarehouseAdapter.ingest_run` | datetime.datetime.utcnow | wall-clock | - | unless: event_dict.get('timestamp'); if os.path.exists(events_path); try |
| 307 | `src/observability/warehouse/clickhouse.py` | 572 | `ClickHouseWarehouseAdapter.ingest_run` | time.perf_counter | wall-clock | - | none in this function |
| 308 | `src/observability/warehouse/clickhouse.py` | 586 | `ClickHouseWarehouseAdapter.ingest_sweep` | time.perf_counter | wall-clock | - | none in this function |
| 309 | `src/observability/warehouse/clickhouse.py` | 587 | `ClickHouseWarehouseAdapter.ingest_sweep` | uuid.uuid4 | entropy | - | none in this function |
| 310 | `src/observability/warehouse/clickhouse.py` | 632 | `ClickHouseWarehouseAdapter.ingest_sweep` | datetime.datetime.utcnow | wall-clock | - | try |
| 311 | `src/observability/warehouse/clickhouse.py` | 672 | `ClickHouseWarehouseAdapter.ingest_sweep` | time.perf_counter | wall-clock | - | none in this function |
| 312 | `src/observability/warehouse/models.py` | 123 | `WarehouseIngestionResult` | datetime.datetime.now | wall-clock | - | none in this function |
| 313 | `src/observability/watchdog.py` | 9 | `<module>` | os.environ.get | environment | LOG_LEVEL | none in this function |
| 314 | `src/observability/watchdog.py` | 12 | `<module>` | os.environ.get | environment | BACKEND_URL | none in this function |
| 315 | `src/observability/watchdog.py` | 13 | `<module>` | os.environ.get | environment | LOKI_URL | none in this function |
| 316 | `src/observability/watchdog.py` | 14 | `<module>` | os.environ.get | environment | POLL_INTERVAL | none in this function |
| 317 | `src/observability/watchdog.py` | 70 | `SimulationWatchdog.check_loki_errors` | time.time | wall-clock | - | try |
| 318 | `src/perf/bench_harness.py` | 38 | `BenchHarness.__init__` | psutil.Process | CPU/host topology | - | none in this function |
| 319 | `src/perf/bench_harness.py` | 70 | `BenchHarness.run_benchmark` | psutil.Process.cpu_times | CPU time | - | try |
| 320 | `src/perf/bench_harness.py` | 83 | `BenchHarness.run_benchmark` | time.perf_counter | wall-clock | - | try |
| 321 | `src/perf/bench_harness.py` | 97 | `BenchHarness.run_benchmark` | psutil.Process.memory_info | memory | - | if i % 10 == 0; try; try |
| 322 | `src/perf/bench_harness.py` | 102 | `BenchHarness.run_benchmark` | time.perf_counter | wall-clock | - | try |
| 323 | `src/perf/bench_harness.py` | 103 | `BenchHarness.run_benchmark` | psutil.Process.cpu_times | CPU time | - | try |
| 324 | `src/perf/bench_harness.py` | 162 | `BenchHarness.run_benchmark` | time.time | wall-clock | - | try |
| 325 | `src/perf/long_run_harness.py` | 123 | `LongRunStabilityHarness.__init__` | psutil.Process | CPU/host topology | - | none in this function |
| 326 | `src/perf/long_run_harness.py` | 171 | `LongRunStabilityHarness.execute_run` | psutil.Process.memory_info | memory | - | none in this function |
| 327 | `src/perf/long_run_harness.py` | 178 | `LongRunStabilityHarness.execute_run` | time.perf_counter | wall-clock | - | none in this function |
| 328 | `src/perf/long_run_harness.py` | 182 | `LongRunStabilityHarness.execute_run` | time.perf_counter_ns | wall-clock | - | none in this function |
| 329 | `src/perf/long_run_harness.py` | 185 | `LongRunStabilityHarness.execute_run` | time.perf_counter_ns | wall-clock | - | none in this function |
| 330 | `src/perf/long_run_harness.py` | 193 | `LongRunStabilityHarness.execute_run` | psutil.Process.memory_info | memory | - | if t % sample_interval == 0 or t == total_ticks |
| 331 | `src/perf/long_run_harness.py` | 229 | `LongRunStabilityHarness.execute_run` | time.perf_counter | wall-clock | - | none in this function |
| 332 | `src/perf/long_run_harness.py` | 340 | `LongRunStabilityHarness._get_gc_collections` | gc.get_stats | memory | - | try |
| 333 | `src/perf/long_run_harness.py` | 348 | `LongRunStabilityHarness._get_gc_collections` | gc.get_count | memory | - | none in this function |
| 334 | `src/perf/profile_governance.py` | 36 | `profile_governance` | time.perf_counter | wall-clock | - | none in this function |
| 335 | `src/perf/profile_governance.py` | 38 | `profile_governance` | time.perf_counter | wall-clock | - | none in this function |
| 336 | `src/simulation_quality/api/routes.py` | 28 | `_is_disabled` | os.environ.get | environment | QUALITY_SCORING_DISABLED | none in this function |
| 344 | `src/simulation_quality/worker.py` | 63 | `QualityWorker.__init__` | os.environ.get | environment | QUALITY_WEIGHTS_PATH | none in this function |
| 345 | `src/simulation_quality/worker.py` | 66 | `QualityWorker.__init__` | os.environ.get | environment | QUALITY_GRADE_PATH | none in this function |
| 346 | `src/simulation_quality/worker.py` | 69 | `QualityWorker.__init__` | os.environ.get | environment | QUALITY_DETECTION_PATH | none in this function |
| 347 | `src/simulation_quality/worker.py` | 72 | `QualityWorker.__init__` | os.environ.get | environment | QUALITY_PROFILE | none in this function |
| 348 | `src/simulation_quality/worker.py` | 73 | `QualityWorker.__init__` | os.environ.get | environment | QUALITY_RUN_ID | none in this function |
| 349 | `src/simulation_quality/worker.py` | 74 | `QualityWorker.__init__` | os.environ.get | environment | QUALITY_RUN_DIR | none in this function |
| 350 | `src/simulation_quality/worker.py` | 81 | `QualityWorker.__init__` | os.environ.get | environment | QUALITY_BROKER_URL | none in this function |
| 351 | `src/simulation_quality/worker.py` | 82 | `QualityWorker.__init__` | os.environ.get | environment | QUALITY_STREAM_NAME | none in this function |
| 352 | `src/simulation_quality/worker.py` | 83 | `QualityWorker.__init__` | os.environ.get | environment | QUALITY_CONSUMER_GROUP | none in this function |
| 353 | `src/simulation_quality/worker.py` | 96 | `QualityWorker.run` | os.environ.get | environment | QUALITY_WORKER_PORT | none in this function |
| 354 | `src/simulation_quality/worker.py` | 113 | `QualityWorker.run` | os.environ.get | environment | QUALITY_STALE_WARNING_SECONDS | none in this function |
| 355 | `src/testing/scenario_runner.py` | 32 | `ScenarioRunner.execute` | time.perf_counter | wall-clock | - | none in this function |
| 356 | `src/testing/scenario_runner.py` | 139 | `ScenarioRunner.execute` | time.perf_counter | wall-clock | - | none in this function |
| 357 | `src/worldassembly/resolver.py` | 709 | `WorldAssemblyResolver.assemble` | datetime.datetime.now | wall-clock | - | none in this function |
| 363 | `src/worldgeneration/generator.py` | 332 | `WorldProceduralGenerator.generate` | datetime.datetime.now | wall-clock | - | none in this function |
| 364 | `src/worldgeneration/generator.py` | 599 | `ProceduralCompositionGenerator.generate` | datetime.datetime.now | wall-clock | - | none in this function |

### G3. Counts by kind

| Kind | Reads |
|---|---|
| CPU time | 2 |
| CPU/host topology | 10 |
| entropy | 34 |
| environment | 73 |
| memory | 9 |
| wall-clock | 236 |

### G4. Calls whose receiver the scanner could not resolve by name

| File | Line | Enclosing function | Call | Reachable from kernel |
|---|---|---|---|---|
| `src/certification/harness.py` | 145 | `CertificationHarness.run_scenario` | `kernel._replay.get_stats` | no |
| `src/engine/kernel.py` | 544 | `Kernel._phase_init` | `self._worker_manager.get_stats` | yes |
| `src/engine/kernel.py` | 545 | `Kernel._phase_init` | `self._replay.get_stats` | yes |
| `src/engine/kernel.py` | 772 | `Kernel._record_runtime_signals` | `self._worker_manager.get_stats` | yes |
| `src/engine/kernel.py` | 773 | `Kernel._record_runtime_signals` | `self._replay.get_stats` | yes |
| `src/engine/observability.py` | 116 | `SignalCollector.get_snapshot` | `kernel._worker_manager.get_stats` | yes |
| `src/engine/observability.py` | 117 | `SignalCollector.get_snapshot` | `kernel._replay.get_stats` | yes |
| `src/engine/replay_manager.py` | 120 | `ReplayManager.on_tick_end` | `self.get_stats` | yes |
| `src/engine/replay_manager.py` | 171 | `ReplayManager.finalize` | `self.get_stats` | yes |
| `src/engine/replay_manager.py` | 352 | `ReplayManager.get_stats` | `self._buffer.get_stats` | yes |

<!-- END GENERATED -->

## 3. Reads in modules the kernel imports, traced to their sinks

"Reachable" means imported, directly or through any chain, from `src/engine/kernel.py` (module-level or
function-level imports), so it over-approximates "can run inside a tick": it includes observability,
alerts, SimQ and world-building modules the kernel imports. Each group below was read by hand. The
classification column uses PERF-D1's own table: **Recorded**, **Derived**, **Not recorded and no effect on
authoritative state**, or **not in the PERF-D1 table**. `audit_mode` is `flags["audit_mode"]`
(`kernel.py:82`).

Sink classes: **control** (a decision that changes what is computed), **state** (an `AuthoritativeState`
field), **metric/log** (a counter, report, or log line), **artifact/event** (written outward, never read
back by the tick), **sink not traced** (last known hand-off point given).

| Group | Reads (file:line, function) | Value flows to | Sink | PERF-D1 class | `audit_mode` or other flag neutralizes it |
|---|---|---|---|---|---|
| T1 | `kernel.py:389,392,407,416,425,431,435,440,444,452,454` `Kernel._tick_once_inner` (11 `perf_counter_ns` stamps) | `_phase_costs[...]` (`:393,408,417,...`) summed into `_final_compute_ms` (`:456`) and later `:805`; `_record_runtime_signals` stores it as `PressureSignals.tick_compute_ms` (`:810-812`) | control (governor, `phase_governor.py:139`, end-of-tick drop `:458-463`) and state (§4.1) | the mode, the drop and the phase budgets are Recorded rows; the state path is not in the table | yes for the control uses: `audit_mode` zeroes the signals (`:541-553`) and gates the drop (`:461`); the `tick <= 5` clamp (`:556-557`) only limits the first ticks |
| T2 | `kernel.py:240` `Kernel.__init__`; `:390` `_tick_once_inner` (tick start `_start_perf_ts`); `:614` `_phase_resolution`; `:805` `_phase_cleanup` | elapsed time compared with `max_tick_budget_ms` every 10th result; on breach, results are dropped, `record_dropped_work` is called and `governor.force_mode(DEGRADED)` runs (`:613-628`) | control (PERF-D1 input 2) | Recorded (mid-tick cutoff, how many results applied) | yes: `should_throttle = not self._audit_mode and elapsed > hard_cap` (`:616`) |
| T3 | `kernel.py:143` `Kernel.__init__` (`time.time()` run id) | `_run_id` goes to artifact paths, manifests, recorders, alert envelopes (`:175,195-200,250,276-281,307-324,469,634,916,1001,1299-1303`) | artifact/event | Not recorded; no effect on authoritative state | the suffix draw `self._rng.get_int(Domain.INIT, 0, 0, 1000, 9999)` (`:142`) is stateless (`src/platform/rng.py:90-93`); passing `run_id` skips the clock read |
| T4 | `kernel.py:180`, `:1306` `Kernel.__init__`, `Kernel.shutdown` (`datetime.now`) | manifest `started_at` and `ended_at` | artifact/event | Not recorded; no effect on authoritative state | none needed |
| T5 | `kernel.py:269` (`QUALITY_PROFILE`) | scoring weights for `QualityHub` | sink not traced: the hub is constructed from the weights at `:270-284`; whether the hub can write to authoritative state was not traced | not in the PERF-D1 table | `QUALITY_SCORING_DISABLED=1` removes the hub (`feed.py:129`, `quality_hub.py:117`) |
| T6 | `kernel.py:1277` `Kernel.shutdown` (`psutil.Process().open_files()`) | `report.open_file_handles` in the shutdown report | metric/log | Not recorded; no effect on authoritative state | wrapped in `try`, sets `-1` on failure |
| T7 | `engine/observability.py:47,48,69,136` `SignalCollector` (`psutil.Process`, `memory_info`, `perf_counter`) | `rss_mb` sampled every `sampling_interval_ticks` ticks (`:66-75`) becomes `memory_estimate_mb` (`kernel.py:563`) and drives `governor.py:80` (SURVIVAL) and `:109` (CONSTRAINED); `uptime_seconds` (`:136`) goes to a snapshot | control (PERF-D1 input 1) for RSS; metric/log for uptime | Recorded (RuntimeMode transition) | yes: audit signals set `memory_estimate_mb=0.0` (`kernel.py:547`) |
| T8 | `engine/pipeline.py:95-472` `AuthoritativeApplyPipeline.refine` (54 `perf_counter_ns` stamps into `costs`, returned as `update.sub_phase_costs`, `:472`) | `kernel.py:690-691` merges them into `_phase_costs`, which feed `_final_compute_ms` (`:456`) and next tick's `phase_costs_ms` (`:567-568`) read by `phase_governor.py:109-135` | control (§4.3) | Recorded as emitted values (phase budgets row) | yes: audit signals use `phase_costs_ms={}` (`:551`) |
| T9 | `engine/worker_manager.py:193,196` `WorkerManager._wrap_work`; `:27,30` `_process_chunk_wrapper` | `compute_time_ns` on `WorkerResult` (`core/worker_protocol.py:103`), copied by `executor.py:384`; the result sort key is `(class_priority, -local_priority, entity_id)` (`kernel.py:608`) and does not use it; no other reader found | metric/log | Not recorded; no effect on authoritative state (worker completion order row) | none needed |
| T10 | `domains/cooperation/phase.py:54,240`; `domains/world_emergence/phase.py:35,128` | `metric_counters["cooperation_phase_ms"]` and `["world_emergence_ms"]` on the `StateUpdate`; `kernel.py:693` copies them to `_metrics`; `metric_counters` is not referenced by `apply.py` or `checkpoint.py` | metric/log; one caveat: `StateUpdate.is_noop` includes `sub_phase_costs` and `metric_counters` (`core/updates.py:1100`); no caller was found that tests it on an update carrying refine's costs (callers at `engine/world_dynamics.py:220-243` act on updates those helpers build) | Not recorded; no effect on authoritative state (caveat above) | none |
| T11 | `engine/replay_manager.py:61,164` (`time.time`), `:128,141,155` (`perf_counter`) | manifest `start_time`, `end_time`; the finalize timeout decides `status` and the `LifecycleOutcome` (`:140-157`) | artifact/event: replay artifact status and shutdown outcome | Not recorded; no effect on authoritative state | none needed |
| T12 | `observability/alerts/{deduplicator,sinks,models,manager}.py` | dedup window, webhook circuit breaker, alert id and timestamp, environment-configured routing | artifact/event (alert delivery) | Not recorded; no effect on authoritative state | none needed |
| T13 | `observability/{config,event_extractor,event_shapers,events,stream/adapters,stream/consumer}.py` | `ObservabilityConfig` mode and flag environment reads choose which recorders and shapers exist (`kernel.py:138-146,258-334,1014-1024`); event timestamps (`time.time`), event ids (`uuid.uuid4`, `events.py:56`), stream and DLQ timestamps | artifact/event; the mode switch is a control decision about non-authoritative recorders: no `AuthoritativeState` read was found to change with it in the kernel ranges above (not traced exhaustively) | not in the PERF-D1 table (observability mode) | `QUALITY_*`/`RPG_OBS_MODE` are environment inputs (§1) |
| T14 | `simulation_quality/{feed,quality_hub,quality_report}.py` | environment selects feed mode and whether scoring runs; report timestamp | sink not traced: `QualityHub` consumes the tick's events and state; whether it can write back was not traced | not in the PERF-D1 table | `QUALITY_SCORING_DISABLED=1` |
| T15 | `worldbuilding/{compiler,repository}.py` | `compile_duration_ms` in the compile report (`compiler.py:343,806-807`); index timestamps | artifact/event (world compile, before any tick) | Not recorded; no effect on authoritative state | none needed |
| T16 | `engine/kernel.py` (frame pacing, `:437-443`, part of group T1's stamps) | elapsed time chooses a sleep and `gc.collect(0)` | none: affects timing only | Not recorded; no effect on authoritative state (frame pacing and GC row) | `no_frame_pacing` flag (`kernel.py:241`) |
| T17 | environment reads in `src/observability/alerts/manager.py`, `src/observability/config.py` | per-variable configuration (see the Env var column in §2); every name has an `RPG_` and a `SIM_` form | control of observability and alert routing only | not in the PERF-D1 table | none |

PERF-D1 control-decision classification, as found. Rows 1 to 5 restate PERF-D1's table with the code
that implements them. Rows 6 to 8 are not in it.

| # | Decision | Wall-clock or host input | Code | PERF-D1 class |
|---|---|---|---|---|
| 1 | `RuntimeMode` transition | `tick_compute_ms` (`governor.py:78,97,105`), RSS (`:80,109`), worker and queue utilization (`:99,107`), replay backlog (`:101-102`) | `ResourceGovernor._get_indicated_mode` (`governor.py:70-112`) | Recorded |
| 2 | Mid-tick cutoff | elapsed wall-clock since tick start | `Kernel._phase_resolution` (`kernel.py:613-628`) | Recorded |
| 3 | End-of-tick dropped-work marker | `_final_compute_ms` against `min(max_tick_budget_ms, max(20, 2 x previous tick_compute_ms))`, after tick 5 | `Kernel._tick_once_inner` (`kernel.py:456-463`); `record_dropped_work(9999)` | Recorded |
| 4 | Phase budgets (scan policy, candidate, movement, strategic budgets, sweep interval, compaction level) | previous tick's `phase_costs_ms` (`locomotion`, `final_integrity`) and `tick_compute_ms` | `PhaseBudgetGovernor.evaluate` (`phase_governor.py:108-141`) | Recorded as emitted values |
| 5 | Scan policy, cadence, LOD, sweep interval derived from the recorded mode | none directly | `phase_governor.py:54-106` | Derived |
| 6 | `AuthoritativeState.pressure_signals` (`global_salience`, `compute_ratio`, `debt_ratio`) | previous tick's `tick_compute_ms` | `Kernel._phase_resolution` (`kernel.py:661-681`), `ApplyPath` (`apply.py:335,510`) | **not in the PERF-D1 table** |
| 7 | Shop buy price | `global_salience` from row 6 | `DynamicPriceService.calculate_buy_price` (`economy.py:20-48`), `ShopService.buy_item` (`town/shop.py:36-41`) | **not in the PERF-D1 table** |
| 8 | Observability mode and flags | environment variables | `ObservabilityConfig` (`config.py:209-222`) | **not in the PERF-D1 table** (affects non-authoritative recorders only, per the trace above) |

## 4. The fourth-input candidates

### 4.1 Wall-clock into `AuthoritativeState.pressure_signals`, read by the shop price

*Closed 2026-10-06 (`TCK-20261003-SALIENCE-WALL-CLOCK-PRICE-COUPLING`). The path below is kept as the finding; it was removed, not guarded.*

Path, each hop read in the code named:

1. `Kernel._tick_once_inner` stamps phase times (`kernel.py:389-435`), `_final_compute_ms` is set
   (`:456`, `:805`), and `_record_runtime_signals` stores it as `PressureSignals.tick_compute_ms`
   (`:807-812`).
2. Next tick, `Kernel._phase_init` assembles the signals and takes `signal_history[-1].tick_compute_ms`
   (`kernel.py:555`), clamps it on ticks 1 to 5 (`:556-557`), and stores it in `_current_signals`
   (`:558-570`). Under `audit_mode` it is `0.0` instead (`:541-553`).
3. `Kernel._phase_resolution` computes `compute_ratio = tick_compute_ms / max_tick_budget_ms` and
   `global_salience = min(2.0, debt_ratio + compute_ratio)` (`:661-667`) and puts all three in
   `pressure_signals_set` (`:669-678`).
4. `ApplyPath` replaces `AuthoritativeState.pressure_signals` with it (`apply.py:335`, `:510`).
5. `DynamicPriceService.calculate_buy_price(base_value, state)` reads
   `state.pressure_signals["global_salience"]` and returns `max(1, int(base_value * min(3.0, 1 + salience)))`
   (`economy.py:27-48`). Its docstring says "Same State + Same Pressure = Same Price"; the pressure is
   wall-clock derived.
6. `ShopService.buy_item` uses it for `total_cost`, the gold check and the price multiplier
   (`town/shop.py:36-41`); the function continues to build a purchase intent from line 48, which was not
   read. `buy_item` is called from the action-intent path (`engine/intent/action_intent.py:246`).

What was not established: whether `pressure_signals` itself is in the canonical hash (a search of
`src/engine/checkpoint.py` for `pressure_signals` and `current_mode` found no reference, so a hash
difference would appear through the gold and inventory a purchase changes, not through the field); how
often a shop purchase happens in a certification or calibration scenario; and whether a different
`global_salience` changes a purchase decision as well as its price (the gold check at `shop.py:41` does
depend on the price).

Other readers of `state.pressure_signals`: `pipeline.py:86-92` treats keys starting with `ENABLE_` as feature
flags (the kernel's dict has only the three keys above, so nothing starts with `ENABLE_` today), and
`economy.py:27`. No other reader was found by a text search of `src/`.

### 4.2 Replay backlog as a governor input

`governor.py:101-102` returns DEGRADED when `max_replay_buffer_kb > 0` and `replay_backlog_kb >=
max_replay_buffer_kb * 0.9`. `replay_backlog_kb` is `ReplayManager.get_stats()["backlog_kb"]`
(`replay_manager.py:352`) and enters the signals at `kernel.py:564`. The backlog is the unflushed buffer
size, so it depends on a background flush thread and the disk. `audit_mode` sets it to `0` (`:548`);
`flags["no_replay"]` makes `replay_allowed` false (`kernel.py:582-583`). The decision's classification is
unchanged (it is part of the recorded `RuntimeMode` transition); the point for PERF-D1 is that the proxy
set for the Canonical contract must include it.

### 4.3 `PhaseBudgetGovernor` reading per-phase wall-clock costs

`phase_governor.py:108-135` reads `signals.phase_costs_ms["locomotion"]` and `["final_integrity"]` and lowers
scan policy to `EXACT_DIRTY`, caps movement and strategic budgets, and widens the sweep interval, whatever
the current mode; `:139` sets `compaction_level` from `tick_compute_ms`. `governor.py:61-62` calls it on
every evaluation. Under `audit_mode` the costs are `{}` (`kernel.py:551`).

## 5. Reads outside the tick path (not reachable from the kernel's imports)

One line per module group, not traced individually. All 204 reads are in the G2 table of §2.

| Modules | Reads | Why they are outside the tick path |
|---|---|---|
| `src/api/` (`admission_control.py`, `engine_manager.py`, `agent_ops_dashboard/ingest.py`, `ws/stream.py`) | `time.time`, `datetime.now` | request timing, rate limits, and stream timestamps in the API process; the engine manager's four reads were not traced to its kernel calls |
| `src/certification/` (`hardware.py`, `harness.py`), `src/core/certification_reporter.py` | `psutil.cpu_count`, `psutil.virtual_memory`, `psutil.cpu_freq`, `time.*`, `uuid.uuid4`, `datetime.utcnow` | host classification and certification run ids and timings; they drive the kernel from outside; host class is a recorded input (row CC-09 of `docs/performance/performance_clause_inventory.md`) |
| `src/cli/entry.py` | `time.time` | command-line timing |
| `src/config/loader.py` | `os.environ` (profile overrides) | builds the `RuntimeProfile` before the kernel exists; see §1 |
| `src/domains/campaigns/runner.py` | `perf_counter_ns` x10 | campaign episode timing; campaigns drive the kernel from outside; `CampaignEvent.event_id` ordering (`behavior_change.py:24`) was not traced |
| `src/lab/**` | `datetime.now`, `time.time` | lab workflow timestamps |
| `src/logging/formatter.py` | `datetime.utcnow` | log line timestamps |
| `src/observability/**` outside the kernel's import closure (analytics, anomaly, behavior, mining, readiness, reporting, understanding, warehouse, `sweeper.py`, `watchdog.py`, `live/`, `performance/`) | `uuid.uuid4`, `datetime`, `time`, `psutil`, environment | offline or out-of-process analysis, retention, and warehouse writers that read artifacts after or beside the run |
| `src/perf/**` (`bench_harness.py`, `long_run_harness.py`, `profile_governance.py`) | `psutil`, `perf_counter`, `gc.get_*`, `time.time` | benchmark harnesses; they measure the kernel and do not feed it |
| `src/simulation_quality/{api/routes.py,worker.py}` | environment | the external scoring worker and its API |
| `src/testing/scenario_runner.py` | `perf_counter` | test runner timing |
| `src/worldassembly/resolver.py`, `src/worldgeneration/generator.py` | `datetime.now` | world assembly and generation metadata stamps; whether a stamp enters a generated world's content was not traced |

## 6. How the scan was checked, and what it cannot see

**Check against a text search.** A hand-written search over `src/` for the source names (`time.time`,
`perf_counter`, `monotonic`, `process_time`, `thread_time`, `datetime.now/utcnow/today`, `date.today`,
`getloadavg`, `cpu_count`, `sched_getaffinity`, `getrusage`, `get_traced_memory`, `gc.get_count/get_stats`,
`psutil.`, `os.environ`, `getenv`, `urandom`, `uuid.uuid1/uuid4`, `SystemRandom`, `random.seed`) matched
every recorded read, and found one match the scanner did not record:
`src/engine/observability.py:76`, `except (psutil.NoSuchProcess, psutil.AccessDenied)`, an exception class,
not a read. The search is described in the test plan so it can be repeated. `process_time`, `thread_time`,
`monotonic`, `sched_getaffinity`, `getrusage`, `tracemalloc.get_traced_memory`, `date.today` and `time.time_ns`
have no read in `src/`.

**What the scan cannot see:**
- **Reads through a name the scanner cannot resolve.** Ten calls are listed in §2 (G4); all are
  `get_stats` methods on kernel-owned objects, not clock sources.
- **Indirect reads.** A function that returns a clock value read elsewhere appears once, at the read. A
  value read from `PressureSignals` or `signal_history` is a consumer, found by hand (§3, §4), not by the
  scan.
- **Thread and process timing.** Worker completion order, replay-flush progress, and executor scheduling are
  host timing without a clock call. PERF-D1's table treats worker order as sorted away; replay backlog is
  §4.2. No other thread-timing dependence was searched for.
- **Iteration order.** `dict`/`set` order of strings under `PYTHONHASHSEED`, `id()`, and file-system listing
  order are not clock reads and were not searched.
- **Reads outside `src/`.** `tests/`, `tools/`, `scripts/` and `config/` YAML are out of scope.
- **Sinks past the last hand-off.** Groups T5 and T14 stop at the QualityHub boundary, and §4.1 stops at
  `shop.py:48`.
- **Import-graph reachability is an over-approximation** (it counts an import inside a function that may
  never run in a tick) and an under-approximation for dynamic imports (`importlib`, string-built module
  names); neither was searched for.
