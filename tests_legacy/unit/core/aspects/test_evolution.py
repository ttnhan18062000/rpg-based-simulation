from __future__ import annotations
import os
import sys
import pytest
from unittest.mock import MagicMock

from src_legacy.core.entities.entity import Entity
from src_legacy.core.models.vectors import Vector2
from src_legacy.core.gameplay.attributes import Attributes, AttributeCaps
from src_legacy.core.models.enums import EnemyTier, RACE_PROFILES
from src_legacy.core.models.world_state import WorldState
from src_legacy.platform.rng import DeterministicRNG
from src_legacy.systems.lifecycle.progression_system import ProgressionSystem
from src_legacy.systems.infrastructure.base import SystemContext
from src_legacy.core.world.grid import Grid
from src_legacy.systems.spatial_hash import SpatialHash
from src_legacy.core.aspects.identity import IdentityAspect
from src_legacy.core.aspects.spatial import SpatialAspect
from src_legacy.core.aspects.combat import CombatAspect
from src_legacy.core.aspects.progression import ProgressionAspect
from src_legacy.core.aspects.mind import MindAspect
from src_legacy.core.aspects.inventory import InventoryAspect
from src_legacy.core.registry.registry_loader import load_all_registries
from src_legacy.config import SimulationConfig

@pytest.fixture(scope="module", autouse=True)
def setup_registries():
    # Load from the project root data directory
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
    data_dir = os.path.join(project_root, "data")
    load_all_registries(data_dir)

def test_entity_evolution_transformation():
    """Verify that a goblin evolves into a warrior/scout when hitting level cap. [AOA REFACTOR]"""
    cfg = SimulationConfig(world_seed=42)
    rng = DeterministicRNG(cfg.world_seed)
    
    # Goblin tier BASIC (1), level 11 (next level is cap 12)
    actor = Entity(
        id=1, kind="goblin",
        identity=IdentityAspect(display_name="Goblin", tier=1),
        spatial=SpatialAspect(pos=Vector2(10, 10)),
        combat=CombatAspect(hp=50, max_hp=50),
        progression=ProgressionAspect(
            level=11, xp=999, xp_to_next=100,
            attributes=Attributes(),
            attribute_caps=AttributeCaps()
        ),
        mind=MindAspect()
    )
    
    grid = Grid(20, 20)
    spatial = SpatialHash(cell_size=2)
    world = WorldState(seed=42, grid=grid, spatial_index=spatial)
    world.add_entity(actor)
    
    # Setup System and Context
    system = ProgressionSystem(cfg, rng)
    context = SystemContext(
        config=cfg,
        world=world,
        rng=rng,
        generator=MagicMock(),
        faction_reg=MagicMock(),
        emit=MagicMock()
    )
    
    # Level it up to 12
    system._check_level_ups(context)
    
    # Should have triggered evolution
    # Goblin cap is 12. Level 11 -> 12 -> Evolve
    assert actor.progression.level == 1
    assert actor.identity.tier > 1
    assert actor.kind != "goblin"
    assert "goblin" in actor.kind
    assert actor.combat.max_hp > 50

def test_evolution_equipment_refresh():
    """Verify that evolution provides new equipment. [AOA REFACTOR]"""
    cfg = SimulationConfig(world_seed=42)
    rng = DeterministicRNG(cfg.world_seed)
    
    actor = Entity(
        id=1, kind="goblin",
        identity=IdentityAspect(display_name="Goblin", tier=1),
        spatial=SpatialAspect(pos=Vector2(10, 10)),
        combat=CombatAspect(hp=50, max_hp=50),
        progression=ProgressionAspect(level=12, xp=0, xp_to_next=1000),
        mind=MindAspect(),
        inventory=InventoryAspect()
    )
    
    grid = Grid(20, 20)
    spatial = SpatialHash(cell_size=2)
    world = WorldState(seed=42, grid=grid, spatial_index=spatial)
    world.add_entity(actor)
    
    system = ProgressionSystem(cfg, rng)
    mock_generator = MagicMock()
    context = SystemContext(
        config=cfg,
        world=world,
        rng=rng,
        generator=mock_generator,
        faction_reg=MagicMock(),
        emit=MagicMock()
    )
    
    # Manually trigger evolution
    profile = RACE_PROFILES["goblin"]
    system._evolve_entity(context, actor, profile)
    
    # Check tier increase
    assert actor.identity.tier in (2, 3) 
    assert any(x in actor.kind for x in ("warrior", "scout", "shaman", "goblin"))
    
    # Verify generator was called to equip the new evolved entity
    assert mock_generator.equip_entity.called
    mock_generator.equip_entity.assert_called_with(actor)
