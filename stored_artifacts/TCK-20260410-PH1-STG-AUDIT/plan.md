# Audit Plan - Strategic Design Shift (Phase 1 & 2)

## Goal
Reconcile the historical implementation of the Strategic Design Shift with the requested "Phase N Stage M" convention and ensure documentation is accurate.

## Investigation Notes
- [x] Phase 1 Foundation: Tasks 1-8 verified in `models/strategy.py`, `aspects/mind.py`, `actions/base.py`, `action_system.py`, `entity_builder.py`, and `inspector.py`.
- [x] Phase 1 Stage 7: Strategic Appraisal: Verified in `strategic_evaluator.py`, `brain.py`, and `test_strategic_biasing.py`.
- [x] Phase 3 Knowledge: Recently finalized and verified.

## Implementation Steps

### 1. Update Phase 1 Documentation
- **File**: `thinking_implementation_phase_1.md`
- **Action**: Check off Tasks 1-8.
- **Action**: Add "Implementation Comment" to each task referencing the specific files and logic.

### 2. Ticket Reconciliation
- **Action**: Move `TCK-20260409-PH1-STG1-STRATEGIC-STATE` to a slightly different name or update its content to clearly show it covered Stage 1-8?
- **Decision**: I'll create small, retrospective "Done" tickets for each Stage to ensure the history is clean and granular.
- **Stages**:
    - Phase 1 Stage 1: Domain Models (Task 1)
    - Phase 1 Stage 2: Mind Integration (Task 2)
    - Phase 1 Stage 3: Strategic Update Actions (Task 3)
    - Phase 1 Stage 4: Authoritative Logic (Task 4)
    - Phase 1 Stage 5: Snapshot & Safety (Task 5)
    - Phase 1 Stage 6: Seed & Inspector (Task 6, 7)
    - Phase 1 Stage 8: Structural Regression (Task 8)
    - Phase 1 Stage 7: Strategic Appraisal Logic
    - Phase 2 Stage 2: Intent-based Multipliers & UI

### 3. Verify Snapshot Safety (Stage 5 Audit)
- **Investigation**: Ensure `StrategicState` and its nested records (`DirectiveRecord`, `ProjectRecord`, etc.) are correctly handled during `Snapshot` serialization and cloning.
- **Test**: Add a specific test case to `tests/core/test_strategy_models.py` or a new integration test for deep cloning.

### 4. Update Working Log
- **File**: `tickets/working_log.csv`
- **Action**: Add the retrospective entries.

## Test Plan
- `pytest tests/core/test_strategy_models.py`
- `pytest tests/ai/test_strategic_biasing.py`
- Manual check: `python -m src.ui.cli.inspector 1` (or similar) to verify strategic domain output.
