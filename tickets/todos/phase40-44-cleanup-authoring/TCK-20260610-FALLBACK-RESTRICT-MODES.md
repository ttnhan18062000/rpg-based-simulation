# TCK-20260610-FALLBACK-RESTRICT-MODES

## Title
Restrict legacy fallback to test_manual and explicit debug modes; forbid in normal startup and strict modes

## Status
OPEN

## Tier
standard

## Type
refactor

## Priority
P1

## Request Summary
Phase 44.2. Once retirement criteria are defined (TCK-20260610-FALLBACK-RETIREMENT-CRITERIA), fallback must be restricted to controlled contexts. Currently fallback can activate silently in any mode. After this ticket, fallback in forbidden modes raises a clear error. Allowed modes: `test_manual`, `legacy_fallback` explicitly selected, `debug_migration`. Forbidden modes: `normal_startup`, `catalog_with_compatibility`, `catalog_strict`, `content_pack_validation`, `scenario_strict_matrix`. Compatibility projections remain allowed; hardcoded fallback does not.

## Scope
- Add mode guard in fallback entrypoint(s): check current catalog mode before activating fallback
- Raise `FallbackRestrictedError` (not silent pass) in forbidden modes with message naming the mode and suggesting the catalog path
- Explicit `legacy_fallback` mode bypasses restriction (for debugging)
- Add tests: normal startup cannot use fallback; `catalog_with_compatibility` cannot use hardcoded fallback; `legacy_fallback` mode still works when explicitly selected; strict matrix fails if fallback used; compatibility projection path still works

## Out of Scope
- Removing fallback code from codebase (that is TCK-20260610-FALLBACK-RECORDS-REMOVAL)
- Changing compatibility projection logic

## Acceptance Criteria
- [ ] Normal startup raises `FallbackRestrictedError` if fallback required
- [ ] `catalog_with_compatibility` mode raises error if hardcoded fallback required
- [ ] `legacy_fallback` mode explicitly selected still works
- [ ] `test_manual` mode still supports direct builders
- [ ] Strict matrix fails if fallback activated
- [ ] Compatibility projection still works in all modes
- [ ] Existing old regression tests either migrated to catalog or marked `legacy_fallback` mode
- [ ] Error message names mode and suggests catalog replacement path

## Related Tickets
- TCK-20260610-FALLBACK-RETIREMENT-CRITERIA (prerequisite — criteria must be defined first)
- TCK-20260610-FALLBACK-RECORDS-REMOVAL (downstream — removal follows restriction)

## Related Docs
- `docs/guidelines/fallback_retirement_criteria.md` (created by prerequisite ticket)
- `docs/guidelines/v2_intentional_divergences.md`

## Related Code Areas
- `src/content/registry.py` or equivalent — fallback entrypoints
- `src/content/catalog_mode.py` or equivalent — mode selection

## Assumptions / Open Questions
- How is `catalog mode` currently passed/selected? Check `CatalogRepository` and startup code before designing mode guard.

## Implementation Notes
<!-- Fill during implementation -->

## Test Summary
<!-- Fill after implementation -->

## Files Changed
<!-- Fill after implementation -->

## Completion Summary
<!-- Fill after completion -->
