---
status: historical
layer: strategy
authority: P2
audience: agent
ticket_id: TCK-20260410-PH3-STRATEGIC-KNOWLEDGE
artifact_type: plan
tags: [ph3, strategic, knowledge]
---

# Implementation Plan - Phase 3 Strategic Knowledge

Phase 3 implements the "Uncertainty, Leads, and Blocker-Driven Investigation" layer. The goal is to move from fake omniscience to a structural representation of uncertain world knowledge that drives investigative behavior and branching detours.

## User Review Required

> [!IMPORTANT]
> This phase modifies the `StrategicState` and existing building handlers (`VisitGuildHandler`, etc.). It will shift AI behavior from "magically knowing where to go" to "having to investigate leads."

> [!WARNING]
> The `LeadRecord` and `BlockerRecord` models in `src/core/models/strategy.py` will be significantly expanded, potentially requiring updates to existing snapshots or test mocks.

## Proposed Changes

### Core Models

#### [MODIFY] [strategy.py](file:///home/vboxuser/Work/rpg-based-simulation/src/core/models/strategy.py)
- Enrich `LeadRecord`: Add subject, source_type, directness, source_confidence, semantic_tags, and related_project_ids.
- Enrich `BlockerRecord`: Add explicit taxonomy (KNOWLEDGE, CAPABILITY, etc.), severity, detour suggestions, and resolution tracking.
- [NEW] Add `HypothesisRecord` and `CandidateZoneRecord` for representing spatial and semantic uncertainty.

### Logic Services

#### [NEW] `src/core/logic/strategic_knowledge_ingestion.py`
- Centralized service to normalize information from Guild, Blacksmith, Class Hall, and Gossip into structured leads and blockers.

#### [NEW] `src/ai/strategy/blocker_inference.py`
- Service to inspect project failures and infer the specific blocker type (e.g., location unknown, missing materials).

#### [NEW] `src/ai/strategy/detour_suggestion.py`
- Service to map blocker types to detour objective classes (e.g., KNOWLEDGE_BLOCKER -> INVESTIGATE objective).

### Handlers & Systems

#### [MODIFY] `src/ai/states/...` (Building Handlers)
- Update `VisitGuildHandler`, `VisitBlacksmithHandler`, and `VisitClassHallHandler` to use the `StrategicKnowledgeIngestionService`.
- Replace free-form prose strings/goals with formatted `LeadRecord`s and `BlockerRecord`s.

#### [MODIFY] `src/core/logic/knowledge_propagation.py`
- Extend gossip logic to propagate `LeadRecord`s with degraded certainty and directness.

#### [MODIFY] `src/ai/brain.py`
- Integrate blocker inference into the `_strategic_appraisal_phase`.
- Integrate detour suggestions into the `ObjectiveDerivationService` (hook point in `strategic_evaluator`).

#### [NEW] `tests/ai/test_strategic_uncertainty.py`
- Consolidated integration test suite for leads, blockers, detours, and search narrowing.

## Open Questions

> [!CAUTION]
> **Candidate Zone Granularity**: Should we use region-based anchors (e.g. "somewhere in the North Highlands") or fuzzy tile circles?
> *Decision*: Use region-based anchors with search patterns, as it aligns better with the existing `SimulationGrid` and `Region` models. Search narrowing follows localized search within these regions.

## Verification Plan

### Automated Tests
- `pytest tests/ai/test_strategic_uncertainty.py`: Main integration test for detour spawning and investigation execution.

### Manual Verification
- Use `EntityInspector` to verify an entity's "Leads" and "Blockers" lists after failing to find a target.
