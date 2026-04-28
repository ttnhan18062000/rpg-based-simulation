# Consolidated Certification Report

**Last Run ID**: `b794ee67-168c-404b-8e6b-e974934e79ca`
**Commit SHA**: `6353b6f3cf21673cd7f7232dcf2d766c86692c1d`

## Scenario Summary

| Profile | Scenario | Status | Fail Kind | Reason |
| :--- | :--- | :--- | :--- | :--- |
| STRESS_TEST | COMBAT_ARENA_STRESS_50V50 | ⚠️ | none | Certification PASS |

---

## Latest Run Detail

# Certification Report: COMBAT_ARENA_STRESS_50V50
**Commit SHA**: `6353b6f3cf21673cd7f7232dcf2d766c86692c1d`
**Status**: ✅ **PASS**
**Allowed Failure Observed**: `False`

## 1. Certified Execution Context (M10 Scoped Truth)
- **Runtime Profile**: `STRESS_TEST`
- **Hardware Class**: `CLASS_B`
- **Scenario**: `COMBAT_ARENA_STRESS_50V50`
- **Seed**: `42`
- **Peak RAM (RSS)**: `75.4 MB`
- **Total CPU Time**: `1.511 sec`

## 2. Resource Conformance Evidence
| Tick | Mode | RAM (MB) | Compute (ms) | Worker % | Queue % |
| :--- | :--- | :--- | :--- | :--- | :--- |
| 1 | NORMAL | 69.6 | 12.6 | 0.00 | 0.00 |
| 2 | NORMAL | 69.6 | 5.6 | 0.00 | 0.00 |
| 3 | NORMAL | 69.6 | 7.4 | 0.00 | 0.00 |
| 26 | NORMAL | 73.5 | 7.9 | 0.00 | 0.00 |
| 27 | NORMAL | 73.5 | 8.4 | 0.00 | 0.00 |
| 28 | NORMAL | 73.5 | 7.8 | 0.00 | 0.00 |
| 47 | NORMAL | 74.5 | 7.5 | 0.00 | 0.00 |
| 48 | NORMAL | 74.5 | 9.1 | 0.00 | 0.00 |
| 49 | NORMAL | 74.5 | 10.8 | 0.00 | 0.00 |
| 50 | NORMAL | 75.4 | 9.7 | 0.00 | 0.00 |
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