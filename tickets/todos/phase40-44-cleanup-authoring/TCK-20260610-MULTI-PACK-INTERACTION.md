# TCK-20260610-MULTI-PACK-INTERACTION

## Title
Add multi-pack composition integration test for base, first pack, second pack, and both packs

## Status
OPEN

## Tier
standard

## Type
chore

## Priority
P2

## Request Summary
Phase 43.3. Verify that `frontier_extended_pack` and `swamp_border_pack` can coexist without accidental ID collisions or unresolved references. Test four modes: base only, base + frontier_extended_pack, base + swamp_border_pack, base + both packs. Each mode validates ID uniqueness, reference graph, composition resolution, scenario setup, registry projection, and strict matrix.

## Scope
- Add `tests/integration/content_packs/test_multi_pack_composition.py`
- Add `tests/integration/content_packs/__init__.py` if missing
- Test modes (parametrized): `base_only`, `base_plus_frontier`, `base_plus_swamp`, `base_plus_both`
- Per-mode assertions: ID uniqueness across pack records; reference graph resolves; all compositions resolve; scenario setup produces modifiers; strict matrix passes; disabled pack content not accidentally consumed
- Test: ID collision between packs fails clearly with pack names in error
- Test: Pack dependency resolution error fails clearly

## Out of Scope
- Running simulation ticks
- Testing more than 2 simultaneous packs

## Acceptance Criteria
- [ ] Base only passes
- [ ] Base + frontier_extended_pack passes
- [ ] Base + swamp_border_pack passes
- [ ] Both packs together pass
- [ ] ID collision fails with clear error naming the packs
- [ ] Pack dependency error fails clearly
- [ ] Disabled pack content is not accidentally consumed by other tests
- [ ] Test is parametrized (data-driven over modes)

## Related Tickets
- TCK-20260610-SWAMP-BORDER-PACK (prerequisite — second pack must exist)
- TCK-20260610-SECOND-PACK-THEME (prerequisite — theme must be confirmed)

## Related Docs
- `docs/mechanics/06_worldbuilding_foundation.md`

## Related Code Areas
- `tests/integration/content_packs/` — new directory
- `src/content/repository.py` — pack loading
- `content_packs/frontier_extended_pack/` — first pack

## Assumptions / Open Questions
- `swamp_border_pack` from TCK-20260610-SWAMP-BORDER-PACK must be DONE before this test can fully pass.

## Implementation Notes
<!-- Fill during implementation -->

## Test Summary
<!-- Fill after implementation -->

## Files Changed
<!-- Fill after implementation -->

## Completion Summary
<!-- Fill after completion -->
