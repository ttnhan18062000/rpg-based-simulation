import pytest
from src.core.models.world_state import WorldState
from src.core.entities.entity import Entity
from src.core.aspects.identity import IdentityAspect
from src.core.models.enums import DamageType, Element, SkillType, SkillTarget, ActionType, Faction
from src.core.gameplay.classes import SkillDef, SkillInstance, SKILL_DEFS
from src.systems.gameplay.action_system import ActionSystem
from src.actions.base import ActionProposal, CombatTraceUpdate
from src.config import SimulationConfig
from src.core.registry.registry_loader import load_all_registries
from unittest.mock import MagicMock

@pytest.fixture(autouse=True)
def setup_registries():
    load_all_registries()

@pytest.fixture
def rng():
    from src.platform.rng import DeterministicRNG
    return DeterministicRNG(42)

@pytest.fixture
def world():
    mock_grid = MagicMock()
    mock_spatial = MagicMock()
    w = WorldState(seed=42, grid=mock_grid, spatial_index=mock_spatial)
    return w

def test_physical_skill_scaling(world, rng):
    # Setup
    config = SimulationConfig()
    
    attacker = Entity(id=1, kind="hero", identity=IdentityAspect(faction=Faction.HERO_GUILD))
    attacker.combat.atk_base = 100
    attacker.combat.matk_base = 10
    
    defender = Entity(id=2, kind="mob", identity=IdentityAspect(faction=Faction.GOBLIN_HORDE))
    defender.combat.hp = 1000
    defender.combat.def_base = 50
    
    world.entities[attacker.id] = attacker
    world.entities[defender.id] = defender
    
    # Power Strike (1.8x physical)
    instance = SkillInstance(skill_id="power_strike")
    attacker.progression.skills.append(instance)
    
    proposal = ActionProposal(actor_id=attacker.id, verb=ActionType.USE_SKILL, target=defender.id, reason="Test")
    
    # Execute
    updates = ActionSystem._get_use_skill_updates(world, config, rng, None, attacker, "power_strike", defender.id, proposal)
    
    # Verify: Should use DamageResolutionService (diminishing returns)
    # atk_final = 100 * 1.8 = 180
    # def_final = 50
    # Expected dmg ~= 115
    trace = next((u for u in proposal.updates if isinstance(u, CombatTraceUpdate)), None)
    assert trace is not None
    assert trace.result.damage > 100
    assert trace.result.metadata["power"] == 1.8

def test_magical_skill_scaling(world, rng):
    # Setup
    config = SimulationConfig()
    
    attacker = Entity(id=1, kind="hero", identity=IdentityAspect(faction=Faction.HERO_GUILD))
    attacker.combat.atk_base = 10
    attacker.combat.matk_base = 100
    
    defender = Entity(id=2, kind="mob", identity=IdentityAspect(faction=Faction.GOBLIN_HORDE))
    defender.combat.hp = 1000
    defender.combat.mdef_base = 50
    
    world.entities[attacker.id] = attacker
    world.entities[defender.id] = defender
    
    # Arcane Bolt (2.0x magical)
    instance = SkillInstance(skill_id="arcane_bolt")
    attacker.progression.skills.append(instance)
    
    proposal = ActionProposal(actor_id=attacker.id, verb=ActionType.USE_SKILL, target=defender.id, reason="Test")
    
    # Execute
    ActionSystem._get_use_skill_updates(world, config, rng, None, attacker, "arcane_bolt", defender.id, proposal)
    
    # Verify
    trace = next((u for u in proposal.updates if isinstance(u, CombatTraceUpdate)), None)
    assert trace is not None
    assert trace.result.damage > 100
    assert trace.result.details.elemental_mult == 1.0 # none element

def test_elemental_skill_scaling(world, rng):
    # Setup
    config = SimulationConfig()
    
    attacker = Entity(id=1, kind="hero", identity=IdentityAspect(faction=Faction.HERO_GUILD))
    attacker.combat.matk_base = 100
    
    defender = Entity(id=2, kind="mob", identity=IdentityAspect(faction=Faction.GOBLIN_HORDE))
    defender.combat.hp = 1000
    # Give defender fire vulnerability
    defender.combat.elem_vuln[Element.FIRE] = 1.5
    
    world.entities[attacker.id] = attacker
    world.entities[defender.id] = defender
    
    # Fireball (1.8x fire magical)
    instance = SkillInstance(skill_id="fireball")
    attacker.progression.skills.append(instance)
    
    proposal = ActionProposal(actor_id=attacker.id, verb=ActionType.USE_SKILL, target=defender.id, reason="Test")
    
    # Execute: AoE mock setup
    world.spatial_index.query_radius.return_value = [defender.id]
    ActionSystem._get_use_skill_updates(world, config, rng, None, attacker, "fireball", defender.id, proposal)
    
    # Verify
    trace = next((u for u in proposal.updates if isinstance(u, CombatTraceUpdate)), None)
    assert trace is not None
    assert trace.result.details.elemental_mult == 1.5
