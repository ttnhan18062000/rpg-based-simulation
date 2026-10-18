---
status: historical
layer: engine
authority: P1
audience: agent
ticket_id: TCK-20261014-A-CONQUEST-STRONGHOLD-OVERWRITES-ENTITY-1
phase: done
date: 2026-10-14
tags: []
---

# TCK-20261014-A-CONQUEST-STRONGHOLD-OVERWRITES-ENTITY-1

## Title
A monster conquest's stronghold is spawned by a generator whose id counter starts at 0, so it takes id 1 and silently overwrites entity 1. The entity add path has no collision check.

## Status
DONE

## Tier
hotfix

## Type
bug

## Priority
P1

## Request Summary
Found by rpg-planner's spawn-site inventory (2026-10-14) and confirmed in code.
- src/systems/lifecycle_systems/lifecycle.py:~299 builds `EntityGenerator(state.seed + state.tick)` for `FactionInfluenceService.process_conquest_lifecycle` and never sets `_last_id`. Compare pipeline.py:342, which sets `generator._last_id = state.next_entity_id - 1`.
- `spawn_stronghold` takes `get_next_id()`, which is 1.
- apply.py:~293-298 does `new_entities[ent.id] = ent` with no collision check, and `next_entity_id` is not advanced for the stronghold.
- It is live, with no flag, whenever a region is conquered by MONSTER_HORDE (unowned region, influence <= -50).

## Scope
1. Reproduce: a kernel test that forces a conquest and shows entity 1 replaced.
2. Fix the generator. Every mid-run generator takes its id base from state.next_entity_id, through one shared factory rather than per-site setup, so no site can forget it.
3. Make apply refuse an add whose id already exists: a loud failure or a typed violation, never a silent overwrite. Advance next_entity_id for every add.
4. Tests:
   - the conquest stronghold gets a fresh id and entity 1 survives;
   - a duplicate-id add is refused loudly;
   - next_entity_id advances;
   - determinism.
5. Divergence (Bug Fix) and parity entry.

## Out of Scope
- Whether the stronghold itself is a legitimate source (V1/V8). That is a designer question, asked 2026-10-14.

## Acceptance Criteria
- No mid-run add can reuse an existing id.
- The conquest path is fixed and tested.

## Related Tickets
TCK-20261014-CAMPS-STOP-SPAWNING-MONSTERS-FROM-NOTHING-D70; TCK-20261013-RPG-GATE-V8-SPAWN-SOURCE-CHECK (testing).

## Related Docs
docs/engine/authoritative_mutation_pipeline_contract.md; docs/core/entities.md.

## Related Stored Artifacts
None.

## Related Code Areas
src/systems/lifecycle_systems/lifecycle.py; src/systems/world_systems/generator.py; src/engine/apply.py; src/engine/pipeline.py; src/world/influence.py.

## Assumptions / Open Questions
None.

## Implementation Notes
- One factory, `EntityGenerator.for_state(state, update=None)` in `src/systems/world_systems/generator.py`: the id base is past `next_entity_id`, every live id, and (when an update is given) the ids and reservation of earlier adds in the same tick. `pipeline.py` and `lifecycle.py` use it; a source-scan test forbids hand-built `EntityGenerator(` outside `api/engine_manager.py`, `certification/scenarios.py` and `generator.py`.
- `ApplyPath` raises `DuplicateEntityIdError(ValueError)` for an `entities_add` whose id already exists, or repeats within the add list. `next_entity_id` advances past every added id.
- Divergence 2.121 (Bug Fix), parity entry PROG-135, `docs/core/entities.md` note.

## Test Summary
- New `tests/unit/engine/test_mid_run_adds_never_reuse_an_entity_id.py`: 7 tests, red with the old call put back at the lifecycle site, green now.
- Broad run (tests/unit, mechanic_scenarios, certification, api; extra_slow and unit/visual_assets excluded): 8213 passed, 16 failed, 1 error. 12 of the failures are identical on plain main (corpus-diversity grade-stability, timing-sensitive). 4 more (three certification harness tests and a ws_protocol error) passed when re-run alone. `test_hero_guild_routing_seed42_1000t_cognition_grade_stability` fails alone on both main and this branch (different event counts, 20 on main and 50 here, with watchdog trips in the log), so it is timing-dependent, not caused by this change.

## Files Changed
src/systems/world_systems/generator.py; src/engine/pipeline.py; src/systems/lifecycle_systems/lifecycle.py; src/engine/apply.py; tests/unit/engine/test_mid_run_adds_never_reuse_an_entity_id.py; docs/core/entities.md; docs/guidelines/intentional_divergences.md; docs/parity_ledger/progression.yaml.

## Completion Summary
No mid-run add can reuse an entity id: a conquest's stronghold gets a fresh id and entity 1 survives; a duplicate-id add fails loudly. Whether the stronghold is a legitimate source is D71, a separate ticket.
