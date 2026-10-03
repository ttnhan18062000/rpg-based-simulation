---
content_type: doc
status: historical
layer: misc
authority: P2
audience: agent
tags: [quest, progress, stabilization]
---

# Quest Progress Stabilization Plan

Resolve double-counting and data loss in quest progression by hardening the update merge logic and ensuring strictly authoritative delta application.

## User Review Required

> [!IMPORTANT]
> This change strictly enforces that worker proposals cannot specify quest progress. Any AI thoughts that previously "cheated" or "predicted" quest progress will now have those deltas stripped at the trust boundary.

## Proposed Changes

### Core Updates

#### [MODIFY] [updates.py](file:///home/vboxuser/Work/rpg-based-simulation/src/core/updates.py)
- Refactor `QuestUpdate.merge` to:
  - Flatten and deduplicate `multi_updates` by `quest_id`.
  - Ensure that when merging single updates for the same ID, `progress_delta` is summed.
  - Reset top-level `progress_delta` to 0.0 when `quest_id` is "MULTI" to prevent accidental double counting in legacy loops.

### Authoritative Pipeline

#### [MODIFY] [pipeline.py](file:///home/vboxuser/Work/rpg-based-simulation/src/engine/pipeline.py)
- Update `_strip_untrusted_world_effects` to set `progress_delta = 0.0` and `multi_updates = []` for all `QuestUpdate`s received from workers.
- Replace `_resolve_quest_rewards` with a call to `QuestResolutionSystem.enforce(state, update)`. This ensures proper handling of multiple quest completions in a single tick.

### Domain Logic

#### [MODIFY] [domain_logic.py](file:///home/vboxuser/Work/rpg-based-simulation/src/engine/domain_logic.py)
- Update `execute_move` and `ATTACK` handler to merge *all* updates returned by the `QuestResolutionSystem` instead of just taking the first one.
- Update `AOE_ATTACK` to evaluate hunt quests for all killed targets and merge the results into the attacker's update.

### Quest System

#### [MODIFY] [quests.py](file:///home/vboxuser/Work/rpg-based-simulation/src/engine/quests.py)
- Harden `QuestResolutionSystem.enforce` to ensure it doesn't accidentally re-apply deltas if called multiple times (idempotency check).
- Ensure `evaluate_combat_victory` correctly handles multiple attackers (though currently it takes one, we should align with potential multi-attacker logic).

---

## Verification Plan

### Automated Tests
- Run `pytest tests/engine/test_quest_progression.py` (if it exists, otherwise create it).
- Add a new test case `test_quest_double_counting_regression` that simulates a worker proposal with a delta and an authoritative re-execution with a delta.
- Verify that `ApplyPath` applies the delta exactly once.

### Manual Verification
- Run a simulation and observe logs for "QUEST_REWARD" intents to ensure they are emitted exactly once per quest completion.
