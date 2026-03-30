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
    boss.mind.memory_log.append({"tick": 100, "type": "GLORY", "impact": 60.0})
    
    # Run system update
    system.on_tick(context, 500)
    
    # Verify evolution
    assert boss.mind.memory.get("evolution_level") == 1
    assert boss.combat.max_hp == 1200 # +20%
    assert boss.combat.atk == 60 # +20%
    assert "Evolved" in boss.identity.display_name
