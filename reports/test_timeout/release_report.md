# Consolidated Certification Report

**Last Run ID**: `fcf81ce3-1464-4495-8364-c1964875b4da`
**Commit SHA**: `20d6a1ef5bb632e343cbfaa8cb47d5cd8a5d5f66`

## Scenario Summary

| Profile | Scenario | Status | Fail Kind | Reason |
| :--- | :--- | :--- | :--- | :--- |
| ARENA_TEST | TIMEOUT_TEST | ⚠️ | none | Certification PASS |

---

## Latest Run Detail

# Certification Report: TIMEOUT_TEST
**Commit SHA**: `20d6a1ef5bb632e343cbfaa8cb47d5cd8a5d5f66`
**Status**: ✅ **PASS**
**Allowed Failure Observed**: `False`

## 1. Certified Execution Context (M10 Scoped Truth)
- **Runtime Profile**: `ARENA_TEST`
- **Hardware Class**: `CLASS_B`
- **Scenario**: `TIMEOUT_TEST`
- **Seed**: `42`
- **Peak RAM (RSS)**: `53.0 MB`
- **Total CPU Time**: `0.001 sec`

## 2. Resource Conformance Evidence
| Tick | Mode | RAM (MB) | Compute (ms) | Worker % | Queue % |
| :--- | :--- | :--- | :--- | :--- | :--- |
| 10 | DEGRADED | 53.0 | 1.1 | 1.00 | 0.00 |

## 3. Semantic Integrity Proof (Milestone D Law)
- **Baseline Hash**: `8c4271a1b6e7347c85afe47545edb178c0ce0d22272cade88949647fb8d8a55d`
- **Final Hash**: `8c4271a1b6e7347c85afe47545edb178c0ce0d22272cade88949647fb8d8a55d`
- **Status**: MATCHED

## 4. Conformance Verdict
> [!IMPORTANT]
> This engine is certified to adhere to profile **ARENA_TEST** on Hardware Class **CLASS_B** for the given scenario duration.

## Honest Reporting Disclaimer
Performance and safety metrics in this report apply ONLY to the (Profile, Scenario, Hardware Class) bundle defined above. Claims of universal throughput or unbounded scaling are explicitly unsupported by this certification and violate Milestone E project laws.