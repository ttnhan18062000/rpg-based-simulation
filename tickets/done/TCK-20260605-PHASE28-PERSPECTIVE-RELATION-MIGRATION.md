# TCK-20260605-PHASE28-PERSPECTIVE-RELATION-MIGRATION

## Title

Perspective/relation usage and legacy-safe migration

## Status

DONE

## Request Summary

Implement Phase 28 ("Perspective/relation usage and legacy-safe migration") sequentially, following strict AGENTS.md rules.

## Scope

- Implement `RelationProjectionService` in `src/content_semantics/relation.py` projecting relationship labels (`ally`, `neutral`, `enemy`, `threat`, `intruder`, `opportunity`, `prey`, `ignored`, `protected`) from perspectives and relationship models.
- Implement compatibility wrapper `is_hostile_compat(source, target, context=None)` to try clean projection and fallback to legacy bucket semantics, logging fallback usage in debug mode.
- Assertions:
  - Goblin warband projects as `enemy` from hero perspective.
  - Wild beast pack projects as contextual `threat` (or intruder), not enemy-by-race.
  - Merchant league projects as `neutral` or trade.
  - Legacy `is_hostile` wrapper still works.

## Out of Scope

- Rewriting all simulation systems to use the new relation projection service directly in this phase.
- Modifying other semantic services unrelated to factions and relationships.

## Acceptance Criteria

- `RelationProjectionService` successfully projects all 9 relationship labels.
- `is_hostile_compat` attempts clean projection and falls back to legacy semantics if clean data is missing.
- Fallback usage is logged at `DEBUG` level.
- Assertions for Goblin warband, Wild beast pack, Merchant league, and legacy `is_hostile` wrapper are satisfied.
- No runtime simulation imports.
- Maintain 100% semantic parity with documentation.

## Related Tickets

- None

## Related Docs

- `world_phase_20_28.md`

## Related Stored Artifacts

- None

## Related Code Areas

- `src/content_semantics/relation.py`
- `src/content_semantics/faction.py`
- `tests/unit/content_semantics/test_semantics.py`

## Assumptions / Open Questions

- None

## Implementation Notes

- We defined `RelationContext` and `RelationProjection` as Pydantic models.
- The `is_hostile_compat` wrapper was added to `FactionSemanticsService`.

## Test Summary

- Added and ran unit tests in `tests/unit/content_semantics/test_semantics.py` verifying all labels and `is_hostile_compat` behavior. (7/7 passed)
- Ran legacy arena compatibility tests `tests/arena/test_arena_startup.py` and `tests/arena/test_arena_quests.py`. (3/3 passed)

## Files Changed

- `src/content_semantics/relation.py`
- `src/content_semantics/faction.py`
- `tests/unit/content_semantics/test_semantics.py`

## Completion Summary

- Implemented `RelationProjectionService` that projects dynamic relationship labels using perspective and faction relationship configurations.
- Implemented `is_hostile_compat` compatibility wrapper inside `FactionSemanticsService` that falls back cleanly to legacy bucket-based semantics with debug logging when clean data is not found.

