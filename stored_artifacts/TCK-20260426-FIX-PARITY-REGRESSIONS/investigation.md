---
status: historical
layer: misc
authority: P2
audience: agent
ticket_id: TCK-20260426-FIX-PARITY-REGRESSIONS
artifact_type: investigation
tags: [fix, parity, regressions]
---

# Investigation: RPG Progression and Readiness Regressions

## 1. RPG Progression Delay
**Issue**: `EvolutionSystem` was failing to trigger a level-up in the same tick as a combat reward.
**Finding**: `EvolutionSystem.evaluate` was only inspecting `IdentityUpdate`. It did not see the `RewardUpdate` XP gain until the `ApplyPath` phase. Since evolution needs to happen *before* standard leveling in the refinement loop, it was missing the XP needed for the milestone.
**Root Cause**: Lack of cross-update visibility in `EvolutionSystem.evaluate`.

## 2. Readiness Double-Subtraction
**Issue**: Combat and Movement were failing due to insufficient readiness.
**Finding**: The pipeline was subtracting readiness twice: once from the "Brain" update and again from the "Physical" update.
**Root Cause**: The merge logic in `Pipeline._refine_step` was incorrectly summing the deltas instead of enforcing the "most restrictive" delta (intent budget).
