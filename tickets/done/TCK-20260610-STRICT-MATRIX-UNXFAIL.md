# TCK-20260610-STRICT-MATRIX-UNXFAIL

## Title
Convert strict world matrix full-assembly xfails to passing tests after CAT-REL-099 fix

## Status
DONE

## Tier
hotfix

## Type
repair

## Priority
P1

## Request Summary
`tests/integration/content/test_strict_world_matrix.py` has full-assembly rows that are currently marked `xfail` solely because of the pre-existing CAT-REL-099 defect (moon_cult_ruins / apprentice_mage). Once CAT-REL-099 is resolved, these rows must be verified to actually pass and their xfail markers removed. This ticket is the verification and cleanup step that closes Phase 31 as genuinely complete.

## Scope
- After TCK-20260610-CAT-REL-099-FIX is merged: run the strict world matrix suite
- Confirm all previously xfailed full-assembly rows now pass
- Remove xfail markers and any associated reason comments referencing CAT-REL-099
- If any rows still fail for reasons other than CAT-REL-099, document each separately and do not remove those xfail markers without a separate fix ticket

## Out of Scope
- Adding new matrix test cases
- Changes to the matrix test structure beyond removing xfail markers

## Acceptance Criteria
- [x] All rows in `test_strict_world_matrix.py` that were xfailed due to CAT-REL-099 now pass without xfail marker
- [x] No xfail markers remain in the strict matrix suite unless they reference a different, separately tracked defect
- [x] Deterministic assembly fingerprint test passes
- [x] No-hidden-legacy-fallback test passes

## Related Tickets
- TCK-20260610-CAT-REL-099-FIX (must be completed first — this ticket is blocked on it)

## Related Docs
- `docs/engine/authoritative_pipeline.md`

## Related Stored Artifacts
- `stored_artifacts/TCK-20260609-STRICT-WORLD-MATRIX/`

## Related Code Areas
- `tests/integration/content/test_strict_world_matrix.py`

## Assumptions / Open Questions
- xfail removal was done as part of TCK-20260610-CAT-REL-099-FIX (side effect of resolving the root cause). No markers remain for any reason.

## Implementation Notes
No additional code changes needed. xfail markers (`_PREEXISTING_CAT_BUG`) were removed from `test_strict_world_matrix.py` during TCK-20260610-CAT-REL-099-FIX. This ticket verified that all tests pass.

## Test Summary
73/73 tests pass in `tests/integration/content/test_strict_world_matrix.py`. No xfail markers remain. All deterministic-assembly and no-hidden-legacy-fallback rows green across all 9 module configurations.

## Files Changed
- None (all changes made in TCK-20260610-CAT-REL-099-FIX)

## Completion Summary
Verified 73/73 strict matrix tests pass. xfail markers were already removed in TCK-20260610-CAT-REL-099-FIX. Ticket closed as verification-only.
