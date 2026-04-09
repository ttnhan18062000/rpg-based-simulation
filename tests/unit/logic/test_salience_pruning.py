import pytest
from src.core.entities.entity import Entity
from src.core.aspects.mind import MindAspect, InterpretedEvent
from src.core.logic.memory_salience import MemorySalienceService
from src.core.models.vectors import Vector2

def test_weighted_salience_calculation():
    event = InterpretedEvent(tick=100, type="test", impact=1.0, details={})
    
    # Same tick: multiplier should be 1.0
    weight_now = MemorySalienceService.calculate_weighted_impact(event, 100)
    assert weight_now == 1.0
    
    # 100 ticks later: multiplier should be 1.0 - (100 * 0.001) = 0.9
    weight_later = MemorySalienceService.calculate_weighted_impact(event, 200)
    assert pytest.approx(weight_later, 0.01) == 0.9
    
    # 1000 ticks later: multiplier should be 0.1 (clamped)
    weight_far_future = MemorySalienceService.calculate_weighted_impact(event, 1100)
    assert weight_far_future == 0.1

def test_memory_pruning_priority():
    # Setup entity with mock memories
    # We need a minimal entity setup
    from src.core.world.grid import Grid
    from src.platform.spatial_hash import SpatialHash
    from src.core.models.world_state import WorldState
    
    world = WorldState(seed=0, grid=Grid(10,10), spatial_index=SpatialHash(10))
    entity = Entity(id=1, kind="hero", pos=Vector2(0,0))
    
    # Event 1: High impact but OLD (Tick 0, Impact 2.0)
    # Event 2: Medium impact and RECENT (Tick 90, Impact 1.5)
    # Event 3: Low impact and RECENT (Tick 95, Impact 0.5)
    
    current_tick = 100
    e1 = InterpretedEvent(tick=0, type="old_boss", impact=2.0, details={})
    e2 = InterpretedEvent(tick=90, type="recent_duel", impact=1.5, details={})
    e3 = InterpretedEvent(tick=95, type="recent_loot", impact=0.5, details={})
    
    entity.mind.narrative.memory_log = [e1, e2, e3]
    
    # Prune to 2 entries
    MemorySalienceService.prune(entity, current_tick, max_entries=2)
    
    # Weighted impacts (decay=0.002 as used in prune):
    # e1 (age 100): 2.0 * (1 - 100*0.002) = 2.0 * 0.8 = 1.6
    # e2 (age 10): 1.5 * (1 - 10*0.002) = 1.5 * 0.98 = 1.47
    # e3 (age 5): 0.5 * (1 - 5*0.002) = 0.5 * 0.99 = 0.495
    
    # e1 and e2 should be kept. e3 should be discarded.
    assert len(entity.mind.narrative.memory_log) == 2
    assert any(m.type == "old_boss" for m in entity.mind.narrative.memory_log)
    assert any(m.type == "recent_duel" for m in entity.mind.narrative.memory_log)
    assert not any(m.type == "recent_loot" for m in entity.mind.narrative.memory_log)
