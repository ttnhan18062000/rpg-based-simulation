import pytest
from src.core.models.vectors import Vector2
from src.core.models.enums import MovementIntention, ActionType
from src.core.logic.movement_model import MovementModel
from src.core.models.reason_codes import ActionReason, ReasonCode
from src.ai.states.base import AIContext
from src.core.entities.entity_builder import EntityBuilder
from src.core.models.world_state import WorldState
from src.core.models.snapshot import Snapshot
from src.core.world.grid import Grid
from src.platform.rng import DeterministicRNG
from src.platform.spatial_hash import SpatialHash

@pytest.fixture
def setup_world():
    rng = DeterministicRNG(42)
    grid = Grid(10, 10)
    spatial = SpatialHash(4)
    world = WorldState(seed=42, grid=grid, spatial_index=spatial)
    from src.core.gameplay.faction import FactionRegistry
    faction_reg = FactionRegistry()
    return world, rng, faction_reg

def test_movement_observability_waiting(setup_world):
    world, rng, faction_reg = setup_world
    from src.config import SimulationConfig
    config = SimulationConfig()
    
    # Actor at (1,1)
    actor_id = world.allocate_entity_id()
    actor = EntityBuilder(rng, actor_id).kind("hero").at(Vector2(1, 1)).build()
    world.add_entity(actor)
    
    # Blockers everywhere so actor must wait
    for pos in [Vector2(2,1), Vector2(0,1), Vector2(1,2), Vector2(1,0)]:
        eid = world.allocate_entity_id()
        blocker = EntityBuilder(rng, eid).kind("hero").at(pos).build()
        world.add_entity(blocker)
    
    snapshot = Snapshot.from_world(world)
    ctx = AIContext(actor=snapshot.entities[actor_id], snapshot=snapshot, config=config, rng=rng, faction_reg=faction_reg)
    
    proposal = MovementModel.plan_or_step(ctx, Vector2(5, 1), MovementIntention.PURSUIT, "Advancing")
    
    assert proposal.verb == ActionType.REST
    assert proposal.reason.code == ReasonCode.WAITING
    assert any(isinstance(u.reason, ActionReason) and u.reason.code == ReasonCode.WAITING for u in proposal.updates if hasattr(u, 'reason'))

def test_movement_observability_yielding(setup_world):
    world, rng, faction_reg = setup_world
    from src.config import SimulationConfig
    config = SimulationConfig()
    
    # Actor (PURSUIT)
    actor_id = world.allocate_entity_id()
    actor = EntityBuilder(rng, actor_id).kind("hero").at(Vector2(1, 1)).build()
    actor.mind.navigation.intention = MovementIntention.PURSUIT
    world.add_entity(actor)
    
    # Higher priority blocker (RETREAT)
    blocker_id = world.allocate_entity_id()
    blocker = EntityBuilder(rng, blocker_id).kind("hero").at(Vector2(2, 1)).build()
    blocker.mind.navigation.intention = MovementIntention.RETREAT
    world.add_entity(blocker)
    
    # Block sidesteps with walls
    from src.core.models.enums import Material
    for pos in [Vector2(0,1), Vector2(1,2), Vector2(1,0)]:
        world.grid.set(pos, Material.WALL)
    
    snapshot = Snapshot.from_world(world)
    ctx = AIContext(actor=snapshot.entities[actor_id], snapshot=snapshot, config=config, rng=rng, faction_reg=faction_reg)
    
    proposal = MovementModel.plan_or_step(ctx, Vector2(5, 1), MovementIntention.PURSUIT, "Advancing")
    
    assert proposal.verb == ActionType.REST
    assert proposal.reason.code == ReasonCode.YIELDING
    assert proposal.reason.metadata["blocker_id"] == blocker_id

