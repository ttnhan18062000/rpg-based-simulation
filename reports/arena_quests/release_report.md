# Consolidated Certification Report

**Last Run ID**: `fb4ac032-e042-49e4-ae06-bb622aa4119c`
**Commit SHA**: `24ca4b4ef067795006e9c32c563f1b13071f3b33`

## Scenario Summary

| Profile | Scenario | Status | Fail Kind | Reason |
| :--- | :--- | :--- | :--- | :--- |
| QUEST_ARENA_TEST | COMBAT_ARENA_QUESTS | ⚠️ | none | Certification PASS |

---

## Latest Run Detail

# Certification Report: COMBAT_ARENA_QUESTS
**Commit SHA**: `24ca4b4ef067795006e9c32c563f1b13071f3b33`
**Status**: ✅ **PASS**
**Allowed Failure Observed**: `False`

## 1. Certified Execution Context (M10 Scoped Truth)
- **Runtime Profile**: `QUEST_ARENA_TEST`
- **Hardware Class**: `CLASS_B`
- **Scenario**: `COMBAT_ARENA_QUESTS`
- **Seed**: `42`
- **Peak RAM (RSS)**: `67.9 MB`
- **Total CPU Time**: `0.014 sec`

## 2. Resource Conformance Evidence
| Tick | Mode | RAM (MB) | Compute (ms) | Worker % | Queue % |
| :--- | :--- | :--- | :--- | :--- | :--- |
| 1 | NORMAL | 67.9 | 9.8 | 1.00 | 0.00 |
| 2 | NORMAL | 67.9 | 1.0 | 0.00 | 0.00 |
| 3 | NORMAL | 67.9 | 1.0 | 0.00 | 0.00 |
| 4 | NORMAL | 67.9 | 1.3 | 0.00 | 0.00 |
| 5 | NORMAL | 67.9 | 1.1 | 0.00 | 0.00 |

## 3. Semantic Integrity Proof (Milestone D Law)
- **Baseline Hash**: `4d7fec2e58656b793b2441b8641f818806827c0dbe3415596db29c2c8fd9c157`
- **Final Hash**: `4d7fec2e58656b793b2441b8641f818806827c0dbe3415596db29c2c8fd9c157`
- **Status**: MATCHED

## 4. Conformance Verdict
> [!IMPORTANT]
> This engine is certified to adhere to profile **QUEST_ARENA_TEST** on Hardware Class **CLASS_B** for the given scenario duration.

## Honest Reporting Disclaimer
Performance and safety metrics in this report apply ONLY to the (Profile, Scenario, Hardware Class) bundle defined above. Claims of universal throughput or unbounded scaling are explicitly unsupported by this certification and violate Milestone E project laws.