---
status: active
layer: economy
authority: P1
audience: agent
ticket_id: TCK-20260822-WIRE-REGIONAL-PRESSURE-ECONOMY
phase: open
date: 2026-08-22
tags: [economy, world, observability]
---

# TCK-20260822-WIRE-REGIONAL-PRESSURE-ECONOMY

## Title
Wire Cross-Region Resource-Pressure Propagation into EconomyHealthMonitor

## Status
OPEN

## Tier
standard

## Type
repair

## Priority
P1

## Request Summary
RegionalPressureModel.propagate_cross_region() (E21E) already computes and propagates resource_scarcity pressure between regions every tick, but the WorldEmergenceResult carrying it is discarded at pipeline.py:290 and never reaches EconomyHealthMonitor (E33A) -- the two systems were built independently and never connected. Correcting the concern's original wording: EconomyHealthMonitor's Gini/velocity sampling is global-only today, not per-region as assumed, so wiring requires reconciling two already-existing but disconnected per-region-economy code paths (the kernel-driven global metric_windows.jsonl path and the presenter's on-request per-region grouping) into one canonical target, and must avoid a real name collision with the unrelated state.pressure_signals dict used by an unrelated Phase E5.6 global_salience pricing mechanism.

## Scope
- Recompute a per-region causal resource-scarcity value read-only from the already-propagated E21E output (state.recent_world_events / state.regions), without mutating AuthoritativeState.
- Pick one canonical per-region economy-health target to wire into, reconciling the kernel-driven metric_windows.jsonl global path with the presenter's on-request per-region grouping.
- Preserve existing global-only Gini/monitor behavior guaranteed by TOWN-177.
- Update docs/mechanics/03_economic_laws.md and/or docs/parity_ledger/town_resource.yaml TOWN-177 to document the new causal linkage.

## Out of Scope
- Reimplementing or altering RegionalPressureModel.propagate_cross_region()'s formula (WORLD-104: PROPAGATION_FACTOR=0.30, ADJACENCY_GAP=50, bidirectional, capped at 1.0, single-hop) -- consume as-is.
- Any change to the unrelated state.pressure_signals dict (Phase E5.6 global_salience pricing) -- must not repurpose or touch it.
- Implementing transaction_velocity as a real metric (it remains a permanent 0.0 stub; out of scope for this ticket).
- Building a new general-purpose per-region abstraction layer beyond wiring the existing propagation output into the chosen target.

## Acceptance Criteria
- [ ] A region with zero native resource pressure but a resource-scarce adjacent region produces a non-zero, traceable causal value in the per-region economy-health read model.
- [ ] Wiring recomputes read-only from state.recent_world_events/state.regions; does not mutate AuthoritativeState; does not touch state.pressure_signals -- verified by a fingerprint() before/after equality test.
- [ ] All existing tests/unit/economy/test_economy_health_monitor.py tests still pass, or are updated with a documented reason tied to this change.
- [ ] docs/mechanics/03_economic_laws.md and/or docs/parity_ledger/town_resource.yaml TOWN-177 are updated to document the new causal linkage.

## Related Tickets
- TCK-20260628-E21E-CROSS-REGION-PRESSURE
- TCK-20260619-E33A-HEALTH-MONITOR
- TCK-20260619-E33B-ALERTS-REST
- TCK-20260628-E-RESOURCE-ECOLOGY

## Related Docs
- docs/parity_ledger/town_resource.yaml
- docs/parity_ledger/world_dynamics.yaml
- docs/mechanics/03_economic_laws.md

## Related Stored Artifacts
None.

## Related Code Areas
- src/domains/world_emergence/models.py
- src/domains/world_emergence/phase.py
- src/domains/world_emergence/schema.py
- src/engine/pipeline.py
- src/economy/health_monitor.py
- src/api/presenters/economy.py
- src/api/routes/economy.py
- src/observability/reporting/metric_recorder.py
- src/systems/economy_systems/economy.py
- src/core/state.py
- src/engine/kernel.py

## Assumptions / Open Questions
- Which of the two existing per-region-economy code paths (kernel-driven global metric_windows.jsonl vs. presenter's on-request per-region grouping) becomes the canonical wiring target is an open design decision, not dictated by the concern's original wording.
- src/systems/economy_systems/economy.py's unrelated pressure_signals consumer must be confirmed untouched by the chosen wiring approach before implementation.

## Implementation Notes

## Test Summary

## Files Changed

## Completion Summary
