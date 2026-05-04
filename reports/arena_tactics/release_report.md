# Consolidated Certification Report

**Last Run ID**: `e97edda7-3323-464a-a63b-e233b42668d5`
**Commit SHA**: `5507b2b8d9a38c2ca5274a558307c73b7b4ca2a5`

## Scenario Summary

| Profile | Scenario | Status | Fail Kind | Reason |
| :--- | :--- | :--- | :--- | :--- |
| TACTICS_TEST | COMBAT_ARENA_5V5 | ✅ | none | Certification PASS |

---

## Latest Run Detail

# Certification Report: COMBAT_ARENA_5V5
**Commit SHA**: `5507b2b8d9a38c2ca5274a558307c73b7b4ca2a5`
**Status**: ✅ **PASS**
**Allowed Failure Observed**: `False`

## 1. Certified Execution Context (M10 Scoped Truth)
- **Runtime Profile**: `TACTICS_TEST`
- **Hardware Class**: `CLASS_B`
- **Scenario**: `COMBAT_ARENA_5V5`
- **Seed**: `42`
- **Peak RAM (RSS)**: `83.8 MB`
- **Total CPU Time**: `0.268 sec`

## 2. Resource Conformance Evidence
| Tick | Mode | RAM (MB) | Compute (ms) | Worker % | Queue % |
| :--- | :--- | :--- | :--- | :--- | :--- |
| 1 | NORMAL | 83.7 | 10.7 | 1.00 | 0.09 |
| 2 | NORMAL | 83.7 | 14.0 | 1.00 | 0.09 |
| 3 | NORMAL | 83.7 | 17.3 | 1.00 | 0.09 |
| 11 | NORMAL | 83.7 | 13.8 | 1.00 | 0.09 |
| 12 | NORMAL | 83.7 | 14.4 | 1.00 | 0.09 |
| 13 | NORMAL | 83.7 | 10.8 | 1.00 | 0.09 |
| 17 | NORMAL | 83.7 | 8.8 | 1.00 | 0.09 |
| 18 | NORMAL | 83.7 | 11.6 | 1.00 | 0.09 |
| 19 | NORMAL | 83.7 | 11.6 | 1.00 | 0.09 |
| 20 | NORMAL | 83.8 | 12.2 | 1.00 | 0.09 |
| ... | ... | ... | ... | ... | ... |

## 3. Semantic Integrity Proof (Milestone D Law)
- **Baseline Hash**: `a0da9525da468e44ae6b1e70ff551752e07e997ddce67cf2f734cd131002748b`
- **Final Hash**: `a0da9525da468e44ae6b1e70ff551752e07e997ddce67cf2f734cd131002748b`
- **Status**: MATCHED

## 4. Conformance Verdict
> [!IMPORTANT]
> This engine is certified to adhere to profile **TACTICS_TEST** on Hardware Class **CLASS_B** for the given scenario duration.

## Honest Reporting Disclaimer
Performance and safety metrics in this report apply ONLY to the (Profile, Scenario, Hardware Class) bundle defined above. Claims of universal throughput or unbounded scaling are explicitly unsupported by this certification and violate Milestone E project laws.