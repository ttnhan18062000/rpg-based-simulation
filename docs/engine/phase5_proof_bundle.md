# Phase 5 Proof Bundle

This document serves as the canonical index of all proof artifacts backing the "Official Support" claims for `src_v2` at the conclusion of Phase 5. It ensures that every supported feature is tied to a verifiable proof.

## 1. Bit-Identical Parity Proofs (Oracles)

The following behaviors have been verified as bit-identical to legacy `src` using the "Oracle" capture/verify path.

| Subsystem | Oracle Result | Verification Code |
| :--- | :--- | :--- |
| **Grid Movement** | [movement_oracle/results.json](../../tests_v2/parity/movement_oracle/results.json) | `tests_v2/parity/test_movement_parity.py` |
| **Resource Interaction**| [interaction_oracle/results.json](../../tests_v2/parity/interaction_oracle/results.json) | `tests_v2/parity/test_resource_interaction_parity.py` |
| **Town Resolution** | [town_oracle/results.json](../../tests_v2/parity/town_oracle/results.json) | `tests_v2/parity/test_town_resolution_parity.py` |

## 2. Integrated Behavioral Proofs

The following integrated loops have been verified through high-fidelity parity and integrity scenarios.

| Scenario | Matrix | Verification Code |
| :--- | :--- | :--- |
| **Integrated Progression**| [support_matrix.md](support_matrix.md) | `tests_v2/parity/test_progression_loop_parity.py` |
| **Kernel Determinism** | [m1_test_matrix.md](m1_test_matrix.md) | `tests_v2/engine/test_determinism_suite.py` |
| **Authoritative Apply** | [m7_test_matrix.md](m7_test_matrix.md) | `tests_v2/engine/test_authoritative_apply.py` |

## 3. Contract & Lifecycle Integrity

The following V2 core contracts have been formally validated against the runtime substrate.

| Contract | Matrix | Verification Code |
| :--- | :--- | :--- |
| **Strategic Intelligence**| [ma_test_matrix.md](ma_test_matrix.md) | `tests_v2/contract/test_resource_intelligence_contract.py` |
| **Governor & Boundedness**| [m5_test_matrix.md](m5_test_matrix.md) | `tests_v2/engine/test_resource_governor_contract.py` |
| **Lifecycle & Shutdown** | [mc_test_matrix.md](mc_test_matrix.md) | `tests_v2/engine/test_graceful_shutdown.py` |
| **Worker Equivalence** | [m8_test_matrix.md](m8_test_matrix.md) | `tests_v2/engine/test_worker_equivalence.py` |

## 4. Performance & Certification Gates

The final exit gates for Phase 5 (Milestone E Hardening) are represented by these reports.

| Layer | Baseline / Report | Verification Code |
| :--- | :--- | :--- |
| **Performance Profile B** | [performance_contract.md](performance_contract.md) | `tests_v2/verify_profile_b.py` |
| **API Payload Truth** | [performance-report-api-payload.md](../performance-report-api-payload.md) | `tests_v2/engine/test_signal_truth.py` |
| **Final Release Gate** | [me_test_matrix.md](me_test_matrix.md) | `tests_v2/certification/test_final_gate.py` |

---
*Created: 2026-04-21 as part of Phase 6 Milestone 1 — Entry Gate Proof Package.*
