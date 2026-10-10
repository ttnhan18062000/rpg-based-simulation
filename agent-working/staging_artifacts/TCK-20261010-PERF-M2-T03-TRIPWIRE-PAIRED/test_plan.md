---
status: active
layer: performance
authority: P2
audience: agent
artifact_type: test_plan
ticket_id: TCK-20261010-PERF-M2-T03-TRIPWIRE-PAIRED
date: 2026-10-10
tags: [performance, benchmarking, documentation]
---

# Test plan: TCK-20261010-PERF-M2-T03-TRIPWIRE-PAIRED

`tests/unit/perf/test_tripwire.py` (19; the one real fresh-process test is `slow`) and `tests/perf/test_perf_regression_baseline.py` (reports INCONCLUSIVE for the legacy references).

## Proof Plan

| Criterion | Level | Proof kind | Oracle source | Expected effect | Selected commands |
|---|---|---|---|---|---|
| No `pytest.skip`; missing or incompatible baseline is INCONCLUSIVE naming the field | unit | behaviour | the T03 acceptance criteria | missing: named reason; legacy: "no recorded identity"; `percentile_method` or `signal_contract` mismatch names the field | `pytest tests/unit/perf/test_tripwire.py` |
| Base and head each in their own process over a declared list, through `compare()` | unit + one real run | behaviour | OD-2 | spawn once per side under its own root; a real A/A run writes a report | same, `-m slow` |
| REGRESSION over both thresholds, PASS inside the noise budget | unit | behaviour | `compare()` semantics (schema section 4) | +100% regresses; +30% (the observed noise) passes; a delta under the 5 ms floor passes | same |
| At most one retry; both outcomes reported | unit | behaviour | the T03 acceptance criteria | at most 4 spawns for a persistent regression; a disagreeing retry is INCONCLUSIVE, never a pass | same |
| Non-PASS does not fail the job | unit | behaviour | OD-8 | exit 0, `blocking: false`, a `::warning` annotation | same |
| Retired tools gone, no stale references | unit + guards | check | the T03 acceptance criteria | files absent; scope-map tests and repo-root allowlist test pass | `pytest tests/tools/test_test_scope_coverage_static.py tests/codebase/test_repo_root_allowlist.py` |
| Threshold clears the measured noise | unit | check | the calibration in `investigation.md` | `relative > NOISE_BUDGET` | `pytest tests/unit/perf/test_tripwire.py` |
| Contract values stated in `performance_contract.md` | review | document | owner approval | **not done here** | n/a |

Not proven: the contract edit; the tripwire in real CI; the thresholds on the CI runner.
