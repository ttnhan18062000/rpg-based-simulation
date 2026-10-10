---
status: active
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

   The median is no steadier than the mean, so the noise is whole-process variance (host speed between processes), not a few slow ticks. The largest A/A deviation seen is 0.307, recorded as `NOISE_BUDGET = 0.31`. The old `max(5 ms, 1.25 x)` rule fires inside this noise (movement reached 1.25 twice in 14 pairs). The numbers are this VM's, not the CI runner's.
2. **The retirement list in the ticket was partly wrong**: only `tools/gate_checks/test_scope_coverage_static.py` and `tests/tools/test_test_scope_coverage_static.py` referenced the tools (plus the tools' own test). The Makefile, `test_repo_root_allowlist.py` and `perf_guard.py` do not (the allowlist names `perf_baselines.json`, which is the PerfBudget store, not these tools).
3. **`perf-cert-arena` already creates a base worktree** (`/tmp/base-checkout`, for the collect-only diff, failing open). A paired tripwire step can reuse it. The job runs `-m "not slow and not extra_slow"`, so the old slow-marked tripwire test never ran on pull requests; the paired step is the first pull-request tripwire.
4. **PerfBudget store:** `perf_baselines.json` has `entries: {}`; the `perf_budget` fixture is used by two budget tests (`test_phase2_self_model_budget.py`, `test_phase3_adventure_decision_budget.py`), `tools/perf_guard.py`, `make perf-measure` and `tests/codebase/test_repo_root_allowlist.py`. Of 56 `assert_perf_threshold` / `perf_check` call sites in `tests/perf`, `tests/arena` and `tests/certification`, one passes `hard=True`.
5. **I made the same paths-guard mistake twice** (a literal `agent-working` root in a new test). Both times CI or the guard caught it; the guard is now in my pre-push list.

## Not verified
- The paired step in a real CI run (test.yml is held); the tripwire against a real base checkout of a different commit (only A/A and fakes); the thresholds on the CI runner.
