# Consolidated Certification Report

**Last Run ID**: `8aa42036-8961-4610-981a-94555093bf68`
**Commit SHA**: `6cd189a6add2f169d15838f7f4de5598131965e1`

## Scenario Summary

| Profile | Scenario | Status | Fail Kind | Reason |
| :--- | :--- | :--- | :--- | :--- |
| STRESS_TEST | COMBAT_ARENA_STRESS_50V50 | ⚠️ | failed_envelope | Tick budget violation: 652.7ms > 600.0ms at tick 21 |

---

## Latest Run Detail

# Certification Report: COMBAT_ARENA_STRESS_50V50
**Commit SHA**: `6cd189a6add2f169d15838f7f4de5598131965e1`
**Status**: ❌ **FAIL**
**Allowed Failure Observed**: `False`

## 1. Certified Execution Context (M10 Scoped Truth)
- **Runtime Profile**: `STRESS_TEST`
- **Hardware Class**: `CLASS_B`
- **Scenario**: `COMBAT_ARENA_STRESS_50V50`
- **Seed**: `42`
- **Peak RAM (RSS)**: `75.1 MB`
- **Total CPU Time**: `2.799 sec`

## 2. Resource Conformance Evidence
| Tick | Mode | RAM (MB) | Compute (ms) | Worker % | Queue % |
| :--- | :--- | :--- | :--- | :--- | :--- |
| 1 | NORMAL | 69.4 | 10.5 | 0.00 | 0.00 |
| 2 | NORMAL | 69.4 | 27.0 | 0.00 | 0.00 |
| 3 | NORMAL | 69.4 | 12.9 | 0.00 | 0.00 |
| 26 | SURVIVAL | 73.6 | 15.8 | 0.00 | 0.00 |
| 27 | SURVIVAL | 73.6 | 14.1 | 0.00 | 0.00 |
| 28 | SURVIVAL | 73.6 | 14.8 | 0.00 | 0.00 |
| 47 | DEGRADED | 74.9 | 17.2 | 0.00 | 0.00 |
| 48 | CONSTRAINED | 74.9 | 14.5 | 0.00 | 0.00 |
| 49 | CONSTRAINED | 74.9 | 20.4 | 0.00 | 0.00 |
| 50 | CONSTRAINED | 75.1 | 12.2 | 0.00 | 0.00 |
| ... | ... | ... | ... | ... | ... |

## 3. Semantic Integrity Proof (Milestone D Law)
- **Baseline Hash**: `82db5b1cc83f18cb20cd5d525b78f903f650a8d80b7a133b0b3f0c4f2da8f965`
- **Final Hash**: `82db5b1cc83f18cb20cd5d525b78f903f650a8d80b7a133b0b3f0c4f2da8f965`
- **Status**: MATCHED

## 4. Conformance Verdict
> [!CAUTION]
> **FAILED_ENVELOPE**: Tick budget violation: 652.7ms > 600.0ms at tick 21

## Honest Reporting Disclaimer
Performance and safety metrics in this report apply ONLY to the (Profile, Scenario, Hardware Class) bundle defined above. Claims of universal throughput or unbounded scaling are explicitly unsupported by this certification and violate Milestone E project laws.