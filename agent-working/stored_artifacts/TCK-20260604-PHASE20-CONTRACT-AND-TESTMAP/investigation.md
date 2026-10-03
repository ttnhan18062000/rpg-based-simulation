---
status: historical
layer: engine
authority: P2
audience: agent
ticket_id: TCK-20260604-PHASE20-CONTRACT-AND-TESTMAP
artifact_type: investigation
tags: [phase20, contract, and, testmap]
---

# Investigation: Phase 20 Content Usage Contract

## Overview
We need to map all content families under `data/content/` (and related folders) and define their metadata and implementation states.

## Existing Content Families
Based on `src/content/repository.py` and directory listings, the content families and their schema classes are:

| Family Directory / File | Schema Class | Repo Index | Expected State |
|---|---|---|---|
| `foundation/materials.yaml` | `MaterialDefinition` | `materials` | `RESOLVED_PARTIALLY` |
| `foundation/traits.yaml` | `TraitDefinition` | `traits` | `RESOLVED_PARTIALLY` |
| `foundation/themes.yaml` | `ThemeDefinition` | `themes` | `RESOLVED_PARTIALLY` |
| `foundation/relationship_axes.yaml` | `RelationshipAxisDefinition` | `relationship_axes` | `RESOLVED_PARTIALLY` |
| `foundation/attributes.yaml` | `AttributeDefinition` | `attributes` | `RESOLVED_PARTIALLY` |
| `foundation/elements.yaml` | `ElementDefinition` | `elements` | `RESOLVED_PARTIALLY` |
| `living/races.yaml` | `RaceDefinition` | `races` | `RESOLVED_PARTIALLY` |
| `living/need_profiles.yaml` | `NeedProfileDefinition` | `need_profiles` | `RESOLVED_PARTIALLY` |
| `living/sense_profiles.yaml` | `SenseProfileDefinition` | `sense_profiles` | `RESOLVED_PARTIALLY` |
| `living/body_models.yaml` | `BodyModelDefinition` | `body_models` | `RESOLVED_PARTIALLY` |
| `living/drive_profiles.yaml` | `DriveProfileDefinition` | `drive_profiles` | `RESOLVED_PARTIALLY` |
| `living/cognition_profiles.yaml` | `CognitionProfileDefinition` | `cognition_profiles` | `RESOLVED_PARTIALLY` |
| `social/roles.yaml` | `RoleDefinition` | `roles` | `RESOLVED_PARTIALLY` |
| `social/factions.yaml` | `FactionDefinition` | `factions` | `RESOLVED_PARTIALLY` |
| `social/perspectives.yaml` | `PerspectiveDefinition` | `perspectives` | `RESOLVED_PARTIALLY` |
| `social/faction_relationships.yaml` | `FactionRelationshipDefinition` | `faction_relationships` | `RESOLVED_PARTIALLY` |
| `entities/stat_profiles.yaml` | `StatsProfileDefinition` | `stats_profiles` | `RESOLVED_PARTIALLY` |
| `entities/combat_profiles.yaml` | `CombatProfileDefinition` | `combat_profiles` | `RESOLVED_PARTIALLY` |
| `entities/inventory_profiles.yaml` | `InventoryProfileDefinition` | `inventory_profiles` | `RESOLVED_PARTIALLY` |
| `entities/skill_profiles.yaml` | `SkillProfileDefinition` | `skill_profiles` | `RESOLVED_PARTIALLY` |
| `entities/populations.yaml` | `PopulationRecipeDefinition` | `populations` | `RESOLVED_PARTIALLY` |
| `entities/entity_archetypes.yaml` | `EntityArchetypeDefinition` | `entity_archetypes` | `RESOLVED_PARTIALLY` |
| `world/buildings.yaml` | `BuildingDefinition` | `buildings` | `RUNTIME_AUTHORITATIVE` |
| `world/terrain.yaml` | `TerrainDefinition` | `terrain` | `RUNTIME_AUTHORITATIVE` |
| `world/services.yaml` | `ServiceProfileDefinition` | `services` | `RUNTIME_AUTHORITATIVE` |
| `world/runtime_regions.yaml` | `RuntimeRegionDefinition` | `regions` | `RUNTIME_AUTHORITATIVE` |
| `world/recipes.yaml` | `RecipeDefinition` | `recipes` | `RUNTIME_AUTHORITATIVE` |
| `world/resources.yaml` | `ResourceDefinition` | `resources` | `RUNTIME_AUTHORITATIVE` |
| `world/items.yaml` | `ItemDefinition` | `items` | `RUNTIME_AUTHORITATIVE` |
| `world/biomes.yaml` | `BiomeDefinition` | `biomes` | `RUNTIME_AUTHORITATIVE` |
| `world/ecologies.yaml` | `EcologyDefinition` | `ecologies` | `RUNTIME_AUTHORITATIVE` |
| `defaults.yaml` | `DefaultCompileProfile` | `defaults` | `RESOLVED_PARTIALLY` |
| `spawn_tables.yaml` | `SpawnTableDefinition` | `spawn_tables` | `PROJECTED_TO_LEGACY` |
| `compatibility/legacy_enemy_projection.yaml` | `LegacyEnemyProjectionDefinition` | `legacy_enemy_projections` | `PROJECTED_TO_LEGACY` |
| `world_modules/*` | `WorldModuleSpec` | N/A (ModuleRepo) | `RESOLVED_PARTIALLY` |
| `world_compositions/*` | `WorldCompositionSpec` | N/A | `RESOLVED_PARTIALLY` |
| `simulation_scenarios/*` | N/A | N/A | `RESOLVED_PARTIALLY` |

## Validation & Resolver mappings
Each family needs to declare:
- Schema class
- Repository index (or if it belongs to another repo)
- Validator coverage (which validation rules in `CatalogValidator` cover it)
- Resolver component (e.g. `FoundationResolver`, `LivingDefaultsResolver`, `SocialDefaultsResolver`, `CompileProfileResolver`, `WorldAssemblyResolver`)
- Compile/runtime consumer (e.g. `WorldCompiler`, `CompileContext`, registries)
- Test coverage (unit/integration tests)
- Current state vs Target state
