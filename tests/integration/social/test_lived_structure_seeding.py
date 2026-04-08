import pytest
from src.core.models.world_state import WorldState
from src.systems.world.generator import EntityGenerator
from src.config import SimulationConfig
from src.platform.rng import DeterministicRNG
from src.core.models.vectors import Vector2
from src.core.models.enums import LifeRole, EnemyTier, Faction
from src.core.world.grid import Grid

@pytest.fixture
def mock_world():
    grid = Grid(100, 100)
    from src.systems.spatial_hash import SpatialHash
    spatial = SpatialHash(10)

    return WorldState(seed=42, grid=grid, spatial_index=spatial)

@pytest.fixture
def generator():
    config = SimulationConfig()
    rng = DeterministicRNG(42)
    return EntityGenerator(config, rng)

def test_spawn_hero_lived_structure(generator, mock_world):
    """Verify that a spawned Hero has appropriate world role and routines."""
    entity = generator.spawn_race(mock_world, "hero", tier=EnemyTier.BASIC)
    
    assert entity.identity.world_role == LifeRole.HERO
    assert len(entity.mind.routine_profiles) > 0
    # Should have a sleep routine
    assert any(r.routine_type == "sleeping" for r in entity.mind.routine_profiles)
    # Should have a hero-specific routine
    assert any(r.routine_type == "exploring" for r in entity.mind.routine_profiles)
    # Should have a home attachment
    assert len(entity.mind.place_attachments) > 0
    assert any(a.kind.name == "HOME" or a.kind == 0 for a in entity.mind.place_attachments)

def test_spawn_elite_mob_as_guard(generator, mock_world):
    """Verify that an Elite mob is assigned the GUARD role and routines."""
    entity = generator.spawn_race(mock_world, "goblin", tier=EnemyTier.ELITE)
    
    assert entity.identity.world_role == LifeRole.GUARD
    # Should have guard-specific routines
    assert any(r.routine_type == "patrolling" for r in entity.mind.routine_profiles)
    # Should have a 'post' attachment
    assert any("post" in a.tags for a in entity.mind.place_attachments)

def test_clique_assignment_proximity(generator, mock_world):
    """Verify that entities spawned near each other share a cluster_id."""
    near_pos = Vector2(10, 10)
    e1 = generator.spawn_race(mock_world, "goblin", near_pos=near_pos)
    e2 = generator.spawn_race(mock_world, "goblin", near_pos=near_pos)
    
    assert e1.identity.cluster_id is not None
    assert e1.identity.cluster_id == e2.identity.cluster_id
    assert "clique_" in e1.identity.cluster_id

def test_routine_priority_archetype_bias(generator, mock_world):
    """Verify that archetypes like COWARDLY_SURVIVOR affect routine priorities."""
    from src.core.models.enums import Archetype
    
    # We need to force a cowardly survivor
    # EntityGenerator picks randomly, but we can use EntityBuilder directly since 
    # the integration is in EntityBuilder.build()
    from src.core.entities.entity_builder import EntityBuilder
    
    builder = EntityBuilder(DeterministicRNG(42), 1)
    coward = (
        builder
        .kind("goblin")
        .with_archetype(Archetype.COWARDLY_SURVIVOR)
        .build()
    )
    
    builder2 = EntityBuilder(DeterministicRNG(42), 2)
    balanced = (
        builder2
        .kind("goblin")
        .with_archetype(Archetype.BALANCED)
        .build()
    )
    
    coward_sleep = next(r for r in coward.mind.routine_profiles if r.routine_type == "sleeping")
    balanced_sleep = next(r for r in balanced.mind.routine_profiles if r.routine_type == "sleeping")
    
    assert coward_sleep.priority > balanced_sleep.priority
