# Milestone E Test Matrix - Final Verification

## 1. Certification Proof Tests
| Test Case | Input Condition | Expected Law | Regression Caught |
| :--- | :--- | :--- | :--- |
| `test_recovery_deadline_enforcement` | Pressure run + Delay | FAIL if NORMAL mode not reached by `recovery_time_limit_ticks` | Hang in degraded modes |
| `test_degradation_sequence_order` | Pressure run (RAM+CPU) | FAIL if surrendering doesn't match priority order | Out-of-order resource shedding |
| `test_telemetry_gap_detection` | Missing measurement points | FAIL if gap exceeds `sampling_interval_ticks` | Intermittent monitoring failures |
| `test_hash_equivalence_deep` | Seeded run vs Sequential | FAIL if final hash differs by 1 byte | Execution non-determinism |

## 2. Failure Taxonomy Tests
| Test Case | Input Condition | Expected Law | Regression Caught |
| :--- | :--- | :--- | :--- |
| `test_taxonomy_naming_integrity` | Non-passing run | `FailureKind` matches `FAILED_*` enum naming | Naming drift in reports |
| `test_actionable_reason_presence` | FailureKind != NONE | `failure_reason` is non-empty and descriptive | Vague "fail somehow" outputs |

## 3. Honest Reporting Tests
| Test Case | Input Condition | Expected Law | Regression Caught |
| :--- | :--- | :--- | :--- |
| `test_vanity_language_block` | "Fastest", "Unlimited" in docs | FAIL (Regex check) | Marketing vanity in tech docs |
| `test_scoped_claim_enforcement` | Perf claim missing HW Class | FAIL (Recorder Logic Invariant) | Unscoped performance overclaims |
| `test_hardware_integrity_capture` | Overridden hardware class | `EnvironmentCapture` mirrors fact/class/override split | Blurred environment status |

## 4. Docs/Playbook Integrity Tests
| Test Case | Input Condition | Expected Law | Regression Caught |
| :--- | :--- | :--- | :--- |
| `test_release_target_alignment` | Lawbook claims vs Manifest | FAIL if support targets disagree | Doc drift from release policy |
| `test_terminology_code_binding` | Enum name typo in doc | FAIL if doc term not found in code enums | Terminology drift |

## 5. The Production Gate (Task 5)
| Test Case | Input Condition | Expected Law | Regression Caught |
| :--- | :--- | :--- | :--- |
| `test_bundle_completeness` | Missing target artifact in bundle | FAIL release gate | Ship without critical certification |
| `test_sha_provenance_binding` | Artifact SHA != current commit | FAIL release gate | Shipping stale proof artifacts |
