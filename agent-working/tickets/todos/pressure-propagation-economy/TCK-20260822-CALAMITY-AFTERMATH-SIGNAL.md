---
status: active
layer: world
authority: P1
audience: agent
ticket_id: TCK-20260822-CALAMITY-AFTERMATH-SIGNAL
phase: open
date: 2026-08-22
tags: [world, ecology]
---

# TCK-20260822-CALAMITY-AFTERMATH-SIGNAL

## Title
Define Calamity-Resolution Semantics and Build the calamity_aftermath Recovery Signal

## Status
OPEN

## Tier
standard

## Type
feature

## Priority
P2

## Request Summary
The calamity_aftermath cross-region signal specified in the idea doc -- when a calamity resolves in a region, surrounding regions get a temporarily elevated resource regen rate as a recovery signal -- was never built. Investigation found that calamity_intensity is monotonically non-decreasing in every current code path (CalamityService.apply_calamity_consequences only ever increases it by +0.05 on hero death), so a 'calamity resolved' trigger has no existing definition anywhere in the engine and cannot be assumed pre-existing -- it must be designed as an explicit part of this ticket's scope. Delivering the recovery signal also requires new typed, time-bounded durable state (no regen-multiplier field exists on RegionState or ResourceNodeState today) hooked into ResourceEcologyService.process_ecology(), which only runs every 200 ticks.

## Scope
- Define and document a 'calamity resolved' trigger (e.g. calamity_intensity crossing back below a documented threshold, or a new WorldEventCategory.CALAMITY_RESOLVED) that fires exactly once per resolution, deterministically for a fixed seed/tick.
- New typed, time-bounded regen-rate multiplier durable field (not a string in active_modifiers) applied to adjacent regions via _are_adjacent (ADJACENCY_GAP=50) on resolution.
- Wire the multiplier into ResourceEcologyService.process_ecology()'s effective_regen computation, with an expiry duration chosen relative to the 200-tick ECOLOGY_INTERVAL cadence so the recovery window is not missed between cadence checks.
- Update docs/mechanics/05_world_evolution.md and the relevant parity ledger entry; add a docs/guidelines/intentional_divergences.md entry if resolution/recovery semantics diverge from the idea doc's original formula.

## Out of Scope
- Any change to CalamityPressurePropagator's existing severity-propagation behavior (E52E) -- the recovery signal is additive, not a replacement for severity spread.
- Any change to the calamity_intensity increase-on-hero-death mechanic itself.
- General regen-rate/ecology tuning beyond the new recovery multiplier's own field, application, and expiry.

## Acceptance Criteria
- [ ] A defined 'calamity resolved' trigger fires exactly once per resolution, deterministic given a fixed seed/tick.
- [ ] On resolution, every adjacent region (per _are_adjacent, ADJACENCY_GAP=50) receives a typed, time-bounded regen-rate multiplier that measurably increases effective_regen versus the same scenario without the signal.
- [ ] The elevated regen rate expires after a documented duration; a region whose recovery window has elapsed reverts to normal regen_rate_per_tick*density_mod with no residual effect.
- [ ] A region with no adjacent resolved-calamity neighbor, or whose neighbor's calamity is still active, sees zero change to its regen rate.

## Related Tickets
- TCK-20260628-E52E-SEASONAL-PROPAGATION
- TCK-20260619-E33A-HEALTH-MONITOR

## Related Docs
- docs/mechanics/05_world_evolution.md
- docs/guidelines/intentional_divergences.md

## Related Stored Artifacts
None.

## Related Code Areas
- src/world/calamity.py
- src/domains/world_emergence/models.py
- src/world/ecology.py
- src/core/state.py
- src/domains/world_emergence/schema.py
- src/engine/world_dynamics.py

## Assumptions / Open Questions
- The exact 'resolved' threshold (e.g. calamity_intensity dropping below some documented value) and whether it requires a new WorldEventCategory.CALAMITY_RESOLVED enum member are open design decisions this ticket must make and document, not assumed pre-existing.
- The recovery-window duration relative to the 200-tick ECOLOGY_INTERVAL cadence is unspecified and must be chosen so the effect is not entirely missed between ecology passes.
- Whether the regen multiplier lives on RegionState or on individual ResourceNodeState entries is an open implementation choice not settled by investigation.

## Implementation Notes

## Test Summary

## Files Changed

## Completion Summary
