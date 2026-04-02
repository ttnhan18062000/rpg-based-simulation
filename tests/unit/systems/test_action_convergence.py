import pytest
from unittest.mock import MagicMock
from src.core.models.world_state import WorldState
from src.config import SimulationConfig
from src.core.entities.entity import Entity
from src.core.models.enums import ActionType, AIState
from src.actions.base import ActionProposal, ProgressionUpdate, InteractionUpdate
from src.systems.gameplay.action_system import ActionSystem
from src.core.models import Vector2

@pytest.fixture
def world():
    mock_grid = MagicMock()
    mock_spatial = MagicMock()
    # Mock query_cell to return empty for is_occupied check if needed
    mock_spatial.query_cell.return_value = []
    w = WorldState(seed=42, grid=mock_grid, spatial_index=mock_spatial)
    return w

@pytest.fixture
def entity(world):
    from src.core.aspects.inventory import InventoryAspect
    from src.core.aspects.progression import ProgressionAspect
    from src.core.aspects.spatial import SpatialAspect
    from src.core.aspects.combat import CombatAspect
    from src.core.aspects.identity import IdentityAspect
    from src.core.gameplay.attributes import Attributes, AttributeCaps
    from src.core.gameplay.faction import Faction
    
    e = Entity(
        id=1, kind="hero", 
        spatial=SpatialAspect(pos=Vector2(5, 5)),
        inventory=InventoryAspect(),
        combat=CombatAspect(),
        identity=IdentityAspect(faction=Faction.HERO_GUILD),
        progression=ProgressionAspect(
            attributes=Attributes(),
            attribute_caps=AttributeCaps()
        )
    )
    world.entities[1] = e
    return e

def test_loot_no_duplication(world, entity):
    """Verify that items picked up by the system are not duplicated by AI updates."""
    # 1. Setup world with a ground item
    pos = Vector2(5, 5)
    world.drop_items(pos, ["iron_ore"])
    
    # 2. Mock AI proposing LOOT with its own (incorrectly pre-calculated) updates
    proposal = ActionProposal(
        actor_id=entity.id,
        verb=ActionType.LOOT,
        target=pos,
        updates=[] 
    )
    
    # 3. Process action through ActionSystem
    config = SimulationConfig()
    ActionSystem.apply_action_state_transitions(world, config, [proposal])
    
    # 4. Verification
    assert "iron_ore" not in world.ground_items.get((5, 5), [])
    assert len(entity.inventory.items) == 1
    assert entity.inventory.items[0] == "iron_ore"

def test_corpse_loot_convergence(world, entity):
    """Verify that corpse recovery is authoritatively handled by ActionSystem."""
    from src.core.models.world_objects import CorpseNode
    pos = Vector2(5, 5)
    node = CorpseNode(node_id=101, entity_id=entity.id, pos=pos, items=["sword_of_justice"], gold=100)
    world.corpse_nodes[101] = node
    
    # AI proposes LOOT without pre-calculated updates (Native Convergence)
    proposal = ActionProposal(
        actor_id=entity.id,
        verb=ActionType.LOOT,
        target=pos,
        updates=[] 
    )
    
    config = SimulationConfig()
    ActionSystem.apply_action_state_transitions(world, config, [proposal])
    
    # Verification (Authoritative Handling)
    assert 101 not in world.corpse_nodes
    assert entity.progression.gold == 100
    assert "sword_of_justice" in entity.inventory.items
