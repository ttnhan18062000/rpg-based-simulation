# TCK-20260606-GRAPH-MODELFIX

## Title
Fix duplicate FIELD_TO_TARGET key and stale ResolvedModuleContribution in models.py

## Status
DONE

## Tier
hotfix

## Type
bug

## Priority
P2

## Request Summary
Post-implementation audit of phase 20–28 found two code issues:
1. Duplicate `"provided_recipes"` key in `FIELD_TO_TARGET` dict in `reference_graph.py` (lines 85 and 95 both map to `"recipe"`). Python silently keeps only the second entry; no behavioral impact since values are identical, but it's dead code.
2. `ResolvedModuleContribution` class exists in both `models.py` (with stale `List[str]` types) and `schema.py` (with correct `Dict[str, int]` types from phase 22.3). No code imports it from `models.py`, but it is a naming collision that contradicts the phase 22.3 count-preservation fix.

## Scope
- Remove duplicate `"provided_recipes"` key from `FIELD_TO_TARGET` in `src/content/reference_graph.py`
- Remove stale `ResolvedModuleContribution` class from `src/worldassembly/models.py`

## Out of Scope
- No changes to schema.py
- No changes to any resolver or assembly logic
- No changes to tests (tests already use schema.py's version)
- No new features or v2 assembly changes

## Acceptance Criteria
- `FIELD_TO_TARGET` has no duplicate keys
- `ResolvedModuleContribution` appears only once in the codebase (in `schema.py`)
- All 173 phase-specific tests still pass
- No import breaks

## Related Tickets
- TCK-20260606-PHASE22-3-REPAIR (introduced the schema.py fix, models.py not cleaned up)
- TCK-20260606-PHASE23-REF-GRAPH (introduced FIELD_TO_TARGET)

## Related Docs
- world_phase_20_28_repair.md Phase 22.3

## Related Stored Artifacts
None

## Related Code Areas
- `src/content/reference_graph.py`
- `src/worldassembly/models.py`
- `src/worldassembly/schema.py`

## Assumptions / Open Questions
None — both fixes are safe (confirmed no callers of the affected code paths).

## Implementation Notes
- `models.py` only exports `ResolvedEntityProfile`, `ResolvedBuildingProfile`, `ResolvedResourceProfile`, `ResolvedFactionEconomyProfile` to consumers. `ResolvedModuleContribution` in that file is unreferenced.

## Test Summary
Run `pytest tests/unit/content/ tests/unit/worldassembly/ tests/integration/content/ tests/integration/worldassembly/ -q` — expect all 173 to pass.

## Files Changed
- `src/content/reference_graph.py` — remove duplicate `"provided_recipes"` key
- `src/worldassembly/models.py` — remove stale `ResolvedModuleContribution` class

## Completion Summary
Removed duplicate `"provided_recipes"` key (line 95) from FIELD_TO_TARGET in reference_graph.py.
Removed stale ResolvedModuleContribution class from models.py (authoritative Dict[str,int] version remains in schema.py).
173/173 tests pass.
