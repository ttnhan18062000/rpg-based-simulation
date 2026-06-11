---
content_type: doc
status: historical
layer: economy
authority: P2
audience: agent
tags: [second, pack, theme]
---

# Theme Selection — swamp_border_pack

## Selected Theme

**Pack ID:** `swamp_border_pack`  
**Display Name:** Swamp Border Pack  
**Decision rationale:** `lizardfolk` race, `sunken_swamp` biome, `swamp_tribe` faction, and `swamp` terrain type are all already present in the base catalog. No new race or faction is required — the pack adds only horizontal content on top of a fully validated foundation.

---

## Phase 43 Entry Criteria — Verified ✓

| Criterion | Result |
|---|---|
| Phase 34 pack contract passes | ✓ 85 tests pass (test_strict_world_matrix, test_catalog_fallback, test_registry_bootstrap_modes) |
| `frontier_extended_pack` manifest validates | ✓ strict_validation_result: "PASS" in yaml |
| `frontier_extended_pack` strict matrix passes | ✓ all row tests pass |
| Base-only strict matrix passes | ✓ test_row_assembly_is_deterministic[frontier_only] passes |
| Base + first pack strict matrix passes | ✓ all parametrized rows pass |
| Content source report distinguishes base/pack records | ✓ test_content_source_report_totals_are_consistent passes |
| Hardcoded fallback guard passes | ✓ test_strict_mode_raises_hardcoded_fallback_error_when_no_catalog passes |

---

## Existing Foundation IDs Reused

These IDs exist in the base catalog and the pack reuses them without modification:

| Type | ID | Source file |
|---|---|---|
| Race | `lizardfolk` | `data/content/living/races.yaml` |
| Faction | `swamp_tribe` | `data/content/social/factions.yaml` |
| Biome | `sunken_swamp` | `data/content/world/biomes.yaml` |
| Terrain | `swamp` | `data/content/world/terrain.yaml` |
| Faction | `wild_beast_pack` | `data/content/social/factions.yaml` (co-inhabits sunken_swamp) |

---

## New Horizontal Content to Add

All items below are additive. None introduce new vertical systems.

### Entity Archetypes (new)
| ID | Race | Faction | Role |
|---|---|---|---|
| `lizardfolk_scout` | lizardfolk | swamp_tribe | skirmisher |
| `lizardfolk_shaman` | lizardfolk | swamp_tribe | support / magic user |
| `swamp_troll` | troll | wild_beast_pack | heavy bruiser |

### Populations (new)
| ID | Members | Biome |
|---|---|---|
| `swamp_tribe_patrol` | lizardfolk_scout × 3, lizardfolk_shaman × 1 | sunken_swamp |
| `swamp_ambush_party` | lizardfolk_scout × 4 | sunken_swamp |

### World Modules (new)
| ID | Description |
|---|---|
| `sunken_swamp_border` | Sunken swamp region module — activates swamp_tribe patrol and resource pressure |

### Simulation Scenarios (new)
| ID | Template | Description |
|---|---|---|
| `swamp_border_incursion` | `territorial_pressure` | Lizardfolk defending sunken_swamp against frontier expansion |

### Sample Composition (new)
- `swamp_border_world` — base + `sunken_swamp_border` module

---

## Forbidden Vertical Systems — Must NOT Introduce

The following are explicitly out of scope for this pack and must not appear in any pack files:

- Diplomacy engine (inter-faction treaty, alliance, war declaration)
- Weather system (rain, fog, temperature mechanics)
- Lineage / genealogy system
- New combat engine variant
- New pack schema version (`content_pack.v2` or higher)
- Any new `WorldUpdate` field types

---

## Module / Composition / Scenario Consumer List

| Consumer ID | Type | Uses |
|---|---|---|
| `sunken_swamp_border` | world_module | populations: swamp_tribe_patrol, swamp_ambush_party |
| `swamp_border_world` | world_composition | modules: [sunken_swamp_border] |
| `swamp_border_incursion` | scenario | composition: swamp_border_world, template: territorial_pressure |

---

## Dependencies

| Dependency | Why |
|---|---|
| `swamp_tribe` faction | primary faction identity |
| `lizardfolk` race | archetype race assignment |
| `sunken_swamp` biome | module placement |
| `territorial_pressure` scenario template | scenario uses this template (TCK-20260610-SCENARIO-TEMPLATES) |
| `content_pack.v1` schema | pack manifest format |
