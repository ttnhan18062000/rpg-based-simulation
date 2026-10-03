---
status: historical
layer: strategy
authority: P2
audience: agent
ticket_id: TCK-20260410-PH3-STRATEGIC-KNOWLEDGE
artifact_type: test_plan
tags: [ph3, strategic, knowledge]
---

# Test Plan: Phase 3 Strategic Knowledge

## Strategic Uncertainty & Detours (Integration)
- **Test**: `tests/ai/test_strategic_uncertainty.py`
- **Focus**:
  - `test_strategic_detour_knowledge_blocker`: Verify that missing location information triggers `BlockerInferenceService`, which then drives `DetourSuggestionService` to spawn an `INVESTIGATE` objective.
  - `test_investigating_state_tactical_execution`: Verify that valid investigation objectives correctly set the `INVESTIGATING` AI state and drive movement towards rumored coordinates.

## Rumor Propagation & Ingestion
- **Verification**: Verified via manual inspection and `StrategicKnowledgeIngestionService` unit-level logic. Lead certainty decays by 0.9 on each hop, and directness by 0.8.

## Search Narrowing & History
- **Verification**: `SearchNarrowingService` tracks `visited_tiles` in `CandidateZoneRecord`. Verified that entities skip already-visited tiles when searching for a lead target.

## Regression
- **Test**: `pytest tests/ai/test_strategic_evaluator.py` (Verify existing scoring logic).
- **Test**: `pytest tests/core/test_snapshot_integrity.py`.
