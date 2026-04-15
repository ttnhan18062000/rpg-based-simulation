import pytest
from src.core.entities.entity import Entity
from src.core.models.world_state import WorldState
from src.core.models.life_events import TurningPointRecord
from src.core.models.enums import TurningPointKind, DirectiveKind
from src.core.logic.directive_mutation_service import DirectiveMutationService
from src.actions.base import StrategicUpdate
from src.systems.rng import DeterministicRNG

@pytest.fixture
def base_world():
    from unittest.mock import MagicMock
    world = WorldState(seed=42, grid=MagicMock(), spatial_index=MagicMock())
    # Add an entity
    entity = Entity(id=1, kind="hero")
    world.entities[1] = entity
    return world

def test_directive_mutation_salience_threshold(base_world):
    """Verify that only high-salience turning points trigger mutations."""
    entity = base_world.entities[1]
    rng = DeterministicRNG(42)
    updates = StrategicUpdate()
    
    # 1. Low salience (threshold is 0.8)
    tp_low = TurningPointRecord(
        event_id="ev1",
        kind=TurningPointKind.NEAR_DEATH,
        tick=10,
        salience_score=0.5,
        emotional_impact=-2.0
    )
    
    DirectiveMutationService.evaluate_mutation(base_world, entity, tp_low, updates, rng)
    assert len(updates.directives_add) == 0
    
    # 2. High salience (requires history to satisfy count threshold)
    tp_high = TurningPointRecord(
        event_id="ev2",
        kind=TurningPointKind.NEAR_DEATH,
        tick=11,
        salience_score=0.9,
        emotional_impact=-5.0
    )
    tp_prev = TurningPointRecord(event_id="prev", kind=TurningPointKind.NEAR_DEATH, tick=0, salience_score=1.0)
    entity.mind.narrative.turning_points = [tp_prev, tp_prev, tp_high]
    
    DirectiveMutationService.evaluate_mutation(base_world, entity, tp_high, updates, rng)
    assert len(updates.directives_add) == 1
    assert updates.directives_add[0].label == "Safety & Self-Preservation"
    assert updates.directives_add[0].priority == 3.5

def test_directive_priority_strengthening(base_world):
    """Verify that repeated high-salience events strengthen directive priority."""
    entity = base_world.entities[1]
    rng = DeterministicRNG(42)
    
    # Manually add existing directive
    from src.core.models.strategy import DirectiveRecord
    existing_d = DirectiveRecord(
        directive_id="dir_safety",
        kind=DirectiveKind.PERSONAL,
        label="Safety & Self-Preservation",
        priority=3.5
    )
    entity.mind.strategic.directives.append(existing_d)
    
    updates = StrategicUpdate()
    tp_repeat = TurningPointRecord(
        event_id="ev3",
        kind=TurningPointKind.NEAR_DEATH,
        tick=20,
        salience_score=0.9
    )
    tp_prev = TurningPointRecord(event_id="prev", kind=TurningPointKind.NEAR_DEATH, tick=0, salience_score=1.0)
    entity.mind.narrative.turning_points = [tp_prev, tp_prev, tp_repeat]
    
    DirectiveMutationService.evaluate_mutation(base_world, entity, tp_repeat, updates, rng)
    
    assert len(updates.directives_add) == 1
    assert updates.directives_add[0].priority == 4.0 # 3.5 + 0.5
