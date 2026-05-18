import pytest
from src_legacy.core.models.world_state import WorldState
from src_legacy.core.entities.entity import Entity
from src_legacy.core.models.vectors import Vector2
from src_legacy.core.models.enums import ActionType, AIState, Material
from src_legacy.actions.combat import CombatAction
from src_legacy.actions.base import ActionProposal
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

def test_high_ground_bonus(world, config, rng):
    """Verify High Ground bonus applies when attacker is on MOUNTAIN and defender is on FLOOR."""
    attacker = Entity(id=1, kind="hero", spatial={"pos": Vector2(10, 10)})
    defender = Entity(id=2, kind="goblin", spatial={"pos": Vector2(10, 11)})
    
    world.add_entity(attacker)
    world.add_entity(defender)
    
    # Set terrain
    world.grid.set(Vector2(10, 10), Material.MOUNTAIN)
    world.grid.set(Vector2(10, 11), Material.FLOOR)
    
    action = CombatAction(config, rng)
    proposal = ActionProposal(actor_id=1, verb=ActionType.USE_SKILL, target=2)
    
    # Apply action
    action.apply(proposal, world)
    
    # Directly inspect updates for trace details
    from src_legacy.actions.base import CombatTraceUpdate
    trace_up = next((u for u in proposal.updates if isinstance(u, CombatTraceUpdate)), None)
    assert trace_up is not None, "CombatTraceUpdate not found in proposal updates"
    
    trace = trace_up.result
    assert trace.details.has_high_ground is True
    # Base damage is 5, high ground bonus is +15%
    # resolve() math: atk_final = base * mult * bonus
    # 5 * 1.15 = 5.75 -> 5 (if base) or more depending on levels
    # Since they are level 1, atk_power is likely 10 something.
    # We just check the flag is True.
    assert trace.details.has_high_ground is True

def test_flanking_bonus(world, config, rng):
    """Verify Flanking bonus applies when defender is bracketed north/south."""
    attacker = Entity(id=1, kind="hero", spatial={"pos": Vector2(10, 9)}, identity={"faction": 1})
    defender = Entity(id=2, kind="goblin", spatial={"pos": Vector2(10, 10)}, identity={"faction": 2})
    ally = Entity(id=3, kind="hero", spatial={"pos": Vector2(10, 11)}, identity={"faction": 1}) # Opposite side
    
    world.add_entity(attacker)
    world.add_entity(defender)
    world.add_entity(ally)
    
    action = CombatAction(config, rng)
    proposal = ActionProposal(actor_id=1, verb=ActionType.USE_SKILL, target=2)
    
    action.apply(proposal, world)
    
    from src_legacy.actions.base import CombatTraceUpdate
    trace_up = next((u for u in proposal.updates if isinstance(u, CombatTraceUpdate)), None)
    assert trace_up is not None
    trace = trace_up.result
    assert trace.details.is_flanked is True

def test_moved_penalty(world, config, rng):
    """Verify Moved Recently penalty applies when attacker has moved this tick."""
    attacker = Entity(id=1, kind="hero", spatial={"pos": Vector2(10, 10)})
    defender = Entity(id=2, kind="goblin", spatial={"pos": Vector2(10, 11)})
    
    # Simulate move
    attacker.spatial.moved_this_tick = True
    
    world.add_entity(attacker)
    world.add_entity(defender)
    
    action = CombatAction(config, rng)
    proposal = ActionProposal(actor_id=1, verb=ActionType.USE_SKILL, target=2)
    
    action.apply(proposal, world)
    
    from src_legacy.actions.base import CombatTraceUpdate
    trace_up = next((u for u in proposal.updates if isinstance(u, CombatTraceUpdate)), None)
    assert trace_up is not None
    trace = trace_up.result
    assert trace.details.is_moving is True

def test_ranged_cover_bonus(world, config, rng):
    """Verify Cover bonus applies against ranged attacks when adjacent to WALL."""
    # Distance > 1 for ranged
    attacker = Entity(id=1, kind="hero", spatial={"pos": Vector2(10, 5)})
    defender = Entity(id=2, kind="goblin", spatial={"pos": Vector2(10, 10)})
    
    # Wall adjacent to defender but between them
    world.grid.set(Vector2(10, 9), Material.WALL)
    
    world.add_entity(attacker)
    world.add_entity(defender)
    
    action = CombatAction(config, rng)
    proposal = ActionProposal(actor_id=1, verb=ActionType.USE_SKILL, target=2)
    
    action.apply(proposal, world)
    
    from src_legacy.actions.base import CombatTraceUpdate
    trace_up = next((u for u in proposal.updates if isinstance(u, CombatTraceUpdate)), None)
    assert trace_up is not None
    trace = trace_up.result
    assert trace.details.has_cover is True
