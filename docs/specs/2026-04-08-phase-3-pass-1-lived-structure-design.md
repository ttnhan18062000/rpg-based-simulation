---
status: archive
authority: P2
audience: historical
layer: engine
original_date: 2026-04-08
---

# Design Spec: Phase 3 Pass 1 — Lived-Structure Core Models

**Date**: 2026-04-08
**Topic**: Establishing the data substrate for routines, place attachments, and small-group coordination.

## 1. Goal
To move the simulation from a collection of roaming actors into a world of "lived structures." Entities should have recognizable roles, preferred locations, recurring daily patterns, and loyalties to small subgroups.

## 2. Architecture
Following the Aspect-Oriented Architecture (AOA), we are extending existing aspects to include these new dimensions. This ensures that behavioral data is correctly isolated and persisted.

### 2.1 Domain Models
We will create a new registry file `src/core/models/lived_structure.py` to hold the following:

- **RoutineProfile**: Defines a recurring life-pattern.
  - `schedule_window`: Preferred hour range (Hybrid Schedule).
  - `event_triggers`: List of interpreted event kinds or state thresholds that activate this routine (Event Drive).
  - `anchor_type`: Whether it’s anchored to a `home`, `work`, or `wander` location.
  
- **PlaceAttachment**: Subjective importance assigned to a world location.
  - `sentiment_score`: Dynamic weighting (0.0 to 1.0).
  - `last_action_tick`: For recency decay.
  - `kind`: HOME, WORK, TRAVEL, SHRINE, etc.

- **GroupRecord**: Coordination structure for small scenarios.
  - `kind`: PATROL, RAID, HOUSEHOLD, CLIQUE.
  - `shared_goal`: The `GoalType` currently being pursued by the group.
  - `bonuses`: Mappings for `bravery_boost` or `combat_synergy`.

## 3. Component Integration

### 3.1 IdentityAspect (Roles & Cliques)
- **WorldRole**: Standardized enum (GUARD, RAIDER, CRAFTER, etc.) separate from `HeroClass`.
- **CliqueID**: String identifier for internal faction subgroups. Entities in a clique share a sub-archetype and higher internal trust.

### 3.2 MindAspect (Routines & Sentiment)
- **RoutineState**: Tracking `active_routine_id` and disruption status.
- **SentimentRegistry**: Storing the `PlaceAttachment` records for that specific entity.

### 3.3 WorldState (Registries)
- **GroupRegistry**: Global authoritative map of `GroupRecord` objects.

## 4. Logical Flow

### 4.1 Sentiment Growth & Decay
As actions are performed within the `WorldLoop` (e.g., `SLEEPING` action finishes), the corresponding `PlaceAttachment` in the entity's `MindAspect` will increase in `sentiment_score`. If no actions occur at a location for a long duration, the score decays.

### 4.2 Routine Selection
The AI context will prioritize routines that:
1. Are within their `schedule_window`.
2. HAVE their `event_trigger` satisfied (emergency).
3. Align with their `WorldRole`.

## 5. Testing & Verification
- **Instantiation Tests**: Verify all models can be created with Pydantic validation.
- **Persistence Tests**: Ensure new fields are correctly captured in snapshots and survive a reload.
- **Role Assignment**: Verify building a new entity with a specific `WorldRole` correctly seeds default routine templates.
