# Consolidated Certification Report

**Last Run ID**: `27c75e21-4396-4903-955a-70be7fc52260`
**Commit SHA**: `6353b6f3cf21673cd7f7232dcf2d766c86692c1d`

## Scenario Summary

| Profile | Scenario | Status | Fail Kind | Reason |
| :--- | :--- | :--- | :--- | :--- |
| QUEST_ARENA_TEST | COMBAT_ARENA_QUESTS | ⚠️ | none | Certification PASS |

---

## Latest Run Detail

# Certification Report: COMBAT_ARENA_QUESTS
**Commit SHA**: `6353b6f3cf21673cd7f7232dcf2d766c86692c1d`
**Status**: ✅ **PASS**
**Allowed Failure Observed**: `False`

## 1. Certified Execution Context (M10 Scoped Truth)
- **Runtime Profile**: `QUEST_ARENA_TEST`
- **Hardware Class**: `CLASS_B`
- **Scenario**: `COMBAT_ARENA_QUESTS`
- **Seed**: `42`
- **Peak RAM (RSS)**: `64.5 MB`
- **Total CPU Time**: `0.005 sec`

## 2. Resource Conformance Evidence
| Tick | Mode | RAM (MB) | Compute (ms) | Worker % | Queue % |
| :--- | :--- | :--- | :--- | :--- | :--- |
| 1 | NORMAL | 64.5 | 3.1 | 1.00 | 0.00 |
| 2 | NORMAL | 64.5 | 0.5 | 0.00 | 0.00 |
| 3 | NORMAL | 64.5 | 0.6 | 0.00 | 0.00 |
| 4 | NORMAL | 64.5 | 0.4 | 0.00 | 0.00 |
| 5 | NORMAL | 64.5 | 0.4 | 0.00 | 0.00 |

## 3. Semantic Integrity Proof (Milestone D Law)
- **Baseline Hash**: `30f2ce35d777938cc545f1af26383bec3f8d58eccb2293de53a7f93f851f31d9`
- **Final Hash**: `30f2ce35d777938cc545f1af26383bec3f8d58eccb2293de53a7f93f851f31d9`
- **Status**: MATCHED

## 4. Conformance Verdict
> [!IMPORTANT]
> This engine is certified to adhere to profile **QUEST_ARENA_TEST** on Hardware Class **CLASS_B** for the given scenario duration.

## Honest Reporting Disclaimer
Performance and safety metrics in this report apply ONLY to the (Profile, Scenario, Hardware Class) bundle defined above. Claims of universal throughput or unbounded scaling are explicitly unsupported by this certification and violate Milestone E project laws.