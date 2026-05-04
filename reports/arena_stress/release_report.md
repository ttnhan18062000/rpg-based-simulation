# Consolidated Certification Report

**Last Run ID**: `e7ad15c2-76d5-4fbe-8695-e33c963e31b9`
**Commit SHA**: `5507b2b8d9a38c2ca5274a558307c73b7b4ca2a5`

## Scenario Summary

| Profile | Scenario | Status | Fail Kind | Reason |
| :--- | :--- | :--- | :--- | :--- |
| STRESS_TEST | COMBAT_ARENA_STRESS_50V50 | ✅ | none | Certification PASS |

---

## Latest Run Detail

# Certification Report: COMBAT_ARENA_STRESS_50V50
**Commit SHA**: `5507b2b8d9a38c2ca5274a558307c73b7b4ca2a5`
**Status**: ✅ **PASS**
**Allowed Failure Observed**: `False`

## 1. Certified Execution Context (M10 Scoped Truth)
- **Runtime Profile**: `STRESS_TEST`
- **Hardware Class**: `CLASS_B`
- **Scenario**: `COMBAT_ARENA_STRESS_50V50`
- **Seed**: `42`
- **Peak RAM (RSS)**: `77.0 MB`
- **Total CPU Time**: `5.154 sec`

## 2. Resource Conformance Evidence
| Tick | Mode | RAM (MB) | Compute (ms) | Worker % | Queue % |
| :--- | :--- | :--- | :--- | :--- | :--- |
| 1 | NORMAL | 74.5 | 39.4 | 1.00 | 0.20 |
| 2 | DEGRADED | 74.5 | 136.2 | 1.00 | 0.20 |
| 3 | DEGRADED | 74.5 | 96.0 | 1.00 | 0.20 |
| 26 | DEGRADED | 75.1 | 108.8 | 1.00 | 0.20 |
| 27 | DEGRADED | 75.1 | 95.5 | 1.00 | 0.20 |
| 28 | DEGRADED | 75.1 | 126.3 | 1.00 | 0.20 |
| 47 | DEGRADED | 76.2 | 111.9 | 1.00 | 0.20 |
| 48 | DEGRADED | 76.2 | 77.1 | 1.00 | 0.20 |
| 49 | DEGRADED | 76.2 | 108.7 | 1.00 | 0.20 |
| 50 | DEGRADED | 77.0 | 85.6 | 1.00 | 0.20 |
| ... | ... | ... | ... | ... | ... |

## 3. Semantic Integrity Proof (Milestone D Law)
- **Baseline Hash**: `cd627a3c58fa37f9a2e1a8c575c72a228c0bbb36400b0f38f96a1aa053b19a58`
- **Final Hash**: `cd627a3c58fa37f9a2e1a8c575c72a228c0bbb36400b0f38f96a1aa053b19a58`
- **Status**: MATCHED

## 4. Conformance Verdict
> [!IMPORTANT]
> This engine is certified to adhere to profile **STRESS_TEST** on Hardware Class **CLASS_B** for the given scenario duration.

## Honest Reporting Disclaimer
Performance and safety metrics in this report apply ONLY to the (Profile, Scenario, Hardware Class) bundle defined above. Claims of universal throughput or unbounded scaling are explicitly unsupported by this certification and violate Milestone E project laws.