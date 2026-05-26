# Investigation: World Compiler Implementation (Milestone 70)

This investigation outlines how we translate a validated `WorldSpec` into an engine `AuthoritativeState` deterministically using a seed.

## 1. Engine State Composition

The RPG-based simulation engine utilizes `AuthoritativeState` (defined in `src/core/state.py`) to manage durable gameplay state. The components include:
- `tick`: The current simulation tick (starts at 0).
- `seed`: The world generation / simulation seed.
- `entities`: Dict of entity IDs to `EntityState` objects.
- `resource_nodes`: Dict of resource node IDs to `ResourceNodeState` objects.
- `buildings`: Dict of building IDs to `BuildingState` objects.
- `regions`: Dict of region IDs to `RegionState` objects.
- `terrain`: Dict of coordinate tuples `(x, y)` to terrain strings (e.g. `"WALL"`, `"HILL"`, `"PLAIN"`, `"FOREST"`, etc.).
- `global_resources`: Dict storing global pools, specifically faction vaults (e.g. `"faction_hero_guild_gold": 1000.0`).

## 2. Deterministic Object Placement

Since the map coordinate system is `"grid"`, each object must be assigned discrete coordinates within the boundaries of map topology and specific regions.
- Topology defines the maximum dimensions (`width` and `height`).
- Regions define a bounding box `[min_x, min_y, max_x, max_y]`.
- We initialize a private `random.Random(seed)` generator for compilation.
- For each resource, building, and entity spawned inside a region:
  - We pick a random integer `x` within `[min_x, max_x]`.
  - We pick a random integer `y` within `[min_y, max_y]`.
  - Place the object at `(float(x), float(y))` or `(x, y)` coordinate tuple.
  - This ensures that a given spec + seed will ALWAYS place objects at the exact same locations, but different seeds will generate different placements.

## 3. Entity & Component Initialization

Entities are created using `V2EntityBuilder` from `src/core/builder.py`.
- **IdentityComponent**: Maps the spec's `role` and `faction` to engine enums (`EntityRole`, `Faction`).
- **CombatComponent**: Sets health, attack, defense, alive status, and full readiness (`100.0`).
- **LifecycleComponent**: Active flag set to true, age ticks starting at 0.
- **InventoryComponent**: Initial gold set to standard default or configured value.
- **StrategicComponent**: Projects, blockers, directives, etc. initialized empty.

## 4. State Fingerprint Parity

We will use the existing `StateFingerprinter.get_fingerprint(state)` from `src/replay/fingerprint.py` to produce a deterministic MD5 hash of the compiled state. This ensures that the generated state can be certified for parity in replay and regression tests.

## 5. Post-Compile Validation

After compiling the state, the compiler runs a post-compile validator verifying:
- Quests in `spec.quests` reference valid spawn regions, factions, or entity roles.
- Any mismatches or dangling references generate clear, actionable warnings in the compile report.
