# Consolidated Certification Report

**Last Run ID**: `23889d80-9451-4ce3-925b-cee943055274`
**Commit SHA**: `5507b2b8d9a38c2ca5274a558307c73b7b4ca2a5`

## Scenario Summary

| Profile | Scenario | Status | Fail Kind | Reason |
| :--- | :--- | :--- | :--- | :--- |
| WATCHDOG_TEST | WATCHDOG_SCENARIO | ❌ | failed_reporting_incomplete | No measurement points captured during scenario. |

---

## Latest Run Detail

# Certification Report: WATCHDOG_SCENARIO
**Commit SHA**: `5507b2b8d9a38c2ca5274a558307c73b7b4ca2a5`
**Status**: ❌ **FAIL**
**Allowed Failure Observed**: `False`

## 1. Certified Execution Context (M10 Scoped Truth)
- **Runtime Profile**: `WATCHDOG_TEST`
- **Hardware Class**: `CLASS_B`
- **Scenario**: `WATCHDOG_SCENARIO`
- **Seed**: `42`
- **Peak RAM (RSS)**: `0.0 MB`
- **Total CPU Time**: `0.000 sec`

## 2. Resource Conformance Evidence
| Tick | Mode | RAM (MB) | Compute (ms) | Worker % | Queue % |
| :--- | :--- | :--- | :--- | :--- | :--- |

## 3. Semantic Integrity Proof (Milestone D Law)
- **Baseline Hash**: `84f767e6732554f939e9af1b25b7408eef242ad244e8efa66d05e75788ad9dd0`
- **Final Hash**: `84f767e6732554f939e9af1b25b7408eef242ad244e8efa66d05e75788ad9dd0`
- **Status**: MATCHED

## 4. Conformance Verdict
> [!CAUTION]
> **FAILED_REPORTING_INCOMPLETE**: No measurement points captured during scenario.

## Honest Reporting Disclaimer
Performance and safety metrics in this report apply ONLY to the (Profile, Scenario, Hardware Class) bundle defined above. Claims of universal throughput or unbounded scaling are explicitly unsupported by this certification and violate Milestone E project laws.