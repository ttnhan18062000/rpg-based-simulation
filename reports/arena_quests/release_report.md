# Consolidated Certification Report

**Last Run ID**: `5285987f-9e88-459f-9b75-e00c0255a9e3`
**Commit SHA**: `6cd189a6add2f169d15838f7f4de5598131965e1`

## Scenario Summary

| Profile | Scenario | Status | Fail Kind | Reason |
| :--- | :--- | :--- | :--- | :--- |
| QUEST_ARENA_TEST | COMBAT_ARENA_QUESTS | ⚠️ | none | Certification PASS |

---

## Latest Run Detail

# Certification Report: COMBAT_ARENA_QUESTS
**Commit SHA**: `6cd189a6add2f169d15838f7f4de5598131965e1`
**Status**: ✅ **PASS**
**Allowed Failure Observed**: `False`

## 1. Certified Execution Context (M10 Scoped Truth)
- **Runtime Profile**: `QUEST_ARENA_TEST`
- **Hardware Class**: `CLASS_B`
- **Scenario**: `COMBAT_ARENA_QUESTS`
- **Seed**: `42`
- **Peak RAM (RSS)**: `63.9 MB`
- **Total CPU Time**: `0.018 sec`

## 2. Resource Conformance Evidence
| Tick | Mode | RAM (MB) | Compute (ms) | Worker % | Queue % |
| :--- | :--- | :--- | :--- | :--- | :--- |
| 1 | NORMAL | 63.9 | 12.7 | 1.00 | 0.00 |
| 2 | NORMAL | 63.9 | 1.4 | 0.00 | 0.00 |
| 3 | NORMAL | 63.9 | 1.4 | 0.00 | 0.00 |
| 4 | NORMAL | 63.9 | 0.8 | 0.00 | 0.00 |
| 5 | NORMAL | 63.9 | 1.8 | 0.00 | 0.00 |

## 3. Semantic Integrity Proof (Milestone D Law)
- **Baseline Hash**: `0bd78bb78d9e5feacc661e34cdf54f7aac44ec371d171fbb08ac80064f8901e3`
- **Final Hash**: `0bd78bb78d9e5feacc661e34cdf54f7aac44ec371d171fbb08ac80064f8901e3`
- **Status**: MATCHED

## 4. Conformance Verdict
> [!IMPORTANT]
> This engine is certified to adhere to profile **QUEST_ARENA_TEST** on Hardware Class **CLASS_B** for the given scenario duration.

## Honest Reporting Disclaimer
Performance and safety metrics in this report apply ONLY to the (Profile, Scenario, Hardware Class) bundle defined above. Claims of universal throughput or unbounded scaling are explicitly unsupported by this certification and violate Milestone E project laws.