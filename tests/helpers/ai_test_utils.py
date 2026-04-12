from typing import Any
from src.core.entities.entity import Entity
from src.core.models.snapshot import Snapshot
from src.ai.states.base import AIContext
from src.config import SimulationConfig
from src.platform.rng import DeterministicRNG
from src.core.gameplay.faction import FactionRegistry
from src.core.world.grid import Grid
from src.core.models.vectors import Vector2

def make_test_ai_context(actor: Entity, enemies: list[Entity] | None = None) -> AIContext:
    """Helper to create a minimal valid AIContext for unit testing."""
    entities = {actor.id: actor}
    if enemies:
        for e in enemies:
            entities[e.id] = e
            
    snapshot = Snapshot(
        tick=1,
        seed=42,
        entities=entities,
        grid=Grid(width=20, height=20, tiles=bytearray(400)), 
        ground_items={},
        camps=(),
        buildings=(),
        resource_nodes=(),
        treasure_chests=(),
        regions=()
    )
    
    return AIContext(
        actor=actor,
        snapshot=snapshot,
        config=SimulationConfig(),
        rng=DeterministicRNG(42),
        faction_reg=FactionRegistry.default(),
        _visible_override=enemies
    )