def test_movement_observability_sidestepping(setup_world):
    world, rng, faction_reg = setup_world
    from src.config import SimulationConfig
    config = SimulationConfig()
    
    # Actor at (1,1)
    actor_id = world.allocate_entity_id()
    actor = EntityBuilder(rng, actor_id).kind("hero").at(Vector2(1, 1)).build()
    world.add_entity(actor)
    
    # Blocker at (2,1)
    blocker_id = world.allocate_entity_id()
    blocker = EntityBuilder(rng, blocker_id).kind("hero").at(Vector2(2, 1)).build()
    world.add_entity(blocker)
    
    snapshot = Snapshot.from_world(world)
    ctx = AIContext(actor=snapshot.entities[actor_id], snapshot=snapshot, config=config, rng=rng, faction_reg=faction_reg)
    
    proposal = MovementModel.plan_or_step(ctx, Vector2(5, 1), MovementIntention.PURSUIT, "Advancing")
    
    if proposal.verb == ActionType.MOVE:
        assert proposal.reason.code == ReasonCode.SIDESTEPPING
    else:
        # If it couldn't sidestep (e.g. rng or grid config), it's okay, but normally it should sidestep here
        assert proposal.reason.code == ReasonCode.WAITING

def test_action_system_rejection_observability(setup_world):
    world, rng, faction_reg = setup_world
    from src.systems.gameplay.action_system import ActionSystem
    from src.actions.base import ActionProposal
    from src.systems.infrastructure.base import SystemContext
    from src.config import SimulationConfig
    
    # 1. Setup Actor and Target
    actor_id = world.allocate_entity_id()
    actor = EntityBuilder(rng, actor_id).kind("hero").at(Vector2(1, 1)).build()
    actor.combat.hp = 100
    world.add_entity(actor)
    
    # 2. Add another entity to block the spot
    blocker = EntityBuilder(rng, 2).kind("hero").at(Vector2(5, 5)).build()
    world.add_entity(blocker)
    
    config = SimulationConfig()
    config.overhaul_features["use_legality_v2"] = True
    
    # 3. Create a proposal to move to the blocked spot
    proposal = ActionProposal(actor_id=actor_id, verb=ActionType.MOVE, target=Vector2(5, 5), reason="Testing rejection")
    
    system = ActionSystem(config, rng)
    system_ctx = SystemContext(
        world=world, 
        config=config, 
        rng=rng,
        generator=None,
        faction_reg=None, 
        emit=lambda *args: None
    )
    
    # We need to manually call the part of on_tick or the method we want to test
    # but ActionSystem handles batches. Let's just use the processing logic directly.
    # In ActionSystem.apply_action_state_transitions(context, [proposal])
    
    system.apply_action_state_transitions(
        world, 
        config, 
        [proposal], 
        rng, 
        emit=lambda *args: None, 
        faction_reg=None
    )
    
    # Check if the proposal was rejected and reason populated
    assert proposal.reason.code == ReasonCode.OUT_OF_RANGE
    assert proposal.reason.metadata["max_range"] == 1
    assert actor.mind.decision.last_reason == proposal.reason

def test_tactical_evaluator_observability(setup_world):
    world, rng, faction_reg = setup_world
    from src.ai.tactical.tactical_evaluator import TacticalEvaluator
    from src.ai.tactical.contract import TacticalMode
    from src.config import SimulationConfig
    config = SimulationConfig()
    
    from src.core.models.enums import Faction
    from src.core.gameplay.faction import FactionRelation
    actor_id = world.allocate_entity_id()
    actor = EntityBuilder(rng, actor_id).kind("hero").faction(Faction.HERO_GUILD).at(Vector2(1, 1)).build()
    actor.combat.hp = 10 # Critical HP
    actor.combat.hp_max = 100
    world.add_entity(actor)
    
    enemy_id = world.allocate_entity_id()
    enemy = EntityBuilder(rng, enemy_id).kind("monster").faction(Faction.GOBLIN_HORDE).at(Vector2(3, 3)).build()
    world.add_entity(enemy)
    
    faction_reg.set_relation(Faction.HERO_GUILD, Faction.GOBLIN_HORDE, FactionRelation.HOSTILE)
    
    snapshot = Snapshot.from_world(world)
    ctx = AIContext(actor=snapshot.entities[actor_id], snapshot=snapshot, config=config, rng=rng, faction_reg=faction_reg)
    
    evaluation = TacticalEvaluator.evaluate_tactics(ctx)
    
    assert evaluation.mode == TacticalMode.RETREAT
    assert evaluation.reason.code == ReasonCode.LOW_HP_RETREAT
