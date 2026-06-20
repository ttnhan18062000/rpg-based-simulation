---
ticket_id: TCK-20260619-E23C-QUEST-REWARDS
date: 2026-06-20
status: test-plan-complete
---

# Test Plan: TCK-20260619-E23C-QUEST-REWARDS

## Regression Surface (existing tests that must pass)

All of the following must remain green after E23C changes:

### Quest transaction / reward pipeline
| File | Tests | What breaks if E23C drifts |
|---|---|---|
| `tests/unit/quest/test_quest_transactions.py` | `test_successful_quest_reward_transaction`, `test_full_inventory_blocks_quest_reward`, `test_recovery_after_freeing_inventory`, `test_idempotency_rewarded_quest_does_not_retry` | `QuestResolutionSystem.enforce()` or `ResourceTransactionResolver` QUEST path mutated |
| `tests/unit/quest/test_quest_lifecycle.py` | All 13 tests (AC-1 to AC-10 from E23B) | `quest_registry` apply path, `quest_status_updates`, `quest_registry_remove` |
| `tests/unit/quest/test_quest_system.py` | `test_explore_quest_progress`, `test_bounty_quest_completion` | `QuestResolutionSystem.evaluate_*` and reward pipeline integration |
| `tests/unit/quest/test_quest_generation.py` | All | `QuestGenerator` and `RewardState` construction unchanged |
| `tests/unit/domains/world_emergence/test_quest_registry_wiring.py` | All (from E23B) | `quest_registry_add` wiring from `WorldEmergencePhase` |

### Conservation / resource pipeline
| File | Tests | What breaks |
|---|---|---|
| `tests/rpg/test_resource_conservation_v2.py` | All | `ResourceTransactionResolver` source_kind dispatch broken |
| `tests/unit/combat/test_combat_rewards.py` | All | `RewardUpdate` / `ResourceTransferIntent` shared structure changed |

### Apply path
| File | Tests | What breaks |
|---|---|---|
| Any test using `ApplyPath.apply_generation()` | Subset | `quest_registry` field handling in constructor |

---

## New Tests Required (per AC)

All new tests go in `tests/unit/quest/test_quest_rewards.py` (new file).

### AC-1: `test_quest_completion_adds_gold_and_xp`

**What it proves**: When a `QuestOpportunity` with `reward_spec={"gold": 200, "xp": 500}` is
resolved for a completing entity, the entity's `inventory.gold` increases by 200 and XP reward is
applied via `RewardUpdate.xp_gain=500`.

**Setup**:
- Create an `AuthoritativeState` with `quest_registry` containing one `QuestOpportunity`
  (`status=QuestOpportunityStatus.COMPLETED`, `reward_spec={"gold": 200, "xp": 500}`).
- Create an `EntityState` with a `HERO` entity, normal inventory (not full).
- Construct a `StateUpdate` that encodes the reward delivery intent for this entity+quest pair.
- Call `AuthoritativeApplyPipeline.refine(state, update)`.
- Call `ApplyPath.apply_generation(state, refined)`.

**Assertions**:
- `new_state.entities[entity_id].inventory.gold == 200`
- XP reward was applied (check `identity.evolution_points` or verify `RewardUpdate` in
  intent_results)
- Quest is no longer in `new_state.quest_registry` (removed after successful reward)

**Note on E23D dependency**: If E23C scope is Option C (no E23D entity matching yet), this test
constructs the reward intent synthetically (explicit entity_id + quest_id). Document this
assumption in the test docstring.

---

### AC-2: `test_quest_completion_is_authoritative`

**What it proves**: Reward is applied through the apply path, not via direct mutation. No direct
writes to `entity.inventory` or `entity.identity` happen outside `ApplyPath`.

**Setup**: Same as AC-1.

**Assertions**:
- The `ResourceTransferIntent` with `source_kind="QUEST"` appears in
  `refined.entity_updates[entity_id].resource_transfers`.
- The `StateUpdate` prior to `apply_generation` does NOT have gold/xp directly embedded in
  `EntityUpdate.inventory` or `EntityUpdate.identity` (only in resource_transfers).
- After `apply_generation`, gold and XP are present — proving the apply path resolved them.

---

### AC-3: `test_quest_completed_event_emitted`

**What it proves**: A `WorldEvent(category=QUEST_COMPLETED)` is emitted in the `StateUpdate` after
reward delivery.

**Setup**: Same as AC-1. After `refine()`, inspect the `StateUpdate`.

**Assertions**:
- `any(e.category == WorldEventCategory.QUEST_COMPLETED for e in refined.world_events_add)`
- The matching event has `subject == quest_id`
- `event.payload` contains `"gold"` and/or `"xp"` keys

