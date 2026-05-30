# tests/perf/test_phase8_world_emergence_budget.py
import pytest
import time
from src.core.builder import V2EntityBuilder
from src.core.state import AuthoritativeState, RegionState
from src.core.updates import StateUpdate
from src.domains.world_emergence.phase import WorldEmergencePhase
from src.domains.world_emergence.schema import WorldEvent, WorldEventCategory

def test_phase8_performance_budget():
    """Verify that WorldEmergencePhase executes in under 5.0ms for 100+ entities and 100+ events."""
    regions = {f"region_{i}": RegionState(id=f"region_{i}", name=f"Region {i}", bounds=(0, 0, 10, 10)) for i in range(10)}
    
    entities = {}
    for i in range(100):
        entity = (V2EntityBuilder(i)
                  .kind("HERO")
                  .location(0.0, 0.0)
                  .navigation(region_id=f"region_{i % 10}")
                  .build())
        entities[i] = entity
        
    state = AuthoritativeState(entities=entities, regions=regions, tick=100, seed=0)
    
    # 100 random events
    events = []
    for i in range(100):
        events.append(WorldEvent(
            category=WorldEventCategory.ENTITY_DEATH if i % 2 == 0 else WorldEventCategory.RESOURCE_DEPLETED,
            tick=i,
            region_id=f"region_{i % 10}",
            subject="iron_ore" if i % 2 != 0 else None
        ))
        
    update = StateUpdate()
    
    t_start = time.perf_counter_ns()
    res_upd, result = WorldEmergencePhase.execute(state, update, events)
    duration_ms = (time.perf_counter_ns() - t_start) / 1e6
    
    print(f"Phase 8 execution for 100 entities & 100 events took: {duration_ms:.2f} ms")
    assert duration_ms < 5.0
