# TCK-20260610-COMBAT-RELATION-PROJECTION — Plan

## Changes

### `src/engine/tactical.py`

In the hostile detection loop (currently lines 121–141):

1. Import `EntityIdentityResolver, IdentityResolutionError` from `src.entities.identity_resolver`
2. Before the loop: resolve source entity identity via `EntityIdentityResolver().resolve(entity)` → `_src_faction_id`, `_src_identity_source`; fall back to `get_faction_id_str(entity)` + `"legacy_fallback"` on error
3. Inside the loop: resolve target identity → `_tgt_faction_id`; fall back to `get_faction_id_str(n)` on error
4. Track per-hostile `hostile_identity_sources: dict[int, str]` mapping entity_id → `_src_identity_source`
5. Add `"target_identity_source": hostile_identity_sources.get(target.id, _src_identity_source)` to the ATTACK, SKILL, and PURSUE payloads

`get_race_id_str(n)` remains for `RelationContext.target_race` — not changing.

### Tests

New file `tests/unit/engine/test_combat_relation_projection.py`:

| Test | What it checks |
|---|---|
| `test_identity_resolver_clean_metadata` | faction_id+role_id in props → source="clean_metadata" |
| `test_identity_resolver_legacy_compat_projection` | legacy enum only → source="compatibility_projection" |
| `test_hero_treats_goblin_warband_as_hostile` | is_hostile_compat("hero_guild", "goblin_warband") → True |
| `test_hero_treats_merchant_league_as_neutral` | is_hostile_compat("hero_guild", "merchant_league") → False |
| `test_wild_beast_threat_requires_territory_context` | wild_beast vs town: not hostile (intruding=False), hostile (intruding=True) |
| `test_legacy_monster_horde_is_hostile_via_fallback` | is_hostile("monster_horde", "hero_guild") → True via bucket fallback |
| `test_projection_source_in_combat_payload` | clean_metadata entity → payload["target_identity_source"] == "clean_metadata" |
| `test_projection_source_legacy_in_payload` | legacy entity → payload has target_identity_source |

## No New Classes

`EntityIdentityResolver` is used inline in the targeting loop — no new service layer. The projection logic already lives in `is_hostile_compat()`.
