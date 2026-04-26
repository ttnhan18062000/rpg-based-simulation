# TCK-20260427-LEGACY-RESTORATION

## Title
Legacy Code Restoration and Test Environment Hardening

## Status
DONE

## Request Summary
The user requested the restoration of `src_legacy` and `tests_legacy` which were previously removed, and asked to fix tests that incorrectly pointed to the legacy namespace while ensuring new tests use the authoritative V2 engine.

## Scope
- Restore `src_legacy/` and `tests_legacy/` from Git history (commit `6e5c289^`).
- Refactor legacy imports to use the `src_legacy` namespace.
- Relocate parity tests from `tests/parity/` to `tests_legacy/parity/`.
- Update integrity guards in `tests/integrity/test_parity_guards.py`.
- Verify V2 test suite health (521 passing tests).

## Out of Scope
- Modifying the authoritative V2 engine logic (`src/`).
- Deleting the procedural engine if it exists in earlier commits (user specifically asked to "not remove them").

## Acceptance Criteria
- [x] `src_legacy/` and `tests_legacy/` are present in the root.
- [x] `src_legacy` is importable without errors.
- [x] `tests/` contains only V2-focused tests.
- [x] `tests/integrity/test_parity_guards.py` passes.
- [x] `walkthrough.md` summarizes the restoration.

## Related Tickets
- None

## Related Docs
- [resource_v2_e2_phases.md](file:///home/vboxuser/Work/rpg-based-simulation/resource_v2_e2_phases.md)
- [README.md](file:///home/vboxuser/Work/rpg-based-simulation/README.md)

## Related Stored Artifacts
- None

## Related Code Areas
- `src_legacy/`
- `tests_legacy/`
- `tests/`
- `tests/integrity/`

## Assumptions / Open Questions
- Assumption: The user refers to the V2-draft version deleted in `6e5c289` as "legacy".

## Implementation Notes
- Restored assets from `6e5c289^` using `git checkout`.
- Applied global `sed` for namespace migration.
- Fixed a conflict between `social.py` and `social/` directory in legacy code.

## Test Summary
- 521/523 tests in `tests/` passed (2 skipped).
- `src_legacy` import verified via python CLI.

## Files Changed
- [tests/integrity/test_parity_guards.py](file:///home/vboxuser/Work/rpg-based-simulation/tests/integrity/test_parity_guards.py)
- [src_legacy/` (RESTORED)
- [tests_legacy/` (RESTORED)

## Completion Summary
- Successfully restored legacy assets and established namespace boundaries. 
- V2 engine is now protected from accidental legacy dependencies.
- Legacy code is preserved for parity verification as requested.
