---
status: active
layer: strategy
authority: P1
audience: agent
ticket_id: TCK-20260905-FAME-DERIVER-LEGEND-FACT
phase: open
date: 2026-09-05
tags: [social, strategy]
---

# TCK-20260905-FAME-DERIVER-LEGEND-FACT

## Title
Idea 57 — The Living Legend Feedback Loop (FameDeriver + LegendFact)

## Status
OPEN

## Tier
standard

## Type
feature

## Priority
P1

## Request Summary
Design idea 57 (The Living Legend Feedback Loop, docs/brainstorm/rpg_feature_atlas.html) proposes that once a hero's Chronicle-recorded fame crosses a threshold, it becomes a discoverable fact other entities can perceive and weigh into their Motivation & Doctrine. A design doc (docs/brainstorm/2026-09-04-idea57-entity-scale-fame-aggregation-design.md, already merged via PR #126) fully works out the aggregation-shape half: a FameDeriver/FameState/FameCarryForward/FameExporter/FameImporter 5-piece structure mirroring CultureDeriver's exact 3-layer pattern (src/domains/culture/deriver.py, model.py, exporter.py), keyed by NarrativeLedgerEntry.subject_id instead of payload['region_id']. It recommends Option B for which events feed fame: quest_completed entries (subject-attributed) plus entity_death where the deceased was entity_role==HERO (posthumous fame, reusing CultureDeriver's own existing hero_veneration event-type rule) -- explicitly NOT capturing in-life combat-earned fame, since no combat_victory event type exists in the Narrative Ledger today (a disclosed, accepted limitation, not silently worked around). This ticket implements that design as-is (already reviewed and merged, authoritative for its own scope) plus idea 57's own remaining scope: a new LegendFact class and fame_threshold's numeric value. Investigation (2026-09-05) found a real honesty gap in the epic doc's original framing of the remaining scope: "Perception-system discoverability wiring so Motivation & Doctrine can weigh a specific hero's fame" targets two systems confirmed DORMANT in the live pipeline today -- PerceptionUpdatePhase (zero call sites in AuthoritativeApplyPipeline.refine(), per docs/simulation/domains/perception_contract.md and TCK-20260831-DEAD-COGNITION-SCHEMA-DECISION) and MotivationBiasService.compute_bias_multiplier (zero call sites anywhere outside its own module, confirmed by grep). Additionally, idea 34's real implemented candidate-role set (src/ai/coming_of_age.py, _CANDIDATE_ROLES = (SHOPKEEPER, WORKER, GUARD)) has no ADVENTURER/HERO option to bias toward at all -- the illustrative "lean toward becoming an adventurer" scenario cannot be mechanically realized today without a separate, larger extension to idea 34's own candidate set, which is out of this ticket's scope.

## Scope
- Implement FameDeriver.derive(hierarchy, entity_names=None) -> Dict[str, FameState], keyed by entry.subject_id, summing entry.significance for quest_completed entries plus entity_death entries where payload['entity_role']=='HERO' (Option B), normalised via min(1.0, raw/NORMALISE_DENOMINATOR) exactly mirroring CultureDeriver._normalise -- per the already-merged design doc, verbatim.
- Implement FameState (frozen dataclass, new module e.g. src/domains/fame/model.py per the design doc's own reasoning for a new module over reusing culture/) and FameCarryForward (entity_id + FameState + derived_episode), mirroring CultureCarryForward's exact shape. Resolve the open axis-count question (single fame axis vs. fame+notoriety split mirroring SocialUpdate.heroism_delta/notoriety_delta) as a Plan-phase decision, documented with rationale.
- Implement FameExporter.export(campaign_state, hierarchy, episode_index, entity_names), called from the same CampaignOrchestrator._advance_state() episode-boundary call site as CultureDriftExporter.export() (orchestrator.py, alongside the existing call), writing into a new CampaignState.entity_fame: Dict[str, FameCarryForward] field. Implement FameImporter.get_fame(campaign_state, entity_id), a thin None-safe lookup matching CultureDriftImporter.get_culture()'s contract.
- Implement a new LegendFact class (typed durable state), explicitly named and structured to avoid collision with the pre-existing, unrelated LEGENDARY_ARRIVAL consequence-event concept (src/systems/social_systems/consequence_events.py, chronicle/significance.py's BASE_SIGNIFICANCE map) -- disambiguate explicitly in the ticket's own docs, do not conflate the two. A LegendFact is constructed/discoverable only once FameImporter.get_fame(...).fame (or the chosen axis) crosses a fame_threshold numeric constant, decided and documented during Plan phase (no existing anchor -- a real design-authority decision, same caution the atlas gives idea 34).
- Unit-test LegendFact's discoverability directly against PerceptionFilterService.filter() (src/domains/perception/filter.py) at the service level, WITHOUT wiring PerceptionUpdatePhase into any live pipeline phase and WITHOUT extending idea 34's candidate-role set. Document this honestly in Implementation Notes as "built, not yet visible in play" (matching idea 60's own precedent, TCK-20260904-REPUTATION-LOCALITY-SCOPE), not as a fully live end-to-end feature.

## Out of Scope
- Wiring PerceptionUpdatePhase into AuthoritativeApplyPipeline.refine() or any other live pipeline phase -- a separate, larger, already-disclosed gap (TCK-20260831-DEAD-COGNITION-SCHEMA-DECISION), not this ticket's to fix.
- Wiring MotivationBiasService.compute_bias_multiplier into any live call site -- same reasoning, a separate follow-up.
- Extending idea 34's (Coming of Age) candidate-role set to include an ADVENTURER/HERO option -- idea 34's own ticket scope, not this one; this ticket only makes LegendFact perceivable/queryable, it does not modify idea 34's decision logic.
- Adding a new combat_victory/monster_slain Narrative Ledger event type -- the design doc explicitly scopes this out as "new event-scoring, not aggregation"; the resulting in-life-combat-fame gap is a disclosed, accepted limitation of Option B.
- Idea 62's Chronicle-fidelity-drift transform and idea 63's belief-institution mechanism -- sibling/downstream tickets of the same epic; per this epic's own resolution, idea 57 does NOT need idea 62's output as an input.

## Acceptance Criteria
- FameDeriver.derive() on a hierarchy containing a quest_completed entry and a HERO entity_death entry for two different subject_ids produces two distinct non-zero FameState entries, each attributable to the correct subject_id, verified by a new test.
- FameExporter.export() is called from the same episode-boundary call site as CultureDriftExporter.export(), and an untouched entity's FameCarryForward from a prior episode is preserved (not reset) when a later episode produces zero new events for them, mirroring CultureDriftExporter's own carry-forward guarantee, verified by test.
- A LegendFact is constructed only when FameImporter.get_fame(...)'s relevant axis crosses the Plan-phase-decided fame_threshold; a fame value below threshold produces no LegendFact, verified by test.
- LegendFact is discoverable via a direct unit-level call to PerceptionFilterService.filter(), verified by a new test, without any change to PerceptionUpdatePhase's own call-site count (still zero in the live pipeline) or to idea 34's _CANDIDATE_ROLES.
- This ticket's own LegendFact class is never confused with or merged into the pre-existing LEGENDARY_ARRIVAL concept -- verified by a source-text guard test confirming both remain distinct, separately-named classes.

## Related Tickets
- TCK-20260905-EPIC-RPG-M5-HISTORY-BELIEF
- TCK-20260905-CHRONICLE-FIDELITY-DRIFT
- TCK-20260905-BELIEF-INSTITUTION-DESIGN
- TCK-20260831-DEAD-COGNITION-SCHEMA-DECISION
- TCK-20260902-COMING-OF-AGE-ARCHETYPE-CHOICE

## Related Docs
- docs/brainstorm/2026-09-04-idea57-entity-scale-fame-aggregation-design.md
- docs/brainstorm/rpg_feature_atlas.html
- docs/brainstorm/rpg_expected_schemas.html
- docs/plans/rpg_design_roadmap/rpg_m5_memory_reputation_epic.md
- docs/simulation/domains/perception_contract.md
- docs/mechanics/04_strategic_cognition.md

## Related Stored Artifacts
None

## Related Code Areas
- src/domains/culture/deriver.py
- src/domains/culture/model.py
- src/domains/culture/exporter.py
- src/domains/campaigns/state.py
- src/domains/campaigns/orchestrator.py
- src/domains/perception/filter.py
- src/domains/perception/phase.py
- src/domains/motivation/service.py
- src/ai/coming_of_age.py
- src/systems/social_systems/consequence_events.py
- src/domains/chronicle/significance.py

## Assumptions / Open Questions
- fame_threshold's numeric value and FameState's axis count (single vs. fame+notoriety split) are both explicitly open Plan-phase decisions, not resolved by investigation.
- This ticket has no dependency on idea 62's own ticket landing first (independent sibling, per this epic's own re-confirmed resolution) -- safe to implement in either order relative to it.
- Idea 63's own ticket is hard-blocked on this ticket reaching DONE, since it must consume this ticket's actual shipped FameState/LegendFact shape.

## Implementation Notes

## Test Summary

## Files Changed

## Completion Summary
