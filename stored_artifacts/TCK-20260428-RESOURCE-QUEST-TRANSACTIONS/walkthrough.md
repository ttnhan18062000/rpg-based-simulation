# Walkthrough: Quest Reward Transaction Hardening

Implemented transactional integrity for quest rewards, ensuring that a quest is only marked as `REWARDED` if the associated items and gold are successfully delivered to the hero's inventory.

## Changes Made

### 1. Core Model Enhancements
- **QuestStatus**: Added `REWARD_PENDING` (4). This state represents a quest that is finished but whose reward delivery has not yet been confirmed by the authoritative ledger.
- **ResourceTransferIntent**: Added `transaction_id` to support idempotency and state tracking during resolution.

### 2. Engine Logic Refinement
- **QuestResolutionSystem**:
    - Quests reaching `COMPLETED` now transition to `REWARD_PENDING`.
    - Emits a `ResourceTransferIntent` with `transfer_kind = QUEST_REWARD` and a unique `transaction_id` (`f"quest:{q_id}:reward"`).
    - Retries reward emission on every tick if the quest remains in `REWARD_PENDING`.
- **AuthoritativeApplyPipeline**:
    - Refactored `_resolve_resource_transactions` to handle `QUEST_REWARD` callbacks.
    - If a `QUEST_REWARD` intent is accepted (inventory has space), the quest is atomically updated to `REWARDED` within the same tick.
- **ApplyPath**:
    - Purged legacy auto-reward bypasses in `apply_generation`.
    - Preserved `RewardUpdate` for XP and Evolution points (per user requirement) while delegating Gold and Items to the transaction system.

### 3. Service Layer
- **QuestService**: Updated `mark_rewarded` to accept transitions from `REWARD_PENDING`.

## Verification Results

### Automated Tests
Created [tests/quests/test_quest_transactions.py](file:///home/vboxuser/Work/rpg-based-simulation/tests/quests/test_quest_transactions.py) covering:
- `test_successful_quest_reward_transaction`: Verified `ACTIVE -> COMPLETED -> REWARD_PENDING -> REWARDED` flow with valid inventory.
- `test_full_inventory_blocks_quest_reward`: Verified quest stays in `REWARD_PENDING` if inventory is full.
- `test_recovery_after_freeing_inventory`: Verified quest recovers and transitions to `REWARDED` once inventory space is cleared.
- `test_idempotency_rewarded_quest_does_not_retry`: Verified no duplicate rewards or status regressions.

All tests passed:
```text
tests/quests/test_quest_transactions.py ....                             [100%]
============================== 4 passed in 0.18s ===============================
```

Existing quest tests also passed:
```text
tests/quests/test_quest_lifecycle.py ....                                [100%]
============================== 4 passed in 0.17s = [100%]
```

## Evidence

````carousel
```python
# From src/engine/quests.py
if q.quest_status == QuestStatus.COMPLETED or q.quest_status == QuestStatus.REWARD_PENDING:
    # Emit transactional reward intent
    intent = ResourceTransferIntent(
        source_id=q_id,
        source_kind="QUEST",
        destination_id=e_id,
        gold_delta=q.reward.gold,
        items_add=[ItemStack(item_id=i, quantity=1) for i in q.reward.items],
        transfer_kind="QUEST_REWARD",
        transaction_id=f"quest:{q_id}:reward"
    )
```
<!-- slide -->
```python
# From src/engine/pipeline.py
if intent.transfer_kind == "QUEST_REWARD":
    from src.core.updates import QuestUpdate
    from src.core.quests import QuestStatus
    q_id = str(intent.source_id)
    curr_q_upd = refined_entity_updates[e_id].quest
    if curr_q_upd and curr_q_upd.quest_id == q_id:
        refined_entity_updates[e_id] = replace(refined_entity_updates[e_id],
            quest=replace(curr_q_upd, status_set=QuestStatus.REWARDED)
        )
```
````
