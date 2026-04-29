# Implementation Plan - Combat Reward Hardening (Phase E5)

## Goal
Consolidate combat rewards into the authoritative, intent-based resource transfer flow. Remove legacy fields from `CombatUpdate` and ensure all XP/Gold flows through `ResourceTransferIntent`.

## Proposed Changes

### Core Models
- [MODIFY] `src/core/updates.py`: Add `RewardUpdate` dataclass. Add `RewardUpdate` to `ResourceTransferIntent` and `TransactionResult`.
- [MODIFY] `src/core/updates.py`: Remove `xp_gain` and `gold_gain` from `CombatUpdate`.

### Conservation Logic
- [MODIFY] `src/core/conservation.py`: Refactor `ResourceTransactionResolver` to populate `RewardUpdate` during combat/quest resolution.

### Combat System
- [MODIFY] `src/engine/combat.py`: Update `resolve_attack` and `resolve_skill_usage` to return reward intents.

### Pipeline
- [MODIFY] `src/engine/pipeline.py`: Integrate `RewardUpdate` merging into the atomic transaction resolution loop.
- [MODIFY] `src/engine/pipeline.py`: Sanitize incoming updates to prevent client-side reward injection.

## Verification
- Create `tests/engine/test_combat_reward_hardening.py` with specific checks for intent processing and state conservation.
