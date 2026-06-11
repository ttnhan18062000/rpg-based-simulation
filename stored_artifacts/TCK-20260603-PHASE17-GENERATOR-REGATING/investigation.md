---
status: historical
layer: engine
authority: P2
audience: agent
ticket_id: TCK-20260603-PHASE17-GENERATOR-REGATING
artifact_type: investigation
tags: [phase17, generator, regating]
---

# Investigation - Phase 17 (Procedural Generator Re-gating)

## 1. Context Analysis & Research

### The Hardcoded Factions & Entities Issue
In `src/worldgeneration/generator.py`, the procedural generator populates populations using hardcoded values:
* Factions: `"villagers"` and `"monsters"`.
* Roles: `"citizen"` and `"monster"`.
* Resources: `"wood"` and `"ore"`.
* Buildings: `"shop"`, `"blacksmith"`, and `"tavern"`.

Under strict validation check rules, these names trigger validation errors because they do not match the canonical design loaded from `data/content/`:
1. Factions: `"villagers"` and `"monsters"` do not exist in the production catalog. The correct ones are `"town_council"`, `"hero_guild"`, `"goblin_warband"`, etc.
2. Buildings: `"tavern"` is not in the catalog; instead, `"inn"` is defined.
3. Resources: The resource node IDs should match those in `data/content/world/resources.yaml` (e.g. `wood_node`, `iron_vein`).

### Output Requirements
The unified resolved artifact contract defined in Phase 11 & 12 requires `ResolvedWorldBundle` to carry:
* `world_spec`: `WorldSpec`
* `compile_context`: `CompileContext`
* `provenance_manifest`: `ProvenanceManifest`
* `assembly_report`: `dict`
* `validation_report`: `dict | None`

Currently, `generator.py` instantiates a local `CompileProfileResolver` and calls `resolve` to build `compile_context`. However:
1. It does not carry `validation_report` inside `ResolvedWorldBundle` (it sets it to None or leaves it default).
2. It hardcodes a `created_at` timestamp check hack (`"2026-05-30T12:00:00Z"` if `generation_id.endswith("_test")`), which hides non-determinism instead of using clean stable fingerprints.

## 2. Proposed Refactoring Strategy

### 2.1. Dynamic Faction, Role, Building, and Resource Selection
Instead of hardcoding specific strings, the generator should:
* Query `self.catalog_repo` to find available factions.
  * For civilian populations (like citizens), look for a dynamic defender faction, defaulting to `"town_council"`.
  * For hostile populations (like monsters), look for an invader faction, defaulting to `"goblin_warband"` or `"bandit_company"`.
* For buildings:
  * Check the catalog definitions in `self.catalog_repo.buildings`.
  * Fall back to config-driven choices: `["shop", "blacksmith", "inn"]` instead of using `tavern` which is undefined.
* For resources:
  * Select valid resource types/nodes (like `wood` and `iron_ore` or `wood_node` and `iron_vein`) defined in `self.catalog_repo.resources`.
* For entities roles:
  * Use catalog role IDs (like `"citizen"` and `"raider"` or `"predator_hunter"`).

### 2.2. ResolvedWorldBundle Completeness
* Compile `validation_report` by running `WorldValidator().validate(world_spec, context=ValidationContext.GENERATED_WORLD)`.
* Include the report in `ResolvedWorldBundle`.

### 2.3. Provenance & Determinism Tests Rework
* Rework `test_generator.py` determinism assertions. Instead of doing full string equality on the manifest including `created_at`, extract and verify the `content_fingerprint` or compare only deterministic properties.