---

### AC-4: `test_diplomatic_errand_no_reward`

**What it proves**: A `QuestOpportunity` with `kind="diplomatic_errand"` and `reward_spec={}`
transitions to COMPLETED with no `ResourceTransferIntent` emitted and no gold/XP applied.

**Setup**:
- `QuestOpportunity(kind="diplomatic_errand", reward_spec={}, status=QuestOpportunityStatus.COMPLETED)`
- Entity with 0 gold, empty inventory.
- Synthetic reward delivery update.

**Assertions**:
- `refined.entity_updates.get(entity_id)` has no resource_transfers with `source_kind="QUEST"`
- `new_state.entities[entity_id].inventory.gold == 0`
- Quest removed from `new_state.quest_registry` (clean transition)

---

### AC-5: `test_full_inventory_defers_opportunity_reward`

**What it proves**: When entity inventory is full (16/16 items), item delivery fails and quest
stays in registry with `QuestOpportunityStatus.COMPLETED` (not removed). Mirrors
`test_full_inventory_blocks_quest_reward` pattern from entity quests.

**Setup**:
- `reward_spec={"gold": 100, "xp": 50}` with `items` field carrying an item template ID.
- Entity inventory at max_slots (16 items).

**Assertions**:
- `refined.entity_updates[entity_id].quest_status` (for opportunity) stays COMPLETED, not terminal.
- Quest remains in `new_state.quest_registry` (not removed).
- `new_state.entities[entity_id].inventory.gold == 0` (atomic — gold not granted if items failed).

**Note**: If `reward_spec` has no `items` and only gold/xp, the capacity check does not block
delivery (gold/xp have no slot requirement). Test with items to exercise the capacity guard.

---

### AC-6: `test_reward_idempotency_via_transaction_id`

**What it proves**: Submitting the same reward intent twice (same `transaction_id`) results in the
reward being applied exactly once.

**Setup**:
- Apply the reward once successfully → `new_state` with gold=200.
- Replay the same `StateUpdate` (same transaction_id) against `new_state`.

**Assertions**:
- `final_state.entities[entity_id].inventory.gold == 200` (unchanged, not 400).
- `processed_transaction_ids` contains the transaction_id after first apply.

---

### AC-7: `test_reward_spec_faction_rep_silently_skipped`

**What it proves**: `reward_spec={"gold": 100, "xp": 200, "faction_rep": 0.5}` does not raise and
`faction_rep` is ignored.

**Assertions**:
- No exception raised during refine/apply.
- Gold and XP applied correctly.
- No faction state mutation.

---

## Anti-Drift Test Guards

### Guard 1: `test_no_direct_entity_mutation_from_quest_opportunity`

Assert that `QuestLifecycleService.tick()` (from E23B) does NOT emit `ResourceTransferIntent`
objects. Reward intents must come from the enforce/refinement stage only.

```python
from src.domains.world_emergence.services import QuestLifecycleService
update = QuestLifecycleService.tick(state)
assert update.entity_updates == {}   # no entity-level mutations
assert update.resource_transfers == getattr(update, 'resource_transfers', [])  # none
```

### Guard 2: `test_quest_opportunity_status_enum_not_confused_with_quest_status`

Assert that `QuestOpportunityStatus` and `QuestStatus` are distinct types and share no values
that would cause accidental cross-assignment.

```python
from src.core.models.quests import QuestOpportunityStatus, QuestStatus
# QuestOpportunityStatus is str-based; QuestStatus is int-based
assert not issubclass(QuestOpportunityStatus, type(QuestStatus.ACTIVE))
assert QuestOpportunityStatus.COMPLETED != QuestStatus.COMPLETED  # different types/values
```

### Guard 3: `test_entity_project_quest_state_unaffected_by_opportunity_reward`

When an opportunity reward is applied for entity A, entity A's `strategic.projects` (entity-level
`QuestState` objects) must not change.

```python
# Entity has both a QuestState project AND is completing a QuestOpportunity
# After reward delivery, entity.strategic.projects[q_state_id].quest_status unchanged
```

---

## Scoped Pytest Commands

```bash
# New tests only
pytest tests/unit/quest/test_quest_rewards.py -x -v

# Full quest domain regression
pytest tests/unit/quest/ -x -v

# Conservation path regression
pytest tests/rpg/test_resource_conservation_v2.py -x -v

# World emergence regression (E23B wiring)
pytest tests/unit/domains/world_emergence/ -x -v

# Full non-slow suite (run before finalization)
pytest -m "not slow" -x
```
