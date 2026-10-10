---
status: historical
layer: performance
authority: P2
audience: agent
artifact_type: plan
ticket_id: TCK-20261010-PERF-M2-T04-CAPACITY-RUN
date: 2026-10-10
tags: [performance, benchmarking, documentation]
---

# Plan: TCK-20261010-PERF-M2-T04-CAPACITY-RUN

Pre-planned by perf-planner (M2 epic "Delivery plan"; dispatch 2026-10-10, batch 3). Written at close. Lift: of `src/`, only `long_run_harness.py`,
`bench_harness.py`, `benchmark_record.py`.

## Order
1. `benchmark_record.py`: optional `identity.runner` (schema 1.1), unique exclusive-create samples files, `latency_stats`, `default_samples_dir`.
2. `long_run_harness.py`: nearest-rank, `outcome` for `passed_certification`, `to_record`; net-zero growth of `execute_run` (helpers extracted).
3. `tools/perf/capacity_run.py`; tests; docs; INFRA-432.
4. A real run found the 100-tick window bug in `BenchHarness`; fixed in the same ticket (DEV-021).

## Decisions where the ticket left a choice
- **Outcome of an unpaired run is never PASS.** `INCONCLUSIVE` (dirty tree, excursion, crash, one repetition, CV above the limit) or `NOT_APPLICABLE`;
  a PASS would read as a capacity claim. Exit code 0 means "ran and reported": INCONCLUSIVE and REGRESSION are reported, never blocking.
- **Variance** is the coefficient of variation of avg tick latency across repetitions; limit 0.10 (declared constant, `--cv-limit`). One repetition is INCONCLUSIVE.
- **`runner.controlled` is a new optional section, so schema 1.1** (an additive MINOR change by the schema's own rule). `runner.name` (the host) and
  `controlled` are blocking.
- **One record per repetition**, plus `summary.json`; each record carries the run's outcome.
- **Paired mode takes two checkouts** (`--base ROOT --head ROOT`); each repetition is a fresh subprocess with `CAPACITY_RUN_ROOT` and `cwd` set to that checkout, so each side
  measures its own `src/`. A base without `benchmark_record.py` is INCONCLUSIVE.
- **The long-run record is a different projection** (`gate.projection = long_run_stability`): it times the tick plus the read-model update, so it is never compared with a `BenchHarness` capacity run.
- **`docs/engine/performance_contract.md` §3.3 is not edited** (rpg-owned P1, my role card routes `docs/engine/**` to rpg-planner): the proposed text is in the PR body.
- **Samples:** unique name plus exclusive create (so a stale sha256 is impossible); `PERF_SAMPLES_DIR` redirects them, and both perf test directories set it.
