# TCK-20260426-PH13-LEGACY-RETIREMENT

## Title
Execute Phase 13 Legacy Retirement and Canonical Refactor

## Status
DONE

## Request Summary
Retire all legacy `src/` assets identified in the Phase 13 manifest and promote `src` to the canonical `src` namespace.

## Scope
- Rename legacy `src/` to `src_legacy/` and `tests/` to `tests_legacy/`.
- Rename specified legacy `scripts/`/`config/` assets.
- Rename `src/` to `src/`.
- Rename `tests/` to `tests/`.
- Refactor all import statements from `src` to `src`.
- Verify full suite passes under the new structure.

## Out of Scope
- Adding new features.
- Modifying domain logic (beyond import fixes).

## Acceptance Criteria
- Legacy `src/` and `tests/` directories are gone.
- `src/` contains the V2 engine code.
- `tests/` contains the V2 test suite.
- All tests (585) pass using `pytest tests`.
- `python3 -m src` runs the V2 simulation correctly.

## Related Tickets
- TCK-20260425-PH12-STABILITY (Completed)

## Related Docs
- docs/engine/phase13_retirement_manifest.md

## Related Stored Artifacts
- None

## Related Code Areas
- src/
- src/
- tests/
- tests/

## Assumptions / Open Questions
- Assumption: The user wants `tests` renamed to `tests` for consistency.

## Implementation Notes
- Use `sed` for bulk import refactoring.
- Use `git mv` or `mv` for directory renaming.

## Test Summary
- `pytest tests` (Target)

## Files Changed
- TBD

## Completion Summary
- TBD
