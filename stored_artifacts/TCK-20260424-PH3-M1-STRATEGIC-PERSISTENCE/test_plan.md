# Strategic Persistence Test Plan

## Parity Tests
- `tests/parity/test_strategic_persistence.py`:
  - `test_strategic_project_resumption`: Verify project persists after combat.
  - `test_strategic_combat_interruption`: Verify project suspends during combat.

## Regression Tests
- Verify `DeterministicScheduler` correctly filters inactive entities.
- Verify combat resolution parity remains stable.
