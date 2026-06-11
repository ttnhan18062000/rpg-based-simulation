---
status: historical
layer: misc
authority: P2
audience: agent
ticket_id: TCK-20260609-MIGRATION-MAP-YAML
artifact_type: investigation
tags: [migration, map, yaml]
---


# Investigation

## Hardcoded legacy ID sources found

| Source file | Legacy IDs |
|---|---|
| src/core/registries.py LEGACY_FALLBACK | node_wood, node_herb, node_iron, node_resin, node_flower, small_potion |
| src/worldassembly/resolver.py REGION_MIGRATION_MAP | trade_road → bandit_road |
| src/entities/identity_resolver.py _ROLE_COMPAT | HERO, SHOPKEEPER, MONSTER, CITIZEN, WORKER, GUARD |
| src/entities/identity_resolver.py _FACTION_COMPAT | HERO_GUILD, MONSTER_HORDE, TOWN_COUNCIL, NEUTRAL |
| data/content/compatibility/legacy_enemy_projection.yaml | wolf, goblin, goblin_archer, cave_spider, bandit_scout, elite_goblin |

## Items and recipes
Items catalog has 6 LEGACY-EXPORT items with no current consumer (all marked deprecated in map).
Recipe `craft_small_potion` is compat_projected (stripped to `small_potion` by registries.py).

## Services
3 service profiles exist in catalog (general_store, blacksmith, tavern); IDs unchanged.
Status: catalog_authoritative.
