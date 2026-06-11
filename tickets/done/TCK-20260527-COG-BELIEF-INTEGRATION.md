---
status: historical
layer: misc
authority: P1
audience: agent
ticket_id: TCK-20260527-COG-BELIEF-INTEGRATION
phase: done
date: 2026-05-27
tags: [cog, belief, integration]
---

# TCK-20260527-COG-BELIEF-INTEGRATION

## Title

Wire Belief System into Actual Gameplay

## Status

DONE

## Tier
standard

## Type
chore

## Priority
P1

## Request Summary

Implement a minimal belief-to-action path in the simulation where guild intel creates rumors, direct observations upgrade or contradict belief certainty, and detours weigh lead certainty and source trust to influence final actions.

## Scope

- Connect guild intel: ensures it creates rumor-type beliefs with proper source/certainty mapping.
- Connect direct observation: updates or contradicts belief certainty.
- Implement contradiction tracking: contradiction increments contradiction count and reduces future lead utility.
- Implement detour selection weighting: detour selection weighs lead certainty and source trust, ignoring/deprioritizing exhausted or contradicted leads.
- Emit belief events: outputs events for belief creation, contradiction, and exhaustion.
- Add comprehensive unit tests, integration tests, and belief-driven behavior tests.

## Out of Scope

- Implementing persistent multi-agent dialogue systems for contract negotiation.

## Acceptance Criteria

- Guild intel successfully creates `BeliefEntry` / `LeadState` with source type `"rumor"` / `LeadCertainty.VAGUE`.
- Direct observation upgrades or contradicts belief certainty appropriately, incrementing contradiction counts.
- Detour selection deprioritizes contradicted / exhausted leads.
- Event tracking captures belief creation, contradiction, and exhaustion.
- All tests pass without regression.

## Related Tickets

- `TCK-20260527-COG-GOAL-REGISTRY.md`

## Related Docs

- `entity_cognition_fix_phase0.md`

## Related Stored Artifacts

- None

## Related Code Areas

- `src/systems/strategic_systems/belief.py`
- `src/systems/strategic_systems/intelligence.py`
- `src/core/strategic.py`

## Assumptions / Open Questions

- None

## Implementation Notes

- Successfully integrated first-class `beliefs` dictionary into `StrategicComponent` and serialized it cleanly in the canonical representation.
- Implemented state-update propagation of belief additions/deletions in `StrategicUpdate` and applied it through `StrategicPatch`.
- Refactored fused strategic location checks to correctly verify direct observations or trigger contradiction/exhaustion states.
- Enhanced detour suggestions with a dynamic scoring function utilizing source trust and contradiction penalties.

## Test Summary

- Created comprehensive test suite in `tests/unit/strategic/test_belief_integration.py` covering rumor generation, direct observation verification, contradiction degradation, source trust weighting, and detour loop suppression.
- Executed all 124 strategic unit tests, all of which passed successfully.

## Files Changed

- `src/systems/strategic_systems/belief.py`
- `src/systems/strategic_systems/detour.py`
- `src/systems/strategic_systems/intelligence.py`
- `src/core/strategic.py`
- `src/core/updates.py`
- `src/core/state.py`
- `src/engine/patches.py`
- `src/systems/social_systems/guilds.py`
- `tests/unit/strategic/test_belief_integration.py`

## Completion Summary

- Wired first-class belief-to-action path successfully, meeting all architectural, testing, and gameplay mechanics requirements.
