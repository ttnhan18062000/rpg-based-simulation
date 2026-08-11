---
status: active
layer: strategy
authority: P1
audience: agent
ticket_id: TCK-20260811-MEMORY-INFORMED-ROUTE-SCORING
phase: open
date: 2026-08-11
tags: [cognition, adventure]
---

# TCK-20260811-MEMORY-INFORMED-ROUTE-SCORING

## Title
Wire memory-informed candidates into adventure route scoring (descoped)

## Status
OPEN

## Tier
standard

## Type
feature

## Priority
P3

## Request Summary
Deepen adventure's internal reasoning by wiring memory-informed candidates via src/domains/memory/ into route generation/scoring, so entities' own causal memory measurably shapes route decisions instead of being ignored entirely -- descoped from the author's original vendor-cheating example, which investigation found is not buildable with the memory system's current 4 hardcoded event kinds.

## Scope
- AdventureRouteGenerator/AdventureRouteScorer read entity.cognition.memory's existing CausalMemoryEntry.future_advice values (currently zero references)
- A route family whose future_advice already exists after one of the 4 supported event_kinds (combat_loss, failed_search, failed_craft, party_abandoned) measurably suppresses/promotes that route family's score or benefit term
- New memory read stays the entity's own subjective belief, consistent with scoring.py's documented 'reads only subjective self-model aspects to protect information opacity' boundary

## Out of Scope
- The literal 'vendor who previously cheated the entity' example from the original proposal -- NOT buildable: CausalAttributionService.attribute() has no vendor/trade/cheating event_kind, and buy_item opportunities key to a shop/structure id, not an NPC vendor entity id; would require a new vendor-entity concept, out of scope for this ticket
- Capability-estimate-driven confidence (TCK-20260811-CAPABILITY-CONFIDENCE-ADVENTURE-SCORING) and relationship-aware FORM_PARTY (TCK-20260811-RELATIONSHIP-AWARE-FORM-PARTY) -- separate tickets, different risk/scope
- Any change to AdventureGoalScorer/AdventureDecisionService's wrapper migration -- this concern is orthogonal but touches the same files; recommend landing after that migration settles to avoid merge churn

## Acceptance Criteria
- [ ] A route family whose CausalMemoryEntry.future_advice already exists (e.g. 'avoid_enemy' after combat_loss, 'boost_party_trust' after party_abandoned) measurably suppresses/promotes the matching route family's score/benefit vs. an entity with no matching causal memory
- [ ] The vendor-cheating example is explicitly NOT scoped as a buildable AC for this ticket
- [ ] STRAT-227 parity entry gains a test_path (currently null)

## Related Tickets
- TCK-20260805-SIMQ-ECONOMY-ADVENTURE-ROUTE-SCORER-BIAS

## Related Docs
- docs/mechanics/04_strategic_cognition.md
- docs/parity_ledger/strategic_cognition.yaml

## Related Stored Artifacts
None.

## Related Code Areas
- src/domains/adventure/generator.py
- src/domains/adventure/scoring.py
- src/domains/memory/attribution.py
- src/domains/memory/phase.py

## Assumptions / Open Questions
- Idea's headline example (vendor-cheating) is unbuildable as originally stated and has been descoped to what memory already supports; implementing the literal example would require a new vendor-entity concept, out of scope
- Sequencing/merge conflict risk with the adventure/cognition wrapper migration tickets (which declare AdventureRouteScorer/Generator 'unchanged internally') -- recommend landing after those settle, or explicitly disclaim the risk if landed concurrently
- Related design doc: docs/architecture/2026-08-11-adventure-as-cognition-strategy-subcomponent-design.md (Future Extension Patterns)

## Implementation Notes

## Test Summary

## Files Changed

## Completion Summary
