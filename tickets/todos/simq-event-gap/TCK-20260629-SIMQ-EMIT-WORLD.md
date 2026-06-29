---
status: active
layer: simulation
authority: P2
audience: agent
ticket_id: TCK-20260629-SIMQ-EMIT-WORLD
phase: open
date: 2026-06-29
tags: [simq, observability, event-gap, world-dynamics]
---

# TCK-20260629-SIMQ-EMIT-WORLD

## Title
SimQ: Emit WORLD Dynamics Pillar Events from PP-22 / WD-01 through WD-15

## Status
OPEN

## Tier
standard

## Type
feature

## Priority
P2

## Request Summary
The WORLD pillar scores 14 event types — none of which are currently emitted by the engine.
All are produced by the World Dynamics pipeline (PP-22), which runs WD-01 through WD-15
sub-phases. Each sub-phase owns specific events and should emit them directly via
`EventRecorder.record()` at execution time.

## Scope
Add `EventRecorder.record()` calls in WD-01 through WD-15 sub-phases for the following:

| Event type | Source WD phase | Trigger |
|---|---|---|
| `hazard_drain_applied` | WD-01 | Hazard drain applies damage to entities in hazardous region |
| `region_trauma_delta` | WD-02 | Regional trauma value changes this tick |
| `region_ownership_changed` | WD-03 | Region sovereignty transferred |
| `calamity_spawned` | WD-08 | Calamity entity/event spawned |
| `region_transformed` | WD-04 | Region type transitions (e.g., safe → corrupted) |
| `ecology_cycle_completed` | WD-10 | Resource ecology cycle fires (depleted nodes begin regeneration) |
| `resource_node_depleted` | WD-05 | Node charges reach 0 (also in TCK-20260629-SIMQ-EMIT-STATE-DIFF — coordinate to avoid duplication) |
| `node_recharged` | WD-05 | Node charges restore from 0 |
| `spawn_cadence_fired` | WD-09 | Monster spawn cadence fires and populates a region |
| `boss_spawned` | WD-12 | Boss entity spawned |
| `raid_party_spawned` | WD-13 | Raid party spawned |
| `threat_evolved` | WD-11 | Threat entity evolves to next tier |
| `camp_constructed` | WD-14 | Camp lifecycle: camp built |
| `demographic_birth` | WD-15 | New entity spawned via demographics (separate from EventExtractor spawn — this is intentional demographic, not incidental spawn) |
| `demographic_mortality` | WD-15 | Entity death via demographic pressure (not combat) |

**Coordination note:** `resource_node_depleted` and `node_recharged` are also targeted in
TCK-20260629-SIMQ-EMIT-STATE-DIFF (state diff approach). If state diff ticket is done first,
skip them here. If this ticket is done first, TCK-20260629-SIMQ-EMIT-STATE-DIFF should skip
those two to avoid double-emission. Implement exactly one emission site for each.

## Out of Scope
- Economy events (resource_harvested, item_crafted): TCK-20260629-SIMQ-EMIT-ECONOMY
- Faction/Social events: separate tickets
- Changing WD phase logic or outcomes (emit only)

## Acceptance Criteria
- [ ] All 14 WORLD event types emitted from their WD source phase
- [ ] Each event carries `region_id` in payload where applicable
- [ ] No duplicate emission with TCK-20260629-SIMQ-EMIT-STATE-DIFF (coordinate on node events)
- [ ] No import of `src/simulation_quality/` from WD phases
- [ ] Unit tests for each WD sub-phase emission site
- [ ] WORLD pillar shows non-zero events in calibration run after this ticket

## Related Tickets
- TCK-20260629-SIMQ-EVENT-TRANSLATE (prerequisite)
- TCK-20260629-SIMQ-EMIT-STATE-DIFF (coordinate on resource_node_depleted / node_recharged)
- SIMQ-CALIBRATED-001 parity entry

## Related Docs
- `docs/simulation_quality/quality_scoring_contract.md` §5 WORLD DYNAMICS
- `docs/mechanics/05_world_evolution.md` — WD phase laws
- `docs/engine/kernel.md` — PP-22 world_dynamics is a single pipeline phase

## Related Code Areas
- PP-22 world_dynamics and all WD-01 through WD-15 sub-phase implementations
- `src/observability/events.py` — add new event classes as needed

## Assumptions / Open Questions
- WD sub-phases are discrete method calls within the PP-22 pipeline — each can be
  independently hooked without restructuring the pipeline
- `event_recorder` is threaded into the PP-22 phase (verify in kernel.py phase dispatch)
- `calamity_spawned` and `raid_party_spawned` are distinct from `boss_spawned` — verify
  in WD-08/12/13 that they produce distinct entity types
- `ecology_cycle_completed` is a cadence event — fires once per ecology cycle, not per node.
  Verify it's a single dispatch point in WD-10.
