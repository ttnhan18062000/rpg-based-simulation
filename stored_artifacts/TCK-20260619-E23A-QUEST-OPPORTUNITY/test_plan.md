---
status: active
layer: simulation
authority: P1
audience: agent
ticket_id: TCK-20260619-E23A-QUEST-OPPORTUNITY
artifact_type: test_plan
tags: [quest-generation, pressure-driven, opportunity-type]
---

# Test Plan — TCK-20260619-E23A-QUEST-OPPORTUNITY

---

## Regression Surface (existing tests that must pass)

| Test file | Why it must pass |
|---|---|
| `tests/unit/quest/test_quest_generation.py` | Imports from `src/quests/generator` (legacy QuestGenerator) — must not break |
| `tests/unit/domains/world_emergence/test_phase8_world_emergence_boundary.py` | WorldEmergencePhase.execute() — must still return result with pressures |
| `tests/unit/domains/world_emergence/test_phase8_world_event_aggregator.py` | Aggregator unchanged |
| `tests/unit/domains/world_emergence/test_phase8_regional_pressure_model.py` | PressureModel unchanged |
| `tests/unit/domains/world_emergence/test_phase8_scarcity_model.py` | ScarcityModel unchanged |

---

## New Tests Required (per AC)

All new tests go in `tests/unit/quest/test_quest_generation.py`.

### AC1: `QuestOpportunity` dataclass constructs without error

```python
def test_quest_opportunity_constructs():
    opp = QuestOpportunity(
        id="rc_1_42",
        kind="resource_crisis",
        trigger_condition="iron_ore depleted in old_mine at tick 42",
        objective_chain=("fetch:iron_ore:3",),
        reward_spec={"gold": 50, "xp": 100, "faction_rep": 0.1},
        faction_source=None,
        expiry_ticks=200,
        source_event_id="RESOURCE_DEPLETED_old_mine_42",
    )
    assert opp.kind == "resource_crisis"
    assert opp.id == "rc_1_42"
```

### AC2: `from_resource_depleted()` returns non-None `QuestOpportunity` with `kind="resource_crisis"`

```python
def test_resource_crisis_quest_generated_on_depletion():
    event = WorldEvent(
        category=WorldEventCategory.RESOURCE_DEPLETED,
        tick=42,
        region_id="old_mine",
        subject="iron_ore",
        severity=1.0,
    )
    result = QuestOpportunityGenerator.from_resource_depleted(event, tick=42, seed=0)
    assert result is not None
    assert result.kind == "resource_crisis"
    assert result.source_event_id is not None
    assert len(result.objective_chain) > 0
```

### AC3: Same input + same seed → same `QuestOpportunity.id` (determinism)

```python
def test_quest_generation_determinism_opportunity():
    event = WorldEvent(
        category=WorldEventCategory.RESOURCE_DEPLETED,
        tick=100,
        region_id="forest_node",
        subject="wood",
        severity=0.8,
    )
    r1 = QuestOpportunityGenerator.from_resource_depleted(event, tick=100, seed=7)
    r2 = QuestOpportunityGenerator.from_resource_depleted(event, tick=100, seed=7)
    assert r1 is not None and r2 is not None
    assert r1.id == r2.id
    assert r1.objective_chain == r2.objective_chain
```

### AC4: `WorldEmergencePhase.execute()` includes `quest_opportunities` in result

```python
def test_world_emergence_phase_emits_quest_opportunities():
    regions = {"old_mine": RegionState(id="old_mine", name="Old Mine", bounds=(0,0,10,10))}
    state = AuthoritativeState(entities={}, regions=regions, tick=50, seed=0)
    update = StateUpdate()
    events = [
        WorldEvent(category=WorldEventCategory.RESOURCE_DEPLETED,
                   tick=48, region_id="old_mine", subject="iron_ore", severity=1.0)
    ]
    _, result = WorldEmergencePhase.execute(state, update, events)
    assert hasattr(result, "quest_opportunities")
    assert len(result.quest_opportunities) > 0
    assert result.quest_opportunities[0].kind == "resource_crisis"
```

### AC5: `from_threat_signal()` returns non-None for high-severity threat event

```python
def test_threat_response_quest_generated_on_high_severity():
    event = WorldEvent(
        category=WorldEventCategory.ENTITY_DEATH,
        tick=55,
        region_id="dark_forest",
        subject="hero",
        severity=0.9,
    )
    result = QuestOpportunityGenerator.from_threat_signal(event, tick=55, seed=0)
    assert result is not None
    assert result.kind == "threat_response"
```

### AC6: `from_entity_need()` returns None (stub)

```python
def test_entity_need_quest_stub_returns_none():
    result = QuestOpportunityGenerator.from_entity_need(
        entity_id=1, need_kind="food", ticks_unsatisfied=50, tick=100
    )
    assert result is None
```

---

## Scoped Pytest Commands

```bash
pytest tests/unit/quest/test_quest_generation.py -x -v
pytest tests/unit/domains/world_emergence/test_phase8_world_emergence_boundary.py -x -v
```

Combined:
```bash
pytest tests/unit/quest/test_quest_generation.py tests/unit/domains/world_emergence/ -x -v
```

---

## Anti-Drift Test Guards

- Verify `QuestOpportunity.id` is deterministic by calling generator twice with same inputs (AC3).
- Verify `WorldEmergencePhase` result has `quest_opportunities` attribute (AC4) — guards against
  `WorldEmergenceResult` being returned without the new field.
- Verify `from_entity_need` returns `None` (AC6) — guards against premature implementation of stub.
- Existing `test_world_emergence_is_deterministic` must still pass — guards against breaking phase determinism.
