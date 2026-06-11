---
status: historical
layer: engine
authority: P2
audience: agent
ticket_id: TCK-20260528-PROG-PHASE6-GROWTH
artifact_type: plan
tags: [prog, phase6, growth]
---

# Plan: Phase 6 — Progression / Equipment / Reward Conversion

This document coordinates the technical plan for Phase 6.

## Proposed Changes

### Component: `src/domains/progression`

We will create a modular progression/reward conversion domain.

#### [NEW] `schema.py`
- Define `PossessionMeaning`, `GrowthGap`, `GrowthGapReport`, `RewardEntry`, `ConversionOption`, and `ProgressionDecisionResult` schemas.

#### [NEW] `possession.py`
- Implement `PossessionUnderstandingService` evaluating keep/sell/equip priorities.

#### [NEW] `gaps.py`
- Implement `GrowthGapEvaluator` detecting critical attribute or equipment weaknesses.

#### [NEW] `ledger.py`
- Implement event-driven reward ledger updates.

#### [NEW] `interpretation.py`
- Implement `RewardInterpretationService` mapping gold/loot gains to active gaps.

#### [NEW] `generator.py`
- Implement `ConversionOptionGenerator` spawning valid choices.

#### [NEW] `selector.py`
- Implement `ConversionDecisionService` with personality bias scoring.

#### [NEW] `resolver.py`
- Implement `ConversionIntentResolver` mapping options to intents.

#### [NEW] `phase.py`
- Implement `ProgressionConversionPhase` running behind a feature flag.

## Verification Plan

### Automated Tests
- We will add 15 test files checking unit, integration, scenarios, and budget performance targets.
