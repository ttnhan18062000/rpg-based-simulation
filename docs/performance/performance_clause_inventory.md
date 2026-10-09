---
status: active
layer: performance
authority: P2
audience: agent
tags: [performance, documentation]
---

# Performance Clause Inventory

Evidence for PERF-D4 (`docs/architecture/performance_optimization_decisions.md`), from
`TCK-20261003-PERF-M2-CLAUSE-INVENTORY` (PERF-M2-T01). It was written on 2026-10-03 against the tree
at `ed5001057` (branch `perf-hash-policy-and-p1-doc-alignment`, one commit behind `origin/main`
`b90c3aa9a`. Of the files this inventory reads, only `.github/workflows/test.yml` and `Makefile` differ on
`origin/main` (the uv migration); every CI and Makefile line number below is against `ed5001057`). It measures nothing (no benchmark
was run), changes no gate, threshold, baseline or `hard` flag, and edits none of the documents it
compares. Findings are in §5; the next ticket (`TCK-20261003-PERF-M0-T09-P1-DOC-ALIGNMENT`) applies
the P1 edits and should be driven by §3, §4 and §6.

How to read it: §1 is the answer in short. §2 says how clauses were chosen and how completeness was
checked. §3 is the clause matrix, one table per source document. §4 is the reverse table (live checks
that enforce no documented clause). §5 lists every disagreement with lines on both sides. §6 maps each
clause to its PERF-D4 destination and flags what the PERF-D4 shape cannot express. §7 is the
`assert_perf_threshold` table. §8 lists what the inventory could not establish.

## 1. Summary

- **No performance threshold in the test tree can fail a build.** The call-site scan (§7) finds 55
  calls to `assert_perf_threshold` / `perf_check` and **none passes a literal `hard=True`**. Three
  calls pass `hard` through a variable (`tests/perf/conftest.py:64` and `:76`, and
  `tests/perf/test_perf_regression_baseline.py:40`); every caller of those wrappers leaves it at the
  default `False`, and `_RUNTIME_MODE_HARD_SCENARIOS` (`test_perf_regression_baseline.py:30`) is an
  empty `frozenset`. The "12 of 53 pass `hard=True`" figure recorded in
  `performance_optimization_decisions.md` (PERF-D4 evidence, C-13) and in the roadmap's live-state table
  does not reproduce on this tree: the count is 0 of 55 (§8 lists what the figure might have counted).
- **The only regression-style comparison that runs against committed baselines is soft and nightly.**
  `test_regression_vs_baseline` (`tests/perf/test_perf_regression_baseline.py:49-104`) is marked
  `slow`, so the PR job (`perf-cert-arena`, `-m "not slow and not extra_slow"`) deselects it; it runs in
  the `slow` job only on push to `main`, the nightly schedule, or manual dispatch. Its limit is
  `max(5.0, baseline_avg * 1.25)` on `avg_tick_compute_ms` only, and a breach is a warning.
- **`PerfRegressionGate` (`src/perf/regression_gate.py`) is exercised only against synthetic fixtures**
  (`tests/unit/perf/test_perf_regression_gate.py`). It has no production caller. `perf_baseline_policy.md`
  §3.1-3.3 describe its tolerances (5/10/15 % latency, 15 % RSS) as the CI gate; the code defaults are
  10 % latency and 15 % memory, and neither set of numbers is applied to a real run.
- **Three different regression tolerances exist and none matches the document.** The contract says
  `> 5 %` (`performance_contract.md:61`); the baseline policy says p50 5 %, p95 10 %, p99 15 %
  (`perf_baseline_policy.md:74-76`); `tools/perf/check_perf_regression.py:15-17` uses `max(1.15x, +3 ms)`
  and `+20 MB`; the live test uses `max(5 ms, 1.25x)`. `tools/perf/perf_ci.py` and
  `check_perf_regression.py` are referenced by no CI job, Makefile target or test.
- **Hardware classes are defined three ways.** The certification contract (`certification_contract.md:32-34`)
  and `HardwareClassifier.detect_class` (`src/certification/hardware.py:23-30`) agree (A: >=16 logical
  cores and >=32 GB; B: >=4 and >=8 GB; C: else). The baseline policy (`perf_baseline_policy.md:26-28`)
  says 8+ cores / 16 GB, 4 cores / 8 GB, 2 cores / 2 GB. Every `PERF_*` profile is hard-coded to
  `CLASS_A` (`src/perf/profiles.py:39`), so no perf test is bound to the detected class.
- **Calibration instructions point at things that do not exist.** `perf_baseline_policy.md:103-105` runs
  `tests.integration.optimization.test_perf_regression_gate --generate-baseline` and writes
  `data/baselines/`; neither the module nor the directory exists (committed baselines live in
  `tests/perf/baselines/`). `perf_baseline_policy.md:115` asks to "update the baseline revision timestamp
  in `docs/engine/performance_contract.md`"; that file has no such timestamp.
- **Twelve of the fifteen committed baselines are 20-tick samples.** `tests/perf/baselines/*.json`
  records `sample_ticks: 20` for every synthetic scenario; only the three `simq_corpus_*` files record 1000.
  Both contracts require at least 1000 ticks "for a baseline" (`performance_contract.md:49`,
  `perf_baseline_policy.md:22`).
- **One cited test is missing.** `optimization_invariants.md:123` cites
  `tests/integration/optimization/test_degraded_mode_correctness.py`; the file does not exist.
- **Counts in the architecture documents have drifted from code.** `optimization_architecture.md:126`
  states 17 "authoritative pipeline phases". The generated `docs/performance/phase_inventory.md` shows
  44 refinement phases (`run_phase()` calls in `refine`), `PhaseDependencyGraph.PHASES` has 31 entries,
  and `authoritative_pipeline.md` names 39. These are three different units and are not compared with
  each other here. The "7 urgency tiers" and domain names also do not match the names in code (§3.5).
- **Clause totals:** see §3 for the per-document tables; §6 summarizes the PERF-D4 destinations. Clauses
  PERF-D4's two-projection shape cannot express are in §6.2.

## 2. Method and completeness check

Documents read in full, with line numbers: `docs/engine/performance_contract.md` (208 lines),
`docs/engine/contracts/certification_contract.md` (51), `docs/performance/perf_baseline_policy.md`
(146), `docs/performance/optimization_architecture.md` (135), `docs/performance/optimization_invariants.md`
(123), `docs/engine/runtime_profiles.md` (49), `docs/engine/contracts/resource_governor_contract.md` (43).
`runtime_profiles.md` and the governor contract are included only for clauses that set a performance
budget or threshold (ticket scope).

What counts as a clause: a requirement, threshold, sample size, percentile, hardware class, outcome
rule or claim. Each gets one row. When a clause is ambiguous between two kinds, the row picks one and
says why.

Completeness check (how to repeat it): for each document, every number with a unit (`ms`, `%`, `GB`,
`MB`, ticks, cores) and every "must" / "must not" / "MUST" / "shall" / "required" / "forbidden" /
"prohibited" is either a row in §3 or named below as non-normative.

Non-normative text, not given rows: `performance_contract.md` §8 (derived entity indexes: lifecycle
prose, ticket history and known limitations; it states behavior of `WorldIndexService` and
`SemanticEntityIndexService` rather than a measured claim, so it is outside PERF-D4's measurement
scope; one determinism clause in it is row PC-17); the SimQ coverage list at
`perf_baseline_policy.md:141-146` (history of what was baselined, not a requirement; the clause in
§5 that it implies is row BP-17); ASCII layer diagrams at `optimization_architecture.md:14-39` and
`optimization_invariants.md:149-174`; rationale paragraphs in `optimization_invariants.md` (lines 62 and 111 carry "must" inside a rationale, restating the rules in OI-03 and OI-07); `perf_baseline_policy.md:31-32` (why warmup exists) and `:133` (a suggested follow-up); the
Purpose and Non-Goals sections of the other documents except where a Non-Goal is itself a claim
(rows CC-13, RP-09).

Code and CI consulted: `src/perf/regression_gate.py`, `src/perf/bench_harness.py`,
`src/perf/long_run_harness.py`, `src/perf/profiles.py`, `src/certification/{hardware,models,conformance,harness}.py`,
`src/engine/{kernel,phase_graph,phase_governor,patches,candidate_selector}.py`, `src/core/dirty.py`,
`tests/tools/perf_assertions.py`, `tests/perf/` (including `conftest.py`), `tests/unit/perf/`,
`tests/certification/`, `tools/perf/{check_perf_regression,perf_ci,run_benchmarks}.py`,
`tools/perf_guard.py` (existence only), `Makefile`, `.github/workflows/test.yml`, `pyproject.toml`
markers.

