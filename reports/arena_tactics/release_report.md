# Consolidated Certification Report

**Last Run ID**: `5453342b-704e-4da3-b00d-079c8dc11073`
**Commit SHA**: `6cd189a6add2f169d15838f7f4de5598131965e1`

## Scenario Summary

| Profile | Scenario | Status | Fail Kind | Reason |
| :--- | :--- | :--- | :--- | :--- |
| TACTICS_TEST | COMBAT_ARENA_5V5 | ⚠️ | none | Certification PASS |

---

## Latest Run Detail

# Certification Report: COMBAT_ARENA_5V5
**Commit SHA**: `6cd189a6add2f169d15838f7f4de5598131965e1`
**Status**: ✅ **PASS**
**Allowed Failure Observed**: `False`

## 1. Certified Execution Context (M10 Scoped Truth)
- **Runtime Profile**: `TACTICS_TEST`
- **Hardware Class**: `CLASS_B`
- **Scenario**: `COMBAT_ARENA_5V5`
- **Seed**: `42`
- **Peak RAM (RSS)**: `78.7 MB`
- **Total CPU Time**: `0.045 sec`

## 2. Resource Conformance Evidence
| Tick | Mode | RAM (MB) | Compute (ms) | Worker % | Queue % |
| :--- | :--- | :--- | :--- | :--- | :--- |
| 1 | NORMAL | 78.7 | 1.0 | 0.00 | 0.00 |
| 2 | NORMAL | 78.7 | 0.8 | 0.00 | 0.00 |
| 3 | NORMAL | 78.7 | 0.8 | 0.00 | 0.00 |
| 11 | NORMAL | 78.7 | 21.7 | 1.00 | 0.09 |
| 12 | NORMAL | 78.7 | 1.9 | 0.00 | 0.00 |
| 13 | NORMAL | 78.7 | 1.3 | 0.00 | 0.00 |
| 17 | NORMAL | 78.7 | 2.0 | 0.00 | 0.00 |
| 18 | NORMAL | 78.7 | 1.7 | 0.00 | 0.00 |
| 19 | NORMAL | 78.7 | 1.7 | 0.00 | 0.00 |
| 20 | NORMAL | 78.7 | 1.9 | 0.00 | 0.00 |
| ... | ... | ... | ... | ... | ... |

## 3. Semantic Integrity Proof (Milestone D Law)
- **Baseline Hash**: `851c77e3d4a45fb3c5f95a5c1277c8e9ba1701ace92d459147a47dfc09da1936`
- **Final Hash**: `851c77e3d4a45fb3c5f95a5c1277c8e9ba1701ace92d459147a47dfc09da1936`
- **Status**: MATCHED

## 4. Conformance Verdict
> [!IMPORTANT]
> This engine is certified to adhere to profile **TACTICS_TEST** on Hardware Class **CLASS_B** for the given scenario duration.

## Honest Reporting Disclaimer
Performance and safety metrics in this report apply ONLY to the (Profile, Scenario, Hardware Class) bundle defined above. Claims of universal throughput or unbounded scaling are explicitly unsupported by this certification and violate Milestone E project laws.