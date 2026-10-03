---
status: historical
layer: strategy
authority: P2
audience: agent
ticket_id: TCK-20260410-PH3-STRATEGIC-KNOWLEDGE
artifact_type: investigation
tags: [ph3, strategic, knowledge]
---

# Investigation: Phase 3 Strategic Knowledge

## Current State Analysis
- **Strategic Models**: `src/core/models/strategy.py` contains basic `LeadRecord` and `BlockerRecord` but they lack the depth required for detour generation and search tracking.
- **Knowledge Sources**:
  - `VisitGuildHandler`: Currently emits `MindUpdate(goals_add=...)` and `PerceptionUpdate(terrain_memory=...)`.
  - `VisitBlacksmithHandler`: Emits reason strings for missing materials.
  - `VisitClassHallHandler`: Emits reason strings for prerequisite failures.
  - `KnowledgePropagationService`: Propagates entity beliefs but not rumors/leads.
- **Strategic Appraisal**: `AIBrain` already has a pass for appraisal, but it doesn't yet account for complex blockers or detour objectives.

## Technical Gaps
1. **Model Depth**: `LeadRecord` needs source tracking and uncertainty fields. `BlockerRecord` needs a type taxonomy.
2. **Ingestion Layer**: There is no centralized service to convert building/social info into strategic knowledge.
3. **Inference Logic**: The engine cannot yet "infer" a knowledge blocker from a failure to find a resource, nor suggest an investigation detour.
4. **Uncertainty Persistence**: `terrain_memory` is too precise. We need a way to store "rumored regions" without mapping them immediately.

## Proposed Strategy
- Use `CandidateZoneRecord` (anchors + search types) to represent rumored regions.
- Implement the `StrategicKnowledgeIngestionService` as a singleton logic service.
- Refactor the `ObjectiveDerivationService` from Phase 2 to use the new blocker inference logic.
- Ensure all handlers use `StrategicUpdate` instead of local mind updates for strategy-related info.
