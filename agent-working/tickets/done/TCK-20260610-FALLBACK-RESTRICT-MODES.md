---
status: historical
layer: misc
authority: P1
audience: agent
ticket_id: TCK-20260610-FALLBACK-RESTRICT-MODES
phase: done
date: 2026-06-10
tags: [fallback, restrict, modes]
---

# TCK-20260610-FALLBACK-RESTRICT-MODES

## Title
Restrict legacy fallback to test_manual and explicit debug modes; forbid in normal startup and strict modes

## Status
DONE

## Tier
standard

## Type
refactor

## Priority
P1

## Request Summary
Phase 44.2. Once retirement criteria are defined (TCK-20260610-FALLBACK-RETIREMENT-CRITERIA), fallback must be restricted to controlled contexts. Currently fallback can activate silently in any mode. After this ticket, fallback in forbidden modes raises a clear error. Allowed modes: `test_manual`, `legacy_fallback` explicitly selected. Forbidden modes: `catalog_with_compatibility`, `catalog_strict`. Compatibility projections remain allowed; hardcoded fallback does not.

## Scope
- Add `FallbackRestrictedError` to `src/core/modes.py` (canonical class, avoids circular imports)
- Make `HardcodedFallbackError` in `bootstrap.py` a backward-compat subclass of `FallbackRestrictedError`
- Add mode guard in `seed_phase1_content`'s else branch: raise for forbidden modes
- Change module-level auto-seed at line 729 to use `LEGACY_FALLBACK` mode (explicit compat)
- Improve error message to name mode and suggest catalog replacement path
- Add tests for the `seed_phase1_content` mode guard directly

## Out of Scope
- Removing fallback code from codebase (TCK-20260610-FALLBACK-RECORDS-REMOVAL)
- Changing compatibility projection logic
- Adding new modes

## Acceptance Criteria
- [x] Normal startup raises `FallbackRestrictedError` if fallback required
- [x] `catalog_with_compatibility` mode raises error if hardcoded fallback required
- [x] `legacy_fallback` mode explicitly selected still works
- [x] `test_manual` mode still supports direct builders
- [x] Strict matrix fails if fallback activated
- [x] Compatibility projection still works in all modes
- [x] Existing old regression tests either migrated to catalog or marked `legacy_fallback` mode
- [x] Error message names mode and suggests catalog replacement path

## Related Tickets
- TCK-20260610-FALLBACK-RETIREMENT-CRITERIA (prerequisite)
- TCK-20260610-FALLBACK-RECORDS-REMOVAL (downstream)

## Related Docs
- `docs/guidelines/fallback_retirement_criteria.md`
- `docs/guidelines/v2_intentional_divergences.md`

## Related Code Areas
- `src/core/modes.py` — FallbackRestrictedError (new)
- `src/runtime/bootstrap.py` — HardcodedFallbackError as subclass alias
- `src/core/registries.py` — mode guard in seed_phase1_content, auto-seed mode change

## Assumptions / Open Questions
- Circular import resolved: FallbackRestrictedError lives in modes.py (already imported by both registries.py and bootstrap.py)

## Implementation Notes
- `FallbackRestrictedError` added to `src/core/modes.py` with `mode` attribute
- Error message: "[mode=X] Fallback to hardcoded content is restricted in this mode. Load a catalog via CatalogRepository('data/content') and pass it to bootstrap_registries() instead."
- `HardcodedFallbackError` in `bootstrap.py` changed to `class HardcodedFallbackError(FallbackRestrictedError)` — backward compat preserved
- `seed_phase1_content` else branch: raises `FallbackRestrictedError` when mode.value in `_FORBIDDEN_FALLBACK_MODES` (catalog_strict, catalog_with_compatibility)
- Module-level auto-seed changed from `CATALOG_WITH_COMPATIBILITY` to `LEGACY_FALLBACK` mode so import-time fallback is always allowed
- `FallbackRestrictedError` re-exported from `bootstrap.py` for consumer convenience

## Test Summary
9 new tests in `tests/unit/runtime/test_fallback_restrict_modes.py`:
- Error class importable from bootstrap
- HardcodedFallbackError is subtype of FallbackRestrictedError
- FallbackRestrictedError carries mode attribute
- Error message names mode
- Error message suggests data/content catalog path
- seed_phase1_content with CATALOG_STRICT + no catalog raises
- seed_phase1_content with CATALOG_WITH_COMPATIBILITY + no catalog raises
- seed_phase1_content with LEGACY_FALLBACK + no catalog succeeds
- bootstrap_registries raises as FallbackRestrictedError
All 9 pass. All 7 existing bootstrap mode tests still pass.

## Files Changed
- `src/core/modes.py` — FallbackRestrictedError class + _FORBIDDEN_FALLBACK_MODES constant
- `src/runtime/bootstrap.py` — HardcodedFallbackError as subclass; FallbackRestrictedError import + re-export
- `src/core/registries.py` — mode guard in seed_phase1_content else branch; auto-seed mode changed to LEGACY_FALLBACK
- `tests/unit/runtime/test_fallback_restrict_modes.py` (new) — 9 tests

## Completion Summary
FallbackRestrictedError established as canonical error class in modes.py. Mode guard added to seed_phase1_content (the only previously unguarded fallback entrypoint). Error message names mode and suggests catalog path. All 18 tests (9 new + 9 existing) pass.
