# Consolidated Certification Report

**Last Run ID**: `eb0b5a1d-562a-4ddd-a6d4-02fe5864989b`
**Commit SHA**: `6353b6f3cf21673cd7f7232dcf2d766c86692c1d`

## Scenario Summary

| Profile | Scenario | Status | Fail Kind | Reason |
| :--- | :--- | :--- | :--- | :--- |
| TACTICS_TEST | COMBAT_ARENA_5V5 | ⚠️ | none | Certification PASS |

---

## Latest Run Detail

# Certification Report: COMBAT_ARENA_5V5
**Commit SHA**: `6353b6f3cf21673cd7f7232dcf2d766c86692c1d`
**Status**: ✅ **PASS**
**Allowed Failure Observed**: `False`

## 1. Certified Execution Context (M10 Scoped Truth)
- **Runtime Profile**: `TACTICS_TEST`
- **Hardware Class**: `CLASS_B`
- **Scenario**: `COMBAT_ARENA_5V5`
- **Seed**: `42`
- **Peak RAM (RSS)**: `79.4 MB`
- **Total CPU Time**: `0.057 sec`

## 2. Resource Conformance Evidence
| Tick | Mode | RAM (MB) | Compute (ms) | Worker % | Queue % |
| :--- | :--- | :--- | :--- | :--- | :--- |
| 1 | NORMAL | 79.4 | 2.0 | 0.00 | 0.00 |
| 2 | NORMAL | 79.4 | 2.3 | 0.00 | 0.00 |
| 3 | NORMAL | 79.4 | 1.7 | 0.00 | 0.00 |
| 11 | NORMAL | 79.4 | 17.9 | 1.00 | 0.09 |
| 12 | NORMAL | 79.4 | 2.5 | 0.00 | 0.00 |
| 13 | NORMAL | 79.4 | 2.3 | 0.00 | 0.00 |
| 17 | NORMAL | 79.4 | 2.2 | 0.00 | 0.00 |
| 18 | NORMAL | 79.4 | 2.4 | 0.00 | 0.00 |
| 19 | NORMAL | 79.4 | 1.1 | 0.00 | 0.00 |
| 20 | NORMAL | 79.4 | 2.9 | 0.00 | 0.00 |
| ... | ... | ... | ... | ... | ... |

## 3. Semantic Integrity Proof (Milestone D Law)
- **Baseline Hash**: `752d9092d6cd8a263b2c02dba89285070bee2a7c1ca1a86c25e889bc091a7ccb`
- **Final Hash**: `752d9092d6cd8a263b2c02dba89285070bee2a7c1ca1a86c25e889bc091a7ccb`
- **Status**: MATCHED

## 4. Conformance Verdict
> [!IMPORTANT]
> This engine is certified to adhere to profile **TACTICS_TEST** on Hardware Class **CLASS_B** for the given scenario duration.

## Honest Reporting Disclaimer
Performance and safety metrics in this report apply ONLY to the (Profile, Scenario, Hardware Class) bundle defined above. Claims of universal throughput or unbounded scaling are explicitly unsupported by this certification and violate Milestone E project laws.