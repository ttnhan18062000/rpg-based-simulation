---
status: historical
layer: engine
authority: P2
audience: agent
ticket_id: TCK-20260407-PHASE1-DS
artifact_type: plan
tags: [phase1, ds]
---

# Plan: TCK-20260407-PHASE1-DS

## Goal
Implement Phase 1 of Behavioral Realism (Design Shift). 
This involves migrating from the generic OCEAN personality model to a more RPG-flavored one, adding long-term motives, and shifting perception to a belief-based system.

## Status: DONE

## Proposed Changes

### 1. Data Models (`src/core/aspects/mind.py`)
- [x] Add `PersonalityProfile` to `MindAspect` (or `IdentityAspect`).
    - Traits: `aggression`, `greed`, `caution`, `loyalty`, `ambition`, `curiosity`.
- [x] Add `PersonalMotive` to `MindAspect`.
    - Fields: `motive_id`, `kind`, `priority`, `progress`, `frustration`, `active`.
- [x] Upgrade `MemoryRecord` to `BeliefRecord`.
    - Fields: `last_seen_pos`, `apparent_kind`, `apparent_faction`, `threat_estimate`, `confidence`.
- [x] Add `ThreatEstimate` sub-model.

### 2. Seeding Logic (`src/core/entities/entity_builder.py`)
- [x] Seed personality and motives at spawn/creation.
- [x] Bias by archetype/faction/class.

### 3. Belief Service (`src/ai/beliefs.py`)
- [x] Create `BeliefService`.
- [x] Implement `refresh_belief_from_observation`.
- [x] Implement `decay_stale_beliefs`.

### 4. AI Pipeline Integration (`src/ai/brain.py`)
- [x] Call `BeliefService` in `_sensory_perception_phase`.
- [x] Implement motive/personality bias in `_deliberation_tactical_phase`.
- [x] Use beliefs (not truth) in chosen decision paths (e.g., Flee/Hunt).

### 5. API / Inspection
- [x] Extend `EntityInspectionSchema` and `AIDecisionSchema` in `src/api/schemas.py`.
- [x] Update `entity_presenter.py` and `ai_presenter.py`.

## Rollback / Risk
- **Risk**: Resolved. Breaking changes to SocialAppraisalService were mitigated by providing read-only accessors.
- **Rollback**: Legacy OCEAN traits were migrated to the new `PersonalityProfile` model.
