import pytest
from src_legacy.core.models.vectors import Vector2
from src_legacy.core.models.enums import MovementIntention, ActionType
from src_legacy.core.logic.movement_model import MovementModel
from src_legacy.ai.states.base import AIContext
from src_legacy.core.entities.entity_builder import EntityBuilder
from src_legacy.core.models.world_state import WorldState
from src_legacy.core.models.snapshot import Snapshot
from src_legacy.core.world.grid import Grid
from src_legacy.platform.rng import DeterministicRNG
from src_legacy.platform.spatial_hash import SpatialHash
from src_legacy.config import SimulationConfig

@pytest.fixture
def setup_world():
    rng = DeterministicRNG(42)
    grid = Grid(10, 10)
    spatial = SpatialHash(4)
    world = WorldState(seed=42, grid=grid, spatial_index=spatial)
    from src_legacy.core.gameplay.faction import FactionRegistry
    faction_reg = FactionRegistry()
    return world, rng, faction_reg

def test_rollout_movement_v2_vs_v1(setup_world):
    world, rng, faction_reg = setup_world
    
    # Actor at (1,1)
    actor_id = world.allocate_entity_id()
    actor = EntityBuilder(rng, actor_id).kind("hero").at(Vector2(1, 1)).build()
    world.add_entity(actor)
    
    # Blocker at (2,1)
    blocker_id = world.allocate_entity_id()
    blocker = EntityBuilder(rng, blocker_id).kind("hero").at(Vector2(2, 1)).build()
    world.add_entity(blocker)
    
    # Block sidesteps
    from src_legacy.core.models.enums import Material
    for pos in [Vector2(0,1), Vector2(1,2), Vector2(1,0)]:
        world.grid.set(pos, Material.WALL)
    
    snapshot = Snapshot.from_world(world)
    config = SimulationConfig()
    
    # CASE 1: v2 Enabled (Expected: Yielding/Waiting because it's blocked and can't sidestep)
    config.overhaul_features["use_movement_model_v2"] = True
    ctx_v2 = AIContext(actor=snapshot.entities[actor_id], snapshot=snapshot, config=config, rng=rng, faction_reg=faction_reg)
    prop_v2 = MovementModel.plan_or_step(ctx_v2, Vector2(5, 1), MovementIntention.PURSUIT, "Advancing")
    assert prop_v2.verb == ActionType.REST
    
    # CASE 2: v2 Disabled (Expected: Simple Tile-Step which might just attempt the move or fail differently)
    # In MovementModel.py:68, if v2 is false, it just takes route[0] which is (2,1).
    # Then it checks _get_blocker((2,1)). If blocked, it stays at (1,1) and sets congestion_res = "Legacy: Tile Blocked"
    config.overhaul_features["use_movement_model_v2"] = False
    ctx_v1 = AIContext(actor=snapshot.entities[actor_id], snapshot=snapshot, config=config, rng=rng, faction_reg=faction_reg)
    prop_v1 = MovementModel.plan_or_step(ctx_v1, Vector2(5, 1), MovementIntention.PURSUIT, "Advancing")
    assert "Legacy Fallback" in str(prop_v1.reason)
    assert "Tile Blocked" in str(prop_v1.reason)

def test_rollout_tactical_v2_vs_v1(setup_world):
    world, rng, faction_reg = setup_world
    from src_legacy.ai.tactical.tactical_evaluator import TacticalEvaluator
    from src_legacy.ai.tactical.contract import TacticalMode
    from src_legacy.core.gameplay.faction import Faction, FactionRelation
    
    actor_id = world.allocate_entity_id()
    actor = EntityBuilder(rng, actor_id).kind("hero").faction(Faction.HERO_GUILD).at(Vector2(1, 1)).build()
    actor.combat.hp = 10 
    actor.combat.hp_max = 100
    world.add_entity(actor)
    
    enemy_id = world.allocate_entity_id()
    enemy = EntityBuilder(rng, enemy_id).kind("monster").faction(Faction.GOBLIN_HORDE).at(Vector2(3, 3)).build()
    world.add_entity(enemy)
    
    faction_reg.set_relation(Faction.HERO_GUILD, Faction.GOBLIN_HORDE, FactionRelation.HOSTILE)
    
    snapshot = Snapshot.from_world(world)
    config = SimulationConfig()
    
    # CASE 1: v2 Enabled (Expected: RETREAT because of low HP)
    config.overhaul_features["use_tactical_evaluator_v2"] = True
    ctx_v2 = AIContext(actor=snapshot.entities[actor_id], snapshot=snapshot, config=config, rng=rng, faction_reg=faction_reg)
    eval_v2 = TacticalEvaluator.evaluate_tactics(ctx_v2)
    assert eval_v2.mode == TacticalMode.RETREAT
    
    # CASE 2: v2 Disabled (Expected: Legacy Fallback: Always Close)
    config.overhaul_features["use_tactical_evaluator_v2"] = False
    ctx_v1 = AIContext(actor=snapshot.entities[actor_id], snapshot=snapshot, config=config, rng=rng, faction_reg=faction_reg)
    eval_v1 = TacticalEvaluator.evaluate_tactics(ctx_v1)
    assert eval_v1.mode == TacticalMode.CLOSE
    assert "Legacy Fallback" in str(eval_v1.reason)

def test_rollout_legality_v2_vs_v1(setup_world):
    world, rng, faction_reg = setup_world
    from src_legacy.systems.gameplay.action_system import ActionSystem
    from src_legacy.actions.base import ActionProposal
    from src_legacy.systems.infrastructure.base import SystemContext
    
    actor_id = world.allocate_entity_id()
    actor = EntityBuilder(rng, actor_id).kind("hero").at(Vector2(1, 1)).build()
    world.add_entity(actor)
    
    config = SimulationConfig()
    system = ActionSystem(config, rng)
    system_ctx = SystemContext(
        world=world, 
        config=config, 
        rng=rng,
        generator=None,
        faction_reg=None, 
        emit=lambda *args: None
    )
    
    # Target too far (9,9) - max distance is usually vision or small weapon range
    # LEGACY legality (v1) often didn't check distance or was very permissive.
    
    proposal = ActionProposal(actor_id=actor_id, verb=ActionType.MOVE, target=Vector2(9, 9), reason="Teleport")
    
    # CASE 1: v2 Enabled (Expected: Distance Check Failure)
    config.overhaul_features["use_legality_v2"] = True
    # Note: Movement dist check is usually 1. 2D distance between (1,1) and (9,9) is 8+8=16 (Manhattan)
    system.apply_action_state_transitions(
        world, config, [proposal], rng, emit=lambda *args: None, faction_reg=faction_reg
    )
    # Rejections are now often objects
    assert "Target out of range" in str(proposal.reason)
    
    # CASE 2: v2 Disabled (Expected: Success or different rejection)
    # If v2 is False, it skips the overhaul checks.
    # We might need to reset proposal state
    proposal_v1 = ActionProposal(actor_id=actor_id, verb=ActionType.MOVE, target=Vector2(9, 9), reason="Teleport")
    config.overhaul_features["use_legality_v2"] = False
    system.apply_action_state_transitions(
        world, config, [proposal_v1], rng, emit=lambda *args: None, faction_reg=faction_reg
    )
    assert "Target out of range" not in str(proposal_v1.reason)
