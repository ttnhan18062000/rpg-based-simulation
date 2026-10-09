---
status: active
layer: performance
authority: P2
audience: developer
tags: [performance, certification, testing, governance]
---

# Epic Plan — Performance M2: Authoritative Performance Contract

## Outcome

Create one versioned performance-claim model and explicit executable projections for fast CI and
controlled scheduled runs. A passing smoke gate must not be mistaken for a capacity claim.

## Entry conditions

- PERF-D2 defines the portability/hardware/runtime claim tiers.
- PERF-D4 selects the P1 authority and reconciliation process.
- M1 identifies every correction that changes benchmark or baseline identity.
- Performance and Release/Certification owners are named.

Status 2026-10-09: PERF-D2 and D4 are approved, and M1 is complete. Its invalidation ledger
(`docs/performance/baseline_invalidation_ledger.md`) is the list of corrections that change
identity. The RPG-core entry gate has **not** fully lifted, so every `src/` edit below needs a
named owner lift, and every measurement stays provisional ("Delivery plan", OD-8).

## Candidate child tickets

| Candidate ID | Ticket scope | Depends on | Deliverable |
|---|---|---|---|
| PERF-M2-T01 | Clause-level source inventory | PERF-D4 | Matrix across engine contract, certification contract, baseline policy, gate code, tests, and CI selectors |
| PERF-M2-T02 | Benchmark identity and result schema | T01 + PERF-D2 | Versioned schema for scenario/config/content/checkpoint/runtime/hardware/executor/mode/cardinality/observer identity (provisional design draft: [`docs/performance/benchmark_identity_schema.md`](../../../performance/benchmark_identity_schema.md), `TCK-20261003-PERF-M2-T02-BENCHMARK-IDENTITY-SCHEMA`) |
| PERF-M2-T03 | CI-fast tripwire projection | T02 | Cheap deterministic change detector, relative/absolute thresholds, failure states, and explicit non-capacity claim |
| PERF-M2-T04 | Controlled capacity/confirmation projection | T02 | Warmup/sample/repetition, paired base/head option, and p50/p95/p99/max/variance/memory contract on approved runners |
| PERF-M2-T05 | Baseline and known-debt lifecycle | T02, M1-T05 | Create/promote/invalidate/migrate/reject rules plus owner/expiry quarantine; missing or incompatible evidence cannot silently pass |
| PERF-M2-T06 | P1 publication and gate-conformance map | T03–T05 | Owner-approved P1 contract plus machine-checkable mapping from change classes and live gates to enforced clauses |

T03 and T04 are different products of the same identity schema. They may proceed in parallel and
must use names that make their evidence strength impossible to confuse.

T01 (`TCK-20261003-PERF-M2-CLAUSE-INVENTORY`) and T02 (as a provisional draft) are done. The
remaining work, including three items this table does not name (T02b, T07, T08), is ordered in
"Delivery plan" below.

## Required contract dimensions

- scenario builder/checkpoint and workload cardinality;
- engine, content/rules, config, RNG, schema, and baseline versions;
- hardware/runtime and DET-PORT tier;
- executor/backend and worker count;
- warmup, measured ticks, independent repetitions, and variance handling;
- latency distribution, throughput, CPU/wall time, memory high-water, and scaling slope;
- `RuntimeMode` sequence, verification level, processed/dropped/coalesced work;
- replay/hash/control-trace validity;
- observer level and measured observer overhead;
- gate tier, trigger, blocking/informational status, and maximum feedback latency;
- relative and absolute regression thresholds, noise budget, retry limit, and confirmation rule;
- missing, stale, or incompatible artifact behavior.

## Regression-signal policy

Every executable projection returns one of `PASS`, `REGRESSION`, `INCONCLUSIVE`, or
`NOT_APPLICABLE` with a reason. Only `PASS` satisfies a required gate. Missing baselines, stale
identity, excessive variance, unsupported runners, empty scenario selection, and exhausted retries
are explicit non-pass outcomes rather than skips disguised as success.

The fast PR projection optimizes feedback latency and detects material change; it does not certify
capacity. A controlled projection confirms noisy signals with predeclared repetitions and, where
appropriate, paired base/candidate execution on the same runner. Both projections record raw
samples and use relative thresholds plus absolute floors so tiny benchmarks and shared-runner noise
do not dominate decisions.

Threshold and baseline changes are reviewed changes of evidence, not fixes for a failing build.
They require a cause tied to a ticket/change, compatible before/after identities, owner approval,
and an audit record. A retry may diagnose an inconclusive run; repeated execution until one sample
passes is forbidden.

