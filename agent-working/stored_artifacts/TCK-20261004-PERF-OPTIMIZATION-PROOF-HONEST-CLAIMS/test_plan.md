---
status: historical
layer: performance
authority: P2
audience: agent
artifact_type: test_plan
ticket_id: TCK-20261004-PERF-OPTIMIZATION-PROOF-HONEST-CLAIMS
date: 2026-10-04
tags: [performance, benchmarking]
---

# Test Plan: TCK-20261004-PERF-OPTIMIZATION-PROOF-HONEST-CLAIMS

## Proof Plan

| Acceptance criterion | Level | Proof kind | Oracle source | Expected effect | Selected commands |
|---|---|---|---|---|---|
| No numeric fallback for a measured value | unit | static source assertion plus behavior tests | ticket Scope items 1-2 | missing or non-positive values give `not_comparable` | `pytest tests/perf/test_optimization_proof_claims.py` |
| Every scenario is `compared` or `not_comparable`; ratios only for compared | unit | stubbed run | ticket Scope items 1, 5 | statuses and keys as specified | same |
| Fixed claims gone; counts match the JSON | unit | markdown parse against JSON | ticket Scope item 4 | removed phrases absent, counts equal | same |
| Provisional label in opening lines | unit | markdown check | ticket Scope item 4 | label before the Summary heading | same |
| Fast run, no benchmark executed | test | pytest with stubs | ticket acceptance criteria | well under a minute | `pytest tests/perf/test_optimization_proof_claims.py tests/tools/test_test_scope_coverage_static.py tests/static -q` |
| Ledger or doc claims corrected or listed | static | grep | ticket Scope item 8 | none cite the report as proof | `grep -rn optimization_proof docs/` |
| No `reports/` or `src/` change committed | static | diff check | ticket acceptance criteria | none | `git diff --name-only origin/main...HEAD` |

The slow `test_optimization_proof_report.py` was updated but never run; it executes real benchmarks.
