import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", ".."))


import pytest
from src_legacy.core.entities.entity_builder import EntityBuilder
from src_legacy.platform.rng import DeterministicRNG
from src_legacy.core.models.enums import Faction, EntityRole

def test_eb_stats_scaling():
    rng = DeterministicRNG(42)
    eid = 1
    tick = 0
    
    eb = EntityBuilder(rng, eid, tick)
    eb.kind("boss")
    eb.with_base_stats(hp=600, atk=120)
    eb.is_world_boss(True)
    
    entity = eb.build()
    

    
    assert entity.kind == "boss"
    assert entity.combat.hp >= 600
    assert entity.identity.is_world_boss is True

if __name__ == "__main__":
    test_eb_stats_scaling()
