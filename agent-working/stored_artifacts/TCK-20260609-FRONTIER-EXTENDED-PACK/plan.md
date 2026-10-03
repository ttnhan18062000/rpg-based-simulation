---
status: historical
layer: misc
authority: P2
audience: agent
ticket_id: TCK-20260609-FRONTIER-EXTENDED-PACK
artifact_type: plan
tags: [frontier, extended, pack]
---

# Plan: TCK-20260609-FRONTIER-EXTENDED-PACK

## Files to Modify

| File | Change |
|---|---|
| `data/content/world/biomes.yaml` | Append orc_territory biome |
| `data/content/entities/populations.yaml` | Append orc_clan_warband, sacred_grove_guardians |
| `data/content/world/ecologies.yaml` | Append orc_territory_ecology, sacred_grove_ecology |
| `data/content/simulation_scenarios/frontier_scenarios.yaml` | Append orc_clan_border_tension scenario |
| `tests/integration/content/test_strict_world_matrix.py` | Add 2 matrix rows for new modules |

## Files to Create

| File | Purpose |
|---|---|
| `data/content/world_modules/orc_clan_territory.yaml` | Module: orc_clan_warband in orc territory |
| `data/content/world_modules/forest_warden_grove.yaml` | Module: forest_warden_patrol + sacred_grove_guardians |
| `data/content/world_compositions/frontier_extended.yaml` | New composition consuming the pack |
| `data/content/packs/frontier_extended_pack.yaml` | ContentPackManifest YAML |

## Consumer Chain

```
orc_brute archetype
  → orc_clan_warband population
    → orc_territory_ecology
    → orc_clan_territory module
      → frontier_extended composition
        → orc_clan_border_tension scenario

forest_ranger archetype
  → forest_warden_patrol population (existing)
    → sacred_grove_ecology (new)
    → forest_warden_grove module (new)
      → frontier_extended composition

spirit_guardian archetype
  → sacred_grove_guardians population (new)
    → sacred_grove_ecology (new)
    → forest_warden_grove module (new)
      → frontier_extended composition
```

## Matrix Rows Added

```python
("+ orc_clan",      [...all_frontier_living_world..., "orc_clan_territory"]),
("+ forest_warden", [...all_frontier_living_world..., "orc_clan_territory", "forest_warden_grove"]),
```

## Gate Impact

- Gate 04: no regression — new records are STATE: ADDITIONAL (exempt)
- Gate 07: new modules must normalize — verified by test
- Gate 08: new composition must parse — verified by gate
- Gate 11: remains xfail (CAT-REL-099, catalog-level)
