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

DEV-018 and #380 invalidate nothing committed: no committed baseline records `dropped_work` (the only tracked data file with the field is the Live golden
fixture, where `dropped_work_delta` is the constant 0 of a hand-built signal), and no committed run used the Canonical contract.

## 3. The ledger

Counts reconcile with the search in section 6: `tests/perf/baselines` 15 files, `docs/observability/baselines`
15 files, `perf_baselines.json`, `tests/regression/baseline_5k.json`, the SimQ fixtures, 21 compile reports, and
the generated and test-pinned files.

### 3.1 `tests/perf/baselines/` (tripwire references; `tests/perf/test_perf_regression_baseline.py`, `tools/perf/check_perf_regression.py`)

| Artifact | Captured | Status | Deciding change and evidence |
|---|---|---|---|
| `idle_100_local`, `movement_100_local`, `resource_100_local`, `combat_10_local`, `strategic_100_local`, `mixed_200_local` (6) | 2026-05-15 | **rerun** | **T01.** Profiles `PERF_512MB/1GB/2GB_LOCAL` have 0 workers, so these were measured under the zero-worker `DEGRADED` mistrigger (T01 disposition table). DEV-017 does not apply: no `resolution_overhead` key (older pipeline, `apply/combat/movement/resource/strategic` buckets). DEV-014 does not apply: max tick is at most 0.59x the budget. |
| `idle_100_concurrent`, `movement_100_concurrent`, `resource_100_concurrent`, `combat_10_concurrent`, `strategic_100_concurrent`, `mixed_200_concurrent` (6) | 2026-05-15 | **valid** (with caveats) | T01 retains them: 4 workers, queue 1000, neither half of the fix applies. DEV-017 does not apply (no `resolution_overhead`). Caveat 1: `resource_100_concurrent` has a max tick of 101.0 ms against a 100.0 ms budget (1.01x); no `mode_sequence` is stored, so a DEV-014 cutoff on that tick cannot be excluded, and the effect on a 20-tick average is at most one tick. Caveat 2: the 12 May files predate today's pipeline (their phase set differs from `phase_inventory.md`), so a tripwire against them already drifts for reasons that are not M1. That drift is out of this ledger's scope; the policy compares `avg_tick_compute_ms` only (`perf_baseline_policy.md` 2.1). |
| `simq_corpus_crowded_frontier`, `simq_corpus_frontier_extended`, `simq_corpus_frontier_marches` (3) | 2026-08-07 | **rerun** | **T01** (`PERF_512MB_LOCAL`, 0 workers) and **DEV-017** (`resolution_overhead` present, so `avg`, `p95`, `max` tick and the phase breakdown were inflated by the unlisted refine sub-phases; the double-count ticket's affected list). |

### 3.2 `docs/observability/baselines/`

Consumers: `latest.json` is read by `python3 -m src gate` and `python3 -m src compare-sweep --baseline`
(`docs/guides/simulation.md`, `docs/guides/observability.md`). The other files have no code consumer.

| Artifact | Captured | Status | Deciding change and evidence |
|---|---|---|---|
| `idle_100_local`, `movement_100_local`, `resource_100_local`, `combat_10_local`, `strategic_100_local`, `mixed_200_local`, `test_perf_idle_baseline` (7) | 2026-05-19 | **incomparable** | **T01** (0-worker profiles) and **DEV-017** (all have `resolution_overhead`; tick totals and phase totals read high). |
| `idle_100_concurrent`, `movement_100_concurrent`, `resource_100_concurrent`, `combat_10_concurrent`, `strategic_100_concurrent`, `mixed_200_concurrent` (6) | 2026-05-19 | **incomparable** | **DEV-017.** T01 retains them (4 workers), but the double count alone makes their totals incomparable. Max tick is at most 0.36x the budget, so DEV-014 does not apply. |
| `matrix_full.json` (12 rows: 6 local, 6 concurrent) | 2026-05-19 | **incomparable** | Same as the two rows above, row by row: local rows T01 + DEV-017, concurrent rows DEV-017. |
| `latest.json` (9 scenarios: IDLE_100/500/1000/5000, MOVEMENT_1000, RESOURCE_1000, COMBAT_100, STRATEGIC_500 on `*_LOCAL`; MIXED_1000 on `PERF_4GB_CONC`) | 2026-05-26 (file commit) | **incomparable** | **T01** for the eight local rows, **DEV-017** for all nine. **DEV-014** also bears on `IDLE_5000`: `PERF_4GB_LOCAL` has a 100 ms budget and the row records p95 117.4 ms and max 149.9 ms, so the mid-tick cutoff probably fired on that capture and shed results; no `mode_sequence` is stored to prove it. Operational effect: `src gate` and `compare-sweep` against this file compare today's lower, un-inflated tick costs with inflated ones, so a tick-cost regression check passes vacuously. Do not read a green result from that path as evidence until it is replaced. Follow-up: `TCK-20261009-PERF-GATE-PASSES-VACUOUSLY-AGAINST-PRE-M1-BASELINE`. |

### 3.3 Root and regression baselines

| Artifact | Captured | Status | Deciding change and evidence |
|---|---|---|---|
| `perf_baselines.json` | n/a | **valid** | `"entries": {}`; nothing recorded (T01 disposition: retain). |
| `tests/regression/baseline_5k.json` (`alive_avg`, `gold_avg`, `quest_active_count`; `urban_political`, seed 42, 5000 ticks; also `elapsed_s`) | 2026-08-17 | **rerun** | **2.75 (#387)** and **DEV-014 (#379).** The run is not `audit_mode` (flags are `no_frame_pacing` only, `test_behavioral_5k.py`), so shop prices carried the host-load term and the budget cutoff could shed results. Both are small by the entries' own account (a few percent on a loaded host, 0 on a fast one; unmeasured), but `gold_avg` is price-dependent and the test is a regression tripwire, so the old values are not trusted as a reference. `elapsed_s` (103.7 s) is a host timing, never a comparison value. |
| `tests/simulation_quality/fixtures/grade_anchors.json` and `config/simulation_quality/grade_thresholds.yaml` (grade bands from calibration runs, committed 2026-08-31) | 2026-06-30 calibration, 2026-08-31 anchors | **valid** (unverified) | SimQ anchors count as performance baselines only if an M1 change moves what they measure. The one candidate is **2.75** (ECONOMY pillar, via buy prices); its entry records "SimQ economy calibration drift is **not measured**" and expects small movement, and anchors are coarse grade bands. Nothing else reaches them: T01, DEV-014, DEV-017 and DEV-019 change timings or digests that no anchor stores. Re-check with `tools/evaluate_simq.py` in step 5 of the rerun plan; commit nothing unless the diff is non-empty. |

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

| Step | Artifacts | Tool | Profile | Notes |
|---|---|---|---|---|
| 1 | the three `simq_corpus_*` files | `python3 tools/bench_corpus_world.py --world <name> --commit` | `PERF_512MB_LOCAL` as recorded, canonical | 1000 sampled ticks; first because the tripwire reads them. |
| 2 | the six `tests/perf` `*_local` files | `python3 tools/perf/run_benchmarks.py --smoke`, copy the matching `*_local.json` | the profile named in each file's `profile` field, canonical | 10 warmup, 20 sample ticks as committed; then `pytest tests/perf/test_perf_regression_baseline.py -m slow` against the old file before replacing (policy 2.2 step 4). |
| 3 | the six `tests/perf` `*_concurrent` files | same tool | as recorded | Optional for M1; refresh with step 2 only so the pair stays consistent, and in M2 when the identity schema lands. |
| 4 | `tests/regression/baseline_5k.json` | `make regression-baseline` | `behavioral-regression-5k` | Record that the new values include the 2.75 price change; keep the old file's values in the commit message. |
| 5 | grade anchors | `python3 tools/evaluate_simq.py` (diff against anchors) | n/a | Check only; commit nothing if the diff is empty. |
| 6 | `docs/observability/baselines/*` | none | n/a | Not refreshed in place. The matrix and `latest.json` are replaced by results under the M2 identity schema (M2-T03/T04/T05); until then `src gate` must not be cited as a tick-cost check. Point `compare-sweep` at the replacement when it exists. |
| 7 | the 21 compile reports | the world compile step, on the next recompile | n/a | Becomes `flat-sha256-v2` by construction; not a perf rerun and not scheduled here. |
| 8 | certification recovery rows | the certification harness, when next run | n/a | Re-earns `CERTIFIED` under `certification_result.v2`. |

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
