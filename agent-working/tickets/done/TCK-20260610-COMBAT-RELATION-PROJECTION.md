---
status: historical
layer: combat
authority: P1
audience: agent
ticket_id: TCK-20260610-COMBAT-RELATION-PROJECTION
phase: done
date: 2026-06-10
tags: [combat, relation, projection]
---

# TCK-20260610-COMBAT-RELATION-PROJECTION

## Title
Wire RelationProjectionService into combat target selection, replacing direct legacy enum checks

## Status
DONE

## Tier
standard

## Type
feature

## Priority
P1

## Request Summary
Combat target filtering currently uses direct legacy `Faction`/`EntityRole` enum comparisons to classify targets as hostile or friendly. `EntityIdentityResolver` and `RelationProjectionService` already exist (Phase 28/29) but are not wired into combat. This task wraps combat target selection so that when clean identity is available, it uses projected relation labels (`enemy`, `threat`, `intruder`, `prey` → hostile; `ally`, `neutral`, `protected`, `ignored` → non-hostile). The legacy enum path is preserved as an explicit fallback.

## Scope
- Identify the combat targeting/classification code path in `src/combat/` or `src/systems/`
- Add projection wrapper: `EntityIdentityResolver.resolve(source)` + `EntityIdentityResolver.resolve(candidate)` → `RelationProjectionService.project_relation(source_identity, candidate_identity, context, perspective)` → classify
- If projection unavailable: use legacy enum fallback (preserve existing behavior)
- Include projection source in the debug/result object
- Tests (extend existing combat tests, add focused cases):
  - hero perspective treats goblin warband as enemy
  - hero perspective treats merchant league as neutral
  - wild beast context produces threat only with territory context
  - legacy monster/horde still works through fallback
  - projection source appears in debug result

## Out of Scope
- Combat damage resolution or combat formula changes
- Adding new relationship axes (Phase 28 owns that)
- Changing perspective schema or faction relationship schema
- Rewriting the combat resolution engine

## Acceptance Criteria
- [x] Combat target classification uses `EntityIdentityResolver`
- [x] Combat target classification can use clean projected relation when available
- [x] Legacy enum fallback still works when projection unavailable
- [x] Existing arena combat tests still pass
- [x] Race alone does not determine enemy status
- [x] Projection source is included in debug/result object

## Related Tickets
- TCK-20260610-QUEST-RELATION-PROJECTION (Phase 37.2, parallel concern)
- TCK-20260610-REGION-THREAT-PROJECTION (Phase 37.3, parallel concern)
- TCK-20260609-ENTITY-IDENTITY-RESOLVER (EntityIdentityResolver already done — reuse)

## Related Docs
- `docs/mechanics/02_combat_laws.md`
- `docs/mechanics/04_strategic_cognition.md`

## Related Code Areas
- `src/content_semantics/relation.py` — RelationProjectionService (exists)
- `src/entities/identity_resolver.py` — EntityIdentityResolver (exists)
- `src/combat/` — combat target selection (identify exact file)
- `tests/` — existing arena combat tests (do not break)

## Assumptions / Open Questions
- Which file/function owns combat target classification? Scan before implementing.
- Does `RelationProjectionService.project_relation()` require a perspective object, and how is perspective available in combat context?

## Implementation Notes
Modified `src/engine/tactical.py` hostile detection loop (previously lines 121–141):
- Added `EntityIdentityResolver` import alongside existing faction imports
- Source entity identity resolved before loop; falls back to `get_faction_id_str()` on `IdentityResolutionError`
- Target entity identity resolved per-neighbor; same fallback
- `hostile_identity_sources` dict tracks which identity source was used per hostile entity_id
- ATTACK, SKILL, and PURSUE payloads now include `target_identity_source`

## Test Summary
9/9 pass: EntityIdentityResolver clean_metadata path, legacy compat_projection path, hero vs goblin hostile, hero vs merchant neutral, wild beast territory context, legacy monster_horde fallback, projection source in ATTACK payload (clean_metadata), projection source in payload (legacy), neutral entity not targeted. Regression: 83/83 existing tactical+combat tests pass.

## Files Changed
- `src/engine/tactical.py` — hostile detection loop uses EntityIdentityResolver; ATTACK/SKILL/PURSUE payloads include target_identity_source
- `tests/unit/engine/__init__.py` — new directory
- `tests/unit/engine/test_combat_relation_projection.py` — new (9 tests)

## Completion Summary
`EntityIdentityResolver` is now in the combat targeting path. Source entity identity is resolved before the hostile loop; target entity identity is resolved per-neighbor. Both fall back to `get_faction_id_str()` if resolution fails. The resolved `faction_id` string feeds `is_hostile_compat()` unchanged (which already uses `RelationProjectionService` internally). The identity resolution source ("clean_metadata", "compatibility_projection", "legacy_enum", or "legacy_fallback") is tracked per hostile and recorded as `target_identity_source` in ATTACK, SKILL, and PURSUE payloads. 9 new tests + 83 existing regression tests pass.
