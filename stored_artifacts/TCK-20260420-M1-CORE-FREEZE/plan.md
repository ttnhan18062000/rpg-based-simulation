---
status: historical
layer: misc
authority: P2
audience: agent
ticket_id: TCK-20260420-M1-CORE-FREEZE
artifact_type: plan
tags: [m1, core, freeze]
---

# Implementation Plan - Core Substrate Freeze (M1)

## Goal
Establish a stable, frozen baseline for the `src` engine substrate to support Phase 4 gameplay attachment.

## Proposed Changes

### 1. Documentation Update
- **[MODIFY] docs/engine/runtime_completion_contract_ma.md**: Update headers to reflect "Phase 4 / Milestone 1" freeze status. Add a section about "Freeze Date" and "Scope for Gameplay Attachment".
- **[MODIFY] docs/engine/project_lawbook_m10.md**: Update the table of contents to align with the revised Phase 4 roadmap.

### 2. Code Hardening (Locking)
- **[MODIFY] src/engine/kernel.py**:
    - Add explicit "FROZEN" warnings in docstrings for the 6-phase loop.
    - Finalize `_get_deterministic_neighbor_view` as the official baseline for Movement.
- **[MODIFY] src/engine/apply.py**:
    - Add explicit "FROZEN" warnings in docstrings.
    - Ensure all collections are sorted (already appears done, but double check).
- **[MODIFY] src/core/governance.py**:
    - Add docstrings to `PressureSignals` fields, marking them as the frozen operational surface for M1.
- **[MODIFY] src/engine/runtime_status.py**:
    - Seal the `signal_history` length and trending logic.

### 3. Drift Guardrails (New Tests)
- **[NEW] tests/engine/test_substrate_freeze_m1.py**:
    - Test to ensure `AuthoritativeState` hasn't added non-authoritative fields.
    - Test to ensure `PressureSignals` fields haven't changed (using `__slots__` or inspection).
    - Test to ensure `Kernel` phase execution order hasn't drifted.

## Verification Plan

### Automated Tests
- `pytest tests/engine/test_substrate_freeze_m1.py`
- `pytest tests/engine/test_milestone_a_closure.py`
- `pytest tests/engine/test_determinism_suite.py`
- `pytest tests/certification/test_final_gate.py`

### Manual Verification
- Review updated doc files for clarity and alignment with `resource_phase4_high_level.md`.
