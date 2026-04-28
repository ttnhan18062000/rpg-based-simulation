# Consolidated Certification Report

**Last Run ID**: `25fc7c2f-03de-4322-a9a2-5a01e02ffa62`
**Commit SHA**: `6353b6f3cf21673cd7f7232dcf2d766c86692c1d`

## Scenario Summary

| Profile | Scenario | Status | Fail Kind | Reason |
| :--- | :--- | :--- | :--- | :--- |
| REGIONAL_ARENA_TEST | COMBAT_ARENA_REGIONAL | ⚠️ | none | Certification PASS |

---

## Latest Run Detail

# Certification Report: COMBAT_ARENA_REGIONAL
**Commit SHA**: `6353b6f3cf21673cd7f7232dcf2d766c86692c1d`
**Status**: ✅ **PASS**
**Allowed Failure Observed**: `False`

## 1. Certified Execution Context (M10 Scoped Truth)
- **Runtime Profile**: `REGIONAL_ARENA_TEST`
- **Hardware Class**: `CLASS_B`
- **Scenario**: `COMBAT_ARENA_REGIONAL`
- **Seed**: `42`
- **Peak RAM (RSS)**: `64.8 MB`
- **Total CPU Time**: `0.001 sec`

## 2. Resource Conformance Evidence
| Tick | Mode | RAM (MB) | Compute (ms) | Worker % | Queue % |
| :--- | :--- | :--- | :--- | :--- | :--- |
| 1 | NORMAL | 64.8 | 1.2 | 0.00 | 0.00 |

## 3. Semantic Integrity Proof (Milestone D Law)
- **Baseline Hash**: `78ac688e8e082dd66f0dd5da627cd7fdc6b08fa51e21c538e5052259898dd9b6`
- **Final Hash**: `78ac688e8e082dd66f0dd5da627cd7fdc6b08fa51e21c538e5052259898dd9b6`
- **Status**: MATCHED

## 4. Conformance Verdict
> [!IMPORTANT]
> This engine is certified to adhere to profile **REGIONAL_ARENA_TEST** on Hardware Class **CLASS_B** for the given scenario duration.

## Honest Reporting Disclaimer
Performance and safety metrics in this report apply ONLY to the (Profile, Scenario, Hardware Class) bundle defined above. Claims of universal throughput or unbounded scaling are explicitly unsupported by this certification and violate Milestone E project laws.