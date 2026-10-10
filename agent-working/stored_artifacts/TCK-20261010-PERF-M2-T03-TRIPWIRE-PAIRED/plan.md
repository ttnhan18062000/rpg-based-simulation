---
status: historical
layer: performance
authority: P2
audience: agent
artifact_type: plan
ticket_id: TCK-20261010-PERF-M2-T03-TRIPWIRE-PAIRED
date: 2026-10-10
tags: [performance, benchmarking, documentation]
---

# Plan: TCK-20261010-PERF-M2-T03-TRIPWIRE-PAIRED

Pre-planned by perf-planner (M2 epic "Delivery plan"; dispatch 2026-10-10, batch 3, second ticket). Written alongside the work. Two holds from the dispatch: do not edit
`.github/workflows/test.yml` until testing-planner agrees (issue #488), and `performance_contract.md` §5/§5.2 are rpg-owned P1, so they are a proposal in the PR body.

## Order
1. `tools/perf/capacity_run.py`: `RunSpec` gets `gate_tier` and `gate_projection`, so one fresh-process runner serves both projections.
2. `tools/perf/tripwire.py`: declared scenarios, `pair`, `run_scenario` with one diagnostic retry, `report`, `annotations`, `load_baseline`, `compare_with_baseline`, `calibrate`.
3. Rewrite `tests/perf/test_perf_regression_baseline.py` (INCONCLUSIVE, no skip); tests; retire `check_perf_regression.py`, `perf_ci.py` and their references.
4. A/A calibration on this VM; set `TRIPWIRE_THRESHOLDS` from it; docs, INFRA-433, DEV-022.

## Decisions where the ticket left a choice
- **The retry never converts a failure to a pass.** The first non-PASS result is run once more. Same state: reported as reproduced. Different state: `INCONCLUSIVE` "not reproducible". Repeating until one sample passes is forbidden, so there is no loop and `MAX_RETRIES = 1`.
- **Exit code 0 whenever it ran** (OD-8: reported, never blocking); `::warning` annotations carry the outcome; exit 1 only when it could not run.
- **Declared set: `idle_100_local` and `movement_100_local`** (10 warmup, 50 sampled ticks, canonical contract). The combat builder takes team sizes and the corpus worlds need data loading; both are T08's. The names are the committed baseline names, so a promotion lands under them.
- **The nightly lane stays a pytest test** that compares the head with the latest promoted record; with none it reports INCONCLUSIVE and the reason (legacy reference, or no baseline), and runs nothing.
- **Mode check:** the old `_RUNTIME_MODE_HARD_SCENARIOS` (always empty) and its helper are gone; `compare()`'s excursion rule (OD-3) replaces them.
- **Threshold:** set above the measured A/A noise (see investigation.md), pinned by a test. It is provisional and this VM's.
- **Retired tools' stale scope-map entries are removed** (two files outside my domain; owners named in the PR).
- **Done after the owner's decision (relayed by perf-planner, 2026-10-10):** the `performance_contract.md` edit (§3.3, §5, §5.2) with the word "provisional" kept, and T04's §3.3 text so the contract is edited once.
- **Review notes taken (perf-planner):** the diagnostic retry runs head first; a first INCONCLUSIVE from a side that failed to spawn is not retried (`retryable = False`); `calibrate` alternates the order.
- **Not done:** the `test.yml` step (testing-planner, issue #488); deleting the `PerfBudget` store and `perf_guard.py` (`TCK-20261010-PERF-M2-PERFBUDGET-RETIRE`, filed, not started).