Column key for §3. **Code**: the code that enforces the clause, `file:line`, or `none`. **Tests**:
tests that exercise it, found by searching `tests/` for the clause's identifiers, or `none found`
(a search miss, not a proof of absence). **CI**: the job and selector that run those tests (see the CI
legend below). **H/S**: `hard` fails the build when breached; `soft` only warns
(`PerformanceThresholdWarning`); `n/a` means the clause has no pass/fail check. **Status**:
`enforced as written`, `enforced differently` (how), `not enforced`, `contradicted` (by which clause),
or `target` / `obsolete` for C-15 classification of architecture statements. **D4**: PERF-D4
destination code, defined in §6.

CI legend (all lines in `.github/workflows/test.yml`):
- **PR-perf**: job `perf-cert-arena` (`:774`, run step `:786-791`), `pytest tests/perf tests/certification
  tests/arena tests/mechanic_scenarios -m "not slow and not extra_slow"`; gated by the changed-files job
  (path regex at `:753`, `if:` at `:778`).
- **PR-unit-perf**: step "Run: tests/unit/perf" (`:205-209`), `-m "not slow and not extra_slow"`.
- **Slow**: job `slow` (`:908`), `pytest tests/ -m "slow or extra_slow"` (`:940`), `if:` push to
  `main` / schedule / dispatch only (`:916`).
- **None**: no job selects it.

## 3. Clause matrix

### 3.1 `docs/engine/performance_contract.md` (authority P1)

