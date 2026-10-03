---
ticket_id: TCK-20260619-E41B-LEADERSHIP
phase: plan
date: 2026-06-21
---

# Implementation Plan — TCK-20260619-E41B-LEADERSHIP

## Overview

Implement `PartyLifecycleService` with `check_leadership()` method, `LeadershipChangedEvent` in `events.py`, wire into `GroupPhase.resolve()`, and write tests.

---

## Files to Create/Modify

| File | Action | Notes |
|---|---|---|
| `src/systems/social_systems/party_lifecycle.py` | CREATE | `PartyLifecycleService` class |
| `src/observability/events.py` | MODIFY | Add `LeadershipChangedEvent` |
| `src/engine/pipeline_phases/groups.py` | MODIFY | Call `PartyLifecycleService` after `GroupSystem.update_groups()` |
| `tests/unit/social/test_party_lifecycle.py` | CREATE | 6 unit tests |
| `docs/parity_ledger/social_narrative.yaml` | MODIFY | Add SOC-228 parity entry |

---

## Step 1: `src/systems/social_systems/party_lifecycle.py`

```python
class PartyLifecycleService:
    LEADERSHIP_CHECK_INTERVAL = 100  # ticks

    @staticmethod
    def check_leadership(
        group: GroupRecord,
        members: list[EntityState],
        tick: int
    ) -> tuple[Optional[GroupRecord], Optional[LeadershipChangedEvent]]:
        """
        Elect new leader if current leader's sociability < best member's sociability by >= 0.2.
        Returns (updated_group, event_or_None).
        If interval not reached: returns (None, None).
        If no election needed: returns (updated_group_with_tick, None).
        If election happens: returns (updated_group_with_new_leader, LeadershipChangedEvent).
        """
        if tick - group.last_leadership_check_tick < LEADERSHIP_CHECK_INTERVAL:
            return (None, None)
        # collect sociabilities for members present in this group
        sociabilities = {
            e.id: e.personality.sociability
            for e in members
            if e.id in group.member_ids
        }
        if not sociabilities:
            return (replace(group, last_leadership_check_tick=tick), None)
        current = sociabilities.get(group.leader_id, 0.0)
        best_id = max(sociabilities, key=sociabilities.__getitem__)
        if sociabilities[best_id] - current >= 0.2:
            updated = replace(group, leader_id=best_id, last_leadership_check_tick=tick)
            event = LeadershipChangedEvent(
                tick=tick, group_id=group.id,
                old_leader_id=group.leader_id, new_leader_id=best_id
            )
            return (updated, event)
        return (replace(group, last_leadership_check_tick=tick), None)
```

Return type is `tuple[Optional[GroupRecord], Optional[LeadershipChangedEvent]]`.

---

## Step 2: `src/observability/events.py` — Add `LeadershipChangedEvent`

```python
class LeadershipChangedEvent(SimulationEvent):
    """Emitted when leadership of a party group changes due to sociability election."""
    group_id: int
    old_leader_id: int
    new_leader_id: int
    morale_delta: float = 0.1
    event_type: str = "leadership_changed"
    event_category: EventCategory = "social"
    severity: EventSeverity = "INFO"
    source_system: str = "party_lifecycle_service"
    message: str = ""

    def __init__(self, **data: Any) -> None:
        if "message" not in data or not data["message"]:
            g = data.get("group_id")
            old = data.get("old_leader_id")
            new = data.get("new_leader_id")
            data["message"] = f"Group {g} leadership changed from entity {old} to entity {new}"
        super().__init__(**data)
```

---

## Step 3: `src/engine/pipeline_phases/groups.py` — Wire lifecycle service

After `GroupSystem.update_groups()` merges surviving groups into `groups_add_or_update`, iterate the surviving groups and call `PartyLifecycleService.check_leadership()`. Collect returned `GroupRecord` updates (replace the group in the list) and emit returned events via a module-level event collector list (cleared per call). Tests can inspect the returned events via a `GroupPhase.last_tick_events` class attribute (list, cleared on each `resolve()` call).

This avoids modifying `StateUpdate` and avoids coupling to the kernel's event recorder.

---

## Step 4: Tests (`tests/unit/social/test_party_lifecycle.py`)

Six tests using `V2EntityBuilder` or direct `GroupRecord`/`EntityState` construction. Tests call `PartyLifecycleService.check_leadership()` directly (pure function). One integration-style test verifies `GroupPhase.resolve()` emits event to `GroupPhase.last_tick_events`.

---

## Architecture Review Checkpoints

- All state mutations via typed `GroupRecord` in `groups_add_or_update` — no direct state writes.
- `PartyLifecycleService.check_leadership()` is a pure static method — no side effects, no state mutation.
- Determinism preserved: `max()` over dict with stable key ordering (`e.id` integers); use `min(candidates)` as tiebreaker when multiple members share max sociability.
- No raw domain models exposed from APIs.
- `last_leadership_check_tick` already on `GroupRecord` — no new fields needed.
