# Consolidated Certification Report

**Last Run ID**: `9a2f491b-8e1b-42b6-a4b0-d1b2f74b68b9`
**Commit SHA**: `24ca4b4ef067795006e9c32c563f1b13071f3b33`

## Scenario Summary

| Profile | Scenario | Status | Fail Kind | Reason |
| :--- | :--- | :--- | :--- | :--- |
| CONQUEST_ARENA_TEST | COMBAT_ARENA_REGIONAL | ⚠️ | none | Certification PASS |

---

## Latest Run Detail

# Certification Report: COMBAT_ARENA_REGIONAL
**Commit SHA**: `24ca4b4ef067795006e9c32c563f1b13071f3b33`
**Status**: ✅ **PASS**
**Allowed Failure Observed**: `False`

## 1. Certified Execution Context (M10 Scoped Truth)
- **Runtime Profile**: `CONQUEST_ARENA_TEST`
- **Hardware Class**: `CLASS_B`
- **Scenario**: `COMBAT_ARENA_REGIONAL`
- **Seed**: `42`
- **Peak RAM (RSS)**: `68.0 MB`
- **Total CPU Time**: `0.006 sec`

## 2. Resource Conformance Evidence
| Tick | Mode | RAM (MB) | Compute (ms) | Worker % | Queue % |
| :--- | :--- | :--- | :--- | :--- | :--- |
| 1 | NORMAL | 68.0 | 6.3 | 1.00 | 0.00 |

## 3. Semantic Integrity Proof (Milestone D Law)
- **Baseline Hash**: `564fc868c932d77318f809cf26596651af2ad44b57220dd3051d4872d768370d`
- **Final Hash**: `564fc868c932d77318f809cf26596651af2ad44b57220dd3051d4872d768370d`
- **Status**: MATCHED

## 4. Conformance Verdict
> [!IMPORTANT]
> This engine is certified to adhere to profile **CONQUEST_ARENA_TEST** on Hardware Class **CLASS_B** for the given scenario duration.

## Honest Reporting Disclaimer
Performance and safety metrics in this report apply ONLY to the (Profile, Scenario, Hardware Class) bundle defined above. Claims of universal throughput or unbounded scaling are explicitly unsupported by this certification and violate Milestone E project laws.