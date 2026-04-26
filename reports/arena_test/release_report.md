# Consolidated Certification Report

**Last Run ID**: `d8be2996-a6b2-4276-8b63-f34403fc5697`
**Commit SHA**: `6cd189a6add2f169d15838f7f4de5598131965e1`

## Scenario Summary

| Profile | Scenario | Status | Fail Kind | Reason |
| :--- | :--- | :--- | :--- | :--- |
| ARENA_TEST | COMBAT_ARENA_5V5 | ⚠️ | none | Certification PASS |

---

## Latest Run Detail

# Certification Report: COMBAT_ARENA_5V5
**Commit SHA**: `6cd189a6add2f169d15838f7f4de5598131965e1`
**Status**: ✅ **PASS**
**Allowed Failure Observed**: `False`

## 1. Certified Execution Context (M10 Scoped Truth)
- **Runtime Profile**: `ARENA_TEST`
- **Hardware Class**: `CLASS_B`
- **Scenario**: `COMBAT_ARENA_5V5`
- **Seed**: `42`
- **Peak RAM (RSS)**: `64.5 MB`
- **Total CPU Time**: `0.020 sec`

## 2. Resource Conformance Evidence
| Tick | Mode | RAM (MB) | Compute (ms) | Worker % | Queue % |
| :--- | :--- | :--- | :--- | :--- | :--- |
| 1 | NORMAL | 64.5 | 2.3 | 0.00 | 0.00 |
| 2 | NORMAL | 64.5 | 1.6 | 0.00 | 0.00 |
| 3 | NORMAL | 64.5 | 1.9 | 0.00 | 0.00 |
| 4 | NORMAL | 64.5 | 4.5 | 0.00 | 0.00 |
| 5 | NORMAL | 64.5 | 1.1 | 0.00 | 0.00 |
| 6 | NORMAL | 64.5 | 0.9 | 0.00 | 0.00 |
| 7 | NORMAL | 64.5 | 1.1 | 0.00 | 0.00 |
| 8 | NORMAL | 64.5 | 1.0 | 0.00 | 0.00 |
| 9 | NORMAL | 64.5 | 2.2 | 0.00 | 0.00 |
| 10 | NORMAL | 64.5 | 3.6 | 0.00 | 0.00 |

## 3. Semantic Integrity Proof (Milestone D Law)
- **Baseline Hash**: `bdd156e184bd7c67cb649804aa2c2bbe05175431e7af6ab7c5af84841ddb267d`
- **Final Hash**: `bdd156e184bd7c67cb649804aa2c2bbe05175431e7af6ab7c5af84841ddb267d`
- **Status**: MATCHED

## 4. Conformance Verdict
> [!IMPORTANT]
> This engine is certified to adhere to profile **ARENA_TEST** on Hardware Class **CLASS_B** for the given scenario duration.

## Honest Reporting Disclaimer
Performance and safety metrics in this report apply ONLY to the (Profile, Scenario, Hardware Class) bundle defined above. Claims of universal throughput or unbounded scaling are explicitly unsupported by this certification and violate Milestone E project laws.