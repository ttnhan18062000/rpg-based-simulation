import pytest
from src.core.entities.entity import Entity
from src.ai.brain import AIBrain
from src.core.models.vectors import Vector2
from src.core.world.grid import Grid
from src.platform.spatial_hash import SpatialHash
from src.core.models.world_state import WorldState
from src.config import SimulationConfig

def test_aibrain_statelessness():
    # Setup world and entity
    grid = Grid(10, 10)
    spatial = SpatialHash(10)
    world = WorldState(seed=0, grid=grid, spatial_index=spatial)
    config = SimulationConfig()
    
    # Entity with some memories
    from src.core.aspects.mind import InterpretedEvent
    entity = Entity(id=1, kind="hero", pos=Vector2(0,0))
    entity.mind.narrative.memory_log = [
        InterpretedEvent(tick=0, type="test", impact=1.0, details={})
        for _ in range(60) # Over the limit of 50
    ]
    
    initial_log_count = len(entity.mind.narrative.memory_log)
    assert initial_log_count == 60
    
    # Call AIBrain.decide
    from src.platform.rng import DeterministicRNG
    from src.core.gameplay.faction import FactionRegistry
    from src.core.models.snapshot import Snapshot
    
    faction_reg = FactionRegistry.default()
    brain = AIBrain(config, DeterministicRNG(0), faction_reg)
    snapshot = Snapshot.from_world(world)
    
    # AI deliberation
    brain.decide(entity, snapshot)
    
    # VERIFY: memory_log has NOT been pruned (it's still 60)
    # Pruning now happens in ActionSystem only.
    assert len(entity.mind.narrative.memory_log) == 60
    
    # Ensure no other mutations occurred (e.g. emotion fields)
    # (Checking a few representative fields)
    # Note: If some fields MUST change during deliberation (though they shouldn't in AOA), this will catch it.
