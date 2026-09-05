---
status: active
layer: strategy
authority: P1
audience: agent
ticket_id: TCK-20260905-BELIEF-INSTITUTION-DESIGN
phase: open
date: 2026-09-05
tags: [social, strategy]
---

# TCK-20260905-BELIEF-INSTITUTION-DESIGN

## Title
Idea 63 — Belief Grows Around Real History (BeliefInstitution)

## Status
OPEN

## Tier
standard

## Type
feature

## Priority
P2

## Request Summary
Design idea 63 (Belief Grows Around Real History, docs/brainstorm/rpg_feature_atlas.html) proposes belief/organized reverence that forms around real witnessed events (a hero surviving impossible odds, a shrine that outlasted a catastrophe) rather than an authored pantheon -- whether an actual god exists can stay an open question, the socially real part is that people believe something and organize around it. Confirmed directly: the CHURCH building's services list literally contains the strings ['BLESSING', 'RESURRECTION'] (src/town/buildings.py:23), and grepping all of src/ for either string being read or dispatched anywhere returns zero hits -- two tokens, not a mechanic, no religion/deity/pantheon code exists at all. The card names two real prerequisites: idea 36/40 (Clan, as the container an organized belief would need) and idea 57 (Chronicle-fed fame, the substrate belief would form around). Idea 36/40 is DONE (TCK-20260831-CLAN-STATE-SCHEMA, TCK-20260903-CLAN-LIFECYCLE-SUCCESSION) but investigation (2026-09-05) confirmed ClanState carries zero founding-myth/shared-belief field precedent today -- a belief-institution attachment point is wholly new state, not an extension of an existing shape. Idea 57 (fame substrate) had NO ticket filed anywhere before this epic -- it is being built as a sibling ticket, TCK-20260905-FAME-DERIVER-LEGEND-FACT, in this same batch. This ticket is HARD-BLOCKED (not merely sequenced) on that sibling ticket reaching DONE first, since idea 63 must consume idea 57's actual shipped FameState/LegendFact shape, not an assumed one. Investigation also confirmed the Knowledge/Belief BeliefEntry/KnowledgeFact split (TCK-20260904-KNOWLEDGE-BELIEF-REPRESENTATION-RECONCILIATION, DONE) is a deliberate, non-interchangeable two-track split -- BeliefEntry is for raw/observed/decaying claims with real live tactical consumers (cooperation risk, route-blocking), KnowledgeFact is for structured/queried settled information. Idea 63's belief-institution concept needs a genuinely new, third class -- BeliefInstitution -- distinct from both, per the reconciliation's own resolved split; it must not be built as a repurposing of either existing class, which would recreate the exact representation-fragmentation problem that reconciliation ticket was filed to prevent.

