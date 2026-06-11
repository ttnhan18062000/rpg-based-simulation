---
status: historical
layer: strategy
authority: P2
audience: agent
ticket_id: TCK-20260410-STRAT-REFACTOR
artifact_type: plan
tags: [strat, refactor]
---

# Plan: TCK-20260410-STRAT-REFACTOR

## Goal
Enforce architectural consistency and AOA compliance across the strategic cognition engine. This involves reconciling the `StrategicUpdate` schema, refactoring legacy side-effecting services to be purely functional, and hardening snapshot isolation.

## Proposed Changes

### 1. Schema Reconciliation
- [MODIFY] `src/core/models/strategy.py`: Add canonical `blockers` list to `StrategicState`.
- [MODIFY] `src/actions/base.py`: Add `blockers_add_or_update` and `blockers_remove` to `StrategicUpdate`. Use `model_rebuild` to handle forward references.

### 2. Service Refactoring
- [MODIFY] `src/ai/beliefs.py`: Refactor `BeliefService.decay_stale_beliefs` to return `PerceptionUpdate` instead of performing in-place mutations.
- [MODIFY] `src/core/logic/social_state_applicator.py`: Refactor to return `IntentUpdate` list (Social, Reputation, Perception).
- [MODIFY] `src/core/logic/turning_points.py`: Rename `insert` to `prepare_insertion` and return `PerceptionUpdate`.

### 3. Authoritative Pipeline Integration
- [MODIFY] `src/systems/gameplay/action_system.py`: Update `_apply_updates` to handle canonical blocker merging and turning point additions.

## Verification Plan

### Automated Tests
- [NEW] `tests/test_strategic_consistency.py`:
    - Verify canonical blocker merging by ID.
    - Verify side-effect-freeness of `BeliefService` on frozen snapshots.
    - Verify `SocialStateApplicator` intent emission.
    - Verify deep-copy isolation of strategic trees.

### Manual Verification
- Perform a replay run and inspect the `replay.json` (or summary) to ensure strategic updates are visible and correctly ordered.
