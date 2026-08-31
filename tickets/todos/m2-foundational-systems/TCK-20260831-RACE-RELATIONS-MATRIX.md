---
status: active
layer: combat
authority: P1
audience: agent
ticket_id: TCK-20260831-RACE-RELATIONS-MATRIX
phase: open
date: 2026-08-31
tags: [faction, content, combat]
---

# TCK-20260831-RACE-RELATIONS-MATRIX

## Title
Author race-relations hostility matrix and wire it into legality/tactical scoring

## Status
OPEN

## Tier
standard

## Type
feature

## Priority
P1

## Request Summary
Race-relations hostility matrix — the highest content risk in the whole roadmap. Investigation found the gap is worse than "lookup table missing": RelationContext.target_race is set at 2 real live call sites (attack-legality and tactical scoring) but read by ZERO consuming logic in RelationProjectionService.project_relation() — both the content table and the consuming logic must be built. This ticket must not be started (not just not merged) until the metamorphic-lab pilot ticket is done, per both the concern text and an independently corroborating decision record.

## Scope
- Do not start this ticket until TCK-20260831-METAMORPHIC-LAB-PILOT has landed and passed — hard blocking dependency, stated explicitly here.
- Load a new race_relations content family via a new ContentFamilySpec + Pydantic model (extra="forbid") in src/content/repository.py, matching faction_relationships.yaml's convention — using the corrected schema shape, a flat List[RaceRelationRecord] (source_race/target_race/relationship_model/axes qualitative labels), not the roadmap concern text's stale Dict[Tuple[str,str], float].
- Wire RelationContext.target_race to actually be consumed by RelationProjectionService.project_relation(), resolving a race_relations entry and factoring axes.hostility into the returned label.
- Author a disclosed defensible subset of the 156 directed race pairs (13x12, excluding self-pairs) with explicit rationale for any pair left at a neutral default, following TCK-20260627-P2D-FACTION-RELS's coverage precedent — not all 156 uniformly.
- Run MutationLabOrchestrator.run_mutation_lab() against a real mutation spec varying race-relations hostility and confirm via MetamorphicRuleEngine that increasing hostility does not decrease combat-engagement rate for that pair, on at least one real corpus world.
- Update all 3 touched parity ledgers: docs/parity_ledger/combat_movement.yaml, docs/parity_ledger/social_narrative.yaml, docs/parity_ledger/strategic_cognition.yaml.

## Out of Scope
- Any change to faction_relationships.yaml's own content or FactionState relations — race relations is a separate content family, reusing only its schema convention.
- Starting implementation on this ticket before TCK-20260831-METAMORPHIC-LAB-PILOT is done — hard blocking dependency.

## Acceptance Criteria
- [ ] race_relations content family loads via a new ContentFamilySpec + Pydantic model (extra="forbid") in src/content/repository.py, matching faction_relationships.yaml's convention.
- [ ] RelationContext.target_race is actually consumed by RelationProjectionService.project_relation() to resolve a race_relations entry and factor axes.hostility into the returned label — verified by a test showing two race pairs with different authored hostility produce different projected labels.
- [ ] MutationLabOrchestrator.run_mutation_lab() is invoked against a real mutation spec varying race-relations hostility, and MetamorphicRuleEngine confirms increasing hostility does not decrease combat-engagement rate for that pair, on at least one real corpus world.
- [ ] Authored pair coverage is a disclosed defensible subset with explicit rationale for any neutral-default pair, not all 156 uniformly.
- [ ] This ticket must not be started until TCK-20260831-METAMORPHIC-LAB-PILOT is done, stated explicitly in Scope/Assumptions.

## Related Tickets
- TCK-20260627-P2D-FACTION-RELS
- TCK-20260523-METAMORPHIC-VALIDATION
- TCK-20260612-LAB-CONTRACT
- TCK-20260829-TEMPORAL-CALENDAR-AUTHORITY
- TCK-20260831-METAMORPHIC-LAB-PILOT (hard prerequisite — must land first)

## Related Docs
None.

## Related Stored Artifacts
None.

## Related Code Areas
- src/content_semantics/relation.py
- src/engine/legality.py
- src/engine/tactical.py
- src/lab/metamorphic.py
- src/lab/mutation_orchestrator.py
- src/content/repository.py

## Assumptions / Open Questions
- This ticket is HARD BLOCKED from starting (not just merging) until TCK-20260831-METAMORPHIC-LAB-PILOT is done — per both the concern text and TCK-20260829-TEMPORAL-CALENDAR-AUTHORITY's independently-corroborating decision record.
- Coverage must be a disclosed defensible subset of the 156 pairs, not uniform, following the faction-relations precedent's own rationale approach.
- This idea touches 3 parity ledgers — the widest single-idea cross-ledger footprint alongside idea 39.

## Implementation Notes

## Test Summary

## Files Changed

## Completion Summary
