---
status: active
layer: performance
authority: P2
audience: agent
tags: [performance, determinism, testing]
---

# Baseline Invalidation Ledger (PERF-M1-T05)

What the M1 correctness changes did to every committed performance number, tick or phase cost, dropped-work
count, state digest and certification result. Written on 2026-10-09 against `origin/main` `77fe33645`
(#455) by `TCK-20261009-PERF-M1-T05-BASELINE-INVALIDATION-LEDGER`. It classifies and plans; it
measures nothing, reruns nothing and edits no `src/` or test file. Measurements stay provisional until the
full lift of the RPG-core gate (`performance_optimization_roadmap.md`), and the reruns belong to M2.

## 1. Status vocabulary

| Status | Meaning | What happens to the file |
|---|---|---|
| **valid** | Its numbers are comparable with post-M1 numbers. No M1 change reaches the run that produced it. | Nothing. |
| **rerun** | Its numbers are not comparable with post-M1 numbers, and the artifact is still read by a test, a tool or a gate. | A new capture replaces it (section 5). |
| **incomparable** | Its numbers are not comparable with post-M1 numbers, and the artifact is not refreshed in place. | Kept as history, or replaced by a result recorded under the M2 identity schema (`benchmark_identity_schema.md`). |

Statuses are decided by **applicability**, not by date. Every artifact below was captured before every M1
change (captures run from 2026-05-15 to 2026-08-31, the changes from 2026-09-13 to 2026-10-09), so ordering
never excludes a change; whether the change reaches the artifact's run does. Where a file's own data
cannot settle that, the row says so and takes the conservative status.

## 2. The changes, with merge commits

| ID | Change | Merge commit (date) | Reaches an artifact when |
|---|---|---|---|
| T01 | Zero-capacity worker and queue signals follow PERF-D1; before it a profile with 0 workers read as saturated and the governor left `NORMAL` for `DEGRADED` | worker fix code `bc00caa1a` (2026-09-13); ticket #352 `0b3023d7a` (2026-10-05) | the profile has `max_worker_count == 0` (every `*_LOCAL` profile; `*_CONC` has 4) |
| T02 | Debt-harness correctness, then the harness's debt accounting removed with DEV-019 | #319 `cf7cbcb08` (2026-10-04) | the artifact is a debt-harness or certification result |
| T03a/b | Proof digest named `flat-sha256-v1`; kernel `TICK_END` payload typed | #319, #379 `33588b966` (2026-10-06) | the artifact records a state digest |
| DEV-014 | Tick-budget throttle is report-only; a non-audit run no longer drops results or forces `DEGRADED` mid-tick | #379 `33588b966` (2026-10-06) | a non-`audit_mode` run had a tick above `max_tick_budget_ms` |
| #380 | The scheduler's shedding path sheds nothing; `dropped_work` counts only scheduler-shed work | `ae4388854` (2026-10-06) | the artifact stores `dropped_work` |
| 2.75 | Shop buy price is the base value; no longer varies with host load | #387 `3e466e132` (2026-10-06) | a non-audit run buys items (economy-dependent outputs) |
| DEV-017 | A tick's reported cost no longer counts refine sub-phases twice | #448 `28d0af111` (2026-10-08) | the artifact has a `resolution_overhead` phase and a tick total |
| DEV-018 | Opt-in Canonical signal contract; `WORK_MODEL_V1` provisional | #448 `28d0af111` (2026-10-08) | nothing is invalidated: new opt-in, `LIVE` is unchanged (golden fixture) |
| DEV-019 | Work debt removed; proof digest `flat-sha256-v2`; certification result schema `v2` | #455 `77fe33645` (2026-10-09) | the artifact stores a `CanonicalStateHasher` digest or a certification result |
| DEV-021 | `BenchHarness` statistics cover every sampled tick; before, only the last 100 (`signal_history` is a 100-slot deque) and `compute_tps` was overstated by `sample_ticks / 100` | `PERF-M2-T04` (this ticket's PR) | the artifact was made with `sample_ticks` above 100: the three `simq_corpus_*` baselines (1000 ticks). Already `rerun` for T01 and DEV-017; this is a second reason, and their `compute_tps` / `avg_tps` are about 10x too high |

DEV-018 and #380 invalidate nothing committed: no committed baseline records `dropped_work` (the only tracked data file with the field is the Live golden
fixture, where `dropped_work_delta` is the constant 0 of a hand-built signal), and no committed run used the Canonical contract.

## 3. The ledger

Counts reconcile with the search in section 6: `tests/perf/baselines` 15 files, `docs/observability/baselines`
15 files, `perf_baselines.json`, `tests/regression/baseline_5k.json`, the SimQ fixtures, 21 compile reports, and
the generated and test-pinned files.

### 3.1 `tests/perf/baselines/` (tripwire references; `tests/perf/test_perf_regression_baseline.py`; `tools/perf/check_perf_regression.py` was retired by `PERF-M2-T03`)

| Artifact | Captured | Status | Deciding change and evidence |
|---|---|---|---|
| `resource_100_local` | 2026-05-15 | **re-recorded** | **T01.** Replaced by `resource_100_local.v0001.json` (`PERF-M2-T08` (2026-10-13, main 06aa3a20c, canonical variant, provisional, claims none; each record is the median of 3 fresh-process runs, NOISY when max/min of the averages exceeds 1.15): spread 7.3 %, all NORMAL, profile `PERF_1GB_LOCAL`, 10 + 20 ticks). The old file is deleted (history in git); the old number (35.5 ms) is not comparable with the new one (about 130 ms: the tick now has 30 phases). |
| `idle_100_local`, `movement_100_local`, `combat_10_local` (3) | 2026-05-15 | **re-recorded 2026-10-16: `combat_10_local` promoted (`v0001`); `idle_100_local` and `movement_100_local` owner-approved, promotion waits for testing agreement (#613)** (first attempt: PENDING-NOISY) | **T01.** Measured by `PERF-M2-T08` and **not promoted**: the spread stayed above 15 % in the first window (idle 35.3 %, movement 16.6 %, combat 43.3 %, load 2.2 to 2.7) and in the one quiet-window retry (idle 22.1 %, movement 28.8 %, combat 96.9 %, 1-min load 0.6 to 1.3 at each start). `combat_10_local` was bimodal across processes in the quiet window (about 30 ms, 60 ms, 30 ms). The old legacy files stay as references; the per-run data is in `investigation.md` of the T08 artifacts; a follow-up ticket starts from `rerun_baselines.py record --keep-samples`. `idle_100_local` and `movement_100_local` were measured on the declared tripwire protocol (10 + 50 ticks, projection `tripwire_paired`), the only one comparable with the nightly lane, not the old 10 + 20. **Re-recorded 2026-10-16 (`TCK-20261014-PERF-T08-NOISY-AND-OFF-NORMAL-BASELINES`; the owner's rule "(a) Middle-3 spread": 5 fresh-process runs, the median run, the 15 % spread over the middle 3; every run started with loadavg1 below 1.5, enforced by the tool):** `combat_10_local` (10 + 100 ticks, `PERF_2GB_LOCAL`): middle-3 spread 6.1 % (all five 16.4 %), averages 47.906 / 41.162 / 45.793 / 46.961 / 44.276 ms, **promoted as `combat_10_local.v0001.json`** (it is not comparable with the old 10 + 20 tick file, which stays as a legacy reference). `idle_100_local` (10 + 50, `PERF_512MB_LOCAL`): middle-3 spread 3.2 % (all five 21.2 %), 49.072 / 46.622 / 48.156 / 56.511 / 49.703 ms. `movement_100_local` (10 + 50, `PERF_1GB_LOCAL`): middle-3 spread 13.0 % (all five 17.1 %), 110.603 / 96.060 / 107.863 / 94.471 / 108.498 ms; **its averages form two clusters, about 95 ms (94.5, 96.1) and about 109 ms (107.9, 108.5, 110.6), the median in the upper one, so another five runs could move this baseline by about 12 %; read it as one of two plausible values, not a point.** `idle_100_local` and `movement_100_local`: owner decision 2026-10-16 "(a) Promote all four" (AskUserQuestion via lead-planner); **owner-approved (a); promotion waits for testing agreement, #613** (promoting them makes the nightly slow lane start comparing against them); the legacy files of those two stay until then; the legacy `combat_10_local.json` was deleted when `combat_10_local.v0001.json` was promoted (history in git). The host-regime cause stays inferred: the host-speed probe shows no consistent relation to the tick averages (investigation.md of the T08-NOISY artifacts). |
| `strategic_100_local` | 2026-05-15 | **rerun: not a baseline under canonical: leaves NORMAL (CONSTRAINED x20)** | **T01.** Measured by `PERF-M2-T08`: avg 495.8 ms (`cooperation` 260.0, `resolution_overhead` 101.3, `advancement` 83.9, `combat_engagement` 28.3), mode sequence CONSTRAINED for all 20 ticks in all 3 runs (spread 10.6 %). `baseline_lifecycle promote` refuses it (`mode_not_normal`; `performance_contract.md` 3.1). Not promoted; a larger-budget canonical profile is an owner decision and was not made. The old file (13.2 ms) stays as a legacy reference. |
| `mixed_200_local` | 2026-05-15 | **rerun: not a baseline under canonical: leaves NORMAL (CONSTRAINED x20)** | **T01.** Measured by `PERF-M2-T08` on main 4b5d1bdfb (spawn-collision fix included, #544; engine commit a002cc1dd, `PERF_1GB_LOCAL`, 10 + 20 ticks, 140 entities in the state the 200-entity request builds): avg 167.5 ms (`cooperation` 63.1, `combat_engagement` 42.9, `resolution_overhead` 27.5), CONSTRAINED for all 20 ticks in all 3 runs, spread 4.3 %. Not promoted (`performance_contract.md` 3.1); the old file (18.8 ms, measured with two objects on one tile) stays as a legacy reference. **The name follows the requested size:** `build_mixed_state(entity_count=200)` builds 80 heroes + 60 monsters = 140 entities plus 60 resource nodes, so the 140 above is the entity count, not a short build; the records are not renamed (the lifecycle tool has no rename and neither is promoted), and a test pins the count (`TCK-20261014-PERF-T08-NOISY-AND-OFF-NORMAL-BASELINES`). |
| `idle_100_concurrent`, `movement_100_concurrent`, `combat_10_concurrent`, `resource_100_concurrent` (4) | 2026-05-15 | **re-recorded** | T01 retained them (4 workers); `PERF-M2-T08` re-recorded them as `<name>.v0001.json` (`PERF-M2-T08` (2026-10-13, main 06aa3a20c, canonical variant, provisional, claims none; each record is the median of 3 fresh-process runs, NOISY when max/min of the averages exceeds 1.15)): idle 12.2 % (`PERF_1GB_CONC`), movement 12.1 % (`PERF_2GB_CONC`), combat_10 9.6 % and resource_100 12.5 % (both promoted from the quiet-window retry; their first attempt was NOISY at 137 % and 73.8 %). The old files are deleted (history in git). Caveat 2 below is resolved by the re-record. **`TCK-20261014-PERF-T08-NOISY-AND-OFF-NORMAL-BASELINES` (2026-10-15) checked the two retry-promoted records against their per-tick samples: neither is bimodal (the retry window's three runs form one cluster, 58.9 to 64.6 ms for combat_10 and 210 to 236 ms for resource_100; the first window ran at loadavg 5.2 to 5.7). They stay.** `resource_100_concurrent` rises 30 to 50 % across its 20 sampled ticks in all three retry runs (first fifth 173 to 202 ms, last fifth 256 to 278 ms), so its average **depends on the window length: any later comparison must use the same sampled-tick count (20)**. |
| `strategic_100_concurrent` | 2026-05-15 | **not a baseline under canonical: leaves NORMAL (SURVIVAL x20)** | Measured by `PERF-M2-T08`: avg 398.9 ms (`cooperation` 197.9, `resolution_overhead` 95.3, `advancement` 63.9), SURVIVAL for all 20 ticks in all 3 runs (spread 19.9 %). Not promoted; legacy file kept. |
| `mixed_200_concurrent` | 2026-05-15 | **not a baseline under canonical: leaves NORMAL (CONSTRAINED x20)** | Measured by `PERF-M2-T08` on main 4b5d1bdfb (`PERF_2GB_CONC`, 10 + 20 ticks): avg 182.3 ms (`cooperation` 61.3, `resolution_overhead` 44.4, `combat_engagement` 41.7), CONSTRAINED for all 20 ticks in all 3 runs, spread 13.8 %. Not promoted; the old file (28.2 ms) stays. |
| `simq_corpus_crowded_frontier` | 2026-08-07 | **re-recorded 2026-10-16: promoted (`simq_corpus_crowded_frontier.v0001.json`)** (first attempt: PENDING-NOISY) | **T01** and **DEV-017**. Measured by `PERF-M2-T08` on `PERF_512MB_LOCAL`, 100 + 1000 ticks, all NORMAL, peak RSS 797 MB: spread 35.8 % (first window) and 32.8 % (quiet-window retry, one run saw 1-min load 1.7); the tail ticks are real (max 226 to 867 ms against p50 41 to 80 ms). Not promoted at that time. **Re-recorded 2026-10-16 (`TCK-20261014-PERF-T08-NOISY-AND-OFF-NORMAL-BASELINES`, the 3-run rule, every run started with loadavg1 below 1.5):** averages 57.805 / 56.200 / 55.695 ms (loadavg1 0.97 / 1.27 / 1.32), spread 3.8 %, NORMAL for all 1000 ticks; an earlier attempt that day was discarded because one run started at loadavg1 1.56. **Promoted** as `simq_corpus_crowded_frontier.v0001.json` on the owner's decision 2026-10-16 "(a) Promote all four" (AskUserQuestion via lead-planner). The legacy `simq_corpus_crowded_frontier.json` stays beside it, and in `LEGACY_TRIPWIRE_REFERENCES`, only because `tests/tools/test_corpus_perf_baseline.py` and `tools/bench_corpus_world.py --commit` still use the raw-dict corpus convention; `load_baseline` prefers the promoted version; moving the corpus convention onto lifecycle records is `TCK-20261016-PERF-CORPUS-BASELINES-ON-LIFECYCLE-RECORDS`. |
| `simq_corpus_frontier_extended` | 2026-08-07 | **rerun: not a baseline under canonical: leaves NORMAL (NORMAL 40, CONSTRAINED 44, DEGRADED 14, SURVIVAL 902)** | Measured by `PERF-M2-T08`: avg 165.9 ms (`advancement` 69.9, `resolution_overhead` 35.7, `cooperation` 32.0), spread 7.8 %, peak RSS 1703 MB on a profile that declares 512 MB (nothing checks it). `promote` refuses it (`mode_not_normal`). The old file (13.3 ms) stays. Its numbers also carry the `compute_tps` 10x overstatement of DEV-021 in the old file. **Memory, rechecked (`TCK-20261015-PERF-BENCH-RSS-AFTER-COLLECT-AND-DECLARED-MEMORY-NOTE`, 2026-10-16, 1 process, `PERF_512MB_LOCAL` canonical, 100 + 1000 ticks, loadavg1 0.69, mode split NORMAL 40 / CONSTRAINED 44 / DEGRADED 14 / SURVIVAL 902):** old fields `rss_high_water` 1687.4 MB, `rss_delta` 1587.3 MB (T08 recorded 1703 MB peak); first harness version: `rss_before_window_mb` 100.1, `rss_after_collect_mb` 1701.8 (untrimmed, so it equals the high-water mark), `allocated_blocks_delta` +211,398. **The peak is the disabled collector's garbage, with its freed memory retained by the allocator, not engine memory:** in 200-tick runs on this world RSS grows +285 MB (canonical) / +292 MB (pinned) with the collector off and +9 / +11.5 MB with it on, and after the end collect it stays at 402 MB until `malloc_trim(0)` brings it to 125.6 MB (99.6 MB at the end of warm-up; `tick_cost_growth.md` section 5, corrected). **Three readings of the same 1000-tick run shape, side by side:** (1) the old fields, collector off: peak 1687.4 / 1702 MB (T08 1703 MB); (2) the record with the trim (`TCK-20261015-PERF-BENCH-RSS-AFTER-COLLECT-AND-DECLARED-MEMORY-NOTE`, 2026-10-16, loadavg1 0.91, 4175 MB available): **`rss_after_trim_mb` 311.0 MB** (`rss_before_window_mb` 98.5, trim delta +212.5), `rss_over_declared` 0.61 (of the profile's 512 MB; basis: trim), `peak_rss_over_declared` 3.30, `gc_collected_objects` 1,335,372 (about 1230 per tick: the disabled collector's garbage), `allocated_blocks_delta` +211,800; (3) a diagnostic script, **not the harness** (`rss_diagnose.py`, same kernel call shape, collector ON for the window, loadavg1 0.53, 4405 MB available): RSS 100.6 MB after warm-up, 131.9 MB at the end, **106.2 MB after collect and trim**, `allocated_blocks_delta` +211,691 (the same live growth as with the collector off). **AC1 (100-200 MB) is not met by the record (311 MB): its after-trim reading is an upper bound, because with the collector disabled the freed memory is fragmented and the trim cannot release all of it; the engine's own working set at 1100 ticks is about 106 MB with the collector on.** |
| `simq_corpus_frontier_marches` | 2026-08-07 | **rerun: not a baseline under canonical: leaves NORMAL (NORMAL 10, CONSTRAINED 876, NORMAL 114)** | Measured by `PERF-M2-T08`: avg 97.9 ms, spread 19.6 % (also NOISY), peak RSS 1568 MB. Not promoted; the old file (16.0 ms) stays. Its 1568 MB is the same effect as the sibling record's (disabled collector, freed memory retained; see `simq_corpus_frontier_extended`); not re-measured with the new fields. |

### 3.2 `docs/observability/baselines/`

Consumers: `latest.json` is read by `python3 -m src gate` and `python3 -m src compare-sweep --baseline`
(`docs/guides/simulation.md`, `docs/guides/observability.md`). The other files have no code consumer.

| Artifact | Captured | Status | Deciding change and evidence |
|---|---|---|---|
| `idle_100_local`, `movement_100_local`, `resource_100_local`, `combat_10_local`, `strategic_100_local`, `mixed_200_local`, `test_perf_idle_baseline` (7) | 2026-05-19 | **deleted** (`PERF-M2-T08`) | **T01** and **DEV-017** made them incomparable; they had no consumer (path-qualified search in the T08 investigation, section A), so they were deleted, not refreshed. History is in git. |
| `idle_100_concurrent`, `movement_100_concurrent`, `resource_100_concurrent`, `combat_10_concurrent`, `strategic_100_concurrent`, `mixed_200_concurrent` (6) | 2026-05-19 | **deleted** (`PERF-M2-T08`) | **DEV-017**; no consumer; deleted. |
| `matrix_full.json` (12 rows: 6 local, 6 concurrent) | 2026-05-19 | **deleted** (`PERF-M2-T08`) | Incomparable (T01 + DEV-017); the only reader of a `matrix_full.json` (`tools/perf/perf_report.py`) reads `reports/perf/matrix_full.json`, not this file. |
| `latest.json` | 2026-05-26 (the old perf matrix) and 2026-10-13 (the replacement) | **replaced** (`PERF-M2-T08`) | The old matrix (9 scenarios keyed by profile) could not be parsed by `src gate` / `compare-sweep` (validation error, exit 1) and its costs were incomparable (T01, DEV-017, DEV-014 for `IDLE_5000`). It is now a generated `BaselineConfig` (`baseline_v1`, `cost_accounting_version` `DEV-017`) from a real `idle` sweep (seeds 1 to 5, 50 ticks, sandbox, `LIGHT`). `python3 -m src compare-sweep` and `python3 -m src gate` of a second identical sweep both exit 0 on it with a tick-cost verdict (PASS; the drift table shows `tick_compute_ms_p95` 26.94 to 31.53, DEGRADED, +4.59, inside the threshold), and `tests/unit/perf/test_sweep_gate_baseline.py` pins that it parses and is comparable. It is a one-machine, one-day sample, carries no capacity claim, and `tests/integration/observability/test_baseline_comparison_flow.py` fails on this loaded VM (also on a clean `origin/main`) but passes in CI on main (run 38434570715); it does not read this file (see the T08 ticket). Follow-up `TCK-20261009-PERF-GATE-PASSES-VACUOUSLY-AGAINST-PRE-M1-BASELINE` is satisfied for this path. |

### 3.3 Root and regression baselines

| Artifact | Captured | Status | Deciding change and evidence |
|---|---|---|---|
| `perf_baselines.json` | n/a | **deleted** | `"entries": {}`; nothing was recorded. Deleted with the `PerfBudget` fixture by `PERF-M2-PERFBUDGET-RETIRE` (owner decision 2026-10-10); it was `valid` here before that (T01 disposition: retain). |
| `tests/regression/baseline_5k.json` (`alive_avg`, `gold_avg`, `quest_active_count`; `urban_political`, seed 42, 5000 ticks; also `elapsed_s`) | 2026-08-17 | **rerun** | **2.75 (#387)** and **DEV-014 (#379).** The run is not `audit_mode` (flags are `no_frame_pacing` only, `test_behavioral_5k.py`), so shop prices carried the host-load term and the budget cutoff could shed results. Both are small by the entries' own account (a few percent on a loaded host, 0 on a fast one; unmeasured), but `gold_avg` is price-dependent and the test is a regression tripwire, so the old values are not trusted as a reference. `elapsed_s` (103.7 s) is a host timing, never a comparison value. |
| `tests/simulation_quality/fixtures/grade_anchors.json` and `config/simulation_quality/grade_thresholds.yaml` (grade bands from calibration runs, committed 2026-08-31) | 2026-06-30 calibration, 2026-08-31 anchors | **valid** (unverified) | SimQ anchors count as performance baselines only if an M1 change moves what they measure. The one candidate is **2.75** (ECONOMY pillar, via buy prices); its entry records "SimQ economy calibration drift is **not measured**" and expects small movement, and anchors are coarse grade bands. Nothing else reaches them: T01, DEV-014, DEV-017 and DEV-019 change timings or digests that no anchor stores. Re-checked by `PERF-M2-T08` step 5 (2026-10-13, `python3 tools/evaluate_simq.py`, 2.5 GB cap, peak RSS 202 MB, 18 min 34 s, exit 1): **630 pillars checked, 130 regressions, 0 missing**, so the diff is **not empty**. The regressions appear in several pillars (INFORMATION, NARRATIVE, FACTION and ECONOMY among them), so it is not shown to be the 2.75 price change alone (T08 did not attribute them); an open ticket already covers anchors that were red on main (`TCK-20261001-SIMQ-GRADE-ANCHORS-RED-ON-MAIN-UNREPORTED`), and re-grading anchors is SimQ's decision: **nothing committed** here (no tracked file changed). Status: **rerun: needs SimQ's anchor decision**. |
| every `mixed_*` / `MIXED_*` record (`mixed_200_local`, `mixed_200_concurrent`, `MIXED_1000`, `MIXED_100`, the 200-entity `test_perf_stress` run) | any | **incomparable** from `TCK-20261004-PERF-SCENARIO-MIXED-STATE-SPAWN-COLLISION` | `build_mixed_state` placed monsters on hero and resource-node tiles (2 LAW-SPAWN-OCCUPANCY violations at 100 and 200 entities, 7 at 1000); a colliding monster now slides along y to the first free tile, so positions, occupancy and tick costs change. `PERF-M2-T08` measured the two `mixed_200_*` records after the fix (both leave NORMAL, see 3.1, not promoted); `MIXED_1000`, `MIXED_100` and the `test_perf_stress` run are not recorded by T08. `tools/release/verify_production_profiles.py` (`MIXED_100`) is unowned by the session registry: route to lead-planner. |

### 3.4 State digests

| Artifact | Status | Deciding change and evidence |
|---|---|---|
| `data/worlds/*/world_compile_report.json` (21), field `canonical_state_hash` | **incomparable** | **DEV-019.** Computed under `flat-sha256-v1` and last written 2026-10-09 before #455. A v1 digest is never compared with a v2 digest; no test compares them (`test_resolved_snapshot_freshness.py` checks counts only). They become v2 when a world is recompiled; that is a content step, not a perf rerun. |
| same files, field `state_hash` (MD5 `StateFingerprinter`) | **valid** | `src/replay/fingerprint.py` never read `work_debt` or `periodic_due_ticks` and #455 did not change it. |
| same files, field `compile_duration_ms` | **incomparable** by nature | A host timing, recorded for information, never compared. M1 did not change it. |
| `data/worlds/*/resolved/assembly_report.json`, `provenance_manifest.json` (120 files under `resolved/`) | **valid** | Content, catalog and module fingerprints, not state digests. |
| `tests/unit/engine/test_proof_digest_contract.py` (`FIXTURE_DIGEST_V2`; the v1 value kept as history) | **valid** | Regenerated in #455 and proven by `test_v2_is_v1_without_the_two_removed_keys`. |
| `tests/unit/kernel/golden/live_signals_v1.json` | **valid** | Regenerated in #455 (the `work_debt_total` keys removed); the Live decisions are unchanged. Its `dropped_work_delta` is a constant 0 in hand-built signals, not a measurement. |
| `docs/performance/hash_callsite_inventory.{md,json}` | **valid** | Regenerated in #455 (scheme string); `--check` passes. `phase_inventory.*`, `wall_clock_inventory.*` and `optimization_*` record structure, not measurements. |

### 3.5 Results recorded in documents

| Artifact | Status | Deciding change and evidence |
|---|---|---|
| `docs/performance/simq_isolation_overhead.md` (A/B engine CPU time and wall TPS by SimQ mode, 2026-08-21) | **valid** (caveat) | It reports process CPU time (`psutil cpu_times`) and wall TPS, not `tick_compute_ms`, so DEV-017 does not reach it, and it compares legs within one capture. It names no profile or governor mode, so if it ran on a 0-worker profile both legs shared the T01 mistrigger; the comparison survives, the absolute values do not carry over. |
| `docs/engine/matrices/extended_certification_test_matrix.md`, recovery rows (`CERTIFIED`) and the removed `WORK_DEBT_BUILDUP` row | **rerun** | **DEV-019** and **T02.** The recovery rows no longer inject a debt, and the certification result schema is `certification_result.v2`. Their `CERTIFIED` label was not re-earned in #455 and is not re-earned here; re-certify when certification is next run. No certification result file is committed, so there is nothing else to classify. |
| `docker/grafana/dashboards/simulation.json` | **valid** | Query definitions only; it holds no recorded value and does not reference `sim_work_debt_total` (removed in #455). |
| `docs/audits/unreachable_code_inventory.*` | out of scope | Matched the search on the word "digest" only; it records no performance data. |

## 4. Effect on what is read today

1. The `tests/perf` tripwire against the six `*_local` and three `simq_corpus_*` files compares a post-M1 run
   with numbers taken under the mistrigger and the double count. A pass or a failure there says nothing about a
   regression until those nine files are recaptured. The six `*_concurrent` files remain usable in principle
   (see 3.1 caveat 2).
2. The sweep gate (`src gate`, `compare-sweep`) against `latest.json` is blind to tick-cost regressions (3.2).
3. Behavioural regression (`baseline_5k.json`) may report a price-dependent difference that is the 2.75 change
   and not a regression; read `gold_avg` with that in mind until step 4 below.
4. Any digest quoted in a document or an old artifact without a scheme label is `flat-sha256-v1`.

## 5. Rerun plan (M2 runs it; nothing here is run)

**Contract.** Capture every timing baseline under **CANONICAL** (`signal_contract=canonical`,
`WORK_MODEL_V1`, provisional). Under it the governor reads a modelled cost, so a baseline's mode sequence
cannot depend on the capture host, and `mode_sequence` can be asserted all-`NORMAL` as `perf_baseline_policy.md`
2.2 step 3 requires. The measured `tick_compute_ms` stays in the file as telemetry. Record
`contract.determinism = canonical` in the identity (`benchmark_identity_schema.md`). Keep **LIVE**
captures only for claims that need the real runtime envelope (memory and replay-backlog guards exist only in LIVE),
labelled `live_bounded`; none of the reruns below needs one.

**Caveat.** `WORK_MODEL_V1` is PROVISIONAL and excludes `combat_engagement`, so Canonical reruns of combat-heavy scenarios
(`combat_10_*`, `simq_corpus_*` worlds that fight) should wait for `WORK_MODEL_V2` after the combat hostility-projection fix
(Lane B), or be labelled V1 in the result.

**Prerequisite.** No `PERF_*` profile sets `signal_contract` (`src/perf/profiles.py`), so selecting CANONICAL
for these runs needs a profile field or a canonical variant of each profile. That is an M2 `src/` change and is
not made here. Until it exists, a rerun is LIVE and must pass the all-`NORMAL` check to count.

| Step | Artifacts | Tool | Profile | Notes | Status (`PERF-M2-T08`, 2026-10-13) |
|---|---|---|---|---|---|
| 1 | the three `simq_corpus_*` files | `python3 tools/perf/rerun_baselines.py record simq_corpus_<name> --cause <TCK>`, then `baseline_lifecycle.py promote` | `PERF_512MB_LOCAL` as recorded, canonical | 1000 sampled ticks; first because the tripwire reads them. | **Done in part.** 3 measured: `crowded_frontier` promoted (`v0001`, 2026-10-16); `frontier_extended` and `frontier_marches` not a baseline under canonical (leave NORMAL). None promoted. |
| 2 | the six `tests/perf` `*_local` files | `python3 tools/perf/run_benchmarks.py --smoke`, copy the matching `*_local.json` | the profile named in each file's `profile` field, canonical | 10 warmup, 20 sample ticks as committed; then `pytest tests/perf/test_perf_regression_baseline.py -m slow` against the old file before replacing (policy 2.2 step 4). | **Done in part.** `resource_100_local` re-recorded; `combat_10_local` promoted (`v0001`, 2026-10-16); `idle_100_local`, `movement_100_local` owner-approved, promotion waits for testing agreement (#613); `strategic_100_local` not a baseline (CONSTRAINED); `mixed_200_local` measured after #544: not a baseline (CONSTRAINED). |
| 3 | the six `tests/perf` `*_concurrent` files | same tool | as recorded | Optional for M1; refresh with step 2 only so the pair stays consistent, and in M2 when the identity schema lands. | **Done in part.** `idle_100_concurrent`, `movement_100_concurrent`, `combat_10_concurrent`, `resource_100_concurrent` re-recorded; `strategic_100_concurrent` not a baseline (SURVIVAL); `mixed_200_concurrent` measured after #544: not a baseline (CONSTRAINED). |
| 4 | `tests/regression/baseline_5k.json` | `make regression-baseline` | `behavioral-regression-5k` | Record that the new values include the 2.75 price change; keep the old file's values in the commit message. | **Not T08:** owned by `TCK-20261007-BEHAVIORAL-5K-REBASELINE-AFTER-THE-STARVATION-CHAIN-LANDS`. |
| 5 | grade anchors | `python3 tools/evaluate_simq.py` (diff against anchors) | n/a | Check only; commit nothing if the diff is empty. | **Run, diff not empty:** 130 of 630 pillars REGRESS; nothing committed (see 3.3). |
| 6 | `docs/observability/baselines/*` | none | n/a | Not refreshed in place. The matrix and `latest.json` are replaced by results under the M2 identity schema (M2-T03/T04/T05); until then `src gate` must not be cited as a tick-cost check. Point `compare-sweep` at the replacement when it exists. | **Done** (deviation: a generated `BaselineConfig`, not benchmark records; see 3.2). `compare-sweep` and `gate` exit 0. |
| 7 | the 21 compile reports | the world compile step, on the next recompile | n/a | Becomes `flat-sha256-v2` by construction; not a perf rerun and not scheduled here. | Not scheduled here. |
| 8 | certification recovery rows | the certification harness, when next run | n/a | Re-earns `CERTIFIED` under `certification_result.v2`. | Not scheduled here. |

Order: 1, 2 (with 3), then 4, then 5, with 6 following the M2 identity schema. A step whose
`mode_sequence` is not all `NORMAL` is not a baseline (`performance_contract.md` 3.1) and is discarded.

## 6. How this was found (reproduce with these)

- Tracked data files: `git ls-files '*.json' '*.yaml' '*.yml' '*.jsonl' '*.csv'` less `agent-working`,
  `registries`, `docs/parity_ledger`, lock files (888 files).
- Candidates: `grep -lE 'canonical_state_hash|state_hash|tick_compute|phase_cost|dropped_work|work_debt|digest|p95_tick|tick_ms|ticks_per_second|certification_result'` over those files, grouped by directory.
- Digests: `git grep -lE '\b[0-9a-f]{64}\b' -- ':!*.py'` and a quoted-hex search in `tests/*.py`.
- Certification: `git ls-files | grep -iE 'certification.*\.(json|yaml)|cert.*result'` outside `src`, `tests`, `docs/plans` (none).
- Applicability data: the `profile`, `max_tick_compute_ms`, `timestamp` and `phase_breakdown` keys of every baseline
  against `PERF_PROFILES` (worker count, `max_tick_budget_ms`).

There is no machine-readable twin: no test or tool reads this ledger. `make knowledge-index-update` was not run in
the perf worktree (it is a local cache); run it from the main checkout after merge.

## 7. Related

`performance_m1_correctness_prerequisites_epic.md` (T05), `perf_baseline_policy.md`,
`docs/engine/performance_contract.md`, `benchmark_identity_schema.md`; DEV-014, DEV-017, DEV-018, DEV-019
and 2.75 in `docs/guidelines/intentional_divergences.md`; the T01 disposition table in
`TCK-20261005-PERF-M1-ZERO-CAPACITY-SIGNAL`.
