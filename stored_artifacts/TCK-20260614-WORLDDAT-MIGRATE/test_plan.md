# Test Plan: TCK-20260614-WORLDDAT-MIGRATE

## Baseline

- `test_real_content_world_modules.py`: 5 passed (established before migration)
- `test_strict_world_matrix.py`: 15 pre-existing failures (orc_clan, forest_warden, moon_cult rows) — NOT caused by this ticket

## Tests to Pass After Migration

### test_real_content_world_modules.py (5 tests)
- `test_real_world_modules_load_from_data_content` — All 10 modules load without validation error
- `test_real_world_modules_normalize` — All 7 listed modules normalize cleanly
- `test_real_world_modules_preserve_count_maps` — Count maps preserved (populations, resources, buildings)
- `test_real_world_modules_resolve_contributions` — Modules resolve to valid contributions
- `test_real_world_modules_reference_graph_edges_exist` — References valid catalog archetypes/factions/resources

### test_real_content_world_compositions.py
- Composition `frontier_living_world.yaml` assembles after module migration

## Acceptance Criteria Mapping

| Criterion | Verification |
|---|---|
| All 10 modules load | test_real_world_modules_load_from_data_content |
| ≥4 modules have non-empty relationships/biomes | Direct YAML inspection: goblin_camp_conflict, wolf_den_near_forest, frontier_village_core, old_mine_resource_loop |
| ≥1 module has quest_definitions | old_mine_resource_loop |
| make lane-worldassembly passes | test_real_content_world_modules.py all pass |
| frontier_living_world composition assembles | test_real_content_world_compositions.py |
