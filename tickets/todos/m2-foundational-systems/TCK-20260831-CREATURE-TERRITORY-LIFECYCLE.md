---
status: active
layer: world
authority: P1
audience: agent
ticket_id: TCK-20260831-CREATURE-TERRITORY-LIFECYCLE
phase: open
date: 2026-08-31
tags: [world, ecology]
---

# TCK-20260831-CREATURE-TERRITORY-LIFECYCLE

## Title
Creature Territories & Simple Life Cycles

## Status
OPEN

## Tier
standard

## Type
feature

## Priority
P1

## Request Summary
Creature Territories & Simple Life Cycles. Investigation confirmed this is substantial new subsystem work, not small wiring: monsters get zero biological simulation today, since BiologicalSystem gates hunger/sleep decay to entity.kind in [HERO, VILLAGER] only. CampService already couples camp maturity growth to regional trauma (trauma_score>50.0 -> maturity delta x1.5, matching Mechanics Bible Ch5 §2's exact threshold) — a real existing precedent for the SHAPE of tuning this idea needs, though not the actual per-species numeric values, which are genuinely free creative territory.

## Scope
- Build a creature life-cycle/territory maturity system applying a per-tick maturity delta to monster-kind entities anchored to a camp/territory, increasing when the owning region's trauma_score>50.0, reusing CampService's existing 1.5x multiplier shape.
- Add life-stage transition or new-territory-occupant spawning when creatures reach a defined maturity/age threshold.
- Explicitly decide whether the existing HERO/VILLAGER-only biological gate is respected (monsters stay outside generic hunger/sleep) or superseded, recording any supersession in docs/guidelines/intentional_divergences.md.
- Author per-species pacing constants as real inspectable content and pass at least one metamorphic directional check (region trauma increase does not decrease maturity growth rate) — a good candidate to run through the metamorphic lab tooling once proven working by the pilot ticket.
- Ship behind a FeatureMode flag, default OFF.
- Independently verify no hidden live consumer of CampState/maturity fields exists before extending them, since the atlas has no Cross-Cutting Risk table entry for this idea at all.

## Out of Scope
- Generic hunger/sleep biological simulation expansion beyond monster-kind entities.
- Any change to CampService's existing trauma-to-maturity multiplier for camps themselves — reused, not modified.

## Acceptance Criteria
- [ ] A creature life-cycle/territory maturity system applies a per-tick maturity delta to monster-kind entities anchored to a camp/territory, increasing when owning region's trauma_score>50.0 (reusing CampService's existing 1.5x multiplier), verified by a deterministic test comparing trauma<=50 vs trauma>50 regions.
- [ ] Creatures reaching a defined maturity/age threshold transition life stage or spawn a new territory occupant, verified by a test advancing tick state past the threshold.
- [ ] The existing HERO/VILLAGER-only biological gate is either respected (monsters stay outside generic hunger/sleep) or superseded with an explicit intentional_divergences.md entry.
- [ ] Per-species pacing constants are real inspectable content and pass at least one metamorphic directional check (region trauma increase does not decrease maturity growth rate).
- [ ] Ships behind a FeatureMode flag, default OFF.

## Related Tickets
None.

## Related Docs
- docs/mechanics/05_world_evolution.md
- docs/parity_ledger/world_dynamics.yaml

## Related Stored Artifacts
None.

## Related Code Areas
- src/world/camp.py
- src/systems/lifecycle_systems/biological.py
- src/engine/world_dynamics.py

## Assumptions / Open Questions
- No Cross-Cutting Risk table entry exists for this idea at all — a gap in the atlas's own risk pass; this ticket should independently verify no hidden live consumer of CampState/maturity fields before extending them.
- Per-species numeric pacing has zero anchor anywhere — genuinely free creative territory per Content & Balance Requirements.

## Implementation Notes

## Test Summary

## Files Changed

## Completion Summary
