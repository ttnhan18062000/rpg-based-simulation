---
status: historical
layer: engine
authority: P2
audience: developer
---

# Milestone A: Test Matrix

This document maps the Core Runtime Laws to specific automated test groups. Every law defined in the `runtime_completion_contract_ma.md` must be pinned by at least one regression test.

## 1. Kernel Law Tests
Proves phase order, ownership, and authoritative boundaries.

| Test Case / Group | Law / Requirement | Expected Behavior |
|:---|:---|:---|
| `test_phase_order` | Phase Sequencing | Fails if INIT-ADVANCEMENT order is violated. |
| `test_kernel_boundaries` | Auth Boundary | Fails if non-auth phases mutate state. |
| `test_minimal_kernel` | Tick Advancement | Verified correct world_time and tick increments. |

## 2. Apply-Path Tests
Proves mutation purity and deterministic application.

| Test Case / Group | Law / Requirement | Expected Behavior |
|:---|:---|:---|
| `test_authoritative_apply` | Singular Mutation | Verifies `StateUpdate` application via `ApplyPath`. |
| `test_apply_determinism` | Sort Invariance | Fails if reordered update keys change outcome. |
| `test_no_hidden_mutation` | Immutability | Fails if nested properties can be mutated post-apply. |

## 3. Work-Order Tests
Proves deterministic scheduling and tie-break rules.

| Test Case / Group | Law / Requirement | Expected Behavior |
|:---|:---|:---|
| `test_scheduler_contract` | Class Hierarchy | Verifies Critical > Periodic > Deferred. |
| `test_tie_break_rules` | Sorting Law | Verifies readiness/owner ID sort order. |
| `test_deferred_work_debt` | Debt Draining | Verifies correct debt accounting and selection. |

## 4. Checkpoint Determinism Tests
Proves hash purity and reproducibility.

| Test Case / Group | Law / Requirement | Expected Behavior |
|:---|:---|:---|
| `test_checkpoint_reproducibility` | Seed Determinism | Same input + same state = identical hash. |
| `test_governance_isolation` | Hash Purity | Governance mode changes do NOT change hash. |
| `test_reordered_dict_invariance` | Canonical Sort | Entity dictionary order does NOT change hash. |

## 5. Constraint & Regression Guards
Ensures no silent drift or placeholder contamination.

| Test Case / Group | Law / Requirement | Expected Behavior |
|:---|:---|:---|
| `test_no_placeholders_ma` | Placeholder Guard | Fails if TODO/Placeholder branches are reached in baseline. |
| `test_doc_integrity_ma` | Law Compliance | Fails if code implementation drifts from Milestone A contract. |

## 6. Regression Intent
These tests ensure that as we move into Milestones B-E (Signals, Replay, Workers), the single-process semantic baseline remains a fixed, untouchable reference.
