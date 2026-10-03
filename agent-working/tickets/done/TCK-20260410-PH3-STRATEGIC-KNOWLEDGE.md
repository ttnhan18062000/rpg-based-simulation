---
status: historical
layer: strategy
authority: P1
audience: agent
ticket_id: TCK-20260410-PH3-STRATEGIC-KNOWLEDGE
phase: done
date: 2026-04-10
tags: [ph3, strategic, knowledge]
---

# TCK-20260410-PH3-STRATEGIC-KNOWLEDGE

## Title
Implementation of Phase 3 Strategic Knowledge: Leads, Blockers, and Detours

## Status
DONE

## Tier
standard

## Type
chore

## Priority
P1

## Request Summary
Implement the strategic knowledge layer as defined in `thinking_implementation_phase_3.md`. This involves moving away from "fake omniscience" by representing uncertainty as durable leads, candidate zones, and typed blockers that drive detour branching.

## Scope
- [x] Define enriched `LeadRecord`, `HypothesisRecord`, and `CandidateZoneRecord` models.
- [x] Expand `BlockerRecord` with explicit taxonomy and detour metadata.
- [x] Implement `StrategicKnowledgeIngestionService` to normalize inputs from world producers.
- [x] Refactor Guild, Blacksmith, and Class Hall handlers to emit structured leads/blockers.
- [x] Upgrade Gossip propagation to support rumors and strategic leads with confidence decay.
- [x] Implement Blocker Inference and Detour Suggestion logic.
- [x] Implement Search History tracking and Narrowing logic.

## Out of Scope
- Revision of Phase 2 Strategic Appraisal scoring (unless required for blockers).
- Full implementation of social contracts (reserved for later phase).

## Acceptance Criteria
- [x] Uncertain information is stored as structured leads with provenance and reliability.
- [x] Blockers produce suggested detours (e.g., location unknown -> investigate).
- [x] Guild/Blacksmith/Class Hall outputs are converted into durable strategic knowledge.
- [x] Gossiped leads retain indirect provenance and degraded confidence.
- [x] All Phase 3 unit and integration tests pass.

## Related Tickets
- TCK-20260410-PHASE-2-ALIGNMENT (Prerequisite)

## Related Docs
- thinking_implementation_phase_3.md
- thinking_high_level_implementation.md

## Related Stored Artifacts
- stored_artifacts/TCK-20260410-PH3-STRATEGIC-KNOWLEDGE/

## Related Code Areas
- src/core/models/strategy.py
- src/ai/brain.py
- src/core/logic/strategic_knowledge_ingestion.py
- src/core/logic/knowledge_propagation.py
- src/ai/strategy/blocker_inference.py
- src/ai/strategy/detour_suggestion.py
- src/ai/strategy/objective_to_goal_mapper.py

## Assumptions / Open Questions
- **Assumption**: `BeliefRecord` will remain as is, focusing on entity-perception, while leads handle non-entity knowledge.
- **Decision**: Candidate zones use region-based anchors with search history tracking (`visited_tiles`).

## Implementation Notes
- Strategic updates use the `StrategicUpdate` intent pattern for snapshot safety.
- Detours are spawned as first-class objectives with `detour_` prefixes for traceability.
- Confidence scaling in `ObjectiveToGoalMapper` prevents certainty collapse.

## Test Summary
- `tests/ai/test_strategic_uncertainty.py`: Integration tests for blocker detection, detour spawning, and search execution. (PASSED)
- `tests/ai/test_strategic_evaluator.py`: Regression verification for Phase 2 scoring. (PASSED)

## Files Changed
- src/core/models/strategy.py
- src/actions/base.py
- src/ai/brain.py
- src/core/logic/strategic_knowledge_ingestion.py
- src/core/logic/knowledge_propagation.py
- src/ai/strategy/blocker_inference.py
- src/ai/strategy/detour_suggestion.py
- src/ai/strategy/objective_derivation.py
- src/ai/strategy/objective_to_goal_mapper.py
- src/ai/states/navigation.py
- src/core/logic/search_narrowing.py

## Completion Summary
Phase 3 is 100% complete. The strategic cognition engine now handles structural uncertainty. Entities can receive rumors with degraded confidence, detect when they are blocked by missing knowledge or capability, and automatically spawn remedial detours (investigation, training, collection) to resolve these blockers. Persistent search history prevents redundant exploration, ensuring that investigation is a cumulative process of elimination.
