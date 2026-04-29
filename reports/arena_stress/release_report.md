# Consolidated Certification Report

**Last Run ID**: `6055b0ab-21b9-4da3-b01e-4813e4965246`
**Commit SHA**: `24ca4b4ef067795006e9c32c563f1b13071f3b33`

## Scenario Summary

| Profile | Scenario | Status | Fail Kind | Reason |
| :--- | :--- | :--- | :--- | :--- |
| STRESS_TEST | COMBAT_ARENA_STRESS_50V50 | ⚠️ | none | Certification PASS |

---

## Latest Run Detail

# Certification Report: COMBAT_ARENA_STRESS_50V50
**Commit SHA**: `24ca4b4ef067795006e9c32c563f1b13071f3b33`
**Status**: ✅ **PASS**
**Allowed Failure Observed**: `False`

## 1. Certified Execution Context (M10 Scoped Truth)
- **Runtime Profile**: `STRESS_TEST`
- **Hardware Class**: `CLASS_B`
- **Scenario**: `COMBAT_ARENA_STRESS_50V50`
- **Seed**: `42`
- **Peak RAM (RSS)**: `76.3 MB`
- **Total CPU Time**: `2.229 sec`

## 2. Resource Conformance Evidence
| Tick | Mode | RAM (MB) | Compute (ms) | Worker % | Queue % |
| :--- | :--- | :--- | :--- | :--- | :--- |
| 1 | NORMAL | 70.1 | 14.2 | 0.00 | 0.00 |
| 2 | NORMAL | 70.1 | 13.9 | 0.00 | 0.00 |
| 3 | NORMAL | 70.1 | 9.4 | 0.00 | 0.00 |
| 26 | DEGRADED | 74.2 | 13.0 | 0.00 | 0.00 |
| 27 | CONSTRAINED | 74.2 | 16.7 | 0.00 | 0.00 |
| 28 | CONSTRAINED | 74.2 | 13.9 | 0.00 | 0.00 |
| 47 | DEGRADED | 75.2 | 10.2 | 0.00 | 0.00 |
| 48 | DEGRADED | 75.2 | 14.1 | 0.00 | 0.00 |
| 49 | DEGRADED | 75.2 | 12.3 | 0.00 | 0.00 |
| 50 | DEGRADED | 76.3 | 11.5 | 0.00 | 0.00 |
| ... | ... | ... | ... | ... | ... |

## 3. Semantic Integrity Proof (Milestone D Law)
- **Baseline Hash**: `52070582c29b612978121bf1a1cd67466f07c8c04f05d540fd3ec111d2c9d29d`
- **Final Hash**: `52070582c29b612978121bf1a1cd67466f07c8c04f05d540fd3ec111d2c9d29d`
- **Status**: MATCHED

## 4. Conformance Verdict
> [!IMPORTANT]
> This engine is certified to adhere to profile **STRESS_TEST** on Hardware Class **CLASS_B** for the given scenario duration.

## Honest Reporting Disclaimer
Performance and safety metrics in this report apply ONLY to the (Profile, Scenario, Hardware Class) bundle defined above. Claims of universal throughput or unbounded scaling are explicitly unsupported by this certification and violate Milestone E project laws.