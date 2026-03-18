import pytest
from src.core.entity_builder import EntityBuilder
from src.systems.rng import DeterministicRNG
from src.core.enums import Faction, EntityRole

def test_eb_stats_scaling():
    rng = DeterministicRNG(42)
    eid = 1
    tick = 0
    
    eb = EntityBuilder(rng, eid, tick)
    eb.kind("boss")
    eb.with_base_stats(hp=600, atk=120)
    eb.is_world_boss(True)
    
    entity = eb.build()
    
    print(f"DEBUG: entity.kind={entity.kind}")
    print(f"DEBUG: entity.stats.hp={entity.stats.hp}")
    print(f"DEBUG: entity.is_world_boss={entity.is_world_boss}")
    
    assert entity.kind == "boss"
    assert entity.stats.hp >= 600
    assert entity.is_world_boss is True

if __name__ == "__main__":
    test_eb_stats_scaling()
