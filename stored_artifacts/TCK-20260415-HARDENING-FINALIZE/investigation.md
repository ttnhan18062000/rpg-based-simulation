---
status: historical
layer: misc
authority: P2
audience: agent
ticket_id: TCK-20260415-HARDENING-FINALIZE
artifact_type: investigation
tags: [hardening, finalize]
---

# Investigation - Strategic Learning & Social Consequences

## Uncertainty Resolution (Anti-Cheating)
- **Goal**: Ensure rumors stay vague and don't collapse until evidence is found.
- **Findings**:
    - `src/ai/strategic_uncertainty_resolution.py` does not exist.
    - `StrategicKnowledgeIngestionService` currently sets `certainty` but doesn't strictly enforce the "Zone vs. Coords" split for rumors.
    - `LeadRecord` has `candidate_zone_ids` which are used in `objective_derivation.py` but the logic for "exploring" a zone to find coordinates is missing from the core strategic services.
- **Action**: Create `src/ai/strategy/uncertainty_resolution.py`.

## Source-Trust Learning
- **Goal**: E2E application of source-trust updates to future lead weighting.
- **Findings**:
    - `StrategicLearningService` correctly generates `source_trust_updates`.
    - `ActionSystem` correctly applies them to `entity.mind.strategic.source_trust`.
    - **Gap**: `StrategicKnowledgeIngestionService` and `CandidateBuilder` do not READ `source_trust` to discount new information.
- **Action**: Update `StrategicKnowledgeIngestionService` to check trust during ingestion.

## Social Consequences
- **Goal**: Contract breach affects future recruitment; successful cooperation improves it.
- **Findings**:
    - `ContractOutcomeService.resolve_contract` applies trust/loyalty deltas.
    - `RecruitmentNegotiationService` has a "Betrayal" string check which is fragile.
- **Action**: Update `RecruitmentNegotiationService` to check Turning Point history for "trauma".

## Behavioral Shifting (Directive Mutation)
- **Goal**: Mutation after repeated thresholded events (e.g., betrayal).
- **Findings**:
    - `DirectiveMutationService` exists and handles the logic.
    - `TurningPointRecord` salience must exceed a threshold influenced by `judgment_stability`.
- **Action**: Verify repeated-event priority strengthening in tests.

## Graph Export Coverage
- **Goal**: Export obligations, contracts, zones, and hypotheses.
- **Findings**:
    - `EntityCognitionExporter` currently only exports Directives, Projects, Objectives, Concerns, Blockers, Leads, Turning Points, and Place Attachments.
- **Action**: Add Obligations, Contracts, Offers, Candidate Zones, and Hypotheses.

---

## Research Checklist
- [x] Research `src/ai/strategy/strategic_learning_service.py`
- [x] Research `src/ai/strategy/contract_outcome.py`
- [x] Research `src/ai/strategy/recruitment_negotiation.py`
- [x] Research `src/core/logic/event_interpreter.py`
- [x] Research `src/core/logic/cognition_graph_exporter.py`
- [x] Audit existing tests for social breach and learning.
- [x] Identify location for Uncertainty Resolution (New File: `src/ai/strategy/uncertainty_resolution.py`).