| ID | Line | Clause (short quote) | Kind | Code | Tests | CI | H/S | Status | D4 |
|---|---|---|---|---|---|---|---|---|---|
| PC-01 | 11 | "performance claims are honest, scoped, and reproducible" | claim rule | none | none found | none | n/a | not enforced (statement of purpose) | STAY |
| PC-02 | 16-17 | tick cost = wall-clock inside `Kernel.tick_once()`, from `time.perf_counter_ns()` "with microsecond resolution" | definition | `src/engine/kernel.py:389-435` (`perf_counter_ns` stamps t0..t6) | `tests/perf/test_bench_harness.py`, `tests/perf/test_profiler_integrity.py` | PR-perf, Slow | n/a | enforced as written (resolution is nanosecond; "microsecond" is a floor) | STAY |
| PC-03 | 18 | tick cost "reported per-tick in `PressureSignals`" | requirement | `src/perf/bench_harness.py:109-110` reads `tick_compute_ms` from `kernel.status` history | `tests/perf/test_bench_harness.py` | PR-perf | n/a | enforced as written (not re-read in detail) | STAY |
| PC-04 | 22 | TPS = `1000 / avg_tick_compute_ms` | formula | `src/perf/bench_harness.py:114` computes `(sample_ticks * 1000) / total_compute_ms`, i.e. `1000 / mean`, so equal | `tests/perf/test_profiler_integrity.py:115` (`compute_tps >= wall_clock_tps`) | PR-perf | n/a | enforced as written; the contract's "sustainable TPS" wording is also served by `wall_clock_tps`, which the gate ignores (`regression_gate.py:231` comment) | CAPRUN |
| PC-05 | 25-31 | engine "must report the cost of each authoritative phase separately": six phases `INIT, SCHEDULING, COLLECTION, RESOLUTION, CLEANUP, ADVANCEMENT` | requirement | `src/perf/bench_harness.py:115-134` aggregates `phase_costs_ms`; `src/engine/kernel.py:389-435` stamps phases | `tests/perf/test_bench_harness.py` | PR-perf | n/a | enforced differently: the contract names six phases; `idle_100_local.json` carries 12 `phase_breakdown` keys (`init, scheduling, collection, apply, resource, combat, movement, strategic, resolution, cleanup, advancement, persistence`), and the kernel also emits sub-phase keys such as `resolution_overhead` (`kernel.py:428`) | STAY |
| PC-06 | 36-45 | claims valid "ONLY" with runtime profile, hardware class, scenario, execution mode, RuntimeMode | claim rule | baselines record `profile`, `matrix_scenario`, `matrix_mode`; `bench_harness.py` returns `mode_sequence` | `tests/perf/test_perf_regression_baseline.py:122-125` (checks only that the contract text contains "RuntimeMode") | PR-perf (the text-pin test is unmarked) | hard (plain `assert`) | enforced differently: the test pins the document text, not any claim; no code rejects an unscoped claim | STAY (becomes the tripwire/capacity-run identity) |
| PC-07 | 44-45 | a claim measured while the Governor left NORMAL "is not a valid baseline claim without stating so" | claim rule | `tests/perf/test_perf_regression_baseline.py:36-46` (`_assert_runtime_mode_stayed_normal`) | `test_perf_regression_baseline.py:107-119` (synthetic) | PR-perf (synthetic test); the real check is Slow | soft (`hard=False` unless scenario in `_RUNTIME_MODE_HARD_SCENARIOS`, which is empty) | enforced differently: warns only, and only for 6 scenarios, nightly | TRIP |
| PC-08 | 48 | warmup "minimum of 100 warmup ticks" | threshold | default `warmup_ticks=100` (`src/perf/bench_harness.py:44`) | `tests/perf/test_perf_stress.py` passes 100 | Slow | n/a | enforced differently: it is a default, not a minimum; `test_regression_vs_baseline` runs `warmup_ticks=10` (`test_perf_regression_baseline.py:79`); `tools/perf/run_benchmarks.py:49` uses 10 (smoke) or 50 | CAPRUN (capacity run uses it); TRIP uses a smaller documented value |
| PC-09 | 49 | "minimum of 1000 ticks must be sampled for a baseline" | threshold | default `sample_ticks=1000` (`bench_harness.py:45`) | `tests/perf/test_perf_stress.py` | Slow | n/a | contradicted by the committed data: 12 of 15 files in `tests/perf/baselines/` record `sample_ticks: 20`; only the 3 `simq_corpus_*` baselines record 1000. The smoke path samples 20 or 200 (`run_benchmarks.py:50`) and the regression test samples 50 (`test_perf_regression_baseline.py:80`) | CAPRUN |
| PC-10 | 50 | "run on isolated cores if possible" | requirement (soft wording) | none | none found | none | n/a | not enforced (the CI runner is `ubuntu-latest`) | CAPRUN |
| PC-11 | 55 | optimization "MUST NOT change the semantic outcome"; a hash mismatch vs baseline is a failure | requirement | `src/certification/conformance.py:71-78` (`FAILED_SEMANTIC_DRIFT`) | `tests/certification/test_phase10_enhanced_determinism_parity.py`, `tests/certification/test_harness_contract.py` | PR-perf | hard | enforced as written (this is the parity gate; certification `baseline_hash`) | STAY (outside both projections: a correctness law) |
| PC-12 | 58 | instrumentation overhead "< 1% of total tick time" | threshold | none (the checking test asserts `< 0.6`ms-style absolute limit, see §7 row `test_hard_law_monitor_overhead.py:75`) | `tests/perf/test_hard_law_monitor_overhead.py:16,60-67` (its own comment: the doc says 1 %, the test cannot meet it) | Slow | soft | contradicted by the test's own comment (`test_hard_law_monitor_overhead.py:60-67`); not enforced at 1 % | FLAG (overhead of one subsystem as a fraction of tick; no projection owns it) |
| PC-13 | 61 | "increases `avg_tick_compute_ms` by > 5% on a stable scenario must be flagged" | threshold | none implements 5 %: `test_perf_regression_baseline.py:94` uses `max(5.0, 1.25x)`; `tools/perf/check_perf_regression.py:15` uses 1.15x | `tests/perf/test_perf_regression_baseline.py:49-104` | Slow | soft | contradicted by BP-09 to BP-11 (5/10/15 %), and enforced differently by 25 %/5 ms (live test) and 15 %/3 ms (unwired tool) | TRIP (one number to be chosen by Gate A; this inventory does not choose it) |
| PC-14 | 62 | significant regressions require a "Divergence Reason" in the performance log | requirement | none; no "performance log" artifact is defined | none found | none | n/a | not enforced | DEL (or fold into tripwire outcome wording) |
| PC-15 | 65-68 | memory/pooling rules: differential caching O(Dirty); singletons for no-op updates; deep-freeze caching; incremental `gc.collect(0)` in frame-pacing idle windows | target architecture mixed with behavior | `gc.collect(0)`: `src/engine/kernel.py:437-443` (only when `sleep_ms > 5.0` and frame pacing on); `EMPTY_ENTITY_UPDATE`: not tested by name | `tests/perf/test_perf_passive_scaling.py`, `tests/unit/domains/optimization/test_cache_registry.py` (gc references only) | Slow (passive scaling) | soft | `gc.collect(0)` enforced as written; the other three bullets have no check (`not enforced`); the harness disables frame pacing by default (`tests/perf/test_profiler_integrity.py:68`), so the `gc.collect(0)` path (which needs frame pacing, `kernel.py:439`) is not exercised by benchmarks | STAY as design rules, not measurement clauses (outside D4's two projections) |
| PC-16 | 70-81 | `PhaseBudgetGovernor` emits `PhaseBudgets`; six parameters (`candidate_budget`, `movement_budget`, `strategic_budget`, `scan_policy`, `background_sweep_interval`, `compaction_level`) | requirement | `src/engine/phase_governor.py:29-31` (fields), `:70,77,117` (`ScanPolicy.EXACT_DIRTY`), trigger at `:139` | `tests/unit/domains/optimization/test_phase_budget_governor.py` | a unit job (`tests/unit/domains`), not the perf jobs | hard | enforced as written for existence and shape (parameter semantics not re-verified) | STAY |
| PC-17 | 104-140 (§8.2) | semantic index "excluded from `CanonicalStateHasher` by omission" | determinism claim | `to_canonical_data()` allow-list | `tests/unit/domains/optimization/test_semantic_entity_index.py::test_semantic_index_excluded_from_canonical_state_hash` | a unit job (not the perf jobs) | hard | enforced as written (per the document's own citation; not re-run) | STAY (outside D4) |

### 3.2 `docs/engine/contracts/certification_contract.md` (authority P1)

| ID | Line | Clause | Kind | Code | Tests | CI | H/S | Status | D4 |
|---|---|---|---|---|---|---|---|---|---|
| CC-01 | 14 | a certification run produces "exactly one `certification_run.json`" | requirement | `src/certification/recorder.py`, `src/certification/models.py:250-258` (not read in detail) | `tests/certification/test_harness_contract.py` | PR-perf | hard | enforced as written (assumed from test name; not re-read) | CERT |
| CC-02 | 15-19 | a run must bind `runtime_profile`, `scenario_id`, `detected_hardware_class`, `effective_hardware_class` | requirement | `src/certification/models.py:250-251` | `tests/certification/test_evidence_levels.py` | PR-perf | hard | enforced as written | CERT |
| CC-03 | 20 | all certification runs "must be seeded" | requirement | `src/certification/harness.py` (seed passed through) | `tests/certification/` | PR-perf | hard | enforced as written (not re-read) | CERT |
| CC-04 | 24 | `FAILED_ENVELOPE`: exceeded RAM/CPU/queue ceilings | outcome rule | `src/certification/conformance.py:57,63`; enum `models.py:39` | `tests/certification/test_envelope_violations.py`, `test_allowed_failure_truth.py` | PR-perf | hard | enforced as written | CERT |
| CC-05 | 25 | `FAILED_DEGRADATION_ORDER` | outcome rule | enum is `FAILED_DEGRADATION_SEQUENCE` (`models.py:40`) | `tests/certification/test_envelope_violations.py` (matches "FAILED_DEGRADATION") | PR-perf | hard | enforced differently: name differs | CERT (rename in doc) |
| CC-06 | 26 | `FAILED_RECOVERY`: engine must return to NORMAL "within the declared timeout" | outcome rule | enum is `FAILED_RECOVERY_TIMEOUT` (`models.py:41`), raised at `conformance.py:105,124,128` | `tests/certification/test_resilience_recovery.py`, `test_allowed_failure_truth.py` | PR-perf | hard | enforced differently: name differs | CERT (rename in doc) |
| CC-07 | 27 | `FAILED_SEMANTIC_DRIFT`: final hash differs from deterministic baseline | outcome rule | `conformance.py:71-78` | `tests/certification/test_phase10_enhanced_determinism_parity.py` (token `FAILED_SEMANTIC_DRIFT` itself is not in any test) | PR-perf | hard | enforced as written | CERT |
| CC-08 | 28 | `FAILED_REPORTING_INCOMPLETE`: measurements missing or corrupt | outcome rule | `conformance.py:37` | none found for the token | PR-perf | hard | enforced as written, untested by name | CERT |
| CC-09 | 31-34 | classes: A >= 16 logical cores and >= 32 GB; B >= 4 and >= 8 GB; C otherwise; "binary and deterministic" | definition | `src/certification/hardware.py:23-30` | `tests/certification/test_evidence_levels.py` | PR-perf | hard | enforced as written | CERT (the single hardware-class definition) |
| CC-10 | 35 | override "MUST be recorded with `hardware_class_override_applied: true`" | requirement | field is `override_applied` (`models.py:118,252`; `harness.py:45,216`); no field of the documented name exists | none found for either name | PR-perf | n/a | enforced differently: recorded, under a different key | CERT |
| CC-11 | 38-39 | sampling cadence per scenario; `MeasurementPoint` carries tick, mode, RSS, queue utilization, compute time | requirement | `src/certification/models.py` (not read in detail) | `tests/certification/` | PR-perf | n/a | enforced as written (assumed; not re-read) | CERT |
| CC-12 | 40 | every run includes or references a `baseline_hash` from "a sequential (1-worker) reference run" | requirement | `src/certification/harness.py:88,294` (`_get_baseline_hash`) | `test_evidence_levels.py`, `test_manifest_snapshot.py`, `test_harness_contract.py` | PR-perf | hard | enforced as written (1-worker detail not re-read) | CERT |
| CC-13 | 43-44 | performance claims forbidden unless bound to `(Profile, Scenario, Hardware Class)`; forced vs detected classes must be labeled | claim rule | partial: `models.py:250-251` records both classes | `tests/certification/test_evidence_levels.py` | PR-perf | hard | enforced differently: the report labels, nothing blocks an unbound claim in prose | CERT |
| CC-14 | 45 | JSON is the source of truth; Markdown is derivative | requirement | `src/certification/recorder.py:172-174` writes Markdown from the result | none found | PR-perf | n/a | enforced as written | CERT |

### 3.3 `docs/performance/perf_baseline_policy.md` (authority P1)

| ID | Line | Clause | Kind | Code | Tests | CI | H/S | Status | D4 |
|---|---|---|---|---|---|---|---|---|---|
| BP-01 | 12, 18 | "All commits must pass these automated performance gates" | claim | none: no performance threshold can fail a build (§1, §7) | none | none | soft everywhere | contradicted by `tests/tools/perf_assertions.py:1-27` (stopgap: threshold misses are warnings) | DEL (replaced by tripwire outcome rules) |
| BP-02 | 21 | warmup >= 100 ticks | threshold | same as PC-08 | same as PC-08 | Slow | n/a | enforced differently (as PC-08); duplicates `performance_contract.md:48` | CAPRUN |
| BP-03 | 22 | sampling window >= 1,000 continuous ticks | threshold | same as PC-09 | same as PC-09 | Slow | n/a | enforced differently; duplicates `performance_contract.md:49` | CAPRUN |
| BP-04 | 26 | `CLASS_A`: "8+ Dedicated Cores, 16GB+ RAM. Target: 10,000+ entities at < 50ms per tick" | hardware class + capacity target | classes: `hardware.py:23` says 16 cores / 32 GB; the entity target has no check (`tests/perf/test_perf_metropolis.py:56-60` asserts `< 500` ms at its own scale, soft) | none for the target | Slow | soft | contradicted by CC-09 (cores and RAM); target `not enforced` | HW for the class; CAP for the target |
| BP-05 | 27 | `CLASS_B`: "4 Dedicated Cores, 8GB RAM. Target: 2,500 entities at < 40ms per tick" | hardware class + capacity target | `hardware.py:25` says >= 4 and >= 8 GB (agrees on numbers; the policy reads core count only, per its own note at `:30-35`) | none | none | n/a | target `not enforced`; class text consistent with CC-09 except the AND-rule | HW; CAP |
| BP-06 | 28 | `CLASS_C`: "2 Cores, 2GB RAM. Target: 500 entities at < 30ms per tick" | hardware class + capacity target | `hardware.py:27` (else) | none | none | n/a | contradicted by CC-09 (C is "all other systems", not 2 cores / 2 GB); target `not enforced` | HW; CAP |
| BP-07 | 30-35 | known conflict between this table and the certification contract | disagreement note | n/a | n/a | n/a | n/a | the note is accurate; this inventory confirms it and adds the 8/16 vs 16/32 difference for `CLASS_A` | DEL (resolved by D4: certification §3 is the definition) |
| BP-08 | 38-40 | named result: SimQ isolation overhead in `docs/performance/simq_isolation_overhead.md` | claim | `tests/perf/test_simq_isolation_overhead.py:367,392,441,487` | same file | Slow | soft | enforced differently (soft, nightly; four band constants) | FLAG (an overhead-ratio check with its own `INPROCESS_CPU_OVERHEAD_BAND_PCT`-style bands; no projection owns it) |
| BP-09 | 74 | p50 latency "must not exceed baseline by more than 5.0%" | threshold | none: `PerfRegressionGate` has no p50 check (`regression_gate.py:117` starts at p95) | none | none | n/a | not enforced; contradicted by PC-13 (5 % on average, not p50) and BP-10 | TRIP |
| BP-10 | 75 | p95 latency "more than 10.0%" | threshold | `src/perf/regression_gate.py:117-122` (`tolerance_percent=10.0`, default `:81`) | `tests/unit/perf/test_perf_regression_gate.py` (synthetic fixtures only) | PR-unit-perf (via `tests/unit/perf`) | hard (returns `passed=False`) but never applied to a real run | enforced differently: the gate exists and its unit tests run, but nothing calls it on a measurement | TRIP |
| BP-11 | 76 | p99 latency "more than 15.0%" | threshold | `regression_gate.py:124-129` uses the same 10 % tolerance as p95, not 15 % | same | PR-unit-perf | hard in unit tests; never applied | contradicted by the code (10 % for p99); not applied to a real run | TRIP |
| BP-12 | 79 | RSS delta between tick 100 and tick 1,000 must not exceed 15 % of start | threshold | `regression_gate.py:142-147` compares `peak_rss_mb` (15 % default `:82`) and `memory_delta_mb` (flat 5 MB or 15 %, `:150`); no tick-100/1,000 window | `tests/unit/perf/test_perf_regression_gate.py` | PR-unit-perf | hard in unit tests; never applied | enforced differently (peak and delta, not a tick-100-to-1,000 window); nearest live check: `tests/perf/test_perf_passive_scaling.py:47,70` soft | CAPRUN |
| BP-13 | 80 | GC sweep count "must remain stable"; singletons prevent gen-1/2 fragmentation | requirement | `src/perf/long_run_harness.py:267` (`gc_stable`: gen-2 delta `<= max(10, ticks//10)`, gen-1 `<= max(100, ticks)`) | `tests/certification/test_cert_long_run_stability.py:71` | Slow (`extra_slow`) | soft | enforced differently: different mechanism and numbers, nightly, soft | CAPRUN |
| BP-14 | 83 | a commit over the latency/memory thresholds "fails the CI build instantly with an `UnacceptableRegressionError`" | outcome rule | no `UnacceptableRegressionError` exists in `src/` or `tests/` (the gate returns `PerfGateResult.passed=False`; `MissingBaselineError` at `regression_gate.py:6`) | none | none | soft everywhere | contradicted by the code and by BP-01's own correction (`:46-57`) | DEL |
| BP-15 | 84 | an intentional baseline increase needs a "Divergence Rationale" and re-calibration | requirement | none | none found | none | n/a | not enforced | TRIP (as an outcome-wording clause) |
| BP-16 | 90, 94-115 | baselines "must be re-calibrated" on complexity or hardware change; calibration procedure: pin cores, `PYTHONHASHSEED=42`, `SIMULATION_SCALE=1000`; run `--generate-baseline` for 5,000 ticks into `data/baselines/`; verify with `tests/unit/perf/test_perf_regression_gate.py`; commit; update a "baseline revision timestamp" | procedure | `tests.integration.optimization.test_perf_regression_gate` does not exist; `data/baselines/` does not exist; the contract has no timestamp; real baselines are `tests/perf/baselines/*.json` | step 3's test exists but tests synthetic fixtures, not "bit-identical state hash parity" | n/a | n/a | not enforced; two of four steps point at nothing | DEL and rewrite as the calibration procedure PERF-D4 keeps here |
| BP-17 | 125-146 | corpus-world baselines via `tools/bench_corpus_world.py --world {name} [--commit]`; `PERF_512MB_LOCAL`; three worlds committed | procedure | `tools/bench_corpus_world.py` exists; baselines `tests/perf/baselines/simq_corpus_*.json` | `tests/perf/test_perf_regression_baseline.py:55-57`, `tests/tools/test_corpus_perf_baseline.py` | Slow (regression test), PR-perf (tool test) | soft | enforced as written (the only baselined real worlds) | TRIP and CAPRUN input (baseline identity) |

### 3.4 `docs/performance/optimization_invariants.md` (authority P1; C-15 classification)

| ID | Line | Clause | Kind | Code | Tests | CI | H/S | Status | D4 |
|---|---|---|---|---|---|---|---|---|---|
| OI-00 | 12 | "Violating any of these invariants constitutes an immediate test failure and blocks production deployment" | claim | the invariant tests are plain hard assertions in their own jobs; no deployment gate was found that reads them | the tests cited in OI-01 to OI-08 | static, unit and integration jobs | hard (test failure) | partly verified: the test-failure half holds; the "blocks production deployment" half was not traced to a deployment pipeline | N/A |
| OI-01 | 49 | gameplay systems "strictly prohibited from referencing `state.dirty_set`" | invariant | static AST test | `tests/static/test_no_direct_dirtyset_candidate_selection.py` | static/architecture job (not the perf jobs) | hard | verified current behavior | N/A (not a measurement clause) |
| OI-02 | 50-51 | dirty queries via `CandidateSelector.select_candidates()` or indexes; mutation only via `StateUpdate` | invariant | `src/core/dirty.py:477` `CandidateSelector.entities(...)`; no `select_candidates` method found by name | same test | static/architecture job | hard | verified current behavior except the method name (`entities`, not `select_candidates`) | N/A |
| OI-03 | 65-68 | 7 phases must check `force_full_scan`; full-scan hash must equal optimized hash; `refine()` dirty set covers every entity under force-full-scan | invariant | `src/engine/pipeline.py`, `phase_graph.py:88`, `candidate_selector.py`, `core/dirty.py` (all grep hits for `force_full_scan`) | `tests/integration/optimization/test_force_full_scan_phase_compliance.py`, `test_force_full_scan_dirty_set_completeness.py` | integration job | hard | verified current behavior (7-phase list not re-checked against code) | N/A |
| OI-04 | 82-84 | compactor preserves order; patch order `EquipmentPatch -> IdentityPatch -> CombatPatch -> TaskPatch`; no-ops become singletons | invariant | `src/engine/patches.py` defines all four classes; ordering mechanism not located in `apply_plan.py`/`apply.py` by name | `tests/unit/domains/optimization/test_state_update_compactor.py`, `tests/integration/optimization/test_component_patch_apply_parity.py` | unit and integration jobs | hard | partly verified (order not confirmed by this scan) | N/A |
| OI-05 | 98-100 | all caches register with `CacheRegistry`; invalidation on dirty domains; `CacheBudgetPolicy` max items; deterministic FIFO/LRU eviction at `Cleanup` start | invariant | `src/engine/cache_registry.py` (both classes exist) | `tests/integration/optimization/test_cache_memory_bounds.py`, `tests/unit/domains/optimization/test_cache_registry.py` | integration and unit jobs | hard | verified current behavior (not re-run) | N/A |
| OI-06 | 104 | "continuous memory tracking harnesses asserting bounded RSS containment over 5,000+ ticks" | claim | `src/perf/long_run_harness.py:258` (`rss_bounded = growth <= 2.0 or peak <= 512 MB`) | `tests/certification/test_cert_long_run_stability.py:68` | Slow (`extra_slow`) | soft | enforced differently: threshold is 2x growth or 512 MB peak; tick count is the harness parameter, not 5,000 | CAPRUN |
| OI-07 | 114 | governor may defer routine strategic, gossip, non-urgent pathfinding, non-combat scans | invariant | `src/engine/phase_governor.py` | `tests/unit/domains/optimization/test_phase_budget_governor.py` | a unit job | hard | verified current behavior | N/A |
| OI-08 | 115-118 | governor "MUST NEVER defer" mortality/succession, accepted transactions and quest rewards, inventory weight, active combat | invariant | `src/engine/phase_graph.py:37-39` (`must_run_every_tick=True` entries) | `test_phase_budget_governor.py`; cited `tests/integration/optimization/test_degraded_mode_correctness.py` is missing | a unit job | hard | enforced as written for the unit test; **cited integration test does not exist** | N/A |
| OI-09 | 123 | "Proves flawless correctness under degraded mode throttling" | test citation | missing file | none | none | n/a | not enforced (file absent) | N/A (fix citation) |

### 3.5 `docs/performance/optimization_architecture.md` (authority P1; C-15 classification)

Each statement is classified as verified current behavior (**V**), target architecture (**T**) or
obsolete (**O**), as C-15 requires. Statements without a number or a requirement word are grouped by
paragraph.

| ID | Line | Statement | Class | Evidence | Status | D4 |
|---|---|---|---|---|---|---|
| OA-01 | 12 | runs "10,000+ concurrent entities" under "a strict 50ms compute latency budget and 2GB memory footprint" | T | no check at 10,000 entities; `max_tick_budget_ms` is a profile field (`src/perf/profiles.py`), not a measured pass/fail; 2 GB appears in no profile value checked (`PERF_512MB_LOCAL`/`PERF_1GB_LOCAL` exist) | target, not enforced; the same targets differ in `perf_baseline_policy.md:26-28` (CLASS_A 10,000 @ < 50 ms; CLASS_B 2,500 @ < 40 ms) | CAP |
| OA-02 | 12, 14-39 | "5-layer optimization stack" with 17 named classes | V | all 17 named classes exist (`src/core/dirty.py`, `src/engine/{phase_governor,candidate_selector,compactor,apply_plan,patches,occupancy_snapshot,movement_cache,cache_registry,phase_graph,world_index}.py`, `src/api/read_model_cache.py`, `src/config/optimization_profiles.py`, `src/systems/strategic_systems/work_queue.py`) | verified current behavior | N/A |
| OA-03 | 45, 48 | "all systems must query the centralized `CandidateSelector`"; "15 distinct simulation domains (e.g., `LOCOMOTION`, `STRATEGIC_INTELLIGENCE` ...)" | V/O | `CandidateSelector.entities` handles 14 named domain strings plus `"all"` (`src/core/dirty.py:487-509`), lower-case (`movement`, `combat`, `strategic` ...); the example names in the document appear nowhere in that code | count approximately right (15); names obsolete | N/A |
| OA-04 | 49-50 | `EXACT_DIRTY` bypasses O(N) scans; `THROTTLED` caps candidates by tier and cadence | V | `ScanPolicy` in `src/engine/phase_governor.py`; used at `:70,77,117` | verified current behavior | N/A |
| OA-05 | 56 | `StrategicWorkQueue` narrows into "7 urgency tiers (`SURVIVAL`, `COMBAT`, `HAZARD`, `SOCIAL`, `MAINTENANCE`, `CAPABILITY`, `OPPORTUNITY`)" | V/O | `src/systems/strategic_systems/work_queue.py:39-45` has 7 tiers, named by cause (failed action/path, unresolved blockers, active project transition, biological emergency, contract expiration, dirty strategic entities, background sweep sample) | count right (7); names obsolete | N/A |
| OA-06 | 62-71 | `DirtySet`, `DirtyDependencyGraph` expansion (`DIRTY_INVENTORY` -> `DIRTY_ATTRIBUTES`, `DIRTY_MOVEMENT`), `CacheInvalidationPolicy` | V | `src/core/dirty.py:212,417`, `src/engine/world_index.py` (`CacheInvalidationPolicy`); expansion table not re-read | verified (class level) | N/A |
| OA-07 | 81-90 | compactor prunes no-ops; `ApplyPlan` precomputed; patches sorted by dependency | V | `compactor.py`, `apply_plan.py`, `patches.py` exist | verified (class level); ordering see OI-04 | N/A |
| OA-08 | 99-110 | `ReadModelCache`, `OccupancySnapshot`, `MovementPlanCache`, `CacheRegistry`/`CacheBudgetPolicy` "guarantees bounded memory (RSS) containment" | V/T | classes exist; the RSS guarantee is a claim backed only by soft/nightly checks (OI-06, BP-13) | classes verified; guarantee target | CAPRUN (for the guarantee) |
| OA-09 | 119-123 | `OptimizationProfileResolver` with `COMBAT_HEAVY`, `METROPOLIS`, `LOW_MEMORY`, `DEBUG_REFERENCE` | V | `src/config/optimization_profiles.py` defines these plus `MOVEMENT_HEAVY`, `RESOURCE_HEAVY`, `DEFAULT_PROFILE`; the document omits two | verified; incomplete | N/A |
| OA-10 | 126 | "Rather than executing all 17 authoritative pipeline phases unconditionally, `PhaseDependencyGraph` ..." | O | `PhaseDependencyGraph.PHASES` has 31 entries (`src/engine/phase_graph.py:36`); `docs/engine/authoritative_pipeline.md` says 39 | obsolete count | N/A |
| OA-11 | 129 | governor lowers budgets "if recent tick compute latencies (p95) exceed the scenario target (50ms)" | V/O | trigger is `effective_tick_cost > max_tick_ms * 0.8` (`src/engine/phase_governor.py:138`; the work-debt clause was removed in Phase B): latest tick, not p95, and 80 % of the profile's `max_tick_budget_ms`, not a fixed 50 ms | enforced differently | FLAG (the governor trigger is a budget rule, not a measurement clause) |
| OA-12 | 135 | all mechanisms "proven to maintain 100% exact bit-identical state hash parity" by `tests/integration/optimization/` | V | directory exists with the cited files (OI-03..OI-05); one citation missing (OI-09) | partly verified | N/A |

### 3.6 `docs/engine/runtime_profiles.md` and `docs/engine/contracts/resource_governor_contract.md`

Only clauses that set a performance budget or threshold.

| ID | Line | Clause | Kind | Code | Tests | CI | H/S | Status | D4 |
|---|---|---|---|---|---|---|---|---|---|
| RP-01 | runtime_profiles 23-29 | `max_ram_mb` hard limit; `max_cpu_percent` operational target; `max_tick_budget_ms` "latency target"; `degradation_threshold` percentage | thresholds (profile fields) | `src/perf/profiles.py` (`make_perf_profile`: `max_cpu_percent=90.0`, `max_tick_budget_ms=tick_budget_ms`), `src/config/profiles.py` | `tests/certification/test_envelope_violations.py` | PR-perf | hard (envelope) | enforced as written for the field set (value correctness not re-read) | N/A (budgets, not claims) |
| RP-02 | runtime_profiles 32, 37 | a profile guarantees "Envelope Compliance, not a fixed throughput"; same profile on different classes "must yield identical semantics and identical resource ceilings" | claim rule | every `PERF_*` profile is `CLASS_A` regardless of host (`src/perf/profiles.py:39`) | none found | none | n/a | enforced differently: ceilings are identical because the class is hard-coded | HW |
| RP-03 | runtime_profiles 34-36 | classes by name: A server, B dev/workstation, C legacy/edge | hardware class (names only) | `hardware.py` | `test_evidence_levels.py` | PR-perf | n/a | consistent with CC-09 (no numbers); a fourth definition of the same names | HW |
| RG-01 | governor 26-29 | de-escalation only if all signals below recovery threshold and after dwell time `N` ticks | outcome rule | `src/engine/phase_governor.py`, `src/engine/resource_governor.py` (not read) | `tests/certification/test_resilience_recovery.py` | PR-perf | hard | enforced as written (assumed from test name) | N/A |
| RG-02 | governor 32 | `tick_compute_ms`: "Wall-clock time of the previous kernel loop" | definition | `PressureSignals.tick_compute_ms`, used at `phase_governor.py:139` | `tests/perf/test_bench_harness.py` | PR-perf | n/a | enforced as written | STAY (shares PC-02's definition) |
| RG-03 | governor 37 | identical pressure patterns "MUST produce identical mode transitions" | determinism claim | governor | `tests/certification/test_resilience_recovery.py` | PR-perf | hard | enforced as written (assumed) | N/A |

## 4. Reverse table: live performance checks that enforce no documented clause

Every performance or resource check found in code, tests or CI that does not map to a clause in §3.

| Check | Location | What it does | Why no clause |
|---|---|---|---|
| Absolute tick-time and memory limits per scenario | `tests/perf/test_perf_idle.py:27-30`, `test_perf_stress.py:27-30`, `test_perf_metropolis.py:56-60,112-115,145`, `test_perf_passive_scaling.py:40-47,70`, `test_perf_combat.py:25`, `test_perf_strategic.py:40`, `test_perf_movement.py:23`, `test_perf_resource.py:23`, `tests/arena/test_arena_stress.py:44` | hard-coded ms / MB / TPS limits (e.g. 750.0, 1650.0, 375.0), all soft | no document sets per-scenario absolute limits (BP-04..06 give entity-count targets only) |
| Phase-budget ceilings | `tests/perf/test_phase2_self_model_budget.py:45,55,59`, `test_phase3_adventure_decision_budget.py:100`, `test_phase4_combat_engagement_budget.py:68`, `test_phase5_...:78`, `test_phase6_...:42`, `test_phase7_...:70`, `test_phase8_...:43`, `test_phase9_...:53` | per-phase wall-time budgets at 100 entities (5-70 ms) | no clause sets a per-feature-phase budget |
| `PerfBudget` against `perf_baselines.json` | `tests/perf/conftest.py:29-81` (`assert_within_budget`, 20 % default tolerance), file `perf_baselines.json` at the repo root, `make perf-measure` (`Makefile:215-216`), `tools/perf_guard.py` | time and RSS-KB budget per named test | no document mentions `perf_baselines.json` or `PerfBudget`; consumers: `test_phase2_self_model_budget.py`, `test_phase3_adventure_decision_budget.py`, `tests/unit/perf/test_perf_guard.py` |
| Long-run stability | `src/perf/long_run_harness.py:258-269`; `tests/certification/test_cert_long_run_stability.py:68-71` | `rss_bounded` (2x or 512 MB), `latency_stable` (1.5x or +15 ms), `caches_bounded` (`10*N`, `2*N`), `gc_stable` | BP-13 and OI-06 describe the intent; the numbers appear in no document |
| Smoke benchmark gate | `tools/perf/perf_ci.py`, `run_benchmarks.py:49-50`, `check_perf_regression.py:15-17` | `max(1.15x, +3 ms)` average and per-phase p95, `+20 MB` RSS | nothing calls it (no CI, Makefile or test reference); thresholds appear in no document |
| Observability overhead | `tests/perf/test_hard_law_monitor_overhead.py:75`, `test_production_observatory_overhead.py:84,103`, `test_observability_scale_validation.py:80`, `test_phase28_behavior_observability_overhead.py:7` | overhead ratios and `max_live_publish_ms_per_tick <= 0.5` (a hard `assert`, `:7`) | PC-12 states a 1 % ceiling; these check different numbers |
| API projection and snapshot | `tests/perf/test_api_projection_perf.py:43`, `test_perf_api_snapshot.py:104-127` | speed-up ratios of 1.5x, 2.5x, 3.0x | no clause on API projection performance |
| Persistence phase share | `tests/perf/test_persistence_phase_cost.py:85` (`PERSISTENCE_SHARE_CEILING_PCT`) | share of tick spent in persistence | no clause |
| SimQ isolation overhead | `tests/perf/test_simq_isolation_overhead.py:367,392,441,487` | four CPU overhead bands | only referenced by name in BP-08 |
| `compute_tps >= wall_clock_tps` | `tests/perf/test_profiler_integrity.py:115` | hard `assert` that compute TPS is not below wall-clock TPS | PC-04 defines TPS; this integrity check is not a clause |
| Frame pacing off in benchmarks | `tests/perf/test_profiler_integrity.py:68` | benchmark disables frame pacing by default | no clause; affects PC-15's `gc.collect(0)` path |

## 5. Disagreements between documents, with lines on both sides

| # | Topic | Side A | Side B | Code |
|---|---|---|---|---|
| D-1 | `CLASS_A` definition | `perf_baseline_policy.md:26`: 8+ cores, 16 GB+ | `certification_contract.md:32`: >= 16 logical cores and >= 32 GB | `src/certification/hardware.py:23` agrees with the certification contract |
| D-2 | `CLASS_C` definition | `perf_baseline_policy.md:28`: 2 cores, 2 GB | `certification_contract.md:34`: all other systems | `hardware.py:27` agrees with the contract |
| D-3 | `CLASS_B` rule shape | `perf_baseline_policy.md:27` and its note `:30-35`: core count read alone | `certification_contract.md:33`: >= 4 cores AND >= 8 GB | `hardware.py:25` AND rule |
| D-4 | Regression tolerance on latency | `performance_contract.md:61`: > 5 % on `avg_tick_compute_ms` | `perf_baseline_policy.md:74-76`: p50 5 %, p95 10 %, p99 15 % | live test `:94`: `max(5 ms, 1.25x)`; unwired tool `check_perf_regression.py:15-16`: `max(1.15x, +3 ms)`; `regression_gate.py:81`: 10 % for p95 and p99 |
| D-5 | RSS regression | `perf_baseline_policy.md:79`: 15 % between tick 100 and 1,000 | `perf_baseline_policy.md:80`: GC sweeps stable | gate: peak RSS 15 % and delta (5 MB or 15 %) `regression_gate.py:142,150`; unwired tool: `+20 MB` `check_perf_regression.py:17`; long-run harness: 2x or 512 MB `long_run_harness.py:258` |
| D-6 | Warmup and sample minimums | `performance_contract.md:48-49` and `perf_baseline_policy.md:21-22`: 100 and 1,000 | (same, so documents agree) | regression test: 10 and 50 (`test_perf_regression_baseline.py:79-80`); smoke: 10/20 or 50/200 (`run_benchmarks.py:49-50`) |
| D-7 | Gate mechanism | `perf_baseline_policy.md:59` and `:83`: `PerfRegressionGate` fails CI with `UnacceptableRegressionError` | `perf_baseline_policy.md:46-57` (its own correction): zero real consumers | `UnacceptableRegressionError` does not exist; gate is test-only |
| D-8 | Calibration procedure | `perf_baseline_policy.md:103-105`: `tests.integration.optimization.test_perf_regression_gate --generate-baseline` into `data/baselines/` | `perf_baseline_policy.md:130-139` (§5): `tools/bench_corpus_world.py ... --commit` into `tests/perf/baselines/` | the §4 module and directory do not exist |
| D-9 | Failure-kind names | `certification_contract.md:25-26`: `FAILED_DEGRADATION_ORDER`, `FAILED_RECOVERY` | `src/certification/models.py:40-41`: `FAILED_DEGRADATION_SEQUENCE`, `FAILED_RECOVERY_TIMEOUT` | (code is the reference) |
| D-10 | Override field | `certification_contract.md:35`: `hardware_class_override_applied` | `src/certification/models.py:118,252`: `override_applied` | (code is the reference) |
| D-11 | Instrumentation overhead | `performance_contract.md:58`: < 1 % of tick time | `tests/perf/test_hard_law_monitor_overhead.py:60-67`: test's own comment says the monitor cannot meet 1 % | test asserts an absolute limit instead |
| D-12 | Governor trigger | `optimization_architecture.md:129` and `optimization_invariants.md:111` (rationale): p95 exceeds 50 ms | `docs/engine/contracts/resource_governor_contract.md:26-29`: any signal over the escalation threshold, relative to the active profile | `phase_governor.py:138`: latest effective tick cost > 0.8 x `max_tick_budget_ms` (the debt clause was removed in Phase B) |
| D-13 | Pipeline phase count | `optimization_architecture.md:126`: 17 "authoritative pipeline phases" | `docs/performance/phase_inventory.md` (generated): 44 refinement phases (`run_phase()` calls in `refine`); `docs/engine/authoritative_pipeline.md`: 39 names | `phase_graph.py:36`: 31 `PhaseDependencyGraph.PHASES` entries (different units; not equated) |
| D-14 | Class names for the same hardware | `runtime_profiles.md:34-36`: Class A server / B dev / C legacy | `perf_baseline_policy.md:26-28`: High-Performance Server / Standard Gaming Desktop / Constrained Edge | names only; numbers per D-1..D-3 |
| D-15 | Capacity targets | `optimization_architecture.md:12`: 10,000+ entities, 50 ms, 2 GB | `perf_baseline_policy.md:26-28`: 10,000 @ 50 ms (A), 2,500 @ 40 ms (B), 500 @ 30 ms (C) | no check enforces either |

## 6. PERF-D4 mapping

Destination codes. **STAY**: stays in `performance_contract.md`. **CERT**: stays in `certification_contract.md`, which PERF-D4 point 2 makes the hardware-class and certification authority. **CAP**: moves from the baseline policy
into the contract as a capacity-run target. **CAPRUN**: becomes a capacity-run clause. **TRIP**:
becomes a tripwire clause. **HW**: replaced by a reference to the certification-contract hardware classes
(CC-09, `certification_contract.md` §3). **DEL**: deleted, because it describes a mechanism that does not run
or is superseded. **N/A**: not a measurement clause (a design invariant or architecture statement
that PERF-D4 does not touch). **FLAG**: PERF-D4's shape cannot express it.

### 6.1 Counts by destination

Generated from the **D4** column of §3 by taking the first code in each cell, so every row counts exactly once. A row whose cell names two destinations (for example BP-04: HW for the class, CAP for the target) is counted under the first and its second half is stated in the row.

| Destination | Rows | Count |
|---|---|---|
| STAY | PC-01, PC-02, PC-03, PC-05, PC-06, PC-11, PC-15, PC-16, PC-17, RG-02 | 10 |
| CERT | CC-01, CC-02, CC-03, CC-04, CC-05, CC-06, CC-07, CC-08, CC-09, CC-10, CC-11, CC-12, CC-13, CC-14 | 14 |
| CAP | OA-01 | 1 |
| CAPRUN | PC-04, PC-08, PC-09, PC-10, BP-02, BP-03, BP-12, BP-13, OI-06, OA-08 | 10 |
| TRIP | PC-07, PC-13, BP-09, BP-10, BP-11, BP-15, BP-17 | 7 |
| HW | BP-04, BP-05, BP-06, RP-02, RP-03 | 5 |
| DEL | PC-14, BP-01, BP-07, BP-14, BP-16 | 5 |
| N/A | OI-00, OI-01, OI-02, OI-03, OI-04, OI-05, OI-07, OI-08, OI-09, OA-02, OA-03, OA-04, OA-05, OA-06, OA-07, OA-09, OA-10, OA-12, RP-01, RG-01, RG-03 | 21 |
| FLAG | PC-12, BP-08, OA-11 | 3 |
| **Total** | | **76** |

### 6.2 Clauses the PERF-D4 shape cannot express (PERF-D4's revisit condition)

PERF-D4's projections are a tripwire (cheap regression check) and a capacity run (sustained,
class-bound claim), with outcomes `PASS` / `REGRESSION` / `INCONCLUSIVE` / `NOT_APPLICABLE`. These
clauses fit neither:

1. **PC-12 (instrumentation overhead < 1 % of tick time).** It is a ratio between a subsystem's cost
   and the tick, measured as an A/B pair. The same shape is behind the observability overhead checks
   and the four SimQ isolation bands (§4). A tripwire compares one build to a baseline; an
   overhead-ratio compares two configurations of one build.
2. **BP-08 / SimQ isolation overhead.** Same shape as 1, with three modes (disabled, in-process,
   broker).
3. **OA-11 (governor trigger at 80 % of the profile's tick budget).** A runtime control rule, not a
   measurement claim; its threshold is relative to a profile field, so no class-bound number exists.
4. **Absolute per-scenario and per-phase ceilings (§4 rows 1-2).** They have no document clause and
   are neither tripwire (no baseline) nor capacity run (no class binding). They need either a home or
   deletion; this inventory does not decide which.
5. **`PerfBudget` / `perf_baselines.json` (§4 row 3).** A third baseline store, per named test, with its
   own 20 % tolerance. It overlaps the tripwire but is keyed by test id, not by benchmark identity.
6. **Long-run stability (`rss_bounded`, `latency_stable`, `caches_bounded`, `gc_stable`).** A
   within-run trend check (end vs. start of one run), not a comparison with a baseline; the closest
   fit is a capacity-run clause but PERF-D4 does not list trend checks.
7. **Correctness laws that live in perf documents (PC-11, OI-01 to OI-09).** Not measurements at all;
   they stay where they are. Listed so T09 does not move them.

## 7. `assert_perf_threshold` / `perf_check` call sites

Generated by `python3 tools/perf/perf_threshold_inventory.py --format md` against `ed5001057`.
Two runs are byte-identical. `Limit` is the second positional argument as written for
`assert_perf_threshold`, and the boolean expression for `perf_check`. `hard` is `absent` when the call
does not pass it (the helper defaults to `False`, i.e. a warning). Markers shown are the subset of
`slow`, `extra_slow`, `perf`, `arena`, `certification` in force. `slow` and `extra_slow` are excluded from
the PR job.

| File | Line | Function | Helper | Limit (as written) | `hard` | `op` | Markers |
|---|---|---|---|---|---|---|---|
| `tests/arena/test_arena_stress.py` | 44 | `test_arena_stress_50v50` | `assert_perf_threshold` | `375.0` | `absent` | `<` | extra_slow, slow |
| `tests/certification/test_cert_long_run_stability.py` | 68 | `test_long_run_pure_stability` | `perf_check` | `report.rss_bounded` | `absent` |  | certification, extra_slow, slow |
| `tests/certification/test_cert_long_run_stability.py` | 69 | `test_long_run_pure_stability` | `perf_check` | `report.latency_stable` | `absent` |  | certification, extra_slow, slow |
| `tests/certification/test_cert_long_run_stability.py` | 70 | `test_long_run_pure_stability` | `perf_check` | `report.caches_bounded` | `absent` |  | certification, extra_slow, slow |
| `tests/certification/test_cert_long_run_stability.py` | 71 | `test_long_run_pure_stability` | `perf_check` | `report.gc_stable` | `absent` |  | certification, extra_slow, slow |
| `tests/perf/conftest.py` | 64 | `PerfBudget.assert_within_budget` | `perf_check` | `measured_ms <= limit_ms` | `expr: hard` |  | - |
| `tests/perf/conftest.py` | 76 | `PerfBudget.assert_within_budget` | `perf_check` | `measured_kb <= limit_kb` | `expr: hard` |  | - |
| `tests/perf/test_api_projection_perf.py` | 43 | `test_api_projection_performance_benchmark` | `assert_perf_threshold` | `3.0` | `absent` | `>=` | slow |
| `tests/perf/test_hard_law_monitor_overhead.py` | 75 | `test_hard_law_monitor_overhead` | `assert_perf_threshold` | `0.6` | `absent` | `<` | perf, slow |
| `tests/perf/test_observability_scale_validation.py` | 80 | `test_scale_performance_and_footprint` | `assert_perf_threshold` | `1.0` | `absent` | `<` | - |
| `tests/perf/test_perf_api_snapshot.py` | 104 | `test_api_snapshot_performance_comparison` | `assert_perf_threshold` | `1.5` | `absent` | `<` | perf, slow |
| `tests/perf/test_perf_api_snapshot.py` | 105 | `test_api_snapshot_performance_comparison` | `assert_perf_threshold` | `1.5` | `absent` | `<` | perf, slow |
| `tests/perf/test_perf_api_snapshot.py` | 126 | `test_api_snapshot_performance_stress` | `assert_perf_threshold` | `2.5` | `absent` | `<` | perf, slow |
| `tests/perf/test_perf_api_snapshot.py` | 127 | `test_api_snapshot_performance_stress` | `assert_perf_threshold` | `2.5` | `absent` | `<` | perf, slow |
| `tests/perf/test_perf_combat.py` | 25 | `test_perf_combat` | `assert_perf_threshold` | `750.0` | `absent` | `<` | perf, slow |
| `tests/perf/test_perf_idle.py` | 27 | `test_perf_idle_baseline` | `assert_perf_threshold` | `20.0` | `absent` | `>` | perf, slow |
| `tests/perf/test_perf_idle.py` | 28 | `test_perf_idle_baseline` | `assert_perf_threshold` | `512.0` | `absent` | `<` | perf, slow |
| `tests/perf/test_perf_idle.py` | 30 | `test_perf_idle_baseline` | `assert_perf_threshold` | `100.0` | `absent` | `<` | perf, slow |
| `tests/perf/test_perf_metropolis.py` | 56 | `test_perf_metropolis_stress` | `assert_perf_threshold` | `3.0` | `absent` | `>` | extra_slow, perf |
| `tests/perf/test_perf_metropolis.py` | 58 | `test_perf_metropolis_stress` | `assert_perf_threshold` | `500.0` | `absent` | `<` | extra_slow, perf |
| `tests/perf/test_perf_metropolis.py` | 60 | `test_perf_metropolis_stress` | `assert_perf_threshold` | `1024.0` | `absent` | `<` | extra_slow, perf |
| `tests/perf/test_perf_metropolis.py` | 112 | `test_perf_metropolis_longevity` | `assert_perf_threshold` | `5.0` | `absent` | `>` | extra_slow, perf |
| `tests/perf/test_perf_metropolis.py` | 115 | `test_perf_metropolis_longevity` | `assert_perf_threshold` | `1.0` | `absent` | `<` | extra_slow, perf |
| `tests/perf/test_perf_metropolis.py` | 145 | `test_perf_chaos_items` | `assert_perf_threshold` | `250.0` | `absent` | `<` | perf |
| `tests/perf/test_perf_movement.py` | 23 | `test_perf_movement` | `assert_perf_threshold` | `threshold` | `absent` | `<` | perf, slow |
| `tests/perf/test_perf_passive_scaling.py` | 40 | `test_perf_passive_scaling` | `assert_perf_threshold` | `25.0` | `absent` | `<` | perf, slow |
| `tests/perf/test_perf_passive_scaling.py` | 42 | `test_perf_passive_scaling` | `assert_perf_threshold` | `175.0` | `absent` | `<` | perf, slow |
| `tests/perf/test_perf_passive_scaling.py` | 44 | `test_perf_passive_scaling` | `assert_perf_threshold` | `450.0` | `absent` | `<` | perf, slow |
| `tests/perf/test_perf_passive_scaling.py` | 47 | `test_perf_passive_scaling` | `assert_perf_threshold` | `expected_max_rss` | `absent` | `<` | perf, slow |
| `tests/perf/test_perf_passive_scaling.py` | 70 | `test_perf_passive_scaling` | `assert_perf_threshold` | `allowed_delta` | `absent` | `<` | perf, slow |
| `tests/perf/test_perf_regression_baseline.py` | 40 | `_assert_runtime_mode_stayed_normal` | `assert_perf_threshold` | `0` | `expr: hard` | `<=` | - |
| `tests/perf/test_perf_regression_baseline.py` | 101 | `test_regression_vs_baseline` | `assert_perf_threshold` | `threshold` | `absent` | `<=` | perf, slow |
| `tests/perf/test_perf_resource.py` | 23 | `test_perf_resource` | `assert_perf_threshold` | `threshold` | `absent` | `<` | perf, slow |
| `tests/perf/test_perf_strategic.py` | 40 | `test_perf_strategic` | `assert_perf_threshold` | `1650.0` | `absent` | `<` | perf, slow |
| `tests/perf/test_perf_stress.py` | 27 | `test_perf_mixed_stress` | `assert_perf_threshold` | `5.0` | `absent` | `>` | perf, slow |
| `tests/perf/test_perf_stress.py` | 28 | `test_perf_mixed_stress` | `assert_perf_threshold` | `1024.0` | `absent` | `<` | perf, slow |
| `tests/perf/test_perf_stress.py` | 30 | `test_perf_mixed_stress` | `assert_perf_threshold` | `200.0` | `absent` | `<` | perf, slow |
| `tests/perf/test_persistence_phase_cost.py` | 85 | `test_persistence_phase_cost_regression_guard_1000t` | `assert_perf_threshold` | `PERSISTENCE_SHARE_CEILING_PCT` | `absent` | `<` | slow |
| `tests/perf/test_phase2_self_model_budget.py` | 45 | `test_phase2_self_model_perf_budget_and_dirty_check` | `assert_perf_threshold` | `50.0` | `absent` | `<` | slow |
| `tests/perf/test_phase2_self_model_budget.py` | 55 | `test_phase2_self_model_perf_budget_and_dirty_check` | `assert_perf_threshold` | `5.0` | `absent` | `<` | slow |
| `tests/perf/test_phase2_self_model_budget.py` | 59 | `test_phase2_self_model_perf_budget_and_dirty_check` | `assert_perf_threshold` | `5.0` | `absent` | `>=` | slow |
| `tests/perf/test_phase3_adventure_decision_budget.py` | 100 | `test_phase3_adventure_decision_perf_budget` | `assert_perf_threshold` | `70.0` | `absent` | `<` | - |
| `tests/perf/test_phase4_combat_engagement_budget.py` | 68 | `test_performance_budget_100_entities` | `assert_perf_threshold` | `15.0` | `absent` | `<` | slow |
| `tests/perf/test_phase5_information_belief_budget.py` | 78 | `test_performance_budget_100_entities` | `assert_perf_threshold` | `5.0` | `absent` | `<` | - |
| `tests/perf/test_phase6_progression_conversion_budget.py` | 42 | `test_phase6_progression_conversion_performance_budget` | `assert_perf_threshold` | `5.0` | `absent` | `<` | slow |
| `tests/perf/test_phase7_social_cooperation_budget.py` | 70 | `test_cooperation_phase_performance_budget_100_entities` | `assert_perf_threshold` | `25.0` | `absent` | `<` | slow |
| `tests/perf/test_phase8_world_emergence_budget.py` | 43 | `test_phase8_performance_budget` | `assert_perf_threshold` | `5.0` | `absent` | `<` | - |
| `tests/perf/test_phase9_campaign_semantic_budget.py` | 53 | `test_campaign_semantic_budget_overhead` | `assert_perf_threshold` | `5.0` | `absent` | `<` | - |
| `tests/perf/test_production_observatory_overhead.py` | 84 | `test_observatory_light_mode_overhead` | `assert_perf_threshold` | `threshold` | `absent` | `<` | slow |
| `tests/perf/test_production_observatory_overhead.py` | 103 | `test_observatory_off_mode_zero_overhead` | `assert_perf_threshold` | `200.0` | `absent` | `<` | - |
| `tests/perf/test_profiler_integrity.py` | 68 | `test_benchmark_disables_frame_pacing_by_default` | `assert_perf_threshold` | `500.0` | `absent` | `<` | slow |
| `tests/perf/test_simq_isolation_overhead.py` | 367 | `test_inprocess_simq_overhead_within_regression_band` | `assert_perf_threshold` | `INPROCESS_CPU_OVERHEAD_BAND_PCT` | `absent` | `<` | slow |
| `tests/perf/test_simq_isolation_overhead.py` | 392 | `test_broker_mode_engine_cpu_within_disabled_band` | `assert_perf_threshold` | `BROKER_CPU_OVERHEAD_BAND_PCT` | `absent` | `<` | slow |
| `tests/perf/test_simq_isolation_overhead.py` | 441 | `test_push_shaper_registry_overhead_within_regression_band` | `assert_perf_threshold` | `PUSH_SHAPER_CPU_OVERHEAD_BAND_PCT` | `absent` | `<` | slow |
| `tests/perf/test_simq_isolation_overhead.py` | 487 | `test_phase2_shaper_registry_overhead_within_regression_band` | `assert_perf_threshold` | `PHASE2_CPU_OVERHEAD_BAND_PCT` | `absent` | `<` | slow |

Totals: all=55, assert_perf_threshold=49, perf_check=6, hard_true=0, hard_false_or_absent=52, hard_expression=3, slow_marked=45

How to read the totals: `hard_true=0` means no call site passes a literal `hard=True`.
`hard_expression=3` are the pass-through wrappers named in §1. `slow_marked=45` of 55 call sites sit
behind `slow` or `extra_slow` and so are outside the PR job; the 10 that are not (all with markers
`-` or `perf` only) run on PR and are soft.

## 8. What the inventory could not establish

- **Where "12 of 53 pass `hard=True`" came from.** The scan counts 55 sites and 0 literal `hard=True`.
  Candidate sources, none checked beyond the first: the 3 pass-through wrappers; the 9 `assert_within_budget`
  calls in `tests/unit/perf/test_perf_guard.py` (one of which passes `hard=True`, `:113`); a different
  commit; or plain `assert` statements on timing (for example `test_phase28_...py:7`, `test_profiler_integrity.py:115`).
- **Per-clause test coverage is a name search, not a read.** Rows marked "assumed" or "not re-read"
  were matched by file and identifier, not by reading the test body. A passing run was not performed.
- **Rows for `certification_contract.md` §1, §4 and the governor contract** cite code by module, not by
  line, where the clause is a broad requirement (CC-01, CC-03, CC-11, RG-01, RG-03).
- **Candidate-domain and urgency-tier names** (OA-03, OA-05): confirmed that the counts match and the
  document's names do not appear in the checked code; whether a different enum elsewhere carries those
  names was not searched.
- **Whether `tools/perf/perf_ci.py` is run by hand or by an external scheduler.** Nothing in the
  repository calls it.
- **Gate A materiality thresholds, benchmark identity and the projections themselves** are
  out of scope (PERF-M2-T02 to T04); no number in this document is a proposal.