Known historical failures are separately enumerated with owner, scope, expiration/review date, and
expected signature. The quarantine may prevent an already-red lane from blocking temporarily, but
new or worsened deltas still produce a regression signal. Promotion from informational to blocking
requires stable calibration and an explicit P1/CI-owner decision.

## Delivery plan (perf-planner, 2026-10-09)

Written after M1 closed (#473). No ticket below is filed yet; `/create-tickets` files them into
`agent-working/tickets/todos/perf-m2-contract/` once the owner has answered the decisions in step 1.

### 1. Owner decisions needed before filing

Each decision comes with a recommendation. The schema's open questions (`benchmark_identity_schema.md` §7) are
cited as Q*n*.

| ID | Decision | Recommendation | Blocks |
|---|---|---|---|
| OD-1 | Percentile method (Q6) | Nearest-rank, `ceil(q·n)`, for every producer. Record it in `protocol.percentile_method`, which is blocking, so an old `int(n·q)` record never compares with a new one. | T02b |
| OD-2 | How the tripwire stays comparable on shared CI runners (Q1, Q8) | **Paired base/head on the same runner in the same job**, wall-clock, canonical contract. Both sides share one runtime identity, so `cpu_model` can stay blocking without making every PR `INCONCLUSIVE`. The committed `tests/perf/baselines/` files stay for nightly and local use. The instruction-count tool and any hosted service are deferred to a separate spike after M2. | T03 |
| OD-3 | A `RuntimeMode` excursion (Q9) | Under the canonical contract the mode sequence does not depend on the host, so a head-side excursion against an all-`NORMAL` base is a `REGRESSION` (the work changed). Under `live_bounded` it stays `INCONCLUSIVE`. | T02b |
| OD-4 | Hardware class (Q7) | Detect it from cores and RAM (`certification_contract.md` §3, `src/certification/hardware.py`). A runner may declare a class only to match the detected one, and a mismatch is `INCONCLUSIVE`. Remove the hard-coded `CLASS_A` in `src/perf/profiles.py`. | T02b, T04 |
| OD-5 | Capacity runner (T04) | No controlled runner exists, and both development hosts are VMs. T04 builds the projection and runs it on one named host labelled `runner.controlled = false`. No capacity claim, and no §5.1 target enforced, until the owner names an approved runner. | T04 |
| OD-6 | Raw samples (Q5) | Embed them in tripwire records (at most a few hundred values). Capacity records carry a `{uri, sha256}` pointer to an uncommitted file under `reports/perf/`. | T02b |
| OD-7 | `pyperf` (Q2) | Do not adopt it in M2. T04 uses `BenchHarness` with process-level repetitions. Revisit only if T04's variance check fails on the named host. | T04 |
| OD-8 | Owner lift for M2's `src/` files | One lift for the files listed per ticket in step 3. None of them is a core file (`state.py`, `apply.py`, `pipeline.py`, `kernel.py`). Measurements stay provisional, and no check becomes blocking until the full lift. | T02b, T07, T03, X1 |

### 2. Schema revalidation against M1 (schema §8)

`benchmark_identity_schema.md` §8 asks for a re-read after M1. Against the ledger and the merged
M1 changes:

| # | Finding | Source | Change for T02b |
|---|---|---|---|
| R-1 | Nothing records whether a run's governor read a modelled cost or a measured one, or which work model it used. Under `canonical` the mode sequence depends on `WORK_MODEL_VERSION`, so a V1 and a V2 run do different work. | DEV-018 (#448); `src/config/profiles.py` `signal_contract`; `src/engine/work_units.py` `WORK_MODEL_VERSION`; ledger §5 caveat | Add `contract.signal_contract` (`live`, `canonical`) and `contract.work_model_version`, both blocking. |
| R-2 | Tick and phase totals changed meaning at DEV-017, but `engine.commit` is recorded-only, so a pre-#448 record compares as comparable with a post-#448 one. That is the vacuous pass of `TCK-20261009-PERF-GATE-PASSES-VACUOUSLY-AGAINST-PRE-M1-BASELINE`, expressed as a schema gap. | DEV-017 (#448); ledger §3.1, §3.2 | Add `result.cost_accounting_version`, blocking; a record without it is `INCONCLUSIVE`. |
| R-3 | `validity.hash_scheme` is a free string. Digests are `flat-sha256-v2` since #455, and v1 digests stay in compile reports. | DEV-019 (#455); ledger §3.4 | Make it an enum (`flat-sha256-v1`, `flat-sha256-v2`). The rule is unchanged. |
| R-4 | The zero-worker `DEGRADED` mistrigger is already covered by `executor.worker_count` (blocking) and by the all-`NORMAL` rule. | PERF-M1-T01 (#352) | None. |
| R-5 | Work debt is gone, so the M1-T02 row of schema §7 ("debt-related counters") has nothing left to describe. | #455 | Drop the debt wording. `work.*` keeps processed, dropped and coalesced counts. |

T02b also writes the answers to OD-1, OD-3, OD-4 and OD-6 into the schema and removes its
"provisional design draft" banner. The schema stays version `1.0`. Nothing has been written in the
draft shape, so there is nothing to migrate.

### 3. Tickets

| Order | ID | Scope | Depends on | Files (lift needed: **bold**) | Tier |
|---|---|---|---|---|---|
| 1 | **PERF-M2-T02b** Schema adoption | Typed record `BenchmarkRecord` (frozen, schema `1.0`) with R-1 to R-5. An identity collector covers git commit and dirty flag, the profile hash and flags, the runtime, the detected hardware class, signal contract and work model. `compare(base, head, thresholds) -> Outcome` implements schema §4 and returns the four outcomes with a reason. `BenchHarness` emits a record next to its existing dict, and nearest-rank percentiles replace `int(n·q)`. No gate changes. | OD-1, 3, 4, 6, 8 | **new `src/perf/benchmark_record.py`**, **`src/perf/bench_harness.py`**, **`src/perf/profiles.py`** (detected class), `docs/performance/benchmark_identity_schema.md`, `tests/unit/perf/` | standard |
| 1 | **PERF-M2-T07** Canonical perf profiles | Each `PERF_*` profile gets a canonical variant with `signal_contract = CANONICAL` (the ledger §5 prerequisite). The default profiles do not change. | OD-8 | **`src/perf/profiles.py`**, `tests/unit/perf/` | hotfix |
| 2 | **X1** `TCK-20261009-PERF-GATE-PASSES-VACUOUSLY-AGAINST-PRE-M1-BASELINE` (existing todo) | `src gate` and `compare-sweep` refuse a tick-cost verdict against a baseline without `cost_accounting_version` (R-2), using T02b's field name. Plus the two guide edits. | T02b | **`src/observability/reporting/baseline_comparator.py`**, **`src/observability/reporting/sweep_report.py`** (it assembles `gate_status`), `docs/guides/simulation.md`, `docs/guides/observability.md`, tests | hotfix |
| 2 | **PERF-M2-T05** Baseline and known-debt lifecycle | `perf_baseline_policy.md` is rewritten as the lifecycle rules: create, promote, invalidate, migrate, reject. A promotion refuses `dirty_src`, a non-`NORMAL` sequence and a missing cause ticket, and records the before and after identities. A known-debt ledger (`docs/performance/known_debt_ledger.yaml`: owner, scope, expiry, expected signature) is checked by a test. The test also checks that every file in `tests/perf/baselines/` is either a schema record or listed as a legacy unlabelled tripwire reference. Promotion goes through `tools/perf/baseline_lifecycle.py`; no `src/` change. | T02b | `docs/performance/perf_baseline_policy.md`, new `docs/performance/known_debt_ledger.yaml`, new `tools/perf/baseline_lifecycle.py`, `tests/tools/` | standard |
| 3 | **PERF-M2-T03** Tripwire projection | The live tripwire runs paired base/head per OD-2 through `compare()`, with a relative threshold plus an absolute floor and a predeclared noise budget. One diagnostic retry is allowed, and its result is recorded. A missing or incompatible baseline is `INCONCLUSIVE`, not `pytest.skip`. Outcomes are reported, not blocking, until the full lift and an owner promotion (T05 lists them as informational with owner and expiry). It also decides the tripwire-adjacent debt of contract §5.2: absorb or delete the absolute per-scenario and per-phase ceilings and the `PerfBudget` / `perf_baselines.json` store, and retire `tools/perf/check_perf_regression.py` and `perf_ci.py` (schema §6, F6). | T02b, T05, T07 | `tests/perf/test_perf_regression_baseline.py`, `tests/tools/perf_assertions.py`, `tests/perf/conftest.py`, `tools/perf/`, `docs/engine/performance_contract.md` §5 threshold value, CI selector in `.github/workflows/test.yml` (testing-planner told first) | standard |
| 3 | **PERF-M2-T04** Capacity projection | `tools/perf/capacity_run.py`: 100 warmup and 1000 sampled ticks, N process repetitions, an optional paired base/head mode, p50/p95/p99/max, variance, RSS high-water, and records with `gate.projection = capacity_run`. Variance above the declared limit is `INCONCLUSIVE`. The long-run report (schema F22) maps into the record, and `passed_certification` gives way to `outcome`. No claim per OD-5. | T02b, T05, OD-5, OD-7 | new `tools/perf/capacity_run.py`, **`src/perf/long_run_harness.py`** (F22 fields), tests | standard |
| 4 | **PERF-M2-T08** M1 reruns | Ledger §5 steps 1 to 5 under the canonical variants (T07), written as schema records and labelled provisional. Combat-heavy scenarios (`combat_10_*`, corpus worlds that fight) are labelled `WORK_MODEL_V1`, or wait for V2 after `TCK-20261006-COMBAT-ENGAGEMENT-HOSTILITY-PROJECTION-COST-STEP`. Step 6 (`docs/observability/baselines/*`) is replaced by T03-format records, and `compare-sweep` is pointed at them. Promotion goes through T05's tool. | T03, T05, T07 | `tests/perf/baselines/`, `tests/regression/baseline_5k.json`, `docs/observability/baselines/`, ledger status column | standard |
| 5 | **PERF-M2-T06** P1 publication and conformance map | `performance_contract.md` states the decided thresholds, outcomes and the tripwire/capacity/comparative claims. A machine-readable map (`docs/performance/gate_conformance.yaml`) links each live check to the clause it enforces or to "enforces none", and a test fails on an unmapped `assert_perf_threshold` / `perf_check` call site. The P1 owner approves. | T03, T04, T05, T08 | `docs/engine/performance_contract.md`, `docs/engine/contracts/certification_contract.md` (D-9, D-10 name fixes), new `docs/performance/gate_conformance.yaml`, `tests/docs/` | standard |

Parallelism: T02b and T07 together, then X1 and T05 together, then T03 and T04 together. T02b is the
only ticket every other one consumes, so it ships alone and first. No two tickets in the same
row edit the same file, except `src/perf/profiles.py`: T02b changes the class and T07 adds the
variants, so T07 lands after T02b in one batch, or the two are merged.

### 4. Left out of M2

- `TCK-20261006-PERF-LIVE-CONTROL-TRACE` (P2): the PERF-D1 Live contract. It is not a measurement
  clause, and it needs core files. It stays a separate item for the next core window.
- The P3 todos (`PERF-SCENARIO-MIXED-STATE-SPAWN-COLLISION`, `PERF-BUDGET-OVERRUN-TELEMETRY-SURFACING`,
  `PERF-KERNEL-VALIDATES-FLAGS-AFTER-STARTING-WORKERS`): independent, and they can go in any batch.
  The spawn collision must land before T08 reruns `mixed_200_*`: the `"mixed"` scenario is
  `build_mixed_state` itself (`src/perf/scenarios.py` `SCENARIO_BUILDERS`), and a collided build is
  a different workload.
- Making any soft check blocking: that needs the full lift plus a P1/CI-owner promotion (M4).
- The instruction-count tripwire tool (OD-2): a spike after M2.

## Out of scope

- Producing the M4 baseline matrix.
- Selecting optimizations.
- Lowering thresholds to accommodate known-invalid runs.
- Allowing a local developer-machine sample to become a portable capacity promise.

## Exit criteria

- One P1 authority is selected and published by its owner.
- Every live gate states which contract clauses it enforces and which it does not.
- CI-fast and scheduled evidence use the same identity vocabulary but distinct thresholds/claims.
- Missing mandatory evidence fails or produces an explicit non-claim outcome.
- Baseline comparison rejects incompatible identities.
- Tests cover absent baseline, stale schema, mode/cardinality mismatch, and percentile behavior.
- Tests cover changed-file under-selection, new drift inside a known-debt lane, excessive variance,
  bounded retries, and baseline-update authorization.

## Primary surfaces

- `docs/engine/performance_contract.md`
- `docs/engine/contracts/certification_contract.md`
- `docs/performance/perf_baseline_policy.md`
- `src/perf/regression_gate.py`
- `src/perf/bench_harness.py`
- `tests/perf/test_perf_regression_baseline.py`
- CI workflows selecting performance tests

## References

- `performance_optimization_prerequisite_execution_plan.md` PA-04
- `performance_optimization_conflict_approval_review.md` PERF-D4
- `system_design_terms_and_concepts.md` §§11–13
