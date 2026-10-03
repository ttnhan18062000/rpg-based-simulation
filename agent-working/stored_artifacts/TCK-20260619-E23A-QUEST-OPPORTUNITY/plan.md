---
status: active
layer: simulation
authority: P1
audience: agent
ticket_id: TCK-20260619-E23A-QUEST-OPPORTUNITY
artifact_type: plan
tags: [quest-generation, pressure-driven, opportunity-type]
---

# Plan — TCK-20260619-E23A-QUEST-OPPORTUNITY

---

## Ordered Steps

### Step 1 — Add `QuestOpportunity` dataclass to `src/core/models/quests.py`

**Files:** `src/core/models/quests.py`

Add a new frozen dataclass at the bottom of the file, after `QuestState`:

```python
@dataclass(frozen=True, slots=True)
class QuestOpportunity:
    id: str                        # deterministic: f"{kind}_{source_event_id}_{tick % 10000}"
    kind: str                      # "resource_crisis" | "threat_response" | "diplomatic_errand"
    trigger_condition: str         # what caused this opportunity
    objective_chain: tuple[str, ...] # ordered objective IDs e.g. ("fetch:iron_ore:3",)
    reward_spec: dict              # {"gold": int, "xp": int, "faction_rep": float}
    faction_source: str | None     # faction offering the quest (None = world event)
    expiry_ticks: int              # tick at which this EXPIRES if not ACTIVE
    source_event_id: str | None    # event ID that triggered this
```

No other classes in quests.py are changed.

**Scope guard:** Do NOT modify `QuestState`, `QuestKind`, `QuestStatus`, or `RewardState`.

---

### Step 2 — Add `QuestOpportunityGenerator` to `src/domains/world_emergence/services.py`

**Files:** `src/domains/world_emergence/services.py`

Add import of `QuestOpportunity` from `src.core.models.quests` at top of file.

Add new class `QuestOpportunityGenerator` after `RumorSeedService`:

```python
class QuestOpportunityGenerator:
    """Converts world pressure signals into typed QuestOpportunity objects."""

    @staticmethod
    def from_resource_depleted(event: WorldEvent, tick: int, seed: int) -> QuestOpportunity | None:
        # Only process RESOURCE_DEPLETED events
        # source_event_id: deterministic string from event fields
        # objective_chain: ("fetch:{subject}:3",) or ("gather:{subject}:1",)
        # reward_spec: scaled by severity
        # id: f"resource_crisis_{source_event_id}_{tick % 10000}"
        # expiry_ticks: 200 (configurable later)
        ...

    @staticmethod
    def from_threat_signal(threat_event: WorldEvent, tick: int, seed: int) -> QuestOpportunity | None:
        # Only process high-severity (>= 0.5) threat events (ENTITY_DEATH, CAMP_RAID)
        # objective_chain: ("eliminate:{subject}:1",) or ("clear_threat:1",)
        # id: f"threat_response_{source_event_id}_{tick % 10000}"
        # expiry_ticks: 100
        ...

    @staticmethod
    def from_entity_need(entity_id: int, need_kind: str, ticks_unsatisfied: int, tick: int) -> QuestOpportunity | None:
        # Stub — returns None until Phase 5
        return None
```

**Scope guard:** Do NOT modify `WorldOpportunityPressureService`, `DynamicQuestSeedService`,
`RumorSeedService`, or `WorldToEntitySignalBridge`.

---

### Step 3 — Add `quest_opportunities` field to `WorldEmergenceResult` in `src/domains/world_emergence/schema.py`

**Files:** `src/domains/world_emergence/schema.py`

Add import `from src.core.models.quests import QuestOpportunity` at top (after existing imports,
inside TYPE_CHECKING guard or direct — check for circular imports first).

Add field to `WorldEmergenceResult`:
```python
quest_opportunities: Tuple[QuestOpportunity, ...] = field(default_factory=tuple)
```

**Scope guard:** Do NOT modify any other dataclass in schema.py.

