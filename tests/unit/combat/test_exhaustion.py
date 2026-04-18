import pytest
from src.core.entities.entity import Entity
from src.core.models.world_state import WorldState
from src.core.models.enums import ActionType
from src.actions.combat import CombatAction
from src.systems.gameplay.action_system import ActionSystem
from src.actions.base import ActionProposal
from src.core.world.grid import Grid
from src.platform.spatial_hash import SpatialHash
from src.platform.rng import DeterministicRNG
from src.config import SimulationConfig

@pytest.fixture
def world():
    grid = Grid(10, 10)
    spatial = SpatialHash(cell_size=2)
    w = WorldState(seed=42, grid=grid, spatial_index=spatial)
    return w

@pytest.fixture
def config():
    return SimulationConfig()

@pytest.fixture
def rng():
    return DeterministicRNG(seed=42)

def test_stamina_drain_on_attack(world, config, rng):
    """Verify that a basic attack drains stamina from the actor."""
    attacker = Entity(id=1, kind="human")
    attacker.progression.stamina = 50
    defender = Entity(id=2, kind="human")
    world.entities[1] = attacker
    world.entities[2] = defender
    
    action = CombatAction(config, rng)
    proposal = ActionProposal(actor_id=1, verb=ActionType.ATTACK, target=2)
    
    # Validation
    assert action.validate(proposal, world)
    
    # Application
    action.apply(proposal, world)
    
    # Check for ProgressionUpdate with stamina_delta
    stamina_ups = [u for u in proposal.updates if hasattr(u, "stamina_delta") and u.stamina_delta < 0]
    assert len(stamina_ups) > 0
    assert stamina_ups[0].stamina_delta == -8

def test_exhaustion_penalty_application(world, config, rng):
    """Verify that ActionSystem applies fatigue effect when stamina is low."""
    entity = Entity(id=1, kind="human")
    entity.progression.max_stamina = 100
    entity.progression.stamina = 10 # 10% stamina < 15% threshold
    world.entities[1] = entity
    
    # Process a simple move proposal
    proposal = ActionProposal(actor_id=1, verb=ActionType.MOVE, target=(5,5))
    
    ActionSystem.apply_action_state_transitions(
        world, config, [proposal], {1}, rng
    )
    
    # Check if fatigue effect was added
    has_fatigue = any(e.source == "exhaustion" for e in entity.combat.effects)
    assert has_fatigue
    
    # Verify stat penalty
    # 0.5 spd mult, 0.7 atk mult
    # These are applied in CombatAspect.spd and CombatAspect.atk
    assert entity.combat.spd == 5 # 10 base * 0.5
    assert entity.combat.atk == 3 # 5 base * 0.7 = 3.5 -> 3
