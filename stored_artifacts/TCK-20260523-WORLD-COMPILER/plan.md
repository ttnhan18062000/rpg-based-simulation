# Plan: World Compiler Implementation (Milestone 70)

We will build the `WorldCompiler` in `src/worldbuilding/compiler.py` and register it in `src/worldbuilding/__init__.py`.

## 1. Directory & File Strategy

### New Files
- `src/worldbuilding/compiler.py`: Contains `WorldCompiler`, `WorldCompileReport`, and core compilation logic.

### Modified Files
- `src/worldbuilding/__init__.py`: Export `WorldCompiler` to make it accessible to external modules.

## 2. Compilation Sequence

The compiler executes the following 8 stages sequentially:

1. **Topology**: Read `width` and `height` from `TopologySpec`. Initialize `terrain` dict mapping all coordinate points inside the map boundaries `[0, width)` and `[0, height)` to default plain/grass terrain, or map based on region bounds.
2. **Regions**: Create `RegionState` objects for all regions in `spec.regions` and add them to `regions` map of `AuthoritativeState`. Update `terrain` coordinates inside each region's bounds to match the region's `terrain` property.
3. **Factions**: Populate `global_resources` with standard starting wealth for each faction (`faction_<faction_id>_gold: 1000.0`).
4. **Resources**: Spawn resources node states by placing `ResourceNodeSpec` entities randomly within their target region bounds using `random.Random(seed)`. Add to `resource_nodes`.
5. **Buildings**: Spawn building states for each `BuildingSpec` using randomized placement inside their target region bounds. Add to `buildings`.
6. **Entities**: Spawn populations. For each group with `count`, generate that many distinct entities using `V2EntityBuilder`, placing them randomly inside their spawn region bounds. Add to `entities` mapped by unique incremental IDs.
7. **Quests**: If quests exist in `spec.quests`, compile them.
8. **Strategic Setup**: Assign quests to eligible entities (e.g. matching faction or role) by adding a starting `QuestState` in their `strategic.projects` list.

## 3. Post-Compile Validation

- Scan all compiled quests to check that their target regions, target entity roles, or required resource types exist and match valid compiled types.
- If there are unmatched references, add warnings to the compiler report.

## 4. Compilation Report

Write a report `world_compile_report.json` containing:
- `world_id`: The ID of the compiled world.
- `seed`: The seed used.
- `entity_count`: Total compiled entities.
- `region_count`: Total compiled regions.
- `resource_node_count`: Total compiled resource nodes.
- `building_count`: Total compiled buildings.
- `quest_count`: Total compiled quests.
- `warnings`: Array of warning messages from post-compile validation.
- `compile_duration_ms`: Duration of the compile step in milliseconds.
- `state_hash`: Initial MD5 fingerprint of the state via `StateFingerprinter.get_fingerprint(state)["state_hash"]`.
