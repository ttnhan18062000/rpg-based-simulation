# TCK-20260610-ENUM-REWARD-INFLUENCE

## Title
Replace direct Faction/EntityRole enum checks in reward attribution and faction influence update

## Status
OPEN

## Tier
standard

## Type
refactor

## Priority
P1

## Request Summary
Phase 40.1 targets five systems for enum cleanup. Combat target classification (TCK-20260610-COMBAT-RELATION-PROJECTION), quest target matching (TCK-20260610-QUEST-RELATION-PROJECTION), and regional classification (TCK-20260610-REGION-THREAT-PROJECTION) are already done. This ticket covers the two remaining targets: reward attribution and faction influence update. Both currently use `Faction.MONSTER_HORDE` / `Faction.HERO_GUILD` enum comparisons that should use `EntityIdentityResolver` and `FactionSemanticsService` where clean identity is available.

## Scope
- `src/world/influence.py` — replace `region.owner_faction_id == Faction.MONSTER_HORDE` / `Faction.HERO_GUILD` with clean faction_id string lookups via `FactionSemanticsService` (alignment bucket or `is_invader()`/`is_protector()`)
- `src/engine/world_dynamics.py` — replace direct `Faction.HERO_GUILD` / `Faction.MONSTER_HORDE` comparisons in influence threshold logic
- Preserve legacy enum fallback path: if catalog faction definition is absent, fall back to current bucket logic
- Tests: legacy enum entity still behaves the same; clean catalog entity follows clean path; mixed coexist

## Out of Scope
- Rewriting influence accumulation formulas
- Changing conquest/liberation thresholds
- Reward item generation logic unrelated to faction checks

## Acceptance Criteria
- [ ] `influence.py` conquest/liberation logic uses clean faction alignment instead of direct enum comparison
- [ ] `world_dynamics.py` influence threshold logic uses clean faction alignment where possible
- [ ] Legacy entities (only enum identity) still trigger same conquest/liberation behavior through fallback
- [ ] Existing arena and integration tests still pass
- [ ] New tests prove clean and legacy paths produce identical outcomes

## Related Tickets
- TCK-20260610-COMBAT-RELATION-PROJECTION (combat enum cleanup — DONE)
- TCK-20260610-QUEST-RELATION-PROJECTION (quest enum cleanup — DONE)
- TCK-20260610-REGION-THREAT-PROJECTION (regional enum cleanup — DONE)
- TCK-20260610-ENUM-USAGE-LINTER (companion linter ticket)

## Related Docs
- `docs/mechanics/05_world_evolution.md`

## Related Code Areas
- `src/world/influence.py` — `FactionInfluenceService`
- `src/engine/world_dynamics.py` — influence threshold logic
- `src/content_semantics/faction.py` — `FactionSemanticsService.is_invader()`, `is_protector()`

## Assumptions / Open Questions
- `FactionSemanticsService.is_invader(faction_id)` returns True for MONSTER_HORDE bucket. Verify this is consistent with conquest semantics before changing.

## Implementation Notes
<!-- Fill during implementation -->

## Test Summary
<!-- Fill after implementation -->

## Files Changed
<!-- Fill after implementation -->

## Completion Summary
<!-- Fill after completion -->
