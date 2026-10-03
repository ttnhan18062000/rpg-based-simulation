---
ticket_id: TCK-20260619-E23B-QUEST-LIFECYCLE
phase: test_plan
date: 2026-06-20
---

# Test Plan: Quest Lifecycle State Machine + quest_registry

---

## Regression Surface (existing tests that must pass)

These tests exercise the existing `QuestStatus` (ACTIVE/COMPLETED/REWARDED/REWARD_PENDING) and the `QuestState` entity-level state machine. They must all pass unchanged after E23B — if `QuestStatus` is extended (Option A), verify enum values remain importable; if `QuestOpportunityStatus` is introduced (Option B, recommended), no existing test needs to change.

| Test file | What it covers | Risk |
|---|---|---|
| `tests/unit/quest/test_quest_lifecycle.py` | `QuestState` ACTIVE→COMPLETED→REWARDED transition, no-double-completion guard, XP/gold/item delivery | HIGH — directly references `QuestStatus.REWARDED` and `QuestStatus.ACTIVE` |
| `tests/unit/quest/test_quest_system.py` | `QuestResolutionSystem.evaluate_combat_victory`, `evaluate_explore`, `enforce()` | HIGH — uses ACTIVE, COMPLETED, REWARD_PENDING |
| `tests/unit/quest/test_quest_generation.py` | `QuestOpportunityGenerator`, determinism (WORLD-098, WORLD-099) | MEDIUM — constructs `QuestOpportunity` without `status`; will break if `status` is added without a default |
| `tests/unit/quest/test_quest_transactions.py` | Resource transfer on quest reward | MEDIUM — touches `REWARD_PENDING` path |
| `tests/unit/quest/test_progression_lifecycle.py` | XP gain, level-up on quest reward | LOW — indirectly uses reward pipeline |
| `tests/unit/quest/test_progression_regression.py` | Regression: double-reward guard | MEDIUM — uses `QuestStatus.REWARDED` |
| `tests/unit/quest/test_quest_relation_projection.py` | Faction-label matching in HUNT quests | LOW — no status-specific assertions |
| `tests/unit/quest/test_transaction_groups.py` | Atomic transaction group enforcement | LOW |

**Critical constraint**: `QuestOpportunity` already constructed in `test_quest_generation.py` without a `status` field (E23A left `status` absent). Adding `status: QuestOpportunityStatus = QuestOpportunityStatus.OFFERED` with a **default** value is safe — existing constructors continue to work.

---

## New Tests Required (per AC)

All new tests go in `tests/unit/quest/test_quest_lifecycle.py` (extend existing file) unless noted.

### AC-1: `quest_registry` field exists and serializes correctly

```
test_quest_registry_field_on_authoritative_state
```
- Construct `AuthoritativeState(tick=0, seed=42)`.
- Assert `hasattr(state, "quest_registry")` is True.
- Assert `state.quest_registry == {}`.
- Construct a `QuestOpportunity` and put it in a new state via `replace(state, quest_registry={"opp1": opp})`.
- Assert `new_state.quest_registry["opp1"] == opp`.
- Assert `state.quest_registry == {}` (original unchanged — immutability law).

### AC-2: `QuestOpportunityStatus` enum accessible (all six values)

```
test_quest_opportunity_status_enum_values
```
- Import `QuestOpportunityStatus` from `src.core.models.quests`.
- Assert all six values exist: `OFFERED`, `ACTIVE`, `PROGRESSED`, `COMPLETED`, `FAILED`, `EXPIRED`.
- Assert `QuestOpportunityStatus.OFFERED` is a string-valued enum (`isinstance(QuestOpportunityStatus.OFFERED.value, str)`).

### AC-3: `QuestOpportunity.status` field defaults to `OFFERED`

```
test_quest_opportunity_defaults_to_offered
```
- Construct `QuestOpportunity(id="rc_ev1_42", kind="resource_crisis", trigger_condition="...", objective_chain=("fetch:iron_ore:3",), reward_spec={"gold": 10, "xp": 50}, faction_source=None, expiry_ticks=100, source_event_id="ev1")`.
- Assert `opp.status == QuestOpportunityStatus.OFFERED`.

### AC-4: `WorldEmergencePhase` output → `quest_registry` population

```
test_world_emergence_populates_quest_registry  (new file recommended: tests/unit/domains/world_emergence/test_quest_registry_wiring.py)
```
- Build a minimal `AuthoritativeState(tick=5, seed=1, recent_world_events=[...])` with one `RESOURCE_DEPLETED` WorldEvent.
- Build empty `StateUpdate`.
- Call `WorldEmergencePhase.execute(state, update, recent_events=[depleted_event])`.
- Assert returned `StateUpdate` contains a `quest_registry_add` list with one `QuestOpportunity`.
- Apply via `ApplyPath.apply_generation(state, state_upd)`.
- Assert `new_state.quest_registry` has one entry with `status=OFFERED`.

