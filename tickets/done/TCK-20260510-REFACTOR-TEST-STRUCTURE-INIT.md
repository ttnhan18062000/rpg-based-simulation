# TCK-20260510-REFACTOR-TEST-STRUCTURE-INIT

## Title
Initialize Refactored Test Structure and Migrate Pipeline Tests

## Status
INPROGRESS

## Tier
standard

## Type
chore

## Priority
P1

## Request Summary
Create the new test directory hierarchy and move the first batch of integration tests (Pipeline Phase) as per Milestone 1 of the refactor plan.

## Scope
- Create subdirectories in `tests/unit/` and `tests/integration/`.
- Create `tests/integrity/` and `tests/refactor/` (if missing).
- Move specific pipeline integration tests from `tests/rpg/` and `tests/engine/` to `tests/integration/pipeline/`.

## Out of Scope
- Moving unit tests (Task 1.4).
- Moving long-run world tests (Task 1.3).

## Acceptance Criteria
- [x] All target folders listed in Task 1.1 exist.
- [x] Pipeline tests moved to `tests/integration/pipeline/` with same filenames.
- [x] Tests pass in the new location.
- [x] No duplicates left in original folders.

## Related Tickets
- None

## Related Docs
- [refactor_implementation_plan.md](file:///home/vboxuser/Work/rpg-based-simulation/refactor_implementation_plan.md)

## Related Stored Artifacts
- `reports/refactor/collect_before.txt`

## Related Code Areas
- `tests/`

## Implementation Notes
- Use `git mv` for moves.
- Ensure `__init__.py` files are added if necessary.

## Test Summary
- `pytest tests/integration/pipeline -q`

## Files Changed
- TBD

## Completion Summary
- TBD
