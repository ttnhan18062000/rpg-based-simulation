---
status: active
layer: strategy
authority: P1
audience: agent
ticket_id: TCK-20260810-COGNITION-PROFILE-ADVENTURE-ELIGIBILITY
phase: open
date: 2026-08-10
tags: [cognition, strategy]
---

# TCK-20260810-COGNITION-PROFILE-ADVENTURE-ELIGIBILITY

## Title
Cognition-driven adventure eligibility replacing hardcoded HERO role gate

## Status
OPEN

## Tier
standard

## Type
feature

## Priority
P1

## Request Summary
User requested a full fix making adventure-routing eligibility general rather than blindly bound to the HERO role: "generalize is a must-do... you should make it general, then provide maybe configuration to what kind of race/faction to have adventure logics." This ticket replaces the hardcoded `entity.identity.role == EntityRole.HERO` check in `AdventureDecisionPhase.apply()` with a `supports_adventure_routing` flag on `CognitionProfileDefinition`, so any sufficiently cognitively-capable race/faction (elf, human, dwarf, ...) becomes adventure-eligible regardless of role, while instinctive/simple races (wolf, slime, ...) never are, and the existing human/practical_humanoid hero behavior is preserved exactly (zero-regression).

## Scope
- Add `supports_adventure_routing: bool = False` field to `CognitionProfileDefinition` (`src/content/schema.py`)
- Author explicit `supports_adventure_routing` values for all 7 cognition profiles in `data/content/living/cognition_profiles.yaml`, based on real cross-referencing of `disciplined_guard`/`trade_pragmatist` usage in `data/content/social/roles.yaml` and `data/content/entities/entity_archetypes.yaml` — a deliberate evidence-based decision, not a default-False guess
- Replace the hardcoded `entity.identity.role == EntityRole.HERO` check in `AdventureDecisionPhase.apply()` (`src/domains/adventure/phase.py` line 76) with a check against the entity's resolved `cognition_profile.supports_adventure_routing`
- Verify the `cognition_profile_id` resolution path (`src/content/resolver.py`, `src/entities/archetype_factory.py`) is cheap/cached per-tick, consistent with `phase.py`'s existing "resolve once before loop" pattern, to avoid a per-tick per-hero performance regression
- Add a zero-regression test: human/practical_humanoid hero scenario produces identical outcome pre/post fix for a fixed seed/tick count
- Add a negative-case test: an instinctive_animal-profile entity with role artificially set to HERO is NOT included in adventure routing

## Out of Scope
- The 2 other `EntityRole.HERO` checks in `src/domains/adventure/scoring.py` (lines 161, 252) that affect QUEST_OPPORTUNITY scoring — a different concern (scoring, not eligibility), explicitly out of scope per design non-goals
- C2's interruption-bypass generalization (`evaluate_project_switch`) in `src/systems/strategic_systems/intelligence.py`
- Documentation updates to `docs/mechanics/04_strategic_cognition.md`, `docs/simulation/domains/adventure_contract.md`, and `docs/parity_ledger/strategic_cognition.yaml` — tracked in sibling ticket TCK-20260810-COGNITION-ELIGIBILITY-BYPASS-DOCS (C3), not this ticket
- `docs/audits/D22_dormant_content_wiring.md` — tracked in TCK-20260810-D22-DORMANT-WIRING-AUDIT (C4)

## Acceptance Criteria
- [ ] `CognitionProfileDefinition` gains `supports_adventure_routing: bool = False`; all 7 profiles in `data/content/living/cognition_profiles.yaml` get explicit authored values after real cross-referencing of `disciplined_guard`/`trade_pragmatist` usage
- [ ] `AdventureDecisionPhase.apply()`'s eligibility filter (`src/domains/adventure/phase.py:76`) no longer references `EntityRole.HERO` — a non-hero entity with `supports_adventure_routing=True` is included, and a HERO-role entity whose profile has `supports_adventure_routing=False` is excluded
- [ ] Zero-regression: human/practical_humanoid hero scenario produces identical outcome pre/post fix for a fixed seed/tick count
- [ ] Negative case: an instinctive_animal-profile entity with role artificially set to HERO is NOT included — proves "regardless of role" holds in both directions
- [ ] `cognition_profile_id` resolution is confirmed cheap/cached per-tick (not a new per-entity catalog lookup cost) consistent with `phase.py`'s existing resolve-once pattern

## Related Tickets
- TCK-20260703-ADVENTURE-ELIGIBILITY-ROLE-FILTER
- TCK-20260808-HERO-ADVENTURE-ROUTING-DEFAULT-OFF
- TCK-20260810-COMBAT-BRAVERY-QUARTILE-ENGAGEMENT-INVERSION

## Related Docs
- docs/mechanics/04_strategic_cognition.md
- docs/simulation/domains/adventure_contract.md
- docs/parity_ledger/strategic_cognition.yaml

## Related Stored Artifacts
None.

## Related Code Areas
- src/domains/adventure/phase.py
- src/content/schema.py
- data/content/living/cognition_profiles.yaml
- data/content/living/races.yaml
- data/content/social/roles.yaml
- data/content/entities/entity_archetypes.yaml
- src/entities/archetype_factory.py
- src/content/resolver.py
- src/strategy/cognition_capacity.py
- src/domains/adventure/scoring.py

## Assumptions / Open Questions
- disciplined_guard/trade_pragmatist need a deliberate evidence-based `supports_adventure_routing` decision — no test currently targets these two roles
- scoring.py's 2 other HERO checks are explicitly out of scope but share the same file family — real risk of scope creep or reviewer confusion
- the negative-case test (HERO-role instinctive_animal) requires direct test-only entity construction since this combination doesn't occur in real content
- cognition_profile_id resolution must be confirmed cheap/cached, not assumed, before landing

## Implementation Notes

## Test Summary

## Files Changed

## Completion Summary