## Scope
- Design and implement a new BeliefInstitution typed durable class (src/systems/strategic_systems/ or a new module, per the atlas's own underspecified schema-63) with at minimum: origin_event_id (linking to the specific witnessed event/LegendFact it formed around), adherent_entity_ids (which entities believe/organize around it), belief_strength (a float representing how deeply held/widespread the belief is), and a clan_id or equivalent container link (per idea 63's own stated Clan-container dependency). Explicitly distinct from BeliefEntry and KnowledgeFact -- do not repurpose either.
- Wire BeliefInstitution formation to idea 57's actual shipped LegendFact/FameState output (from TCK-20260905-FAME-DERIVER-LEGEND-FACT, confirmed DONE and its real shape re-verified before this ticket's own Implement phase begins) -- a LegendFact/fame-threshold crossing is the only real, evidence-grounded trigger candidate found by investigation; do not invent a 'shrine that outlasted a catastrophe' trigger, since no such calamity-outcome signal exists anywhere in current code (confirmed: src/world/calamity.py has no structure/building-survival tracking, and grep for 'shrine' across src/ returns zero hits).
- Implement the card's own explicit requirement that different groups can interpret the same recorded event differently -- e.g. two different ClanState-linked BeliefInstitutions independently forming around the same origin_event_id with differing belief_strength or interpretation, rather than one single global belief record. This is new logic; CultureDeriver's own region-partitioned CultureState model groups the SAME event pool by region (not literally divergent interpretation of one identical event) and should be understood as a shape precedent only, not reused as-is.
- Write all durable BeliefInstitution state through a typed Update object applied via the authoritative apply path (src/engine/patches.py), per the Durable State Rule -- never a direct state mutation.
- Given the source schema (docs/brainstorm/rpg_expected_schemas.html#schema-63) itself describes idea 63 as 'too underspecified to build a new SimQ pillar around responsibly,' this ticket's own scope must stay to the BeliefInstitution mechanism itself (typed state, formation trigger, divergent-interpretation logic) and explicitly must NOT attempt to define a new SimQ scoring pillar or event-schema category for it.

## Out of Scope
- Any implementation work before TCK-20260905-FAME-DERIVER-LEGEND-FACT (idea 57) reaches DONE and its real FameState/LegendFact shape is re-confirmed -- this ticket's Investigate/Plan phases may proceed now, but Implement must wait.
- Repurposing BeliefEntry or KnowledgeFact for this mechanism -- confirmed the wrong shape by the Knowledge/Belief reconciliation's own resolved split; do not touch either class's core representation.
- Adding a new calamity-outcome/'shrine survival' signal to src/world/calamity.py -- no such signal exists today; inventing one would be an undisclosed second dependency beyond this ticket's own two named prerequisites (Clan, idea 57).
- Defining a new SimQ scoring pillar or CHURCH building mechanic wiring (the BLESSING/RESURRECTION services strings) -- the design doc itself defers both as too underspecified; do not resolve them here.
- Any change to idea 62's Chronicle-fidelity-drift transform -- a separate sibling ticket, not an input this ticket depends on per the atlas's own idea-63 card (which names only Clan and idea 57 as prerequisites).

## Acceptance Criteria
- This ticket's Implement phase does not begin until TCK-20260905-FAME-DERIVER-LEGEND-FACT is confirmed DONE in tickets/done/, verified by a direct check at the start of Implement.
- BeliefInstitution is a new typed dataclass distinct from BeliefEntry and KnowledgeFact, with origin_event_id, adherent_entity_ids, belief_strength, and a clan/container link, verified by a round-trip serialization test.
- A BeliefInstitution can only form when a real LegendFact (from idea 57's shipped implementation) exists for the origin_event_id it references -- verified by a test asserting no BeliefInstitution forms without a qualifying LegendFact.
- Two different clans can independently form BeliefInstitutions around the same origin_event_id with different belief_strength values, verified by a new test demonstrating divergent interpretation of one identical event.
- This ticket introduces zero changes to BeliefEntry's or KnowledgeFact's own field shapes or existing consumers (cooperation risk evaluation, route-blocking, guild rumors, InformationAssimilationService) -- verified by a source-text guard test and by their existing test suites passing unmodified.
- No new SimQ scoring pillar or CHURCH building service wiring is added by this ticket, verified by a source-text guard test confirming BLESSING/RESURRECTION remain unconsumed as before.

## Related Tickets
- TCK-20260905-EPIC-RPG-M5-HISTORY-BELIEF
- TCK-20260905-FAME-DERIVER-LEGEND-FACT
- TCK-20260905-CHRONICLE-FIDELITY-DRIFT
- TCK-20260904-KNOWLEDGE-BELIEF-REPRESENTATION-RECONCILIATION
- TCK-20260831-CLAN-STATE-SCHEMA
- TCK-20260903-CLAN-LIFECYCLE-SUCCESSION

## Related Docs
- docs/brainstorm/rpg_feature_atlas.html
- docs/brainstorm/rpg_expected_schemas.html
- docs/plans/rpg_design_roadmap/rpg_m5_memory_reputation_epic.md
- docs/brainstorm/2026-09-04-core-rpg-legacy-memory-axis-proposal.md
- docs/brainstorm/2026-09-04-idea57-entity-scale-fame-aggregation-design.md

## Related Stored Artifacts
None

## Related Code Areas
- src/systems/strategic_systems/belief.py
- src/core/self_model.py
- src/core/strategic.py
- src/core/state.py
- src/town/buildings.py
- src/domains/culture/deriver.py
- src/domains/culture/applicator.py
- src/world/calamity.py
- src/engine/patches.py

## Assumptions / Open Questions
- This ticket's Investigate/Plan phases can proceed now (scoping-only), but Implement is genuinely blocked on TCK-20260905-FAME-DERIVER-LEGEND-FACT reaching DONE -- not a hedge, a real hard dependency confirmed by investigation.
- The exact belief_strength formation/growth formula is a Plan-phase decision, to be made once idea 57's real LegendFact shape is confirmed, not resolved by investigation.
- Whether an actual in-game deity/supernatural effect exists remains explicitly out of scope per the card's own text -- this ticket models only the social/organizational belief structure, not any mechanical divine effect.

## Implementation Notes

## Test Summary

## Files Changed

## Completion Summary
