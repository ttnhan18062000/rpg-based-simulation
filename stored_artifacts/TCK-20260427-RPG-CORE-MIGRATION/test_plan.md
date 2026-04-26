# Test Plan: RPG Core Migration

## Objective
Verify that the migrated RPG core logic matches `src_legacy` behavior and satisfies the V2 authoritative pipeline constraints.

## Automated Tests

### 1. Parity Tests (Differential Validation)
- **Tool**: `pytest`
- **Targets**:
    - `tests/engine/test_interaction_parity.py`: Verify harvesting, looting, and ground pickup match legacy results.
    - `tests/engine/test_movement_parity.py`: Verify semantic movement modes match legacy pathfinding.
    - `tests/engine/test_combat_parity.py`: Verify damage and reward distribution match legacy.

### 2. Contract Tests (Authoritative Constraints)
- **Targets**:
    - `tests/engine/test_mutation_boundary.py`: Ensure no system performs direct state mutation.
    - `tests/engine/test_determinism_suite.py`: Ensure new systems don't break replay stability.

### 3. Checklist Verification
- **Command**: `python3 tools/parity/verify_checklist.py`
- **Requirement**: Must pass for all items marked `[x]` in `logic_checklist_exhaustive.md`.

## Manual Verification
- Review generated `walkthrough.md` with visual evidence (logs/screenshots) of complex interactions (e.g. multi-entity looting race).
