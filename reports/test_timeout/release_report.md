# Consolidated Certification Report

**Last Run ID**: `46374ced-f6f8-47f9-99d4-452b975e3960`
**Commit SHA**: `5507b2b8d9a38c2ca5274a558307c73b7b4ca2a5`

## Scenario Summary

| Profile | Scenario | Status | Fail Kind | Reason |
| :--- | :--- | :--- | :--- | :--- |
| ARENA_TEST | TIMEOUT_TEST | ✅ | none | Certification PASS |

---

## Latest Run Detail

# Certification Report: TIMEOUT_TEST
**Commit SHA**: `5507b2b8d9a38c2ca5274a558307c73b7b4ca2a5`
**Status**: ✅ **PASS**
**Allowed Failure Observed**: `False`

## 1. Certified Execution Context (M10 Scoped Truth)
- **Runtime Profile**: `ARENA_TEST`
- **Hardware Class**: `CLASS_B`
- **Scenario**: `TIMEOUT_TEST`
- **Seed**: `42`
- **Peak RAM (RSS)**: `81.2 MB`
- **Total CPU Time**: `0.002 sec`

## 2. Resource Conformance Evidence
| Tick | Mode | RAM (MB) | Compute (ms) | Worker % | Queue % |
| :--- | :--- | :--- | :--- | :--- | :--- |
| 10 | DEGRADED | 81.2 | 2.5 | 1.00 | 0.00 |

## 3. Semantic Integrity Proof (Milestone D Law)
- **Baseline Hash**: `86d00b1d29607dc7960047338fda216e4bad9d23218e7c419d77967b56233822`
- **Final Hash**: `86d00b1d29607dc7960047338fda216e4bad9d23218e7c419d77967b56233822`
- **Status**: MATCHED

## 4. Conformance Verdict
> [!IMPORTANT]
> This engine is certified to adhere to profile **ARENA_TEST** on Hardware Class **CLASS_B** for the given scenario duration.

## Honest Reporting Disclaimer
Performance and safety metrics in this report apply ONLY to the (Profile, Scenario, Hardware Class) bundle defined above. Claims of universal throughput or unbounded scaling are explicitly unsupported by this certification and violate Milestone E project laws.