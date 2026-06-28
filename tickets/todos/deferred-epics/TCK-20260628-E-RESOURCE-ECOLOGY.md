---
status: active
layer: economy
authority: P1
audience: agent
ticket_id: TCK-20260628-E-RESOURCE-ECOLOGY
phase: open
date: 2026-06-28
tags: [epic, resource-ecology, regeneration, economy, p3, deferred, blocked]
---

# TCK-20260628-E-RESOURCE-ECOLOGY

## Title
Epic: Resource Ecology Regeneration — complete complex regeneration cycles

## Status
BLOCKED

## Tier
epic

## Type
feature

## Priority
P3

## Request Summary
Basic per-tick resource regeneration is implemented (E21B — `ResourceNodeRegenerationService`
with seasonal multipliers). Remaining gaps are density-dependent rates, multi-stage
ecological cycles, and cross-region pressure propagation. These are the mechanisms that
drive boom/bust cycles → migration → territorial conflict → faction war.

**Gate conditions:**
- P0-A/B/C fixes: DONE ✓
- D06 5,000-tick run: NOT YET DONE ⛔ — required to observe long-run ecological dynamics
  before scoping the repair.

**Status: BLOCKED pending 5,000-tick D06 validation run.**

## Block Resolution

Run `make lab-run-long TICKS=5000 SEED=42` (or equivalent D06 harness) after P0 fixes
have been active for at least one test run. Capture:
- Resource node depletion curves per region.
- Entity migration pressure correlated with scarcity.
- `RegionalPressureModel` outputs over time.

Once this data is available, unblock this epic and scope child tickets based on observed
failure modes.

## Scope (preliminary — subject to 5k-tick findings)
1. Density-dependent regeneration rates (high-entity-density regions regenerate slower).
2. Multi-stage ecological cycles (depletion → low-yield recovery → full recovery phases).
3. Cross-region pressure propagation (scarcity in region A increases migration pressure
   toward resource-rich region B).

## Out of Scope
- Basic per-tick regeneration (done by E21B — do not re-implement).
- Economy/trade systems (these are downstream consumers, not producers).

## Acceptance Criteria
- [ ] A 5,000-tick run shows at least one full depletion-recovery cycle per region.
- [ ] Entity migration pressure correlates with resource scarcity in affected regions.
- [ ] Economy emergence ceiling rises to 4–5 per D01 assessment.
- [ ] No resource node reaches permanent zero-state without ecological event trigger.

## Related Tickets
- Parent: TCK-20260627-P3A-DEFERRED-EPICS
- Block dependency: D06 5,000-tick run (TCK-20260628-E-LONGRUN-REGRESSION covers the
  harness; run it first to get the 5k data)
- Prior: E21B (ResourceNodeRegenerationService — DONE)

## Related Docs
- `docs/audits/D01_rpg_feature_impact.md` §Resource Ecology Regeneration
- `docs/audits/D06_longrun_health.md` — long-run health metrics
- `docs/mechanics/03_economic_laws.md` §resource pressure

## Related Stored Artifacts
- N/A (will populate after 5k-tick run)

## Related Code Areas
- `src/domains/economy/` — ResourceNodeRegenerationService
- `src/world/emergence/` — RegionalPressureModel, ScarcityModel
- `src/engine/world_dynamics.py` — WorldEmergencePhase

## Assumptions / Open Questions
- The 5k-tick run is the primary scoping input. Do not estimate complexity until it runs.

## Implementation Notes

## Test Summary

## Files Changed

## Completion Summary
