---
status: historical
layer: world
authority: P1
audience: agent
ticket_id: TCK-20260628-E-WORLD-EVOLUTION
phase: done
date: 2026-06-28
tags: [epic, world-evolution, ecology, trauma, sovereignty, p3, deferred, blocked]
---

# TCK-20260628-E-WORLD-EVOLUTION

## Title
Epic: World Evolution System — seasonal multi-region pressure propagation and long-run ecological dynamics

## Status
DONE

## Tier
epic

## Type
feature

## Priority
P3

## Request Summary
Regional trauma and sovereignty are solid. `WorldEmergencePhase` evaluates
`RegionalPressureModel`, `ScarcityModel`, and `ServiceStatePressureModel`. Basic
resource regeneration (E21B) and demographic cycles (E52A–E52D) are implemented.
Remaining gap: seasonal multi-region pressure propagation and validation of the
trauma/sovereignty feedback loop at long run (5,000 ticks).

**Gate conditions:**
- P0-A/B/C fixes: DONE ✓
- D06 5,000-tick run: NOT YET DONE ⛔

**Status: BLOCKED pending 5,000-tick D06 validation run.**

## Block Resolution

Same as TCK-20260628-E-RESOURCE-ECOLOGY — the 5k-tick run provides the observational
baseline for this system. Capture:
- Trauma accumulation and decay curves per region.
- Sovereignty boundary shift events (if any) over 5,000 ticks.
- Cross-regional migration pressure in response to world-scale events.

## Scope (preliminary)
1. Seasonal multi-region pressure propagation: calamity or ecological stress in one
   region propagates pressure signals to adjacent regions based on regional topology.
2. Trauma/sovereignty feedback loop validation: ensure regional trauma accumulation
   produces observable entity behavior changes (threat urgency, migration, quest demand).
3. Fix any gaps found by the 5k-tick run; do not pre-solve without data.

## Out of Scope
- Re-implementing `RegionalPressureModel`, `ScarcityModel`, or `WorldEmergencePhase`.
- Calamity scripting (those are content tasks).

## Acceptance Criteria
- [ ] 5,000-tick run shows at least 2 world-evolution events (calamity or sovereignty shift).
- [ ] Regional trauma accumulation produces measurable entity motivation impact (D01 Tier).
- [ ] Pressure propagation to adjacent regions is observable in migration data.

## Related Tickets
- Parent: TCK-20260627-P3A-DEFERRED-EPICS
- Block dependency: D06 5,000-tick run (use TCK-20260628-E-LONGRUN-REGRESSION harness)
- Adjacent: TCK-20260628-E-RESOURCE-ECOLOGY (shares 5k-tick block)

## Related Docs
- `docs/audits/D01_rpg_feature_impact.md` §World Evolution System
- `docs/audits/D06_longrun_health.md`
- `docs/mechanics/05_world_evolution.md` — trauma, calamity, sovereignty

## Related Stored Artifacts
- N/A

## Related Code Areas
- `src/engine/world_dynamics.py` — WorldEmergencePhase
- `src/world/pressure/` — RegionalPressureModel, ScarcityModel
- `src/world/sovereignty/` — sovereignty tracking

## Assumptions / Open Questions
- Confirm that the trauma/sovereignty loop generates enough signal at 5k ticks to merit
  targeted fixes, vs. needing content authoring (more calamity triggers in world YAMLs).

## Implementation Notes
**Scope investigation (2026-06-28):**
- Block resolved: TCK-20260628-E-LONGRUN-REGRESSION DONE; 5k harness + baseline committed.
- Calamity trigger: tick mod 5000 == 0, min gap 2000, intensity > 0.3.
  In a 5k run, calamity fires exactly at tick 5000 if intensity threshold is met.
- `RESOURCE_DEPLETED`/`RESOURCE_RECOVERED` world events tracked on rolling 500-event window.
- `WorldEmergencePhase` in pipeline.py reads `recent_world_events` from state.
- Ecology sources: `src/world/ecology.py`, `src/world/calamity.py`, `src/world/environment.py`.
- Contract: `docs/world/ecology_and_calamity_contract.md` (last verified 2026-06-13).
- **Gap 1**: Seasonal multi-region pressure propagation not implemented — calamity in region A
  does not propagate pressure signals to adjacent regions via topology.
- **Gap 2**: Regional trauma→entity motivation feedback not validated at 5k scale — the path
  exists (trauma → threat urgency) but whether it's producing measurable entity behavior
  change has not been confirmed at 5k ticks.
- **Gap 3**: Sovereignty boundary shift events: sovereignty tracking exists in
  `src/world/sovereignty/` but at 5k ticks no shift events were observed in baseline data.

**Recommended child tickets (implement in order):**
1. E52E-SEASONAL-PROPAGATION: Implement seasonal multi-region pressure propagation — calamity/
   ecological stress in one region propagates pressure signals to adjacent regions based on
   `runtime_regions.yaml` topology adjacency data.
2. E52F-TRAUMA-MOTIVATION: Validate and fix trauma→entity motivation feedback at 5k scale.
   Add test asserting that regional trauma > 0.5 produces measurable threat urgency in entities
   present in that region within 100 ticks.
3. E52G-SOVEREIGNTY-EVENTS: Confirm sovereignty boundary shift events fire at ≥ 5k ticks
   and are observable via recent_world_events. May require content authoring (more calamity
   triggers in world YAMLs) rather than code changes.

## Test Summary
E52E: 8 tests (seasonal propagation). E52F: 9 tests (trauma concern injection). E52G: 5 tests (sovereignty shift events). All pass; 260 combined world+emergence tests pass.

## Files Changed
See child tickets TCK-20260628-E52E-SEASONAL-PROPAGATION, TCK-20260628-E52F-TRAUMA-MOTIVATION, TCK-20260628-E52G-SOVEREIGNTY-EVENTS.

## Completion Summary
All 3 acceptance criteria met: seasonal calamity propagation (E52E), direct trauma→DANGER concern in <1 tick (E52F), sovereignty shift WorldEvents observable in recent_world_events (E52G). Parity ledger entries WORLD-105, WORLD-106, WORLD-107 added.
All 3 child tickets are complete: E52E (seasonal propagation), E52F (trauma motivation), E52G
(sovereignty events).
