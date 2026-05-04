# Consolidated Certification Report

**Last Run ID**: `fc1fd7cc-adea-4292-a241-25df4106dc45`
**Commit SHA**: `5507b2b8d9a38c2ca5274a558307c73b7b4ca2a5`

## Scenario Summary

| Profile | Scenario | Status | Fail Kind | Reason |
| :--- | :--- | :--- | :--- | :--- |
| REGIONAL_ARENA_TEST | COMBAT_ARENA_REGIONAL | ✅ | none | Certification PASS |

---

## Latest Run Detail

# Certification Report: COMBAT_ARENA_REGIONAL
**Commit SHA**: `5507b2b8d9a38c2ca5274a558307c73b7b4ca2a5`
**Status**: ✅ **PASS**
**Allowed Failure Observed**: `False`

## 1. Certified Execution Context (M10 Scoped Truth)
- **Runtime Profile**: `REGIONAL_ARENA_TEST`
- **Hardware Class**: `CLASS_B`
- **Scenario**: `COMBAT_ARENA_REGIONAL`
- **Seed**: `42`
- **Peak RAM (RSS)**: `68.2 MB`
- **Total CPU Time**: `0.004 sec`

## 2. Resource Conformance Evidence
| Tick | Mode | RAM (MB) | Compute (ms) | Worker % | Queue % |
| :--- | :--- | :--- | :--- | :--- | :--- |
| 1 | NORMAL | 68.2 | 3.7 | 0.00 | 0.00 |

## 3. Semantic Integrity Proof (Milestone D Law)
- **Baseline Hash**: `888dfd4d9be0e4df8c3aea2a53736f161e1da770dd214629c818127f684f012c`
- **Final Hash**: `888dfd4d9be0e4df8c3aea2a53736f161e1da770dd214629c818127f684f012c`
- **Status**: MATCHED

## 4. Conformance Verdict
> [!IMPORTANT]
> This engine is certified to adhere to profile **REGIONAL_ARENA_TEST** on Hardware Class **CLASS_B** for the given scenario duration.

## Honest Reporting Disclaimer
Performance and safety metrics in this report apply ONLY to the (Profile, Scenario, Hardware Class) bundle defined above. Claims of universal throughput or unbounded scaling are explicitly unsupported by this certification and violate Milestone E project laws.