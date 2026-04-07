# Plan: TCK-20260407-PHASE1-DS

## Goal
Implement Phase 1 of Behavioral Realism (Design Shift). 
This involves migrating from the generic OCEAN personality model to a more RPG-flavored one, adding long-term motives, and shifting perception to a belief-based system.

## Proposed Changes

### 1. Data Models (`src/core/aspects/mind.py`)
- [ ] Add `PersonalityProfile` to `MindAspect` (or `IdentityAspect`).
    - Traits: `aggression`, `greed`, `caution`, `loyalty`, `ambition`, `curiosity`.
- [ ] Add `PersonalMotive` to `MindAspect`.
    - Fields: `motive_id`, `kind`, `priority`, `progress`, `frustration`, `active`.
- [ ] Upgrade `MemoryRecord` to `BeliefRecord`.
    - Fields: `last_seen_pos`, `apparent_kind`, `apparent_faction`, `threat_estimate`, `confidence`.
- [ ] Add `ThreatEstimate` sub-model.

### 2. Seeding Logic (`src/core/entities/entity_builder.py`)
- [ ] Seed personality and motives at spawn/creation.
- [ ] Bias by archetype/faction/class.

### 3. Belief Service (`src/ai/beliefs.py`)
- [ ] Create `BeliefService`.
- [ ] Implement `refresh_belief_from_observation`.
- [ ] Implement `decay_stale_beliefs`.

### 4. AI Pipeline Integration (`src/ai/brain.py`)
- [ ] Call `BeliefService` in `_sensory_perception_phase`.
- [ ] Implement motive/personality bias in `_deliberation_tactical_phase`.
- [ ] Use beliefs (not truth) in chosen decision paths (e.g., Flee/Hunt).

### 5. API / Inspection
- [ ] Extend `EntityInspectionSchema` and `AIDecisionSchema` in `src/api/schemas.py`.
- [ ] Update `entity_presenter.py` and `ai_presenter.py`.

## Rollback / Risk
- **Risk**: Breaking existing `SocialAppraisalService` which depends on OCEAN/SocialBonds.
- **Rollback**: Keep OCEAN traits as a "legacy" layer for a transition period if needed, or fully migrate `PersonalityLogic`.
