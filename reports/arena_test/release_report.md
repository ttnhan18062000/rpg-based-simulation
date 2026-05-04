# Consolidated Certification Report

**Last Run ID**: `3cb80636-742e-44a7-b713-130182ec5b77`
**Commit SHA**: `5507b2b8d9a38c2ca5274a558307c73b7b4ca2a5`

## Scenario Summary

| Profile | Scenario | Status | Fail Kind | Reason |
| :--- | :--- | :--- | :--- | :--- |
| ARENA_TEST | COMBAT_ARENA_5V5 | ✅ | none | Certification PASS |

---

## Latest Run Detail

# Certification Report: COMBAT_ARENA_5V5
**Commit SHA**: `5507b2b8d9a38c2ca5274a558307c73b7b4ca2a5`
**Status**: ✅ **PASS**
**Allowed Failure Observed**: `False`

## 1. Certified Execution Context (M10 Scoped Truth)
- **Runtime Profile**: `ARENA_TEST`
- **Hardware Class**: `CLASS_B`
- **Scenario**: `COMBAT_ARENA_5V5`
- **Seed**: `42`
- **Peak RAM (RSS)**: `69.0 MB`
- **Total CPU Time**: `0.159 sec`

## 2. Resource Conformance Evidence
| Tick | Mode | RAM (MB) | Compute (ms) | Worker % | Queue % |
| :--- | :--- | :--- | :--- | :--- | :--- |
| 1 | NORMAL | 68.7 | 13.0 | 1.00 | 0.09 |
| 2 | NORMAL | 68.7 | 20.6 | 1.00 | 0.09 |
| 3 | NORMAL | 68.7 | 24.3 | 1.00 | 0.09 |
| 4 | NORMAL | 68.7 | 13.2 | 1.00 | 0.09 |
| 5 | NORMAL | 68.7 | 10.7 | 1.00 | 0.09 |
| 6 | NORMAL | 68.7 | 15.4 | 1.00 | 0.09 |
| 7 | NORMAL | 68.7 | 14.2 | 1.00 | 0.09 |
| 8 | NORMAL | 68.7 | 17.9 | 1.00 | 0.09 |
| 9 | NORMAL | 68.7 | 13.2 | 1.00 | 0.09 |
| 10 | NORMAL | 69.0 | 16.3 | 1.00 | 0.09 |

## 3. Semantic Integrity Proof (Milestone D Law)
- **Baseline Hash**: `59ae289a8aadc791b118cc8725fd5b44ec253b3932785f9f9bd5fb466601e8ea`
- **Final Hash**: `59ae289a8aadc791b118cc8725fd5b44ec253b3932785f9f9bd5fb466601e8ea`
- **Status**: MATCHED

## 4. Conformance Verdict
> [!IMPORTANT]
> This engine is certified to adhere to profile **ARENA_TEST** on Hardware Class **CLASS_B** for the given scenario duration.

## Honest Reporting Disclaimer
Performance and safety metrics in this report apply ONLY to the (Profile, Scenario, Hardware Class) bundle defined above. Claims of universal throughput or unbounded scaling are explicitly unsupported by this certification and violate Milestone E project laws.