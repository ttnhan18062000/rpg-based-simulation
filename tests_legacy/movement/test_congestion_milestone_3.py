import pytest
from src_legacy.core.models.world_state import WorldState
from src_legacy.core.entities.entity import Entity
from src_legacy.core.models.vectors import Vector2
from src_legacy.core.models.enums import ActionType, AIState, MovementIntention, Material
from src_legacy.core.logic.movement_model import MovementModel
from src_legacy.actions.base import ActionProposal, NavigationUpdate
from src_legacy.platform.rng import DeterministicRNG
from src_legacy.config import SimulationConfig

@pytest.fixture
def world():
    from src_legacy.core.world.grid import Grid
    from src_legacy.platform.spatial_hash import SpatialHash
    grid = Grid(50, 50)
    spatial = SpatialHash(cell_size=2)
    w = WorldState(seed=42, grid=grid, spatial_index=spatial)
    return w

@pytest.fixture
def config():
    return SimulationConfig()

@pytest.fixture
def rng():
    return DeterministicRNG(0)

def test_blocked_retreat_yield(world, config, rng):
    """Verify high-priority RETREAT ally forces yield from lower-priority ally."""
    from src_legacy.ai.states.base import AIContext
    
    # Ally 1: Low HP, trying to retreat
    retreat_id = 1
    retreat_pos = Vector2(10, 10)
    retreater = Entity(id=retreat_id, kind="hero", spatial={"pos": retreat_pos})
    retreater.combat.hp = 10
    retreater.mind.navigation.intention = MovementIntention.RETREAT
    
    # Ally 2: High HP, blocking the retreat path
    blocker_id = 2
    blocker_pos = Vector2(11, 10)
    blocker = Entity(id=blocker_id, kind="hero")
    blocker.spatial.pos = blocker_pos
    blocker.combat.hp = 100
    blocker.mind.navigation.intention = MovementIntention.PURSUIT # Lower priority
    
    retreater.combat.hp = 10
    retreater.combat.max_hp_base = 100
    
    world.add_entity(retreater)
    world.add_entity(blocker)
    
    # Threat to the retreaters left (forcing move to the right)
    threat_pos = Vector2(9, 10)
    from src_legacy.core.aspects.mind import BeliefRecord, ThreatEstimate
    threat_belief = BeliefRecord(entity_id=99, pos=threat_pos)
    threat_belief.threat = ThreatEstimate(overall=0.8)
    retreater.mind.perception.entity_memory[99] = threat_belief
    
    from src_legacy.core.gameplay.faction import FactionRegistry
    faction_reg = FactionRegistry()
    
    from src_legacy.core.models.snapshot import Snapshot
    ctx = AIContext(retreater, Snapshot.from_world(world), config, rng, faction_reg)
    
    # Target is far to the right
    target = Vector2(20, 10)
    
    # MovementModel planning
    proposal = MovementModel.plan_or_step(ctx, target, MovementIntention.RETREAT, "Fleeing")
    
    # Should be SIDESTEPPING because blocker is there but a side tile is free
    nav_up = next(u for u in proposal.updates if isinstance(u, NavigationUpdate))
    assert proposal.verb == ActionType.MOVE
    assert nav_up.reason.code.name == "SIDESTEPPING"

def test_oscillation_suppression(world, config, rng):
    """Verify A-B-A-B movement is suppressed after 2 cycles."""
    from src_legacy.ai.states.base import AIContext
    
    actor = Entity(id=1, kind="hero", spatial={"pos": Vector2(10, 10)})
    # Pattern: (10,10) -> (10,11) -> (10,10) -> (10,11)
    nav = actor.mind.navigation
    nav.pos_history = [
        Vector2(10, 10), Vector2(10, 11), # Cycle 1
        Vector2(10, 10), Vector2(10, 11)  # Cycle 2
    ]
    nav.oscillation_counter = 1
    world.add_entity(actor)
    
    from src_legacy.core.gameplay.faction import FactionRegistry
    from src_legacy.core.models.snapshot import Snapshot
    ctx = AIContext(actor, Snapshot.from_world(world), config, rng, FactionRegistry())
    target = Vector2(10, 12)
    
    proposal = MovementModel.plan_or_step(ctx, target, MovementIntention.PURSUIT, "Moving")
    
    # Should force WAIT to break oscillation
    assert proposal.verb == ActionType.REST
    assert proposal.reason.metadata["detail"] == "Oscillation Suppressed"
    
    nav_up = next(u for u in proposal.updates if isinstance(u, NavigationUpdate))
    assert nav_up.oscillation_counter == 0 # Reset after suppression

