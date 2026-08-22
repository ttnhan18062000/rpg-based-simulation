---
status: active
layer: world
authority: P1
audience: agent
ticket_id: TCK-20260822-ECONOMIC-STRESS-SIGNAL
phase: open
date: 2026-08-22
tags: [economy, world]
---

# TCK-20260822-ECONOMIC-STRESS-SIGNAL

## Title
Build the economic_stress Cross-Region Pressure Signal (Generation Only)

## Status
OPEN

## Tier
standard

## Type
feature

## Priority
P2

## Request Summary
The economic_stress cross-region pressure signal specified in the pressure-propagation-economy idea doc was never built: trigger when a region's Gini exceeds 0.6 or velocity drops more than 30%, then propagate to adjacent regions. Investigation confirms the generation half (per-region Gini trigger plus propagation via the existing RegionalPressureModel pattern) is buildable now, but the velocity leg cannot fire until EconomyHealthMonitor actually tracks per-region trade velocity (currently a global 0.0 stub locked by a passing test), and the concern's originally-specified consumer effect -- raising MERCHANT entity trade-route attractiveness -- requires inventing an EntityRole and a trade-route scoring mechanism that don't exist anywhere in the codebase today. This ticket is scoped to signal generation only; the MERCHANT/trade-route consumer is an explicit follow-on decision, not part of this ticket.

## Scope
- Compute per-region Gini by grouping state.entities on entity.movement.region_id (new logic; today's EconomyHealthMonitor Gini is global-only).
- RegionalPressureModel emits RegionalPressure(pressure_kind="economic_stress") for a region whose per-region Gini exceeds 0.6.
- Propagate economic_stress intensity to adjacent regions using the existing _are_adjacent/PROPAGATION_FACTOR pattern, with reason/source_aggregates citing the originating region.

## Out of Scope
- The velocity leg of the trigger (drop >30%) -- cannot fire until EconomyHealthMonitor tracks per-region trade velocity (currently a permanent global 0.0 stub); this is a separate, non-trivial ticket.
- Wiring the propagated signal into MERCHANT entity trade-route attractiveness -- no MERCHANT EntityRole or trade-route RouteFamily exists in src/core/enums.py or src/domains/adventure/; inventing these is materially larger scope and is explicitly deferred pending a scope decision.
- Any change to EconomyHealthMonitor's existing global Gini computation or its currently-passing test_snapshot_fields_present assertion.
- Sibling concern C1's wiring of the already-shipped resource_scarcity signal (see TCK-20260822-WIRE-REGIONAL-PRESSURE-ECONOMY) -- disjoint scope, not touched here.

## Acceptance Criteria
- [ ] RegionalPressureModel emits RegionalPressure(pressure_kind="economic_stress") for a region whose per-region Gini (grouped on entity.movement.region_id) exceeds 0.6.
- [ ] A region below the Gini threshold produces no economic_stress entry (no false positive).
- [ ] economic_stress intensity propagates to adjacent regions via the existing _are_adjacent/PROPAGATION_FACTOR pattern; reason/source_aggregates cites the originating region.
- [ ] The ticket's docs/acceptance record explicitly states the MERCHANT/trade-route consumer is out of scope and deferred, not silently implied as delivered.

## Related Tickets
- TCK-20260619-E33A-HEALTH-MONITOR
- TCK-20260628-E21E-CROSS-REGION-PRESSURE
- TCK-20260619-E52D-DENSITY-SIGNAL
- TCK-20260822-WIRE-REGIONAL-PRESSURE-ECONOMY

## Related Docs
- docs/mechanics/03_economic_laws.md
- docs/plans/idea_pressure_propagation_economy.md

## Related Stored Artifacts
None.

## Related Code Areas
- src/domains/world_emergence/models.py
- src/domains/world_emergence/schema.py
- src/economy/health_monitor.py
- src/core/state.py
- src/core/strategic.py
- src/core/enums.py
- src/domains/adventure/schema.py
- src/domains/adventure/scoring.py

## Assumptions / Open Questions
- Whether the velocity-drop trigger leg and the MERCHANT/trade-route consumer effect become future tickets or are dropped from the idea doc's scope entirely is an open decision for the author, not assumed here.
- The threshold at which per-region Gini is considered valid (minimum entity count per region) is not specified in investigation and needs a decision during implementation.

## Implementation Notes

## Test Summary

## Files Changed

## Completion Summary
