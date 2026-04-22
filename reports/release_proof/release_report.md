# Consolidated Certification Report

**Last Run ID**: `74ff53d9-90fa-4c94-b08c-61f5266d3df6`
**Commit SHA**: `35e0b838014fd1e9e6ba4ff276996d510048b1f4`

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
| NO_RECOVERY | RAM_PRESSURE | ❌ | failed_recovery_timeout | System failed to recover to NORMAL mode within scenario window. |

---

## Latest Run Detail

# Certification Report: RAM_PRESSURE
**Commit SHA**: `35e0b838014fd1e9e6ba4ff276996d510048b1f4`
**Status**: ❌ **FAIL**
**Allowed Failure Observed**: `False`

## 1. Certified Execution Context (M10 Scoped Truth)
- **Runtime Profile**: `NO_RECOVERY`
- **Hardware Class**: `CLASS_B`
- **Scenario**: `RAM_PRESSURE`
- **Seed**: `42`

## 2. Resource Conformance Evidence
| Tick | Mode | RAM (MB) | Compute (ms) | Worker % | Queue % |
| :--- | :--- | :--- | :--- | :--- | :--- |
| 5 | CONSTRAINED | 48.9 | 0.1 | 0.00 | 0.00 |
| 10 | DEGRADED | 48.9 | 0.1 | 0.00 | 0.00 |

## 3. Semantic Integrity Proof (Milestone D Law)
- **Baseline Hash**: `e68ff8d510e1e48fd855b77be68625c80419f2ed6792cad4edb6d76c5b911151`
- **Final Hash**: `e68ff8d510e1e48fd855b77be68625c80419f2ed6792cad4edb6d76c5b911151`
- **Status**: MATCHED

## 4. Conformance Verdict
> [!CAUTION]
> **FAILED_RECOVERY_TIMEOUT**: System failed to recover to NORMAL mode within scenario window.

## Honest Reporting Disclaimer
Performance and safety metrics in this report apply ONLY to the (Profile, Scenario, Hardware Class) bundle defined above. Claims of universal throughput or unbounded scaling are explicitly unsupported by this certification and violate Milestone E project laws.