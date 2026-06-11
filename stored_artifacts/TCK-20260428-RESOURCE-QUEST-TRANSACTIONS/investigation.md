---
status: historical
layer: economy
authority: P2
audience: agent
ticket_id: TCK-20260428-RESOURCE-QUEST-TRANSACTIONS
artifact_type: investigation
tags: [resource, quest, transactions]
---

# Investigation: Quest Reward Transactions

## Current State

### `src/engine/pipeline.py`
- `refine` calls `QuestResolutionSystem.enforce` then `_resolve_resource_transactions`.
- `_resolve_resource_transactions` uses `ResourceTransactionResolver.resolve` to process `ResourceTransferIntent` items in `ent_upd.resource_transfers`.

### `src/engine/quests.py`
- `QuestResolutionSystem.enforce` checks if a quest just transitioned to `COMPLETED`.
- It emits a `ResourceTransferIntent` for the reward.
- **CRITICAL BUG**: It immediately sets `quest_update.status_set = QuestStatus.REWARDED`, bypassing transaction success confirmation.

### `src/engine/apply.py`
- `ApplyPath.apply_generation` contains redundant logic:
    - Auto-transitions `COMPLETED` quests to `REWARDED` (lines 510-512).
    - Directly applies `update.reward` (lines 521-537).
- This logic bypasses the `ResourceTransactionResolver` and the `AuthoritativeApplyPipeline` refinement.

### `src/core/quests.py`
- `QuestStatus` only has `ACTIVE`, `COMPLETED`, `REWARDED`.
- Missing `REWARD_PENDING` to handle failed deliveries.

## Proposed Logic Flow

1. **Quest Service**: Add `REWARD_PENDING` status.
2. **Quest Resolution System**:
    - When a quest is `COMPLETED` or `REWARD_PENDING`:
        - Emit `ResourceTransferIntent` (kind `QUEST_REWARD`, source `QUEST`, id `q_id`).
        - Set `QuestUpdate.status_set = QuestStatus.REWARD_PENDING`.
3. **Pipeline Refinement**:
    - In `_resolve_resource_transactions`:
        - If an intent with `transfer_kind == "QUEST_REWARD"` is `accepted`:
            - Update the `QuestUpdate` in the same `EntityUpdate` to set `status_set = QuestStatus.REWARDED`.
4. **Apply Path**:
    - Remove auto-transition and direct reward application.
    - It should only apply the `QuestUpdate` and `InventoryUpdate` (which the transaction resolver provides).

## Open Questions
- Should `xp_reward` also be tied to transaction success? Currently `ResourceTransactionResolver` includes `identity_update` in the result for `QUEST` source kind. So yes, XP will only be granted if the items/gold can be delivered (if they are part of the same intent).
- Is `REWARD_PENDING` needed if we can just keep it as `COMPLETED`? `REWARD_PENDING` is better as it explicitly shows we tried to reward but failed.
