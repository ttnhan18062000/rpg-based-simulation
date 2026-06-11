---
status: historical
layer: misc
authority: P2
audience: agent
ticket_id: TCK-20260425-PH5-MIND-AND-NEEDS
artifact_type: plan
tags: [ph5, mind, and, needs]
---

# Implementation Plan - Phase 5: Mind and Needs

## Goal Description
Restore the core AI "mind" loop that balances biological survival (Hunger, Sleep), emotional state (Panic, Aggression), and strategic objectives. This ensures entities behave as living characters with needs rather than just combat drones.

## Proposed Changes

### 1. Engine Hardening: Cognition Pipeline
- **File**: `src/engine/domain_logic.py`
- **Change**: Integrate `SensoryFilter` and `AppraisalSystem` into `execute_brain`.
- **Logic**: 
    1. Filter neighbors by saliency.
    2. Evaluate emotional state (Appraisal).
    3. Update beliefs (if changed).
    4. Propose Strategic/Biological goals.

### 2. Biological Needs Recovery
- **File**: `src/systems/strategic.py`
- **Change**: In `evaluate_strategic_intent`, call `RoutineService.evaluate_biological_needs` to generate concerns.
- **Change**: Propose "Sleep" or "Eat" projects when biological concerns are urgent.
- **File**: `src/engine/town_resolution.py`
- **Change**: Implement `REST` and `EAT` actions at appropriate buildings (Inn, Tavern) to clear biological debt.

### 3. Goal Scoring and selection
- **File**: `src/systems/routine.py`
- **Change**: Enhance `apply_role_based_biasing` to handle a wider range of goal types.
- **Change**: Ensure "Survival" goals (Panic Flee, Eat if starving) have very high utility boosts.

## Verification Plan

### Automated Tests
- `tests/parity/test_biological_needs.py`: Verify hunger/sleep debt accumulation and project triggering.
- `tests/parity/test_emotional_appraisal.py`: Verify panic flee behavior under stress.
- `tests/parity/test_sensory_filtering.py`: Verify that entities only process salient neighbors.

### Manual Verification
- Inspect trace logs during a town visit to see biological debt being cleared.
