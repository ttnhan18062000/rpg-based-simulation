import pytest
from unittest.mock import MagicMock
from src.actions.combat import CombatAction
from src.actions.base import ActionProposal, BuildingTarget, BuildingUpdate
from src.core.models.world_state import WorldState
from src.core.gameplay.buildings import Building
from src.core.models.vectors import Vector2 as Position

@pytest.fixture
def mock_world():
    world = MagicMock(spec=WorldState)
    world.entities = {}
    world.buildings = []
    return world

@pytest.fixture
def mock_attacker():
    attacker = MagicMock()
    attacker.id = 1
    attacker.combat.alive = True
    attacker.combat.atk = 20
    attacker.spatial.pos = Position(1, 1)
    attacker.inventory.weapon = None
    return attacker

@pytest.fixture
def mock_building():
    building = MagicMock(spec=Building)
    building.building_id = "B1"
    building.pos = Position(1, 1)
    building.is_functional = True
    return building

def test_validate_building_target(mock_world, mock_attacker, mock_building):
    mock_world.entities[mock_attacker.id] = mock_attacker
    mock_world.buildings.append(mock_building)
    
    action = CombatAction(MagicMock(), MagicMock())
    proposal = ActionProposal(actor_id=mock_attacker.id, verb=4, target=BuildingTarget(building_id="B1"))
    
    # Within range
    assert action.validate(proposal, mock_world) is True
    
    # Out of range
    mock_building.pos = Position(10, 10)
    assert action.validate(proposal, mock_world) is False
    
    # Non-functional
    mock_building.pos = Position(1, 1)
    mock_building.is_functional = False
    assert action.validate(proposal, mock_world) is False

def test_apply_building_sabotage(mock_world, mock_attacker, mock_building):
    mock_world.entities[mock_attacker.id] = mock_attacker
    mock_world.buildings.append(mock_building)
    
    action = CombatAction(MagicMock(), MagicMock())
    proposal = ActionProposal(actor_id=mock_attacker.id, verb=4, target=BuildingTarget(building_id="B1"), updates=[])
    
    action.apply(proposal, mock_world)
    
    # Verify BuildingUpdate was proposed
    updates = [u for u in proposal.updates if isinstance(u, BuildingUpdate)]
    assert len(updates) == 1
    assert updates[0].building_id == "B1"
    assert updates[0].damage_amount == 10 # 50% of 20 ATK
