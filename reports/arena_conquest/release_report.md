# Consolidated Certification Report

**Last Run ID**: `867954bd-713b-45bc-8fd4-561a257ecbae`
**Commit SHA**: `5507b2b8d9a38c2ca5274a558307c73b7b4ca2a5`

## Scenario Summary

| Profile | Scenario | Status | Fail Kind | Reason |
| :--- | :--- | :--- | :--- | :--- |
| CONQUEST_ARENA_TEST | COMBAT_ARENA_REGIONAL | ✅ | none | Certification PASS |

---

## Latest Run Detail

# Certification Report: COMBAT_ARENA_REGIONAL
**Commit SHA**: `5507b2b8d9a38c2ca5274a558307c73b7b4ca2a5`
**Status**: ✅ **PASS**
**Allowed Failure Observed**: `False`

## 1. Certified Execution Context (M10 Scoped Truth)
- **Runtime Profile**: `CONQUEST_ARENA_TEST`
- **Hardware Class**: `CLASS_B`
- **Scenario**: `COMBAT_ARENA_REGIONAL`
- **Seed**: `42`
- **Peak RAM (RSS)**: `68.3 MB`
- **Total CPU Time**: `0.004 sec`

## 2. Resource Conformance Evidence
| Tick | Mode | RAM (MB) | Compute (ms) | Worker % | Queue % |
| :--- | :--- | :--- | :--- | :--- | :--- |
| 1 | NORMAL | 68.3 | 3.9 | 1.00 | 0.01 |

## 3. Semantic Integrity Proof (Milestone D Law)
- **Baseline Hash**: `615a0a275bb5bd8107c4b1a1dd6665a927ce884b42b11ff39732f9de1d9a3e55`
- **Final Hash**: `615a0a275bb5bd8107c4b1a1dd6665a927ce884b42b11ff39732f9de1d9a3e55`
- **Status**: MATCHED

## 4. Conformance Verdict
> [!IMPORTANT]
> This engine is certified to adhere to profile **CONQUEST_ARENA_TEST** on Hardware Class **CLASS_B** for the given scenario duration.

## Honest Reporting Disclaimer
Performance and safety metrics in this report apply ONLY to the (Profile, Scenario, Hardware Class) bundle defined above. Claims of universal throughput or unbounded scaling are explicitly unsupported by this certification and violate Milestone E project laws.