---
status: historical
layer: misc
authority: P2
audience: agent
ticket_id: TCK-20260328
artifact_type: investigation
tags: []
---

# Investigation Report - Backend Restructuring

## Current State Analysis
- **Branch**: `rpg_core` at commit `978ccc2`.
- **Regressions**: 32 test failures (out of 749).
- **Core Model**: `Entity` has been refactored to use `StatsProxy`, but legacy `effective_*` calls remain in some components (e.g., `SkillInstance`, `AIBrain` mocks).
- **Subsystems**: The `WorldLoop` is still handling many responsibilities that were targeted for extraction in the previous session (Territory, Combat Tracking, Memory, Goal Scoring).

## Detailed Failure Analysis
### 1. Stuck Detection (TypeError)
- **Location**: `src/ai/brain.py:148`
- **Error**: `TypeError: '<' not supported between instances of 'MagicMock' and 'float'`
- **Cause**: `actor.stats.hp_ratio` is returning a `MagicMock` during unit tests because the `StatsProxy` is accessing a mocked `combat` component.

### 2. Inventory Goals (AssertionError)
- **Location**: `tests/unit/ai/test_inventory_goals.py`
- **Error**: `AssertionError: Overweight hero should abort looting, got 9`
- **Cause**: The mock setup for `Entity` weights/caps is not being correctly intercepted by `StatsProxy`, or `StatsProxy` is returning default values.

## Subsystem Extraction Status
| System | Status | Targeted Logic |
|---|---|---|
| **CombatTrackingSystem** | Missing | `world_loop.py:_update_combat_targets`, threat decay, engagement state. |
| **TerritorySystem** | Missing | Hostile/Home territory stat multipliers application. |
| **GoalSystem** | Missing | `GoalEvaluator.evaluate()` and scoring plugin coordination. |
| **MemorySystem** | Missing | `AIBrain:Step 3` (Memory Recall), pruning, and terrain sentiment. |

## Strategy
1. Fix the `TypeError` and `AssertionError` by updating test mocks to return numeric values through the `StatsProxy` properties.
2. Re-implement the missing systems in `src/mechanics/` and `src/ai/`.
3. Simplify `WorldLoop` by registering these systems via `SystemManager`.