def test_reroute_hysteresis(world, config, rng):
    """Verify minor reroutes are ignored to prevent flip-flopping."""
    from src_legacy.ai.states.base import AIContext
    
    actor = Entity(id=1, kind="hero", spatial={"pos": Vector2(10, 10)})
    world.add_entity(actor)
    
    # Define two paths: 
    # Current path: 5 steps
    # New path: 4 steps (Improvement 1, threshold is > 2)
    nav = actor.mind.navigation
    nav.cached_path = [Vector2(10,10), Vector2(10,11), Vector2(10,12), Vector2(10,13), Vector2(10,14)]
    nav.cached_path_target = Vector2(10, 15)
    
    # Hash of the current route (simplified)
    nav.last_route_hash = MovementModel._get_route_hash(nav.cached_path)
    
    from src_legacy.core.gameplay.faction import FactionRegistry
    from src_legacy.core.models.snapshot import Snapshot
    ctx = AIContext(actor, Snapshot.from_world(world), config, rng, FactionRegistry())
    
    # The pathfinder will likely find a 5-step path again.
    # We want to test that if a NEW path of length 4 is found, it is REJECTED.
    # This is hard to test deterministically without mocking the pathfinder.
    
    # Let's mock the pathfinder return value
    from unittest.mock import patch
    shorter_path = [Vector2(10,10), Vector2(11,10), Vector2(11,11), Vector2(11,12)] # length 4
    
    with patch('src.ai.pathfinding.Pathfinder.find_path', return_value=shorter_path):
        proposal = MovementModel.plan_or_step(ctx, Vector2(10, 15), MovementIntention.PURSUIT, "Moving")
        
        nav_up = next(u for u in proposal.updates if isinstance(u, NavigationUpdate))
        # It should STICK to the old path because improvement (5-4=1) <= 2
        assert len(nav_up.cached_path) == 5

def test_safe_sidestepping(world, config, rng):
    """Verify yielding entities do not sidestep closer to danger."""
    from src_legacy.ai.states.base import AIContext
    
    actor = Entity(id=1, kind="hero", spatial={"pos": Vector2(10, 10)})
    world.add_entity(actor)
    
    # Threat is at (10, 12)
    threat_pos = Vector2(10, 12)
    from src_legacy.core.aspects.mind import MemoryRecord, ThreatEstimate
    mem = MemoryRecord(entity_id=99, pos=threat_pos)
    mem.threat = ThreatEstimate(overall=0.8)
    actor.mind.perception.entity_memory[99] = mem
    
    # Blocked by an ally at (11, 10)
    ally = Entity(id=2, kind="hero", spatial={"pos": Vector2(11, 10)})
    world.add_entity(ally)
    
    from src_legacy.core.gameplay.faction import FactionRegistry
    from src_legacy.core.models.snapshot import Snapshot
    ctx = AIContext(actor, Snapshot.from_world(world), config, rng, FactionRegistry())
    target = Vector2(12, 10) # Want to move right
    
    # Potential sidesteps: (10, 9), (10, 11).
    # (10, 11) is closer to threat (10, 12) than current (10, 10).
    # So (10, 11) should be REJECTED.
    # (10, 9) is further or equal, so it's OK.
    
    # Let's verify _find_sidestep directly
    sidestep = MovementModel._find_sidestep(ctx, Vector2(11, 10))
    # Both (9, 10) and (10, 9) are valid safe sidesteps
    assert sidestep in [Vector2(10, 9), Vector2(9, 10)]
    assert sidestep != Vector2(10, 11)
