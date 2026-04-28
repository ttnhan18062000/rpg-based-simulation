# Test Plan: Quest Reward Transactions

## Objective
Verify that quest rewards are delivered transactionally and capacity-aware, as defined in Phase 3.1.

## Scenarios

### 1. Successful Quest Completion
- **Setup**: Entity has enough inventory space. Quest is 1 step away from completion.
- **Action**: Perform action to complete quest.
- **Expected**:
    - Quest transitions `ACTIVE` -> `COMPLETED` -> `REWARDED`.
    - Items/Gold/XP added to entity.
    - Transaction is recorded as accepted.

### 2. Full Inventory Block
- **Setup**: Entity inventory is full. Quest is 1 step away from completion.
- **Action**: Perform action to complete quest.
- **Expected**:
    - Quest transitions `ACTIVE` -> `COMPLETED` -> `REWARD_PENDING`.
    - NO items/gold/XP added.
    - Transaction recorded as rejected (reason: `INVENTORY_FULL`).

### 3. Recovery after Full Inventory
- **Setup**: Quest is in `REWARD_PENDING` status.
- **Action**: Entity drops an item to free space. Next tick happens.
- **Expected**:
    - Quest transitions `REWARD_PENDING` -> `REWARDED`.
    - Items/Gold/XP added.
    - Transaction recorded as accepted.

### 4. Multiple Quests in one tick
- **Setup**: Two quests complete in same tick. Space for only one quest reward.
- **Action**: Complete both.
- **Expected**:
    - First quest (by ID or order) succeeds and becomes `REWARDED`.
    - Second quest fails and becomes `REWARD_PENDING`.

## Verification Tools
- `pytest`
- Custom test script using `AuthoritativeApplyPipeline` directly.
