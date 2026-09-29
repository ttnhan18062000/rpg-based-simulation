---
status: active
layer: world
authority: P1
audience: agent
ticket_id: TCK-20260822-MIGRATION-PRESSURE-SIGNAL
phase: open
date: 2026-08-22
tags: [world, faction]
---

# TCK-20260822-MIGRATION-PRESSURE-SIGNAL

## Title
Build the migration_pressure Cross-Region Pressure Signal and Faction-Decision Consumer

## Status
OPEN

## Tier
standard

## Type
feature

## Priority
P2

## Request Summary
The migration_pressure cross-region signal specified in the idea doc -- trigger when entities have unsatisfied needs for N ticks, propagate to neighboring regions by raising their density signal, affecting faction territorial evaluation -- was never built. Investigation found this is a genuinely distinct mechanic from the already-shipped, informally-identically-named E52B migration mechanic (same-region scarcity-driven cohort emigration, triggered by scarcity>0.7) and must not collide with it in naming or behavior. Delivering it requires new durable per-entity need-unsatisfied-duration tracking (nothing like it exists today), generalizing propagate_cross_region() beyond its current resource-only hardcoding, and building a brand-new consumer in src/engine/faction_decision.py, which today reads zero regional-pressure/density signal inputs of any kind.

## Scope
- New durable per-entity needs_unsatisfied_ticks counter (typed field, defined lifecycle) that increments each tick a need goes unsatisfied and resets on satisfaction.
- RegionalPressureModel emits RegionalPressure(pressure_kind="migration") for a region once its aggregate unsatisfied-duration crosses a documented threshold N ticks, using a pressure_kind/identifier that does not collide with E52B's same-name-in-prose mechanic.
- Generalize propagate_cross_region() (or add a sibling function) so this new pressure kind propagates to adjacent regions proportional to source intensity, via the existing _are_adjacent primitive.
- A narrow, explicit addition to src/engine/faction_decision.py's territorial evaluation that reads the propagated signal and changes at least one decision outcome.

## Out of Scope
- Any change to the existing E52B same-region scarcity-driven cohort-migration mechanic in src/domains/demographics/cohort.py -- distinct mechanic, must remain untouched.
- Storing or propagating a general-purpose 'density' field on RegionState beyond what AC3 requires -- compute_population_density() remains the base computation; this ticket only adds the pressure-derived signal/delta.
- Any broader rework of src/engine/faction_decision.py beyond the single new signal-consuming branch needed for the AC.

## Acceptance Criteria
- [ ] A durable per-entity needs-unsatisfied-duration counter exists as a typed field with a defined increment/reset lifecycle, not a local variable or reason string.
- [ ] When the counter for entities in a region crosses threshold N ticks, RegionalPressureModel emits RegionalPressure(pressure_kind="migration") for that region, documented as distinct from E52B's same-name-in-prose mechanic.
- [ ] The propagation function raises the density-relevant pressure value of every adjacent region proportional to source intensity (via _are_adjacent), with zero effect on non-adjacent regions.
- [ ] src/engine/faction_decision.py's territorial evaluation reads the propagated signal and changes at least one decision outcome based on it, demonstrated by a passing test.

## Related Tickets
- TCK-20260619-E52B-MIGRATION
- TCK-20260619-E52D-DENSITY-SIGNAL
- TCK-20260628-E21E-CROSS-REGION-PRESSURE
- TCK-20260619-E33A-HEALTH-MONITOR

## Related Docs
- docs/mechanics/05_world_evolution.md
- docs/parity_ledger/world_dynamics.yaml

## Related Stored Artifacts
None.

## Related Code Areas
- src/domains/world_emergence/models.py
- src/domains/world_emergence/schema.py
- src/domains/demographics/cohort.py
- src/core/state.py
- src/engine/faction_decision.py

## Assumptions / Open Questions
- The specific value of threshold N ticks for 'needs unsatisfied' is not specified anywhere in investigation and is an open design decision for this ticket to make and document.
- Which need types count toward the unsatisfied-duration counter (all biological pressures, or a subset) is unspecified and needs a decision during planning.
- Whether 'raising the density signal' means storing a new pressure-derived field on RegionState or deriving it on read from compute_population_density() plus the propagated delta is an open implementation choice.

## Implementation Notes

## Test Summary

## Files Changed

## Completion Summary
