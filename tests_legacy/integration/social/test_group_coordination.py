import pytest
from src_legacy.core.models.world_state import WorldState
from src_legacy.core.models.vectors import Vector2
from src_legacy.core.models.enums import GoalType, Faction
from src_legacy.core.world.grid import Grid
from src_legacy.systems.spatial_hash import SpatialHash
from src_legacy.core.entities.entity_builder import EntityBuilder
from src_legacy.platform.rng import DeterministicRNG
from src_legacy.config import SimulationConfig
from src_legacy.systems.infrastructure.base import SystemContext
from src_legacy.systems.social.group_system import GroupSystem
from src_legacy.core.models.snapshot import Snapshot
from src_legacy.actions.base import MindUpdate

@pytest.fixture
def group_setup():
    grid = Grid(100, 100)
    spatial = SpatialHash(10)
    world = WorldState(seed=42, grid=grid, spatial_index=spatial)
    config = SimulationConfig()
    rng = DeterministicRNG(42)
    
    from src_legacy.core.gameplay.faction import FactionRegistry
    faction_reg = FactionRegistry.default()
    
    context = SystemContext(
        config=config,
        world=world,
        rng=rng,
        generator=None,
        faction_reg=faction_reg,
        emit=lambda *args, **kwargs: None
    )
    
    builder = EntityBuilder(rng, 1)
    return context, builder

def test_group_formation_simple(group_setup):
    """Verify that 2+ entities with same cluster_id form a group."""
    ctx, builder = group_setup
    system = GroupSystem(ctx.config, ctx.rng)
    
    # 1. Spawn 3 raiders in same cluster
    raider1 = EntityBuilder(ctx.rng, 1).kind("hero").at(Vector2(50, 50)).build()
    raider1.identity.cluster_id = "raider_band_1"
    raider1.identity.faction = Faction.GOBLIN_HORDE
    raider1.combat.hp = 100
    raider1.progression.level = 5
    
    raider2 = EntityBuilder(ctx.rng, 2).kind("hero").at(Vector2(51, 51)).build()
    raider2.identity.cluster_id = "raider_band_1"
    raider2.identity.faction = Faction.GOBLIN_HORDE
    raider2.combat.hp = 100
    raider2.progression.level = 3
    
    raider3 = EntityBuilder(ctx.rng, 3).kind("hero").at(Vector2(52, 52)).build()
    raider3.identity.cluster_id = "raider_band_1"
    raider3.identity.faction = Faction.GOBLIN_HORDE
    raider3.combat.hp = 100
    raider3.progression.level = 4
    
    ctx.world.entities[raider1.id] = raider1
    ctx.world.entities[raider2.id] = raider2
    ctx.world.entities[raider3.id] = raider3
    
    # 2. Tick system
    system.on_tick(ctx, 10)
    
    # 3. Verify group
    assert len(ctx.world.group_registry) == 1
    group = list(ctx.world.group_registry.values())[0]
    assert group.leader_id == raider1.id # Highest Level (5)
    assert len(group.member_ids) == 3
    assert group.anchor_pos == raider1.spatial.pos

def test_group_dissolution_leader_dead(group_setup):
    """Verify group dissolves if leader is dead."""
    ctx, builder = group_setup
    system = GroupSystem(ctx.config, ctx.rng)
    
    raider1 = EntityBuilder(ctx.rng, 4).kind("hero").at(Vector2(50, 50)).build()
    raider1.identity.cluster_id = "band"
    raider1.combat.hp = 100
    raider2 = EntityBuilder(ctx.rng, 5).kind("hero").at(Vector2(51, 51)).build()
    raider2.identity.cluster_id = "band"
    raider2.combat.hp = 100
    
    ctx.world.entities[raider1.id] = raider1
    ctx.world.entities[raider2.id] = raider2
    
    system.on_tick(ctx, 10)
    assert len(ctx.world.group_registry) == 1
    
    # Kill leader
    raider1.combat.hp = 0
    system.on_tick(ctx, 20)
    
    assert len(ctx.world.group_registry) == 0

def test_brain_group_behavior_bias(group_setup):
    """Verify AIBrain applies biases from group membership."""
    ctx, builder = group_setup
    from src_legacy.ai.brain import AIBrain
    brain = AIBrain(ctx.config, ctx.rng, ctx.faction_reg)
    
    raider1 = EntityBuilder(ctx.rng, 6).kind("hero").at(Vector2(50, 50)).build()
    raider1.identity.cluster_id = "band"
    raider1.combat.hp = 100
    raider2 = EntityBuilder(ctx.rng, 7).kind("hero").at(Vector2(60, 60)).build() # 20 tiles away
    raider2.identity.cluster_id = "band"
    raider2.combat.hp = 100
    
    ctx.world.entities[raider1.id] = raider1
    ctx.world.entities[raider2.id] = raider2
    
    # Form group
    system = GroupSystem(ctx.config, ctx.rng)
    system.on_tick(ctx, 10)
    assert len(ctx.world.group_registry) == 1
    group = list(ctx.world.group_registry.values())[0]
    group.shared_goal = GoalType.COMBAT
    
    # Decide for raider2 (member)
    ctx.world.tick = 30 # For appraisal throttle
    snapshot = Snapshot.from_world(ctx.world)
    
    _, proposal = brain.decide(raider2, snapshot)
    mind_up = next(u for u in proposal.updates if isinstance(u, MindUpdate) and u.motive_utility_biases is not None)
    biases = mind_up.motive_utility_biases
    
    # 1. Shared goal bias (COMBAT)
    assert biases.get(GoalType.COMBAT, 1.0) > 1.2
    # 2. Distance bias (SOCIAL) because distance to leader (raider1 at 50,50) from (70,70) is 40.
    assert biases.get(GoalType.SOCIAL, 1.0) > 1.5
