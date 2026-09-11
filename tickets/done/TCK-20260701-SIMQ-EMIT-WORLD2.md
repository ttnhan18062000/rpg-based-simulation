---
status: historical
layer: simulation
authority: P2
audience: agent
ticket_id: TCK-20260701-SIMQ-EMIT-WORLD-DYNAMICS
phase: done
date: 2026-07-01
tags: [simq, event-emission, world-dynamics, scoring]
---

# TCK-20260701-SIMQ-EMIT-WORLD-DYNAMICS

## Title
SimQ: Emit WORLD dynamics ecology and lifecycle signal events

## Status
DONE

## Tier
standard

## Type
feature

## Priority
P2

## Request Summary
The WORLD pillar already scores A/B in most multi-module worlds (dungeon_crawl, frontier_extended,
wilderness_survival, urban_political). The remaining 5 emission gaps (§3.9 of
`event_type_coverage.md`) target ecology cycle, spawn, and node lifecycle signals that
would increase WORLD signal richness in ecology-heavy worlds (forest, swamp, survival modules).

Missing events (from §3.9):
- `ecology_cycle_completed` — no emitter; comment in economy.py: "owned by WorldDynamicsScorer per SQ-08"
- `spawn_cadence_fired` — no emitter; `SpawnService.process_spawns()` fires but doesn't emit
- `camp_constructed` — no emitter; construction event not surfaced in world dynamics
- `threat_evolved` — no emitter; threat escalation logic not emitting quality signal
- `node_recharged` — no emitter; `resource_node_regenerated` is emitted but marked unscored_intentional;
  `node_recharged` is a distinct scored event in WorldDynamicsScorer

## Scope
1. Add `ecology_cycle_completed` emitter in `WorldEmergencePhase` or `world_dynamics.py`:
   fires at the end of each ecological cycle evaluation (per-region, per-tick);
   payload: `region_id`, `cycle_type`, `net_pressure_delta`
2. Add `spawn_cadence_fired` emitter in `SpawnService.process_spawns()`:
   fires whenever a spawn batch is committed; payload: `spawned_count`, `tick`,
   `world_id`, `trigger_reason` (early vs late cadence tier from P2-B fix)
3. Add `camp_constructed` emitter: investigate where camp/structure construction is tracked
   in world state; emit when a new camp-type building appears in `world_updates.building_adds`
4. Add `threat_evolved` emitter: investigate `ThreatEscalationPhase` or equivalent;
   emit when a threat tier increases (e.g., goblin_raid → orc_invasion)
5. Add `node_recharged` emitter: emit in `ResourceNodeRegenerationService.process()`
   (from TCK-20260628-E21B-REGEN-SERVICE) when a node's `remaining_charges` increases
   from 0 to > 0 (distinct from `resource_node_regenerated` which fires on every regen tick)
6. Update `docs/simulation_quality/event_type_coverage.md §3.9`
7. Add unit tests for each emitter

## Out of Scope
- Changing WorldDynamicsScorer thresholds
- Modifying ecology or spawn mechanics
- Changing `resource_node_regenerated` classification (intentionally unscored)

## Acceptance Criteria
- [ ] All 5 event types emitted under correct conditions
- [ ] Each event reaches WorldDynamicsScorer (verify via unit test)
- [ ] `node_recharged` is distinct from `resource_node_regenerated` (different payload, different scorer)
- [ ] `event_type_coverage.md §3.9` updated — 5 entries removed
- [ ] No regression in existing world dynamics tests

## Related Tickets
- TCK-20260629-SIMQ-EMIT-WORLD — prior world dynamics emit pass
- TCK-20260628-E21B-REGEN-SERVICE — ResourceNodeRegenerationService (node_recharged reference)
- TCK-20260627-P2B-SPAWN-CADENCE — SpawnService two-tier cadence (spawn_cadence_fired reference)

## Related Docs
- `docs/simulation_quality/event_type_coverage.md §3.9`
- `docs/mechanics/05_world_evolution.md` — ecology cycles, regional trauma, calamities
- `docs/simulation_quality/quality_scoring_contract.md §5` — WorldDynamicsScorer contract

## Related Code Areas
- `src/systems/world_systems/spawn.py` — SpawnService.process_spawns()
- `src/domains/ecology/` or `src/engine/pipeline_phases/world_emergence.py` — ecology cycles
- `src/worldbuilding/regeneration.py` or equivalent — ResourceNodeRegenerationService
- `src/simulation_quality/scorers/world_dynamics_scorer.py`

## Assumptions / Open Questions
- `camp_constructed` — unclear if "camp" refers to a building type in the catalog or a
  world-state construct. Investigate `catalog.buildings` for camp-type entries before implementing.
- `threat_evolved` — if no ThreatEscalationPhase exists, this may require a stub or
  a state diff on `RegionState.threat_level` field. Confirm threat level is tracked in RegionState.
- `ecology_cycle_completed` — confirm "per-tick" or "per-season" cadence with WorldEmergencePhase;
  per-tick would generate many events; may need to throttle to once per N ticks.

## Test Summary
- Unit: `spawn_cadence_fired` payload includes correct `spawned_count` and `trigger_reason`
- Unit: `node_recharged` fires only on 0→>0 transition, not on incremental regen
- Unit: `ecology_cycle_completed` fires once per ecological phase boundary, not every tick
- Integration: frontier_extended 500-tick run shows > 0 ecology_cycle_completed and spawn_cadence_fired

## Files Changed
- `src/observability/event_extractor.py` — 4 new emitters (ecology_cycle_completed, spawn_cadence_fired, threat_evolved, node_recharged)
- `tests/unit/observability/test_event_extractor_world_dynamics.py` — 14 unit tests
- `docs/parity_ledger/world_dynamics.yaml` — added WORLD-108, WORLD-109
- `docs/simulation_quality/event_type_coverage.md` — §3.9 partially resolved; camp_constructed remains blocked

## Completion Summary
4 of 5 WORLD-DYNAMICS emitters implemented. ecology_cycle_completed (tick%200 per region),
spawn_cadence_fired (tick%50 + non-boss entities_add), threat_evolved (trauma threshold
crossing), node_recharged (remaining_charges 0→>0). camp_constructed blocked —
CampService has no event recorder interface. 14 unit tests pass; 1074 total tests pass.
