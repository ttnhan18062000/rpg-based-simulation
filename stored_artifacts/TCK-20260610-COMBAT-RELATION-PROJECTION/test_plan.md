# TCK-20260610-COMBAT-RELATION-PROJECTION — Test Plan

## Test File

`tests/unit/engine/test_combat_relation_projection.py`

## Coverage

| Test | Scenario | Pass condition |
|---|---|---|
| `test_identity_resolver_clean_metadata` | Entity with faction_id+role_id in properties | source == "clean_metadata" |
| `test_identity_resolver_legacy_compat_projection` | Entity with Faction.HERO_GUILD enum only | source == "compatibility_projection" |
| `test_hero_treats_goblin_warband_as_hostile` | FactionSemanticsService + real catalog | is_hostile_compat == True |
| `test_hero_treats_merchant_league_as_neutral` | FactionSemanticsService + real catalog | is_hostile_compat == False |
| `test_wild_beast_threat_requires_territory_context` | Two contexts: intruding=False / intruding=True | False then True |
| `test_legacy_monster_horde_is_hostile_via_fallback` | is_hostile("monster_horde", "hero_guild") | True (legacy bucket) |
| `test_projection_source_in_combat_payload` | evaluate_entity_intent with clean_metadata entity | payload has target_identity_source=="clean_metadata" |
| `test_projection_source_legacy_in_payload` | evaluate_entity_intent with legacy enum entity | payload has target_identity_source key |

## Regression

Run `tests/unit/tactical/` and `tests/unit/combat/` to confirm existing arena and stickiness tests still pass.

## Not Tested

- Bit-identical output between clean and legacy paths (out of scope)
- `intruding=True` in `evaluate_entity_intent` context (hardcoded to False in tactical.py — tests `is_hostile_compat` directly)
