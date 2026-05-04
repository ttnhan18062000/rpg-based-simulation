# Consolidated Certification Report

**Last Run ID**: `806104bf-25d8-4308-b311-58a857b6897d`
**Commit SHA**: `20d6a1ef5bb632e343cbfaa8cb47d5cd8a5d5f66`

## Scenario Summary

| Profile | Scenario | Status | Fail Kind | Reason |
| :--- | :--- | :--- | :--- | :--- |
| ARENA_TEST | WIPE_TEST | ⚠️ | failed_semantic_drift | Authoritative divergence from baseline: baseline=d9a7e382315ee8ba66dabe566de4466adb5ec73633bf287e7f610de60ab0bedc, final=000db42e276c213539fb0246c7d1a8fbfba8d4c2da3d458f22e5395e9cbc9c5a |

---

## Latest Run Detail

# Certification Report: WIPE_TEST
**Commit SHA**: `20d6a1ef5bb632e343cbfaa8cb47d5cd8a5d5f66`
**Status**: ❌ **FAIL**
**Allowed Failure Observed**: `False`

## 1. Certified Execution Context (M10 Scoped Truth)
- **Runtime Profile**: `ARENA_TEST`
- **Hardware Class**: `CLASS_B`
- **Scenario**: `WIPE_TEST`
- **Seed**: `42`
- **Peak RAM (RSS)**: `52.9 MB`
- **Total CPU Time**: `0.002 sec`

## 2. Resource Conformance Evidence
| Tick | Mode | RAM (MB) | Compute (ms) | Worker % | Queue % |
| :--- | :--- | :--- | :--- | :--- | :--- |
| 10 | DEGRADED | 52.9 | 1.9 | 1.00 | 0.00 |

## 3. Semantic Integrity Proof (Milestone D Law)
- **Baseline Hash**: `d9a7e382315ee8ba66dabe566de4466adb5ec73633bf287e7f610de60ab0bedc`
- **Final Hash**: `000db42e276c213539fb0246c7d1a8fbfba8d4c2da3d458f22e5395e9cbc9c5a`
- **Status**: DRIFT_DETECTED

## 4. Conformance Verdict
> [!CAUTION]
> **FAILED_SEMANTIC_DRIFT**: Authoritative divergence from baseline: baseline=d9a7e382315ee8ba66dabe566de4466adb5ec73633bf287e7f610de60ab0bedc, final=000db42e276c213539fb0246c7d1a8fbfba8d4c2da3d458f22e5395e9cbc9c5a

## Honest Reporting Disclaimer
Performance and safety metrics in this report apply ONLY to the (Profile, Scenario, Hardware Class) bundle defined above. Claims of universal throughput or unbounded scaling are explicitly unsupported by this certification and violate Milestone E project laws.