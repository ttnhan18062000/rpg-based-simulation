from unittest.mock import MagicMock
import pytest
from src_legacy.actions.combat import CombatAction
from src_legacy.actions.base import ActionProposal, BuildingTarget, BuildingUpdate
from src_legacy.core.entities.entity import Entity
from src_legacy.core.models.vectors import Vector2
from src_legacy.core.gameplay.buildings import Building
from src_legacy.platform.rng import DeterministicRNG

@pytest.fixture
def combat_setup():
    config = MagicMock()
    config.damage_variance = 0.1
    rng = DeterministicRNG(0)
    
    # Attacker
    attacker = MagicMock(spec=Entity)
    attacker.id = 1
    attacker.combat = MagicMock()
    attacker.combat.alive = True
    attacker.combat.atk = 20
    attacker.spatial = MagicMock()
    attacker.spatial.pos = Vector2(11, 10)
    attacker.inventory = MagicMock()
    attacker.inventory.weapon = None
    
    # Building
    building = Building(
        building_id="store",
        name="General Store",
        pos=Vector2(11, 11),
        building_type="store",
        durability=100.0,
        max_durability=100.0
    )
    
    world = MagicMock()
    world.entities = {1: attacker}
    world.buildings = [building]
    world.tick = 1
    
    return CombatAction(config, rng), attacker, building, world

def test_building_sabotage_validation(combat_setup):
    action, attacker, building, world = combat_setup
    
    # Valid sabotage (Range 1-2)
    proposal = ActionProposal(actor_id=1, verb=2, target=BuildingTarget(building_id="store"))
    assert action.validate(proposal, world) is True
    
    # Invalid sabotage (Out of Range)
    attacker.spatial.pos = Vector2(20, 20)
    assert action.validate(proposal, world) is False

def test_building_sabotage_application(combat_setup):
    action, attacker, building, world = combat_setup
    proposal = ActionProposal(actor_id=1, verb=2, target=BuildingTarget(building_id="store"))
    
    # AOA Stabilization: Apply should NOT mutate durability directly
    action.apply(proposal, world)
    
    # Verify durability is still 100 (Unchanged in Apply Phase)
    assert building.durability == 100.0
    
    # Verify BuildingUpdate was emitted
    updates = [u for u in proposal.updates if isinstance(u, BuildingUpdate)]
    assert len(updates) == 1
    assert updates[0].building_id == "store"
    assert updates[0].damage_amount == 10 # 50% of atk 20
