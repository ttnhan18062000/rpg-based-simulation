---
status: active
layer: world
authority: P1
audience: agent
ticket_id: TCK-20260628-E-WORLD-EVOLUTION
phase: open
date: 2026-06-28
tags: [epic, world-evolution, ecology, trauma, sovereignty, p3, deferred, blocked]
---

# TCK-20260628-E-WORLD-EVOLUTION

## Title
Epic: World Evolution System — seasonal multi-region pressure propagation and long-run ecological dynamics

## Status
BLOCKED

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

## Test Summary

## Files Changed

## Completion Summary
