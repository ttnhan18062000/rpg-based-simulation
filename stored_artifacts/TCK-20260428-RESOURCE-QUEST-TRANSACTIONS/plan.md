---
status: historical
layer: economy
authority: P2
audience: agent
ticket_id: TCK-20260428-RESOURCE-QUEST-TRANSACTIONS
artifact_type: plan
tags: [resource, quest, transactions]
---

# TCK-20260428-RESOURCE-QUEST-TRANSACTIONS Implementation Plan

This plan aims to make quest reward delivery transactional and capacity-aware, ensuring quest status only advances to `REWARDED` when the reward is successfully delivered.

## User Review Required

> [!IMPORTANT]
> - **REWARD_PENDING status**: Quests will transition `ACTIVE -> COMPLETED -> REWARD_PENDING -> REWARDED`.
> - **Idempotency**: A unique `reward_transaction_id` (`f"quest:{quest_id}:reward"`) will be used to prevent duplicate rewards on retries.
> - **Strict Mapping**: Quest status updates will only trigger if the `ResourceTransferIntent` explicitly matches the `quest_id` and `transfer_kind`.

## Proposed Changes

### [Component] Core Models

#### [MODIFY] [quests.py](file:///home/vboxuser/Work/rpg-based-simulation/src/core/quests.py)
- Add `REWARD_PENDING = 4` to `QuestStatus` enum.

### [Component] Engine Logic

#### [MODIFY] [quests.py](file:///home/vboxuser/Work/rpg-based-simulation/src/engine/quests.py)
- In `QuestResolutionSystem.enforce`:
    - Detect quests that are `COMPLETED` (and were `ACTIVE`) or are already `REWARD_PENDING`.
    - Emit `ResourceTransferIntent` for the reward with `transfer_kind="QUEST_REWARD"` and `source_id=q_id`.
    - Set `QuestUpdate.status_set = QuestStatus.REWARD_PENDING`.
    - Use idempotency key in intent (or ensure system handles retries safely).
    - Remove the immediate `REWARDED` status set.

#### [MODIFY] [pipeline.py](file:///home/vboxuser/Work/rpg-based-simulation/src/engine/pipeline.py)
- In `AuthoritativeApplyPipeline._resolve_resource_transactions`:
    - When a `ResourceTransferIntent` with `transfer_kind == "QUEST_REWARD"` is `accepted`:
        - Verify `intent.source_id` matches the `quest_id`.
        - Locate the `QuestUpdate` for the associated `quest_id` in `ent_upd`.
        - Set `QuestUpdate.status_set = QuestStatus.REWARDED`.

#### [MODIFY] [apply.py](file:///home/vboxuser/Work/rpg-based-simulation/src/engine/apply.py)
- Remove auto-transition logic for quests in `apply_generation`.
- **PRESERVE** `RewardUpdate` for XP/Evolution points to avoid breaking combat progression.
- Gold and items MUST use `ResourceTransferIntent`.

### [Component] Tests

#### [NEW] [test_quest_transactions.py](file:///home/vboxuser/Work/rpg-based-simulation/tests/quests/test_quest_transactions.py)
- Test: Successful quest reward delivery transitions to `REWARDED`.
- Test: Full inventory keeps quest in `REWARD_PENDING`.
- Test: Freeing inventory after `REWARD_PENDING` allows transition to `REWARDED`.
- Test: Already `REWARDED` quest does not emit or apply reward again.
- Test: Accepted `QUEST_REWARD` marks only the matching quest as `REWARDED`.

## Verification Plan

### Automated Tests
- `pytest tests/quests/test_quest_transactions.py`
- `pytest tests/engine/test_pipeline.py` (ensure no regressions)
- `pytest tests/quests/test_service.py`

### Manual Verification
- Verify via logs that `REWARD_PENDING` state is visible when inventory is full.
