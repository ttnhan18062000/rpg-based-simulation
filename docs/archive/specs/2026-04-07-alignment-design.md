---
status: archive
authority: P2
audience: historical
layer: engine
original_date: 2026-04-07
---

# Spec: Phase 0 Corrective Alignment (Strict Foundation)

## Metadata
- **Ticket ID**: TCK-20260407-PH0-FIX
- **Title**: Phase 0 Corrective Alignment & Misdirection Fix
- **Date**: 2026-04-07
- **Status**: DRAFT (Approved by User)

## 1. Problem Description
Phase 0 "foundations" had several conceptual "overclaims" and "fake" logic paths (mutation-discipline violations, naive salience, debug-only inspector). These misalignments will prevent Behavioral Realism in later phases.

## 2. Goals & Success Criteria
- **Stateless AI**: `AIBrain` must not mutate any entity state (including memory pruning).
- **Authoritative Pipeline**: `ActionSystem` owns all state mutation, including memory management.
- **Weighted Salience**: Memory pruning must use a weighted calculation (Impact x Recency).
- **Curated Lens**: `EntityInspector` must present a character-driven "Why/What/Risk" summary.
- **Social Reliability**: `update_bond` must return values for authoritative milestone detection.
- **Single Registry**: Divergent `SocialRegistry` instances in `WorldLoop`/`WorldState` must be unified.

## 3. Architecture & Data Flow

### 3.1 Unvioral Appraisal Flow
1. **Perception**: `AIBrain` proposes updates (IntentUpdate).
2. **Resolution**: `ActionSystem` receives proposals.
3. **Application**: 
    - `ActionSystem` applies updates.
    - `ActionSystem` calls `MemorySalienceService.prune(entity)` via `PerceptionUpdate`.
    - Memory pruning is based on `abs(event.impact) * (1.0 - decay)`.

### 3.2 Inspector Data Pipeline
- `EntityInspector` reads `MindAspect.decision.goal_scores` and `IdentityAspect.archetype` to explain "Likely Next Choices."
- `EntityInspector` filters `NarrativeMemory.memory_log` for "Significant Events" (> 0.5 impact) and groups them by type (Combat, Social) for the "Ongoing Arc."

## 4. Components

### 4.1 `EntityInspector` (src/ui/cli/inspector.py)
- `render_personality()`: Maps OCEAN traits to labels (e.g., "Highly Aggressive").
- `render_likely_choices()`: Lists top 3 goals with scores and "Motive" bias explanations.
- `render_ongoing_arc()`: Hybrid view of salient memories and thematic summaries.

### 4.2 `MindAspect` (src/core/aspects/mind.py)
- **DELETE**: `prune_memories()` (Moved to service/ActionSystem).

### 4.3 `SocialRegistry` (src/core/models/social.py)
- **UPDATE**: `update_bond()` return type: `tuple[dict[str, float], dict[str, float]]` (Old vs New values).

### 4.4 `MemorySalienceService` (src/core/logic/memory_salience.py)
- **NEW/MOVE**: Standardizes `weighted_salience` calculation.
- **FUNCTION**: `prune(entity, current_tick, limit=50)`.

## 5. Error Handling & Testing
- **Test Divergence**: Ensure different archetypes show different "Likely Next Choices" in the Inspector.
- **Test Mutation**: Verify `AIBrain.decide()` does not change `actor.mind.narrative.memory_log.count`.
- **Test Integrity**: Verify `SocialRegistry` updates are correctly captured in `ActionSystem`.

## 6. Implementation Plan Sequence
1.  **Registry Unification**: Fix `WorldLoop` initialization.
2.  **Social Bug**: Fix `update_bond()` return value and `ActionSystem` expectation.
3.  **Salience Move**: Implement `MemorySalienceService` and move pruning to `ActionSystem`.
4.  **Stateless AI**: Remove mutations from `AIBrain`.
5.  **Curated Inspector**: Implement the new "Who/What/Risk" views.
