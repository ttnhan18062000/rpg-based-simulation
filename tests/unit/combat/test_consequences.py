import pytest
from src.core.entities.entity import Entity
from src.core.models.world_state import WorldState
from src.core.models.vectors import Vector2
from src.core.models.enums import Domain, ConsequenceKind, ActionType
from src.core.models.consequence import Consequence
from src.actions.combat import CombatAction, CombatAftermathService
from src.core.world.grid import Grid
from src.platform.spatial_hash import SpatialHash
from src.platform.rng import DeterministicRNG
from src.config import SimulationConfig
from src.actions.base import ActionProposal

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

def test_wound_infliction_massive_hit(world, config, rng):
    """Verify that damage > 25% max HP guarantees a wound."""
    attacker = Entity(id=1, kind="human")
    attacker.progression.stamina = 50
    defender = Entity(id=2, kind="human")
    defender.combat.max_hp = 100
    defender.combat.hp = 100
    world.entities[1] = attacker
    world.entities[2] = defender
    
    proposal = ActionProposal(actor_id=1, verb=ActionType.ATTACK, target=2)
    
    # 30 damage = 30% of max HP
    CombatAftermathService.process(
        attacker, defender, world, 
        damage=30, is_crit=False, is_evasion=False, 
        config=config, proposal=proposal, rng=rng
    )
    
    # Check for ProgressionUpdate with consequences_add
    prog_ups = [u for u in proposal.updates if hasattr(u, "consequences_add") and u.consequences_add]
    assert len(prog_ups) > 0
    wound = prog_ups[0].consequences_add[0]
    assert wound.kind == ConsequenceKind.WOUND
    assert wound.remaining_ticks > 0

def test_wound_stat_impact(world):
    """Verify that wounds correctly reduce properties in CombatAspect."""
    entity = Entity(id=1, kind="human")
    entity.combat.spd_base = 10
    entity.combat.atk_base = 10
    
    # Add a Leg Wound (-20% Speed)
    wound = Consequence(id="w1", kind=ConsequenceKind.WOUND, tag="Leg Wound", spd_mult=0.8, remaining_ticks=100)
    entity.combat.add_consequence(wound)
    
    assert entity.combat.spd == 8  # 10 * 0.8
    assert entity.combat.atk == 10 # Unaffected
    
    # Add an Arm Wound (-20% Atk)
    wound2 = Consequence(id="w2", kind=ConsequenceKind.WOUND, tag="Arm Wound", atk_mult=0.8, remaining_ticks=100)
    entity.combat.add_consequence(wound2)
    
    assert entity.combat.atk == 8
    
def test_scar_permanence(world):
    """Verify that scars are permanent and identifiable."""
    entity = Entity(id=1, kind="human")
    scar = Consequence(id="s1", kind=ConsequenceKind.SCAR, tag="Combat Scar", remaining_ticks=-1)
    entity.combat.add_consequence(scar)
    
    assert scar.is_permanent()
    assert len(entity.combat.scars) == 1
    
    # Pruning shouldn't remove it
    removed = entity.combat.prune_consequences()
    assert removed == 0
    assert len(entity.combat.scars) == 1
