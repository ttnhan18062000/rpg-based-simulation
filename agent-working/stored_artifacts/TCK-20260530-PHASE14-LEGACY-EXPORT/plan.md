---
status: historical
layer: engine
authority: P2
audience: agent
ticket_id: TCK-20260530-PHASE14-LEGACY-EXPORT
artifact_type: plan
tags: [phase14, legacy, export]
---

# Implementation Plan - Phase 14 Adopting Layered Catalog and Populating Profiles

This plan covers adopting the new Layered World Data Direction by copying the layered configurations into the active catalog directory and fully populating the baseline profiles.

## User Review Required

> [!IMPORTANT]
> * This phase imports the entire Layered Data structures from `new_data_design/` into `data/content/`.
> * We are shifting from a flat `EnemyDefinition` schema to a rich composition-based model (`RaceDefinition`, `EntityArchetypeDefinition`, etc.) to align with the new data architecture.
> * A projection system (`LegacyEnemyProjectionDefinition`) is introduced to maintain backward compatibility with legacy registries in Phase 15.
> * We explicitly plan to seed BOTH registries: `src/core/registries.py`'s `ItemRegistry` (using `ItemDef`) and `src/core/items.py`'s `ItemRegistry` (using `ItemDefinition`) to ensure runtime simulation logic maps types like `ItemKind` and properties/slots seamlessly.

## Proposed Changes

### Component 1: Catalog Schema Definition updates (`src/content/schema.py`)
- Define foundational types: `MaterialDefinition`, `TraitDefinition`, `ThemeDefinition`, `RelationshipAxisDefinition`, `AttributeDefinition`.
- Define profile and living types: `RaceDefinition`, `NeedProfileDefinition`, `SenseProfileDefinition`, `DriveProfileDefinition`, `CognitionProfileDefinition`, `SkillProfileDefinition`.
- Define social & identity types: `PerspectiveDefinition`, `FactionRelationshipDefinition`.
- Define construction and compatibility types: `EntityArchetypeDefinition`, `LegacyEnemyProjectionDefinition`.

### Component 2: Catalog Data Layout Updates (`data/content/`)
- Copy all files from `new_data_design/` to `data/content/` maintaining directory partitions.

### Component 3: Catalog Repository and Validator Updates (`src/content/repository.py` & `src/content/validator.py`)
- Update `CatalogRepository` to load all yaml configurations.
- Update `CatalogValidator` to run validation checks across the layered structure:
  - Faction relationships refer to valid factions.
  - Archetypes reference valid races, factions, roles, profiles, and traits.
  - Perspectives reference valid factions.
  - Legacy projections map valid archetypes, items, and regions.

## Verification Plan

### Automated Tests
- Create unit tests in `tests/unit/content/test_layered_catalog.py` to assert that all layered models load cleanly, validate, and raise expected relational validation errors.
- Ensure all content catalog unit tests pass successfully.