### AC-5: `OFFERED → EXPIRED` after `expiry_ticks`

```
test_quest_expires_after_expiry_ticks
```
- Build state with `quest_registry = {"opp1": QuestOpportunity(..., expiry_ticks=10, status=OFFERED)}` at tick 5.
- Advance to tick 11 (> expiry_ticks=10).
- Call `QuestLifecycleService.tick(state)`.
- Assert returned `StateUpdate` contains `quest_registry_remove=["opp1"]` and `world_events_add` has a `QUEST_FAILED`/`QUEST_EXPIRED` event.
- Apply via `ApplyPath.apply_generation(state, state_upd)`.
- Assert `new_state.quest_registry == {}`.

### AC-6: Quest still `OFFERED` before `expiry_ticks`

```
test_quest_not_expired_before_expiry_ticks
```
- Same setup as AC-5 but tick=9 (< expiry_ticks=10).
- Call `QuestLifecycleService.tick(state)`.
- Assert returned `StateUpdate` is noop (`is_noop()` or `quest_registry_remove == []`).

### AC-7: `OFFERED → ACTIVE` transition is authoritative

```
test_quest_offered_to_active_transition
```
- Build state with one `OFFERED` quest in `quest_registry`.
- Emit `QuestStatusUpdate(quest_id="opp1", new_status=QuestOpportunityStatus.ACTIVE)` inside a `StateUpdate`.
- Apply via `ApplyPath.apply_generation`.
- Assert `new_state.quest_registry["opp1"].status == QuestOpportunityStatus.ACTIVE`.

### AC-8: No double-registration (idempotent add)

```
test_quest_registry_add_is_idempotent
```
- Build state with one quest in `quest_registry`.
- Apply a `StateUpdate` with `quest_registry_add=[same_opportunity]`.
- Assert registry still has exactly one entry (no duplicate).
- Idempotency key: `QuestOpportunity.id`.

### AC-9: Expiry sweep is deterministic (sorted order)

```
test_expiry_sweep_deterministic_order
```
- Build state with three `OFFERED` quests all past expiry at different `expiry_ticks`.
- Call `QuestLifecycleService.tick(state)` twice with identical state.
- Assert both calls return identical `StateUpdate` (same `quest_registry_remove` list, same order).

### AC-10: `REWARDED`/`REWARD_PENDING` states on `QuestState` unaffected (regression guard)

```
test_entity_quest_status_unaffected_by_e23b
```
- Run existing `test_quest_completion_and_reward_emission` scenario end-to-end.
- Assert `QuestStatus.REWARDED` still reachable and `QuestStatus.REWARD_PENDING` still present.
- This test explicitly guards against Option A collateral damage.

---

## Scoped Pytest Commands

```bash
# Primary — new and changed lifecycle tests
pytest tests/unit/quest/test_quest_lifecycle.py -x -v

# Wiring test (new file)
pytest tests/unit/domains/world_emergence/test_quest_registry_wiring.py -x -v

# Full quest domain regression
pytest tests/unit/quest/ -x -v

# World emergence domain regression
pytest tests/unit/domains/world_emergence/ -x -v

# Confirm no reward pipeline regression
pytest tests/unit/quest/test_quest_transactions.py tests/unit/quest/test_progression_lifecycle.py tests/unit/quest/test_progression_regression.py -x -v
```

---

## Anti-Drift Test Guards

1. **Guard: `QuestStatus.REWARDED` still importable**
   Add assertion `from src.core.models.quests import QuestStatus; assert QuestStatus.REWARDED` to `test_entity_quest_status_unaffected_by_e23b`. If the implementer accidentally removes `REWARDED`, this test fails loudly.

2. **Guard: `quest_registry` not unbounded**
   In `test_quest_expires_after_expiry_ticks` (AC-5), after applying the expiry update, assert `len(new_state.quest_registry) == 0`. This ensures expired quests are removed, not accumulated.

3. **Guard: registry mutation only through StateUpdate**
   `test_quest_registry_field_on_authoritative_state` (AC-1) uses `replace()` to verify state immutability. Add assertion that `state.quest_registry is not new_state.quest_registry` (different dict objects), confirming no in-place mutation.

4. **Guard: `QuestOpportunity` construction with E23A pattern still works**
   Add to `test_quest_generation.py` a construction that omits `status` and asserts `status == OFFERED` (default). This confirms backward compatibility after the `status` field is added to `QuestOpportunity`.

5. **Guard: pipeline phase 19 (quest_rewards) unaffected**
   Run `pytest tests/unit/quest/test_quest_system.py -k "enforce" -x -v` after implementation to confirm `QuestResolutionSystem.enforce()` still transitions `ACTIVE → REWARD_PENDING → REWARDED` on `QuestState` objects (the entity-level machine, unchanged by E23B).
