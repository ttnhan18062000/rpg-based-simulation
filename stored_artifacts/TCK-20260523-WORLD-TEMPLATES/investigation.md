# Investigation: World Template and Recipe System

We need to allow developers/simulation designers to create worlds with procedural recipes instead of manual listings.

## Existing Mechanics & Parity Constraints

1.  **Topology and Regions**:
    *   Map topology defines `width` and `height` (coordinate bounds `[0, width]` and `[0, height]`).
    *   A Region is bounded by `[min_x, min_y, max_x, max_y]`.
    *   A region spec must lie completely inside the topology.

2.  **Population Recipes**:
    *   Needs: `count`, `role`, `faction`, `spawn_region`, and optional `stats_profile`, `inventory_profile`, `cognition_profile`.
    *   If a population recipe is expanded, it can translate to a single `PopulationSpec` in the expanded `WorldSpec` with a stable identifier like `pop_<role>_<faction>_<spawn_region>`, representing `count` entities.
    *   Wait, is that simple? Yes! The compiler will then place `count` entities deterministically inside the region bounds.
    *   Let's check if additional attributes like `spawn_distribution` are needed. The goal says:
        ```yaml
        entities:
          populations:
            - role: worker
              count: 500
              faction: villagers
              spawn_distribution:
                type: region_random
                region: village
        ```
        And the text mentions:
        ```text
        count
        role
        faction
        spawn_region
        stats_profile
        inventory_profile
        cognition_profile
        ```
        Let's support both `spawn_region` directly on the recipe and `spawn_distribution` / `spawn_region` interchangeably to remain highly robust and user-friendly!

3.  **Resource Recipes**:
    *   Needs: `resource_type`, `count` (number of nodes to spawn), `region` (region to spawn inside), `density` (optional), and `respawn_policy` (optional).
    *   A single resource recipe with `count: 10` will expand to 10 distinct `ResourceNodeSpec` elements in the `WorldSpec`, each representing a resource node with a unique stable identifier (e.g. `res_<resource_type>_<region>_<index>`).

4.  **Building Recipes**:
    *   Needs: `building_type`, `count` (number of buildings to spawn), `region`, and optional `service_profile`.
    *   A building recipe with `count: 5` expands to 5 distinct `BuildingSpec` elements in the `WorldSpec` with unique stable identifiers (e.g. `bld_<building_type>_<region>_<index>`).

5.  **Region Recipes**:
    *   Needs: `grid_bounds`, `type`, `terrain`, and `hazard_level`.
    *   Wait, standard `RegionSpec` defines:
        ```python
        class RegionSpec(BaseModel):
            id: str
            type: str
            bounds: tuple[int, int, int, int]
        ```
        So a region recipe can expand to a standard `RegionSpec`. We will map `grid_bounds` to `bounds`, and keep `id` as part of the recipe or generate it deterministically (e.g., `reg_<type>_<index>`).

## Determinism Requirement
*   Recipe expansion must be completely deterministic under a seed. We can use a standard `random.Random(seed)` instance if we need to randomize or place things.
*   Wait, does the expander itself need random generation?
    *   If the recipes specify bounds or counts, does the expander need to generate coordinates?
    *   Wait! In our architecture:
        *   `WorldSpec` represents the static structure (listing resource nodes and buildings with IDs, regions with bounds).
        *   The `WorldCompiler` compiles `WorldSpec` into `AuthoritativeState` and is the component that actually places entities, resource nodes, and buildings at specific coordinate tuples `(x, y)` inside their region bounds using `random.Random(seed)`.
        *   So, does `WorldTemplateExpander` (which produces a `WorldSpec`) need to place individual coordinates?
        *   No! The `WorldSpec` itself does not have individual coordinates for resource nodes or buildings—it only links them to a region (e.g. `region: wilds`)! The `WorldCompiler` does the spatial coordinate placement.
        *   However, let's verify: does a region recipe need to generate region bounds?
        *   If the region recipe has a specified `grid_bounds`, we just map it. If it specifies sizes or relative layouts, we might compute bounds. But the goal says region recipe has:
            `grid_bounds`, `type`, `terrain`, `hazard_level`.
            This means the coordinates are already specified as `grid_bounds`, so expansion is a direct mapping!
        *   Let's check if the ID generation or sorting needs determinism. Yes! Sorting and generating unique IDs must be deterministic.

## Parity and Validation Integrity
*   The expanded `WorldSpec` must be validated against `WorldValidator`.
*   We must ensure that the expander checks that all region bounds and expanded building/entity regions exist and lie strictly inside the map topology.
