# TCK-20260425-PH8-M1-QUESTS

## Title
Implement Authoritative Quest Lifecycle and Reward Models

## Status
DONE

## Tier
standard

## Type
chore

## Priority
P1

## Request Summary
Establish the foundational models and authoritative lifecycle for RPG quests in the V2 engine.

## Scope
- Define `QuestState`, `QuestKind`, `QuestStatus`, and `RewardState`.
- Implement `QuestUpdate` and `RewardUpdate` in `updates.py`.
- Implement authoritative application logic in `apply.py`.
- Add contract tests for lifecycle and rewards.

## Out of Scope
- Quest generation (Milestone 2).
- Class/Skill systems (Milestone 3).

## Acceptance Criteria
- Quests auto-complete when goals are met.
- Rewards (XP, Gold, Items) are applied atomically.
- Serialization/Pickling of quest state is stable.
- 100% pass rate on `tests/quests/`.

## Related Tickets
- None

## Related Docs
- `resource_v2_e_phases.md`

## Related Stored Artifacts
- `stored_artifacts/TCK-20260425-PH8-M1-QUESTS/`

## Related Code Areas
- `src/core/quests.py`
- `src/core/updates.py`
- `src/engine/apply.py`
- `tests/quests/test_quest_lifecycle.py`

## Implementation Notes
- `QuestState` inherits from `ProjectState` and is stored in `StrategicComponent.projects`.
- Renamed `status` to `quest_status` to avoid collision with `ProjectState`.
- Integrated with `InventoryService` for gold/item rewards.

## Test Summary
- `test_quest_progress_and_auto_complete`: PASS
- `test_quest_reward_application`: PASS
- `test_quest_serialization_integrity`: PASS

## Files Changed
- `src/core/quests.py` [NEW]
- `src/core/updates.py` [MODIFY]
- `src/engine/apply.py` [MODIFY]
- `tests/quests/test_quest_lifecycle.py` [NEW]

## Completion Summary
- Established the V2 quest substrate.
- Verified deterministic lifecycle transitions and reward distribution.
