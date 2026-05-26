import pytest
from pydantic import ValidationError
from collections import deque
from src.observability.events import (
    SimulationEvent, CombatDamageEvent, CombatKillEvent,
    GoldTransactionEvent, QuestEvent, MovementEvent, LifecycleEvent
)
from src.core.state import EntityState
from src.core.state import IdentityComponent, CombatComponent

def test_pydantic_events_validation():
    # Valid CombatDamageEvent
    ev = CombatDamageEvent(
        tick=5,
        entity_id=1,
        attacker_id=2,
        damage=15,
        is_lethal=False
    )
    assert ev.tick == 5
    assert ev.entity_id == 1
    assert ev.damage == 15
    assert ev.event_type == "combat_damage"
    assert ev.timestamp > 0

    # Serialization/Deserialization
    dumped = ev.model_dump()
    assert dumped["event_type"] == "combat_damage"
    assert dumped["damage"] == 15
    
    loaded = CombatDamageEvent.model_validate(dumped)
    assert loaded.attacker_id == 2

    # Validation failure: missing damage
    with pytest.raises(ValidationError):
        CombatDamageEvent(tick=1, entity_id=1, is_lethal=False)

def test_entity_state_timeline_rollover():
    entity = EntityState(
        id=123,
        kind="hero"
    )
    assert hasattr(entity, "timeline")
    assert isinstance(entity.timeline, deque)
    assert entity.timeline.maxlen == 200

    # Fill timeline to roll over
    for i in range(250):
        ev = MovementEvent(
            tick=i,
            entity_id=123,
            start_pos=(float(i), float(i)),
            end_pos=(float(i+1), float(i+1))
        )
        entity.timeline.append(ev)

    # Rollover check
    assert len(entity.timeline) == 200
    assert entity.timeline[0].tick == 50
    assert entity.timeline[-1].tick == 249
