---
status: active
layer: world
authority: P1
audience: agent
ticket_id: TCK-20260831-SPECIES-INTELLIGENCE-TIER
phase: open
date: 2026-08-31
tags: [content]
---

# TCK-20260831-SPECIES-INTELLIGENCE-TIER

## Title
Add intelligence_tier to RaceDefinition (species classification layer)

## Status
OPEN

## Tier
standard

## Type
feature

## Priority
P1

## Request Summary
Add an intelligence_tier field to RaceDefinition, anchored via natural_traits containing tool_user (not attribute_tendencies.intelligence, a false friend), so the 13-race roster gets an explicit high/low classification. This is the foundation idea 27's imitation-sophistication scaling later depends on.

## Scope
- Add intelligence_tier: enum(high|low) to RaceDefinition (src/content/schema.py:134-143), pydantic-validated.
- Author explicit intelligence_tier values for all 13 races in data/content/living/races.yaml, using the tool_user-in-natural_traits anchor confirmed correct for 6/13 (human, goblin, orc, elf, dwarf, lizardfolk).
- Explicitly review and justify the dragonkin and spirit edge cases (both have high/medium_high attribute_tendencies.intelligence and cognition_profile=arcane_scholar, same profile as elf, but lack tool_user in natural_traits) rather than mechanically applying the anchor rule.
- Add a regression test asserting each of the 13 races' intelligence_tier matches the documented anchor rule with justified exceptions.
- Decide and document whether this ticket requires at least a stub consumer/predicate given zero real consumers exist today, or leaves wiring fully out of scope.

## Out of Scope
- settlement_capacity — this is idea 44's field, NOT part of M2's scoped idea list (M2 covers ideas 2,4,5,6,8,11,14,23,27,28,30,35,36,37,43,48); the epic's own text incorrectly said this ticket needs it, but that conflict is resolved by exclusion.
- Wiring intelligence_tier into coming-of-age (idea 34, itself unbuilt and gated on idea 32) or into a Progression Planner eligibility gate (none currently exists).

## Acceptance Criteria
- [ ] RaceDefinition gains intelligence_tier: enum(high|low), pydantic-validated.
- [ ] All 13 races get an explicit authored intelligence_tier derived from the tool_user-in-natural_traits anchor, with dragonkin/spirit exceptions explicitly reviewed and justified in the ticket, not silently mechanized.
- [ ] A regression test asserts each of the 13 races' intelligence_tier matches the documented anchor rule with justified exceptions.
- [ ] settlement_capacity (idea 44) is explicitly OUT of scope for this ticket.

## Related Tickets
- TCK-20260810-COGNITION-PROFILE-ADVENTURE-ELIGIBILITY

## Related Docs
- docs/mechanics/content_usage_matrix.md
- docs/brainstorm/rpg_expected_schemas.html

## Related Stored Artifacts
None.

## Related Code Areas
- src/content/schema.py
- src/content/repository.py
- data/content/living/races.yaml

## Assumptions / Open Questions
- dragonkin and spirit are genuine mechanical edge cases against the tool_user anchor rule and require an explicit design review, not silent mechanization.
- settlement_capacity epic-doc-vs-atlas-schema-doc conflict is resolved by excluding it from this ticket.
- intelligence_tier will land with zero real production consumers today — the ticket must decide whether a stub predicate is required.
- layer assigned as `world` (species/race content data lives under data/content/living/ and src/content/, closest registered fit to worldbuilding content; no dedicated `content` layer exists in registries/layer_registry.jsonl).

## Implementation Notes

## Test Summary

## Files Changed

## Completion Summary
