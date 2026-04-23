# Consolidated Certification Report

**Last Run ID**: `14962a8d-0e86-4a19-9382-ed228c316bb9`
**Commit SHA**: `b020fce3ed22ef20f0748b7f319f8908d7148725`

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
**Commit SHA**: `b020fce3ed22ef20f0748b7f319f8908d7148725`
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
| 5 | CONSTRAINED | 68.5 | 0.3 | 0.00 | 0.00 |
| 10 | DEGRADED | 68.5 | 1.0 | 0.00 | 0.00 |

## 3. Semantic Integrity Proof (Milestone D Law)
- **Baseline Hash**: `e68ff8d510e1e48fd855b77be68625c80419f2ed6792cad4edb6d76c5b911151`
- **Final Hash**: `e68ff8d510e1e48fd855b77be68625c80419f2ed6792cad4edb6d76c5b911151`
- **Status**: MATCHED

## 4. Conformance Verdict
> [!CAUTION]
> **FAILED_RECOVERY_TIMEOUT**: System failed to recover to NORMAL mode within scenario window.

## Honest Reporting Disclaimer
Performance and safety metrics in this report apply ONLY to the (Profile, Scenario, Hardware Class) bundle defined above. Claims of universal throughput or unbounded scaling are explicitly unsupported by this certification and violate Milestone E project laws.