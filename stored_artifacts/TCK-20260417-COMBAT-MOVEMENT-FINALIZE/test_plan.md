---
status: historical
layer: combat
authority: P2
audience: agent
ticket_id: TCK-20260417-COMBAT-MOVEMENT-FINALIZE
artifact_type: test_plan
tags: [combat, movement, finalize]
---

# Test Plan - Milestone 7 Stabilization

## Scope
Verification of observability contract and rollout hardening boundaries.

## Automated Tests

### 1. Documentation Integrity
- **Command**: `pytest tests/docs/test_combat_movement_documentation_integrity.py`
- **Goal**: Ensure all documented reasons exist in the code base.

### 2. Rollout Verification
- **Command**: `pytest tests/rollout/test_combat_movement_rollout_boundaries.py`
- **Goal**: Ensure toggling `overhaul_features` flags results in correct legacy/v2 behavior transitions.

### 3. API Observability
- **Command**: `pytest tests/observability/test_combat_movement_observability_contract.py`
- **Goal**: Ensure `ReasonCode` and `ActionReason` are correctly serialized through the API layer.

## Manual Verification
- N/A (Automated tests are authoritative for this milestone).
