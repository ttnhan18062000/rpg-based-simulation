# TCK-20260610-MULTI-PACK-INTERACTION

## Title
Add multi-pack composition integration test for base, first pack, second pack, and both packs

## Status
DONE

## Tier
standard

## Type
chore

## Priority
P2

## Request Summary
Phase 43.3. Verify frontier_extended_pack and swamp_border_pack can coexist without ID collisions or unresolved references.

## Scope
- Add `tests/integration/content_packs/test_multi_pack_composition.py`
- 4 modes: base_only, base_plus_frontier, base_plus_swamp, base_plus_both
- ID uniqueness, assembly, module isolation, collision error, dependency error tests

## Out of Scope
- Running simulation ticks
- Testing more than 2 simultaneous packs

## Acceptance Criteria
- [x] Base only passes
- [x] Base + frontier_extended_pack passes
- [x] Base + swamp_border_pack passes
- [x] Both packs together pass
- [x] ID collision fails with clear error naming the packs
- [x] Pack dependency error fails clearly
- [x] Disabled pack content is not accidentally consumed by other tests
- [x] Test is parametrized (data-driven over modes)

## Related Tickets
- TCK-20260610-SWAMP-BORDER-PACK (prerequisite)
- TCK-20260610-SECOND-PACK-THEME (prerequisite)

## Related Docs
- `docs/mechanics/06_worldbuilding_foundation.md`

## Related Code Areas
- `tests/integration/content_packs/test_multi_pack_composition.py` (new)

## Assumptions / Open Questions
N/A

## Implementation Notes
No ID collision found between the two packs. `comp.modules` is None after schema normalization — module membership is stored in `comp.module_refs`, fixed in isolation tests. 17 tests total.

## Test Summary
17 tests: 1 collision check, 4×ID uniqueness, 4×assembly no blocking errors, 4×determinism, 2×module isolation, 1×artificial collision detection, 1×dependency error. All pass.

## Files Changed
- `tests/integration/content_packs/__init__.py` (new)
- `tests/integration/content_packs/test_multi_pack_composition.py` (new)

## Completion Summary
Multi-pack coexistence verified across 4 modes. Both packs can run simultaneously with no ID collisions or assembly errors.
