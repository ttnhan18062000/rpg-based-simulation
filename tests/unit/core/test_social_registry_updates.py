import pytest
from src.core.models.world_state import WorldState
from src.core.entities.entity import Entity
from src.core.models.vectors import Vector2
from src.core.models.enums import Archetype, Faction, ActionType
from src.actions.base import ActionProposal, SocialUpdate
from src.actions.combat import CombatAftermathService
from src.systems.gameplay.action_system import ActionSystem

from src.core.world.grid import Grid
from src.platform.spatial_hash import SpatialHash

@pytest.fixture
def mock_config():
    class MockConfig:
        threat_damage_mult = 1.0
        threat_heal_mult = 1.0
    return MockConfig()

@pytest.fixture
def world():
    return WorldState(seed=42, grid=Grid(10, 10), spatial_index=SpatialHash(cell_size=10))

@pytest.fixture
def attacker(world):
    e = Entity(id=world.allocate_entity_id(), kind="mob")
    e.identity.display_name = "Attacker"
    e.identity.archetype = Archetype.BLOODTHIRSTY_SLAYER
    e.identity.faction = Faction.GOBLIN_HORDE
    world.add_entity(e)
    return e

@pytest.fixture
def defender(world):
    e = Entity(id=world.allocate_entity_id(), kind="hero")
    e.identity.display_name = "Defender"
    e.identity.archetype = Archetype.BALANCED
    e.identity.faction = Faction.HERO_GUILD
    world.add_entity(e)
    return e

def test_combat_updates_social_registry(world, attacker, defender, mock_config):
    # 1. Setup a combat outcome
    damage = 25
    proposal = ActionProposal(actor_id=attacker.id, verb=ActionType.ATTACK, target=defender.id)
    
    # 2. Process aftermath (emits SocialUpdate)
    CombatAftermathService.process(
        attacker=attacker,
        defender=defender,
        world=world,
        damage=damage,
        is_crit=False,
        is_evasion=False,
        config=mock_config,
        proposal=proposal
    )
    
    # Check that a SocialUpdate was produced
    social_updates = [u for u in proposal.updates if isinstance(u, SocialUpdate)]
    assert len(social_updates) == 1
    update = social_updates[0]
    assert update.source_id == defender.id
    assert update.target_id == attacker.id
    assert update.trust_delta < 0
    assert update.fear_delta > 0
    
    # 3. Apply updates via ActionSystem
    ActionSystem.apply_action_state_transitions(
        world=world,
        config=None,
        applied=[proposal],
        rng=None
    )
    
    # 4. Verify SocialRegistry state
    bond = world.social_registry.get_bond(defender.id, attacker.id)
    assert bond.trust < 0
    assert bond.fear > 0
    assert bond.interaction_count == 1
    assert bond.last_interaction_tick == world.tick

def test_archetype_influence_on_social_deltas(world, attacker, defender, mock_config):
    # Bloodthirsty slayer should cause more fear
    damage = 20
    proposal = ActionProposal(actor_id=attacker.id, verb=ActionType.ATTACK, target=defender.id)
    
    CombatAftermathService.process(attacker, defender, world, damage, False, False, mock_config, proposal)
    
    social_up = next(u for u in proposal.updates if isinstance(u, SocialUpdate))
    fear_with_slayer = social_up.fear_delta
    
    # Switch to balanced attacker
    attacker.identity.archetype = Archetype.BALANCED
    proposal_2 = ActionProposal(actor_id=attacker.id, verb=ActionType.ATTACK, target=defender.id)
    CombatAftermathService.process(attacker, defender, world, damage, False, False, mock_config, proposal_2)
    
    social_up_2 = next(u for u in proposal_2.updates if isinstance(u, SocialUpdate))
    fear_with_balanced = social_up_2.fear_delta
    
    assert fear_with_slayer > fear_with_balanced
