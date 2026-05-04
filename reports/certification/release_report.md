# Consolidated Certification Report

**Last Run ID**: `838e4321-75c7-475d-837a-6ac5ae4aba3d`
**Commit SHA**: `5507b2b8d9a38c2ca5274a558307c73b7b4ca2a5`

## Scenario Summary

| Profile | Scenario | Status | Fail Kind | Reason |
| :--- | :--- | :--- | :--- | :--- |
| CRUSH_TEST | IDLE_CLEAN | ❌ | failed_envelope | RAM violation: 80.328125MB > 1MB at tick 1 |
| NORMAL_ONLY | RAM_PRESSURE | ❌ | failed_degradation_sequence | Required mode 'DEGRADED' was never entered during scenario. |

---

## Latest Run Detail

# Certification Report: RAM_PRESSURE
**Commit SHA**: `5507b2b8d9a38c2ca5274a558307c73b7b4ca2a5`
**Status**: ❌ **FAIL**
**Allowed Failure Observed**: `False`

## 1. Certified Execution Context (M10 Scoped Truth)
- **Runtime Profile**: `NORMAL_ONLY`
- **Hardware Class**: `CLASS_B`
- **Scenario**: `RAM_PRESSURE`
- **Seed**: `42`
- **Peak RAM (RSS)**: `81.0 MB`
- **Total CPU Time**: `0.001 sec`

## 2. Resource Conformance Evidence
| Tick | Mode | RAM (MB) | Compute (ms) | Worker % | Queue % |
| :--- | :--- | :--- | :--- | :--- | :--- |
| 1 | NORMAL | 81.0 | 1.0 | 0.00 | 0.00 |

## 3. Semantic Integrity Proof (Milestone D Law)
- **Baseline Hash**: `46341d561ae11e37ccffedd7362ed031e840b9f2424e2399d8c7dcb30060bdf3`
- **Final Hash**: `46341d561ae11e37ccffedd7362ed031e840b9f2424e2399d8c7dcb30060bdf3`
- **Status**: MATCHED

## 4. Conformance Verdict
> [!CAUTION]
> **FAILED_DEGRADATION_SEQUENCE**: Required mode 'DEGRADED' was never entered during scenario.

## Honest Reporting Disclaimer
Performance and safety metrics in this report apply ONLY to the (Profile, Scenario, Hardware Class) bundle defined above. Claims of universal throughput or unbounded scaling are explicitly unsupported by this certification and violate Milestone E project laws.