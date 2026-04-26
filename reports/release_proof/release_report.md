# Consolidated Certification Report

**Last Run ID**: `17ef6c4d-1794-43a9-a28d-1c1474c8f2e2`
**Commit SHA**: `6cd189a6add2f169d15838f7f4de5598131965e1`

## Scenario Summary

| Profile | Scenario | Status | Fail Kind | Reason |
| :--- | :--- | :--- | :--- | :--- |
| CRUSH_TEST | IDLE_CLEAN | ✅ | None | None |
| CRUSH_TEST | INTEG_RESOURCE_LOOP | ✅ | None | None |
| CRUSH_TEST | RAM_PRESSURE | ✅ | None | None |
| NORMAL_ONLY | IDLE_CLEAN | ✅ | None | None |
| NORMAL_ONLY | INTEG_RESOURCE_LOOP | ✅ | None | None |
| NORMAL_ONLY | RAM_PRESSURE | ✅ | None | None |
| NO_RECOVERY | IDLE_CLEAN | ✅ | None | None |
| NO_RECOVERY | INTEG_RESOURCE_LOOP | ✅ | None | None |
| NO_RECOVERY | RAM_PRESSURE | ⚠️ | failed_recovery_timeout | System failed to recover to NORMAL mode within scenario window. |

---

## Latest Run Detail

# Certification Report: RAM_PRESSURE
**Commit SHA**: `6cd189a6add2f169d15838f7f4de5598131965e1`
**Status**: ❌ **FAIL**
**Allowed Failure Observed**: `False`

## 1. Certified Execution Context (M10 Scoped Truth)
- **Runtime Profile**: `NO_RECOVERY`
- **Hardware Class**: `CLASS_B`
- **Scenario**: `RAM_PRESSURE`
- **Seed**: `42`
- **Peak RAM (RSS)**: `142.4 MB`
- **Total CPU Time**: `0.001 sec`

## 2. Resource Conformance Evidence
| Tick | Mode | RAM (MB) | Compute (ms) | Worker % | Queue % |
| :--- | :--- | :--- | :--- | :--- | :--- |
| 5 | CONSTRAINED | 142.4 | 0.5 | 0.00 | 0.00 |
| 10 | DEGRADED | 142.4 | 0.6 | 0.00 | 0.00 |

## 3. Semantic Integrity Proof (Milestone D Law)
- **Baseline Hash**: `fa09d0ba0918226006101020e0bc66d5239f183dd3a008f94f6b8d231d9dcf1f`
- **Final Hash**: `fa09d0ba0918226006101020e0bc66d5239f183dd3a008f94f6b8d231d9dcf1f`
- **Status**: MATCHED

## 4. Conformance Verdict
> [!CAUTION]
> **FAILED_RECOVERY_TIMEOUT**: System failed to recover to NORMAL mode within scenario window.

## Honest Reporting Disclaimer
Performance and safety metrics in this report apply ONLY to the (Profile, Scenario, Hardware Class) bundle defined above. Claims of universal throughput or unbounded scaling are explicitly unsupported by this certification and violate Milestone E project laws.