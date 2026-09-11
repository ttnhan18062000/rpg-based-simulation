---
status: historical
layer: world
authority: P1
audience: agent
ticket_id: TCK-20260614-WORLDGEN-E2E-SMOKE
phase: done
date: 2026-06-14
tags: [worldgen, e2e, smoke, integration-gate]
---

# TCK-20260614-WORLDGEN-E2E-SMOKE

## Title
Epic gate: generated and authored world compositions run 10 simulation ticks

## Status
DONE

## Tier
standard

## Type
chore

## Priority
P2

## Request Summary
Data authoring tickets (WORLDDAT-COMPOSE, WORLDGEN-COMPOSE) create new world compositions but deliberately exclude runtime smoke testing to keep data correctness separate from runtime stability. This final epic gate confirms all new compositions — both authored archetypes and procedurally generated — survive 10 simulation ticks without error.

## Scope
Run 10-tick smoke tests for each of the following and confirm no errors:
- `wilderness_survival` (from TCK-20260614-WORLDDAT-COMPOSE)
- `urban_political` (from TCK-20260614-WORLDDAT-COMPOSE)
- `dungeon_crawl` (from TCK-20260614-WORLDDAT-COMPOSE)
- A generated composition: `python3 -m src.worldbuilding.cli generate --danger-level 3 --settlement-style frontier --seed 42`, then compile, then run 10 ticks.

## Out of Scope
- Fixing unrelated engine runtime failures (those are separate tickets)
- Performance benchmarking
- Balancing or tuning world content

## Acceptance Criteria
- `make sim WORLD=wilderness_survival TICKS=10` completes without unhandled exceptions
- `make sim WORLD=urban_political TICKS=10` completes without unhandled exceptions
- `make sim WORLD=dungeon_crawl TICKS=10` completes without unhandled exceptions
- `make world-compile WORLD=generated_frontier_3_42 && make sim WORLD=generated_frontier_3_42 TICKS=10` completes without unhandled exceptions
- Any failures are triaged: if caused by unrelated runtime code, a separate hotfix ticket is created and this gate passes

## Related Tickets
- TCK-20260614-WORLDDAT-COMPOSE (prerequisite — authored archetypes)
- TCK-20260614-WORLDGEN-COMPOSE (prerequisite — procedural generator)
- TCK-20260614-WORLDSCEN-PERSPECTIVES (prerequisite — perspective wiring)

## Related Docs
- `docs/observability/how_to_run_simulation.md`

## Related Stored Artifacts
- `staging_artifacts/TCK-20260614-WORLDGEN-E2E-SMOKE/`

## Related Code Areas
- `data/content/world_compositions/wilderness_survival.yaml`
- `data/content/world_compositions/urban_political.yaml`
- `data/content/world_compositions/dungeon_crawl.yaml`
- `data/content/world_compositions/generated/generated_frontier_3_42.yaml`
- `tests/integration/worldassembly/test_e2e_smoke.py`

## Assumptions / Open Questions
- If a composition fails at tick 1 due to a world data gap (not engine code), that is a data bug to fix here, not a separate ticket

## Implementation Notes
- CLI invocation confirmed: `python3 -m src cli --ticks 10 --seed 42 --world <world_id>`
- World compile: `python3 -m src.worldbuilding.cli compile <world_id>`
- Integration test uses compile + assemble + AuthoritativeState validation (full 10-tick is Bash-only due to runtime weight)

## Test Summary
Bash smoke (2026-06-15T19:50Z):
- wilderness_survival: 10 ticks, 11 entities — SUCCESS (LifecycleOutcome.SUCCESS)
- urban_political: 10 ticks, 27 entities — SUCCESS
- dungeon_crawl: 10 ticks, 32 entities — SUCCESS
- generated_frontier_3_42: 10 ticks, 44 entities — SUCCESS

Integration: tests/integration/worldassembly/test_e2e_smoke.py — 4/4 pass (compile+assemble path)

## Files Changed
- `tests/integration/worldassembly/test_e2e_smoke.py` (new)

## Completion Summary
All 4 compositions (wilderness_survival, urban_political, dungeon_crawl, generated_frontier_3_42) completed 10 simulation ticks with LifecycleOutcome.SUCCESS and no unhandled exceptions. No hotfix tickets required. 4/4 integration compile-path tests pass. Epic gate PASSED.
