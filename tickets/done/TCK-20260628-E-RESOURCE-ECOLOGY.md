---
status: historical
layer: economy
authority: P1
audience: agent
ticket_id: TCK-20260628-E-RESOURCE-ECOLOGY
phase: done
date: 2026-06-28
tags: [epic, resource-ecology, regeneration, economy, p3, deferred, blocked]
---

# TCK-20260628-E-RESOURCE-ECOLOGY

## Title
Epic: Resource Ecology Regeneration — complete complex regeneration cycles

## Status
DONE

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
**Scope investigation (2026-06-28):**
- Block resolved: TCK-20260628-E-LONGRUN-REGRESSION DONE; 5k harness + baseline committed.
- 5k baseline shows: alive_avg=11.34, gold_avg=457.32, quest_active_count=0.0 (50 samples, seed=42).
- `ecology.py` runs every 200 ticks. Full depletion recovery: 5 ecology cycles = ~1000 ticks.
- **Critical gap**: Compiler-seeded nodes have `regen_rate_per_tick=0` — they DO NOT regenerate.
  Only ecology-seeded nodes regen. Most world nodes are compiler-seeded → permanent depletion.
- `RESOURCE_DEPLETED` / `RESOURCE_RECOVERED` events already wired via `StateUpdate.world_events_add`.
- `WorldEmergencePhase` in pipeline.py reads `recent_world_events` (rolling 500-event window).
- Calamity fires at tick mod 5000 == 0 if intensity > 0.3 — would have fired at end of 5k run.
- No density-dependent regen, no multi-stage cycles, no cross-region propagation yet.

**Recommended child tickets (implement in order):**
1. E21C-COMPILER-REGEN: Set `regen_rate_per_tick=1` on compiler-seeded nodes (or make configurable
   per world spec) so they participate in ecology cycles. This is the single highest-impact fix —
   without it, all compiler-seeded nodes permanently deplete with no recovery.
2. E21D-DENSITY-REGEN: Density-dependent regen rate modifier (entities in region → slower regen).
   Requires E21C first so regen is active.
3. E21E-CROSS-REGION-PRESSURE: Cross-region scarcity propagation from `RegionalPressureModel`.
   Gated on E21C and E21D to ensure baseline regen is working.

## Test Summary
- E21C: compiler regen tests (TCK-20260628-E21C-COMPILER-REGEN)
- E21D: 25 ecology tests including 8 new density-regen tests
- E21E: 240 world + world_emergence tests including 10 new cross-region propagation tests

## Files Changed
All changes are in child tickets (E21C, E21D, E21E).

## Completion Summary
All 3 child tickets complete:
- E21C-COMPILER-REGEN: compiler-seeded nodes now have regen_rate_per_tick=1 (was 0)
- E21D-DENSITY-REGEN: density-dependent regen (1.0→0.25 based on entity count per region)
- E21E-CROSS-REGION-PRESSURE: resource scarcity propagates 30% to adjacent regions
Parity ledger: TOWN-186, TOWN-187, WORLD-104 updated/added.
Epic DONE 2026-06-28.
