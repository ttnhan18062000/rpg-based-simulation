import pytest
from src.core.models.world_state import WorldState
from src.core.entities.entity import Entity
from src.core.models.enums import Archetype, Faction, ActionType
from src.actions.base import ActionProposal, SocialUpdate, PerceptionUpdate
from src.systems.gameplay.action_system import ActionSystem
from src.core.world.grid import Grid
from src.platform.spatial_hash import SpatialHash

@pytest.fixture
def world():
    return WorldState(seed=42, grid=Grid(10, 10), spatial_index=SpatialHash(cell_size=10))

@pytest.fixture
def hero(world):
    e = Entity(id=world.allocate_entity_id(), kind="hero")
    e.identity.faction = Faction.HERO_GUILD
    world.add_entity(e)
    return e

@pytest.fixture
def rival(world):
    e = Entity(id=world.allocate_entity_id(), kind="mob")
    e.identity.faction = Faction.GOBLIN_HORDE
    world.add_entity(e)
    return e

def test_nemesis_milestone_creation(world, hero, rival):
    # 1. Start with neutral rivalry
    bond = world.social_registry.get_bond(hero.id, rival.id)
    assert bond.rivalry == 0.0
    
    # 2. Trigger an update that pushes rivalry to Nemesis (>0.8)
    up = SocialUpdate(source_id=hero.id, target_id=rival.id, rivalry_delta=0.85)
    proposal = ActionProposal(actor_id=hero.id, verb=ActionType.REST, updates=[up])
    
    # 3. Apply updates
    ActionSystem.apply_action_state_transitions(world, None, [proposal], None)
    
    # 4. Verify SocialRegistry
    assert world.social_registry.get_bond(hero.id, rival.id).rivalry == 0.85
    
    # 5. Verify Narrative Milestone in Hero's memory
    # The narrative should have been emitted from the SocialUpdate in ActionSystem
    log = hero.mind.narrative.memory_log
    social_entries = [e for e in log if e.type == "social"]
    assert len(social_entries) == 1
    
    entry = social_entries[0]
    assert "nemesis" in entry.details.change_type
    assert entry.details.bond_type == "rivalry"
    assert entry.details.target_id == rival.id

def test_memory_salience_retention(world, hero, rival):
    # 1. Create a "major" memory (Nemesis)
    up_major = SocialUpdate(source_id=hero.id, target_id=rival.id, rivalry_delta=0.9)
    prop_major = ActionProposal(actor_id=hero.id, verb=ActionType.REST, updates=[up_major])
    ActionSystem.apply_action_state_transitions(world, None, [prop_major], None)
    
    # 2. Fill memory with "minor" memories (impact 0.1)
    # We exceed 50 to trigger pruning
    for i in range(100):
        minor_up = PerceptionUpdate(memory_log_add=[{
            "tick": world.tick,
            "type": "trauma",
            "impact": 0.1,
            "details": {"type": "minor"}
        }])
        prop_minor = ActionProposal(actor_id=hero.id, verb=ActionType.REST, updates=[minor_up])
        ActionSystem.apply_action_state_transitions(world, None, [prop_minor], None)
        
    # 3. Verify that the Nemesis memory survived pruning while minor ones were removed
    log = hero.mind.narrative.memory_log
    assert len(log) <= 50
    
    nemesis_entries = [e for e in log if e.type == "social" and "nemesis" in e.details.change_type]
    assert len(nemesis_entries) == 1, "Nemesis memory should be locked/retained due to high salience"
