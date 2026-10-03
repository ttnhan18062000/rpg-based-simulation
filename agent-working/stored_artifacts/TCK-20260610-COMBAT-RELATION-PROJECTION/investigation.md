---
status: historical
layer: combat
authority: P2
audience: agent
ticket_id: TCK-20260610-COMBAT-RELATION-PROJECTION
artifact_type: investigation
tags: [combat, relation, projection]
---

# TCK-20260610-COMBAT-RELATION-PROJECTION — Investigation

## Key Files

- `src/engine/tactical.py` lines 121–141: hostile detection loop
  - Already imports `get_faction_id_str`, `get_race_id_str`, `RelationContext`
  - Calls `semantics_service.is_hostile_compat(get_faction_id_str(entity), get_faction_id_str(n), context)`
  - `is_hostile_compat()` already internally uses `RelationProjectionService` when perspectives/relationships exist
- `src/content_semantics/faction.py` — `FactionSemanticsService.is_hostile_compat()`: checks perspective/relationship presence, delegates to `RelationProjectionService.project_relation()`, falls back to `is_hostile()`
- `src/content_semantics/relation.py` — `RelationProjectionService.project_relation()`: resolves label from perspective projected_labels → relationship axes → legacy fallback
- `src/entities/identity_resolver.py` — `EntityIdentityResolver.resolve()`: returns `ResolvedEntityIdentity` with `faction_id`, `role_id`, `source` (clean_metadata / runtime_identity_extension / compatibility_projection / legacy_enum)

## What's Missing

`EntityIdentityResolver` is NOT in the combat targeting path. `get_faction_id_str()` is used instead, which provides the faction_id string but loses the `source` field (clean_metadata vs legacy). This means:
1. No traceability of which identity resolution path was used
2. No debug/result object includes the projection source

## Catalog Data

Confirmed from `data/content/social/perspectives.yaml` and `faction_relationships.yaml`:
- `hero_guild_perspective.hostile_groups = ["goblin_warband", ...]`
- `hero_guild_perspective.neutral_groups = ["merchant_league", ...]`
- `wild_beast_pack_perspective.contextual_intruder_groups = ["town_council", "hero_guild", ...]`
- `wild_beasts_to_town` relationship: `territorial_conflict: "high_if_intruding"` — hostile only when intruding

## V2EntityBuilder Notes

- `.properties({"faction_id": "...", "role_id": "..."})` → replaces `identity.properties` with the given dict
- EntityIdentityResolver path 1 (clean_metadata): requires both `faction_id` AND `role_id` in `identity.properties`
- EntityIdentityResolver path 3 (compatibility_projection): legacy `Faction` enum maps to string via `_FACTION_COMPAT`

## No Other Files Need Changes

The `is_hostile_compat()` already handles the projection internally. Only `tactical.py` needs the `EntityIdentityResolver` wrapper for the identity resolution path.
