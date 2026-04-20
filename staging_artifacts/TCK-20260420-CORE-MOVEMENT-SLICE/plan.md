# Implementation Plan: Deterministic Grid Movement (Task 1-3)

## Goal
Establish the data models and authoritative contracts for movement in `src_v2`.

## Proposed Changes

### Component: Models & Enums
- **[MODIFY] `src_v2/core/models/enums.py`**:
  - Ensure `MovementIntention` exists and covers cardinal directions.
- **[MODIFY] `src_v2/core/models/updates.py`**:
  - Define `NavigationUpdate` and `SpatialUpdate`.

### Component: Authoritative Application
- **[MODIFY] `src_v2/engine/apply.py`**:
  - Add handlers for `NavigationUpdate` and `SpatialUpdate`.

## Verification Plan
### Automated Tests
- `pytest tests_v2/engine/test_movement_models.py` (New test to verify data structures).
