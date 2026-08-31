---
status: active
layer: strategy
authority: P1
audience: agent
ticket_id: TCK-20260831-ROLE-MODEL-IMITATION
phase: open
date: 2026-08-31
tags: [strategy, cognition]
---

# TCK-20260831-ROLE-MODEL-IMITATION

## Title
Learning by Watching & Choosing Role Models

## Status
OPEN

## Tier
standard

## Type
feature

## Priority
P1

## Request Summary
Learning by Watching & Choosing Role Models. Investigation found the epic's "standalone, no cross-idea dependency" grouping for this idea is wrong — a hard dependency on idea 14 (species classification / intelligence_tier) was discovered during a Milestone-2 cross-cutting trace, because the imitation-sophistication scaling integration point cites intelligence_tier, a field idea 14 hasn't built yet. This idea is independently rated the weakest implementability fit of its ideation batch and needs genuinely new durable per-entity state (who a character watches/admires) — a prior atlas revision wrongly said no new state was needed; that was later corrected.

## Scope
- Do not start this ticket until TCK-20260831-SPECIES-INTELLIGENCE-TIER has landed and merged.
- Add a new typed role-model/imitation state on EntityState (who a character watches/admires) with a defined lifecycle, round-trip tested via serialize/deserialize — not a free-form field.
- Wire imitation-sophistication scaling to read intelligence_tier (landed by TCK-20260831-SPECIES-INTELLIGENCE-TIER) to modulate behavior.
- If this ticket must ship before intelligence_tier work completes for any reason, explicitly stub/defer the scaling with a documented known-limitation rather than silently coupling to a nonexistent field.
- Consider pairing with idea 22 (Relationship Roles, already shipped in M1) to make the role-model relationship visible — a suggested pairing, not a hard dependency.

## Out of Scope
- Any change to idea 14/intelligence_tier's own field definition or race classifications — consumed read-only here.
- Building idea 22's Relationship Roles system — already shipped, only optionally referenced.

## Acceptance Criteria
- [ ] This ticket's related_tickets MUST list TCK-20260831-SPECIES-INTELLIGENCE-TIER as a hard prerequisite — do not schedule/start before it lands.
- [ ] A new typed role-model/imitation state exists on EntityState with a defined lifecycle (who is watched/admired), not a free-form field, round-trip tested via serialize/deserialize.
- [ ] Imitation-sophistication scaling reads intelligence_tier (from the now-landed idea 14 ticket) to modulate behavior.
- [ ] If this ticket must ship before intelligence_tier work completes for any reason, the scaling is explicitly stubbed/deferred with a documented known-limitation, never silently coupled to a nonexistent field.

## Related Tickets
- TCK-20260831-SPECIES-INTELLIGENCE-TIER (hard prerequisite — must land first)

## Related Docs
- docs/brainstorm/rpg_expected_schemas.html

## Related Stored Artifacts
None.

## Related Code Areas
- src/strategy/cognition_capacity.py

## Assumptions / Open Questions
- Rated "the weakest implementability fit of the twelve" in its ideation batch, "medium at best" visible impact.
- This ticket must not be scheduled or started before idea 14 (TCK-20260831-SPECIES-INTELLIGENCE-TIER) lands — hard code-confirmed dependency (zero intelligence_tier concept anywhere in src/strategy/cognition_capacity.py today).

## Implementation Notes

## Test Summary

## Files Changed

## Completion Summary
