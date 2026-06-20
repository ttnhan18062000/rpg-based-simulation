---
status: open
layer: simulation
authority: P1
audience: agent
ticket_id: TCK-20260619-E23B-QUEST-LIFECYCLE
phase: open
date: 2026-06-20
tags: [quest-generation, lifecycle, quest-registry, durable-state, phase-2]
---

# TCK-20260619-E23B-QUEST-LIFECYCLE

## Title
Epic 2.3B · Quest Lifecycle State Machine + quest_registry

## Status
OPEN

## Tier
standard

## Type
feature

## Priority
P1

## Request Summary
No world-level `quest_registry` exists in `AuthoritativeState` and `QuestState` has no OFFERED/ACTIVE/PROGRESSED/EXPIRED lifecycle states. This ticket adds both: the durable registry and the lifecycle state machine with authoritative transitions.

**Requires:** TCK-20260619-E23A-QUEST-OPPORTUNITY

## Scope

### 1. Add `quest_registry` to `AuthoritativeState` — `src/core/state.py`

```python
quest_registry: Dict[str, QuestOpportunity] = field(default_factory=dict)
```

Keyed by `QuestOpportunity.id`. Stores all currently OFFERED and ACTIVE quests. COMPLETED/FAILED/EXPIRED quests are removed (moved to event log, not durable state).

### 2. Add lifecycle state enum to `src/core/models/quests.py`

```python
class QuestStatus(str, Enum):
    OFFERED = "OFFERED"
    ACTIVE = "ACTIVE"
    PROGRESSED = "PROGRESSED"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    EXPIRED = "EXPIRED"
```

Add `status: QuestStatus = QuestStatus.OFFERED` to `QuestOpportunity` (update E23A's dataclass definition accordingly — coordinate with E23A implementer).

### 3. Implement lifecycle transitions (authoritative)

All transitions must go through the authoritative mutation pipeline. Create update model `QuestStatusUpdate(quest_id: str, new_status: QuestStatus)` in `src/core/updates.py` (or equivalent location).

Lifecycle rules:
- `OFFERED → ACTIVE`: entity accepts quest (picks up in routing decision)
- `ACTIVE → PROGRESSED`: entity completes first objective
- `PROGRESSED → COMPLETED`: all objectives done
- `OFFERED → EXPIRED`: tick > `expiry_ticks` and quest still OFFERED
- `ACTIVE → FAILED`: entity dies or abandons route for N ticks

### 4. Implement `QuestLifecycleService` — `src/domains/world_emergence/` or `src/systems/`

```python
class QuestLifecycleService:
    @staticmethod
    def tick(state: AuthoritativeState) -> StateUpdate:
        """Expire OFFERED quests past their expiry_ticks."""
        updates = []
        for quest in state.quest_registry.values():
            if quest.status == QuestStatus.OFFERED and state.tick > quest.expiry_ticks:
                updates.append(QuestStatusUpdate(quest_id=quest.id, new_status=QuestStatus.EXPIRED))
        return StateUpdate(quest_status_updates=updates)
```

### 5. Wire `QuestOpportunity` objects from E23A into `quest_registry`

When `WorldEmergencePhase` produces `QuestOpportunity` objects (from E23A), they must be added to `quest_registry` via the authoritative apply path (not direct assignment). Add to apply path in `authoritative_pipeline.py` or equivalent.

## Out of Scope
- Reward application (E23C)
- HERO matching (E23D)

## Acceptance Criteria
- `AuthoritativeState.quest_registry` field exists and serializes correctly
- `QuestStatus.OFFERED`, `ACTIVE`, `PROGRESSED`, `COMPLETED`, `FAILED`, `EXPIRED` are all accessible
- After `WorldEmergencePhase` runs: `state.quest_registry` contains new `QuestOpportunity` with `status=OFFERED`
- After `expiry_ticks` ticks: quest transitions to `EXPIRED`
- Tests in `tests/unit/quest/test_quest_lifecycle.py` pass

## Related Tickets
- TCK-20260619-E23-QUEST-GENERATION (parent epic)
- TCK-20260619-E23A-QUEST-OPPORTUNITY (required first — provides QuestOpportunity type)
- TCK-20260619-E23C-QUEST-REWARDS (blocked on this)
- TCK-20260619-E23D-HERO-MATCHING (blocked on this)

## Related Docs
- `docs/engine/authoritative_pipeline.md` (verify phase insertion for quest_registry mutations)
- `docs/core/state.md` (immutability law — quest_registry must follow durable state rule)

## Related Code Areas
- `src/core/state.py` (add quest_registry to AuthoritativeState)
- `src/core/models/quests.py` (add QuestStatus enum; add status field to QuestOpportunity)
- `src/core/updates.py` (add QuestStatusUpdate)
- `src/domains/world_emergence/` (QuestLifecycleService + wire into WorldEmergencePhase output)
- `tests/unit/quest/test_quest_lifecycle.py` (new)

## Assumptions / Open Questions
- Does `AuthoritativeState` use `frozen=True`? If so, adding `quest_registry` with `default_factory=dict` needs care — check if mutable containers are allowed (they likely are, as other dict fields exist like `resource_nodes`).
- Where does `WorldEmergencePhase` output flow? Find how phase outputs get applied to `AuthoritativeState` before wiring quest_registry additions.

## Test Summary
```bash
pytest tests/unit/quest/test_quest_lifecycle.py -x -v
pytest tests/unit/quest/ -x -v  # regression
```

## Files Changed
_To be filled on completion._

## Completion Summary
_To be filled on completion._
