---
content_type: doc
status: historical
layer: misc
authority: P2
audience: agent
tags: [core, import, stabilization]
---

# Consolidated Certification Report

**Last Run ID**: `1fa3a82b-90bd-4ff3-aff0-1ae7428bba9d`
**Commit SHA**: `7f0feb8e7e20336d89dc3b132f02216b515593c8`

## Scenario Summary

| Profile | Scenario | Status | Fail Kind | Reason |
| :--- | :--- | :--- | :--- | :--- |
| NO_RECOVERY | RAM_PRESSURE | ❌ | failed_recovery_timeout | System failed to recover to NORMAL mode within scenario window. |

---

## Latest Run Detail

# Certification Report: RAM_PRESSURE
**Commit SHA**: `7f0feb8e7e20336d89dc3b132f02216b515593c8`
**Status**: ❌ **FAIL**
**Allowed Failure Observed**: `False`

## 1. Certified Execution Context (M10 Scoped Truth)
- **Runtime Profile**: `NO_RECOVERY`
- **Hardware Class**: `CLASS_B`
- **Scenario**: `RAM_PRESSURE`
- **Seed**: `42`
- **Peak RAM (RSS)**: `81.6 MB`
- **Total CPU Time**: `0.031 sec`

## 2. Resource Conformance Evidence
| Tick | Mode | RAM (MB) | Compute (ms) | Worker % | Queue % |
| :--- | :--- | :--- | :--- | :--- | :--- |
| 1 | CONSTRAINED | 81.6 | 2.3 | 0.00 | 0.00 |
| 2 | CONSTRAINED | 81.6 | 4.4 | 0.00 | 0.00 |
| 3 | DEGRADED | 81.6 | 2.7 | 0.00 | 0.00 |
| 4 | DEGRADED | 81.6 | 3.2 | 0.00 | 0.00 |
| 5 | DEGRADED | 81.6 | 3.4 | 0.00 | 0.00 |
| 6 | DEGRADED | 81.6 | 2.1 | 0.00 | 0.00 |
| 7 | DEGRADED | 81.6 | 3.2 | 0.00 | 0.00 |
| 8 | DEGRADED | 81.6 | 3.0 | 0.00 | 0.00 |
| 9 | DEGRADED | 81.6 | 2.8 | 0.00 | 0.00 |
| 10 | DEGRADED | 81.6 | 3.6 | 0.00 | 0.00 |

## 3. Semantic Integrity Proof (Milestone D Law)
- **Baseline Hash**: `67a1522e90dc2d39a019ef892840613d82087b8c165e18f1138539c30b38dc3d`
- **Final Hash**: `67a1522e90dc2d39a019ef892840613d82087b8c165e18f1138539c30b38dc3d`
- **Status**: MATCHED

## 4. Conformance Verdict
> [!CAUTION]
> **FAILED_RECOVERY_TIMEOUT**: System failed to recover to NORMAL mode within scenario window.

## Honest Reporting Disclaimer
Performance and safety metrics in this report apply ONLY to the (Profile, Scenario, Hardware Class) bundle defined above. Claims of universal throughput or unbounded scaling are explicitly unsupported by this certification and violate Milestone E project laws.