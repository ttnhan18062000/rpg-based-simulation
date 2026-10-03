---
status: historical
layer: world
authority: P2
audience: agent
ticket_id: TCK-20260523-WORLD-TEMPLATES
artifact_type: plan
tags: [world, templates]
---

# Plan: World Template and Recipe System

We will implement a clean, robust, and decoupled Recipe expansion system.

## 1. Directory & File Structures

*   `src/worldbuilding/recipe.py`: Contains the Pydantic spec models for templates and recipes:
    *   `RegionRecipeSpec`: Maps `grid_bounds`, `type`, `terrain`, `hazard_level`.
    *   `PopulationRecipeSpec`: Maps `role`, `count`, `faction`, `spawn_region`, `spawn_distribution`, profiles.
    *   `ResourceRecipeSpec`: Maps `resource_type`, `count`, `region`, `density`, `respawn_policy`.
    *   `BuildingRecipeSpec`: Maps `building_type`, `count`, `region`, `service_profile`.
    *   `WorldTemplateSpec`: Extends topological definitions and defines lists of recipes.
*   `src/worldbuilding/recipe_expander.py`: Implements `WorldTemplateExpander` to expand `WorldTemplateSpec` to `WorldSpec`.
*   `src/worldbuilding/__init__.py`: Exports models and classes.
*   `tests/unit/worldbuilding/test_world_recipes.py`: Robust unit test suite.

## 2. Expansion Logic

1.  **Topology Mapping**: Copy topology and basic metadata from template to target `WorldSpec`.
2.  **Region Expansion**:
    *   Map each `RegionRecipeSpec` to a standard `RegionSpec`.
    *   If bounds are invalid or exceed topology, raise clean containment errors.
    *   Verify uniqueness of region IDs.
3.  **Factions**: Factions list is copied or mapped cleanly.
4.  **Population Recipe Expansion**:
    *   Convert `PopulationRecipeSpec` to standard `PopulationSpec` records.
    *   Support stable ID generation: `pop_<role>_<faction>_<spawn_region>`.
    *   If duplicate roles are defined in the same region/faction, append an index suffix to preserve uniqueness.
5.  **Resource Recipe Expansion**:
    *   For a recipe with `count: N`, expand to `N` distinct `ResourceNodeSpec` elements.
    *   Generate stable traceable IDs: `res_<resource_type>_<region>_<index>`.
6.  **Building Recipe Expansion**:
    *   For a recipe with `count: N`, expand to `N` distinct `BuildingSpec` elements.
    *   Generate stable traceable IDs: `bld_<building_type>_<region>_<index>`.
7.  **Quest Copy**:
    *   Any defined quests in the template are validated and copied to the output `WorldSpec`.
8.  **Post-Expansion Validation**:
    *   Run `WorldValidator.validate(world_spec)` to guarantee that the generated output spec is perfectly correct and conforms to all engine regulations.
