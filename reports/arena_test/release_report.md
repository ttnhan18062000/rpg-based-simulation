# Consolidated Certification Report

**Last Run ID**: `b27c8794-7285-42d7-9e21-bfce96bbb69f`
**Commit SHA**: `6353b6f3cf21673cd7f7232dcf2d766c86692c1d`

## Scenario Summary

| Profile | Scenario | Status | Fail Kind | Reason |
| :--- | :--- | :--- | :--- | :--- |
| ARENA_TEST | COMBAT_ARENA_5V5 | ⚠️ | none | Certification PASS |

---

## Latest Run Detail

# Certification Report: COMBAT_ARENA_5V5
**Commit SHA**: `6353b6f3cf21673cd7f7232dcf2d766c86692c1d`
**Status**: ✅ **PASS**
**Allowed Failure Observed**: `False`

## 1. Certified Execution Context (M10 Scoped Truth)
- **Runtime Profile**: `ARENA_TEST`
- **Hardware Class**: `CLASS_B`
- **Scenario**: `COMBAT_ARENA_5V5`
- **Seed**: `42`
- **Peak RAM (RSS)**: `65.1 MB`
- **Total CPU Time**: `0.013 sec`

## 2. Resource Conformance Evidence
| Tick | Mode | RAM (MB) | Compute (ms) | Worker % | Queue % |
| :--- | :--- | :--- | :--- | :--- | :--- |
| 1 | NORMAL | 65.0 | 1.0 | 0.00 | 0.00 |
| 2 | NORMAL | 65.0 | 1.6 | 0.00 | 0.00 |
| 3 | NORMAL | 65.0 | 1.2 | 0.00 | 0.00 |
| 4 | NORMAL | 65.0 | 0.8 | 0.00 | 0.00 |
| 5 | NORMAL | 65.0 | 1.3 | 0.00 | 0.00 |
| 6 | NORMAL | 65.0 | 2.2 | 0.00 | 0.00 |
| 7 | NORMAL | 65.0 | 1.6 | 0.00 | 0.00 |
| 8 | NORMAL | 65.0 | 0.9 | 0.00 | 0.00 |
| 9 | NORMAL | 65.0 | 0.9 | 0.00 | 0.00 |
| 10 | NORMAL | 65.1 | 1.0 | 0.00 | 0.00 |

## 3. Semantic Integrity Proof (Milestone D Law)
- **Baseline Hash**: `17678c3f95fd7c6c7e11443248253d152ee31f9a86f42d0943c370dfdececa03`
- **Final Hash**: `17678c3f95fd7c6c7e11443248253d152ee31f9a86f42d0943c370dfdececa03`
- **Status**: MATCHED

## 4. Conformance Verdict
> [!IMPORTANT]
> This engine is certified to adhere to profile **ARENA_TEST** on Hardware Class **CLASS_B** for the given scenario duration.

## Honest Reporting Disclaimer
Performance and safety metrics in this report apply ONLY to the (Profile, Scenario, Hardware Class) bundle defined above. Claims of universal throughput or unbounded scaling are explicitly unsupported by this certification and violate Milestone E project laws.