**Circular import check:** `schema.py` currently imports nothing from `src.core.models`. Adding
`QuestOpportunity` from `src.core.models.quests` is safe — `quests.py` does NOT import from
`world_emergence`.

---

### Step 4 — Wire `QuestOpportunityGenerator` into `WorldEmergencePhase.execute()`

**Files:** `src/domains/world_emergence/phase.py`

Add import of `QuestOpportunityGenerator` from `src.domains.world_emergence.services`.

After step 5 (quest seeds, after `q_seeds = DynamicQuestSeedService.generate(...)`), add:

```python
# 5b. Generate quest opportunities from RESOURCE_DEPLETED and high-severity events
quest_opps = []
for ev in recent_events:
    if ev.category == WorldEventCategory.RESOURCE_DEPLETED:
        opp = QuestOpportunityGenerator.from_resource_depleted(ev, state.tick, state.seed)
        if opp is not None:
            quest_opps.append(opp)
    elif ev.severity >= 0.5 and ev.category in (
        WorldEventCategory.ENTITY_DEATH,
        WorldEventCategory.CAMP_RAID,
    ):
        opp = QuestOpportunityGenerator.from_threat_signal(ev, state.tick, state.seed)
        if opp is not None:
            quest_opps.append(opp)
```

Pass `quest_opportunities=tuple(quest_opps)` to `WorldEmergenceResult(...)`.

**Scope guard:** Do NOT change any other step in `execute()`. Do NOT write to `quest_registry` or
any durable store.

---

### Step 5 — Extend `tests/unit/quest/test_quest_generation.py` with new tests

**Files:** `tests/unit/quest/test_quest_generation.py`

Add imports at top:
```python
from src.core.models.quests import QuestOpportunity
from src.domains.world_emergence.services import QuestOpportunityGenerator
from src.domains.world_emergence.schema import WorldEvent, WorldEventCategory
from src.core.state import AuthoritativeState, RegionState
from src.core.updates import StateUpdate
from src.domains.world_emergence.phase import WorldEmergencePhase
```

Add 6 new test functions per test plan:
- `test_quest_opportunity_constructs`
- `test_resource_crisis_quest_generated_on_depletion`
- `test_quest_generation_determinism_opportunity` (named per AC: `test_quest_generation_determinism`)
- `test_world_emergence_phase_emits_quest_opportunities`
- `test_threat_response_quest_generated_on_high_severity`
- `test_entity_need_quest_stub_returns_none`

---

## Dependency Map

```
Step 1 (QuestOpportunity dataclass)
  ↓
Step 2 (QuestOpportunityGenerator) — depends on Step 1 for return type
Step 3 (WorldEmergenceResult field) — depends on Step 1 for field type
  ↓
Step 4 (phase wiring) — depends on Steps 2 and 3
  ↓
Step 5 (tests) — depends on Steps 1, 2, 3, 4
```

Steps 2 and 3 are independent of each other; both depend on Step 1.

---

## Acceptance Criteria → Steps

| AC | Step |
|---|---|
| `QuestOpportunity(...)` constructs without error | Step 1 |
| `from_resource_depleted()` returns non-None with `kind="resource_crisis"` | Step 2 |
| Same input + seed → same `QuestOpportunity.id` | Step 2 |
| `test_resource_crisis_quest_generated_on_depletion` passes | Steps 2, 5 |
| `test_quest_generation_determinism` passes | Steps 2, 5 |
| `WorldEmergencePhase` result includes `quest_opportunities` | Steps 3, 4, 5 |

---

## Scope Guards (Global)

- Do NOT add `quest_opportunities` to `quest_registry` (E23B's job).
- Do NOT use `uuid()` or non-deterministic ID generation.
- Do NOT import `QuestOpportunity` in hot-path entity brain code.
- Do NOT change existing services: `WorldOpportunityPressureService`, `DynamicQuestSeedService`, `RumorSeedService`.
- Do NOT implement `from_entity_need` logic — it is a stub returning `None`.

---

## Deviations

_None yet — to be filled if implementation diverges from plan._
