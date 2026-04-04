import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", ".."))


import pytest
from src.core.models.world_state import WorldState
from src.core.entities.entity import Entity, Vector2
from src.core.models.enums import Faction, AIState
from src.systems.calamity.calamity_evolution import CalamityEvolutionSystem
from src.systems.infrastructure.base import SystemContext
from src.platform.rng import DeterministicRNG
from src.config import SimulationConfig

@pytest.fixture
def context():
    config = SimulationConfig()
    rng = DeterministicRNG(0)
    class MockSpatialIndex:
        def insert(self, *args): pass
        def remove(self, *args): pass
        def move(self, *args): pass
    
    world = WorldState(seed=0, grid=None, spatial_index=MockSpatialIndex())
    return SystemContext(
        config=config,
        world=world,
        rng=rng,
        generator=None,
        faction_reg=None,
        emit=lambda *args, **kwargs: None
    )

def test_calamity_evolution(context):
    system = CalamityEvolutionSystem(context.config, context.rng)
    
    # Create a world boss entity
    from src.core.entities.entity_builder import EntityBuilder
    builder = EntityBuilder(context.rng, 100, 0)
    boss = (
        builder
        .kind("demon_lord")
        .is_world_boss(True)
        .with_base_stats(hp=1000, atk=50)
        .build()
    )
    context.world.entities[100] = boss
    
    # Give boss some glory
    from src.core.aspects.mind import MemoryLogEntry, CombatNarrative
    boss.mind.narrative.memory_log.append(
        MemoryLogEntry(
            tick=100, 
            type="glory", 
            impact=60.0,
            details=CombatNarrative(target_id=999, target_kind="hero", was_fatal=True)
        )
    )
    
    # Capture stats before evolution
    initial_hp = boss.combat.max_hp
    initial_atk = boss.combat.atk_base
    
    # Run system update
    system.on_tick(context, 500)
    
    # Verify evolution
    assert boss.mind.bonuses.get("evolution_level") == 1
    assert boss.combat.max_hp == int(initial_hp * 1.2)
    assert boss.combat.atk_base == int(initial_atk * 1.2)
    assert "Evolved" in boss.identity.display_name
