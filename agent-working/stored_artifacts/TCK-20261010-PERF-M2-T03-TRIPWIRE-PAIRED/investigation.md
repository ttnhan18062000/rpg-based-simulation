---
status: historical
layer: performance
authority: P2
audience: agent
artifact_type: investigation
ticket_id: TCK-20261010-PERF-M2-T03-TRIPWIRE-PAIRED
date: 2026-10-10
tags: [performance, benchmarking, documentation]
---

# Investigation: TCK-20261010-PERF-M2-T03-TRIPWIRE-PAIRED

Search order: `search_docs`, then targeted reads and `grep` for references.

## Findings
1. **Noise.** A/A runs (the same checkout as base and as head, each in a fresh process; `tripwire.py calibrate`; 6-vCPU VM, `class_b`, 2026-10-10), head/base ratio of 50-tick average latency:

   | Run | Scenario | Metric | Pairs | Largest deviation | Ratios |
   |---|---|---|---|---|---|
   | 1 | idle_100_local | avg | 6 | 0.156 | 1.008 0.845 1.006 0.889 0.969 1.014 |
   | 1 | movement_100_local | avg | 6 | **0.307** | 0.951 1.222 0.693 1.250 0.974 0.907 |
   | 2 | idle_100_local | avg | 8 | 0.237 | 1.002 1.142 1.050 1.237 0.982 1.020 0.981 0.955 |
   | 2 | movement_100_local | avg | 8 | 0.233 | 0.871 1.062 1.030 0.948 0.791 1.231 0.799 0.767 |
   | 2 | idle_100_local | p50 | 8 | 0.240 | 0.991 1.179 1.025 1.240 1.003 1.008 0.976 0.986 |
   | 2 | movement_100_local | p50 | 8 | 0.252 | 0.836 1.031 1.105 0.979 0.772 1.252 0.814 0.772 |

   | 3 (order alternated, after perf-planner's note) | idle_100_local | avg | 8 | **0.352** | 1.074 0.971 0.919 1.352 0.936 0.822 0.924 0.817 |
   | 3 | movement_100_local | avg | 8 | 0.315 | 1.264 1.030 1.315 1.134 0.985 0.938 1.033 0.969 |
   | 3 | idle_100_local | p50 | 8 | 0.283 | 1.022 0.974 0.948 1.283 0.946 0.816 0.904 0.809 |
   | 3 | movement_100_local | p50 | 8 | **0.397** | 1.256 1.017 1.397 1.297 0.971 0.961 0.948 0.976 |

   The median is no steadier than the mean, so the noise is whole-process variance (host speed between processes), not a few slow ticks. Over all three runs (22 pairs per scenario, 44 in all) the largest A/A deviation of the metric the tripwire uses (average) is **0.352**, so `NOISE_BUDGET = 0.35`. This **supersedes the 0.31 from the first two runs (28 pairs)**: the first numbers understated the noise, and the owner approved the 1.40 rule on 2026-10-10 against 0.31. 1.40 still clears the worst average pair (1.352), but the margin is 0.05 and the worst movement median pair reached 1.397. The old `max(5 ms, 1.25 x)` rule fires inside this noise. The numbers are this VM's, not the CI runner's.
   **Order effect (perf-planner's note):** run 3 alternated which run goes first. Mean head/base ratio, base first against head first: idle 0.963 / 0.991, movement 1.149 / 1.018 (4 pairs each). Movement differs by 0.13, but the pair-to-pair spread is about 0.15, so 8 pairs show no conclusive order bias. The retry runs head first and `calibrate` alternates, so a bias would average out of the calibration and could not repeat in a retry.
2. **The retirement list in the ticket was partly wrong**: only `tools/gate_checks/test_scope_coverage_static.py` and `tests/tools/test_test_scope_coverage_static.py` referenced the tools (plus the tools' own test). The Makefile, `test_repo_root_allowlist.py` and `perf_guard.py` do not (the allowlist names `perf_baselines.json`, which is the PerfBudget store, not these tools).
3. **`perf-cert-arena` already creates a base worktree** (`/tmp/base-checkout`, for the collect-only diff, failing open). A paired tripwire step can reuse it. The job runs `-m "not slow and not extra_slow"`, so the old slow-marked tripwire test never ran on pull requests; the paired step is the first pull-request tripwire.
4. **PerfBudget store:** `perf_baselines.json` has `entries: {}`; the `perf_budget` fixture is used by two budget tests (`test_phase2_self_model_budget.py`, `test_phase3_adventure_decision_budget.py`), `tools/perf_guard.py`, `make perf-measure` and `tests/codebase/test_repo_root_allowlist.py`. Of 56 `assert_perf_threshold` / `perf_check` call sites in `tests/perf`, `tests/arena` and `tests/certification`, one passes `hard=True`.
5. **I made the same paths-guard mistake twice** (a literal `agent-working` root in a new test). Both times CI or the guard caught it; the guard is now in my pre-push list.

## Not verified
- The paired step in a real CI run (test.yml is held); the tripwire against a real base checkout of a different commit (only A/A and fakes); the thresholds on the CI runner.
