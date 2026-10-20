---
status: historical
layer: api
authority: P1
audience: agent
ticket_id: TCK-20261014-THE-LIVE-SERVER-RUNS-THE-AUTHORED-WORLD-NOT-A-DEMO-SPAWN-D69
phase: done
date: 2026-10-14
tags: []
---

# TCK-20261014-THE-LIVE-SERVER-RUNS-THE-AUTHORED-WORLD-NOT-A-DEMO-SPAWN-D69

## Title
The live API server runs the authored compiled world, the same one the simulation and the gate run, and the hard-coded demo spawn is removed.

## Status
DONE

## Tier
hotfix

## Type
repair

## Priority
P1

## Request Summary
src/api/engine_manager.py spawns 1 hero, 9 goblins on a diagonal and an unexplained wolf, and discards the world's authored entities (24 on sandbox_world). Owner ruling D69: what a viewer watches is what gets measured. No debug switch keeps the demo spawn.

## Scope
- Build the live world through the same compile/assembly path the simulation uses (one path, no second spawner).
- Delete the hard-coded spawns.
- Trace the unexplained wolf. If it comes from a path that makes a body from nothing, file it or fix it as a V1 violation wherever else that path runs.
- Tests: the API world's entity set equals the compiled world's for at least two worlds, and no entity lacks an authored or born source.

## Out of Scope
- The tile-colour fix, which has its own branch.
- Asset-domain scene copies.

## Acceptance Criteria
- The live entity set matches the compiled world.
- No demo spawn code remains.
- The wolf's origin is explained and handled.

## Related Tickets
TCK-20261011-LIVE-MAP-COLOURS-TERRAIN-BY-A-FIXED-CODE-TABLE-THE-API-DOES-NOT-USE.

## Related Docs
docs/audits/D28_live_map_functional_correctness.md; designer memo row 69.

## Related Stored Artifacts
None.

## Related Code Areas
src/api/engine_manager.py; the world compile/assembly entry the simulation uses.

## Assumptions / Open Questions
The wolf (id 25 at (87,50) on sandbox_world) is NOT a second spawn path: it is CampService.process_camps step 2 calling EntityGenerator.spawn_monster(kind='wolf') for the wolf_den_nest camp (a wolf species declares no camp_spawn_kind, so a wolf nest spawns wolves). It also fires in the headless simulation (the den holds one monster against a cap of 2). The camp spawn is being removed under D70; this ticket does not change it and its test does not pin it. Perf tools tools/perf/live_map_ws_payload_measure.py and turbo_run.py: the --entities scale knob no longer scales the live world (perf owner to re-point at a world).

## Implementation Notes
V2EngineManager._build now loads the world with load_world_with_context and compiles it with the context (the way the simulation and tests/helpers/scenario.compile_world do), keeps every authored entity, and deletes the hero/goblin demo diagonal. entities_count is removed from V2EngineManager, create_v2_app, the serve CLI (--entities) and the callers; there is no switch. Also fixed (found because authored entities carry items and the demo ones did not): StatePresenter.present_entity read item.metadata but an ItemStack has properties, so the entity DTO raised AttributeError for any entity carrying items; the API key stays metadata, sourced from properties. Tests that relied on the demo count now read the authored world (sandbox_world for paging and coin-circulation, the compiled count for the metrics snapshot).

## Test Summary
tests/api/test_live_map_terrain_codes_resolve_through_the_manifest.py: the API world's starting entity set equals the compiled world's for sandbox_world and dungeon_crawl, and V2EngineManager/create_v2_app have no entities_count. Updated for the authored world: tests/api/test_paged_logic.py, tests/observability/test_metrics_export.py. tests/unit/api, tests/api and the metrics test pass except the known pre-existing test_metadata_api.py::test_resources_real_fields_from_catalog.

## Files Changed
src/api/engine_manager.py; src/api/presenters/state_presenter.py; src/api/server.py; src/cli/entry.py; tools/perf/turbo_run.py; tools/perf/live_map_ws_payload_measure.py; tests as above.

## Completion Summary
Done: the live server runs the authored compiled world; the demo spawn is deleted.
