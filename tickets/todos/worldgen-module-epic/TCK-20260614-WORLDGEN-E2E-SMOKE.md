---
status: active
layer: world
authority: P1
audience: agent
ticket_id: TCK-20260614-WORLDGEN-E2E-SMOKE
phase: open
date: 2026-06-14
tags: [worldgen, e2e, smoke, integration-gate]
---

# TCK-20260614-WORLDGEN-E2E-SMOKE

## Title
Epic gate: generated and authored world compositions run 10 simulation ticks

## Status
OPEN

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
- A generated composition: `python3 -m src.worldbuilding.cli generate --danger-level 3 --settlement-style frontier --seed 42`, then `make world-compile WORLD=generated_frontier_3_42`, then `make sim WORLD=generated_frontier_3_42 TICKS=10`

If any test fails due to unrelated engine logic (combat, economy, etc.), open a targeted hotfix ticket rather than blocking this gate.

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
<!-- filled during implementation -->

## Related Code Areas
- `data/content/world_compositions/wilderness_survival.yaml`
- `data/content/world_compositions/urban_political.yaml`
- `data/content/world_compositions/dungeon_crawl.yaml`
- `data/content/world_compositions/generated/generated_frontier_3_42.yaml`

## Assumptions / Open Questions
- If a composition fails at tick 1 due to a world data gap (not engine code), that is a data bug to fix here, not a separate ticket

## Implementation Notes
<!-- filled during implementation -->

## Test Summary
- Bash smoke: `make sim WORLD=<world> TICKS=10` for each composition (exit code 0 = pass)
- Triage any failures: data bug → fix here; engine bug → hotfix ticket + pass gate

## Files Changed
<!-- filled during implementation -->

## Completion Summary
<!-- filled during implementation -->
