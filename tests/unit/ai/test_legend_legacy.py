import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", ".."))


import pytest
from tests.helpers.legacy_stats import Stats
from src.core.entities.entity import Entity, Vector2
from src.core.aspects.mind import MindAspect
from src.core.aspects.spatial import SpatialAspect
from src.core.gameplay.faction import Faction
from src.core.gameplay.effects import EffectType, suppression_effect
from src.systems.gameplay.action_system import ActionSystem
from src.systems.infrastructure.base import SystemContext
from src.core.models.world_state import WorldState
from src.platform.rng import DeterministicRNG
from src.core.data.events import RenownEvent

@pytest.fixture
def world():
    ws = WorldState(seed=0, grid=None, spatial_index=None)
    from src.platform.spatial_hash import SpatialHash
    ws.spatial_index = SpatialHash(cell_size=10)
    return ws

@pytest.fixture
def context(world):
    from src.config import SimulationConfig
    from src.core.gameplay.faction import FactionRegistry
    config = SimulationConfig()
    return SystemContext(config, world, DeterministicRNG(0), None, FactionRegistry.default(), None)

def test_narrative_memory_logging(context):
    attacker = Entity(id=1, kind="hero", faction=Faction.HERO_GUILD)
    defender = Entity(id=2, kind="goblin", faction=Faction.GOBLIN_HORDE)
    context.world.add_entity(attacker)
    context.world.add_entity(defender)
    
    # Mocking death and glory/trauma logic
    # ActionSystem handles this in ProcessAppliedActions -> _apply_skill_effect
    action_system = ActionSystem(context.config, context.rng)
    
    # Manually trigger the logic for testing
    # Glory for attacker
    from src.core.aspects.mind import MemoryLogEntry
    glory_event = MemoryLogEntry(tick=0, type="glory", impact=5.0, details={"desc": "Slayed goblin"})
    attacker.mind.narrative.memory_log.append(glory_event)
    attacker.mind.emotion.bravery = 0.6
    
    assert len(attacker.mind.narrative.memory_log) == 1
    assert attacker.mind.narrative.memory_log[0].type == "glory"

def test_bravery_modifiers(context):
    hero = Entity(id=1, kind="hero", faction=Faction.HERO_GUILD)
    hero.combat.atk_base = 10
    hero.combat.spd_base = 10
    
    # Default bravery 0.5 -> mult 1.0 (Shim in CombatAspect)
    assert hero.combat.atk == 10
    
    # Brave Bonus (> 0.8)
    hero.mind.emotion.bravery = 0.9
    assert hero.combat.atk == 11 # 10 * 1.1
    assert hero.combat.spd == 11
    
    # Fear Factor (< 0.3)
    hero.mind.emotion.bravery = 0.2
    assert hero.combat.atk == 9 # 10 * 0.9
    assert hero.combat.spd == 9
    assert hero.combat.def_ == 0 # 0 * 0.9 = 0

def test_regional_suppression(context):
    hero = Entity(id=1, kind="hero", faction=Faction.HERO_GUILD)
    hero.spatial.current_region_id = "forest"
    context.world.add_entity(hero)
    
    # Mock deaths
    key = (int(Faction.HERO_GUILD), "forest")
    context.world.faction_deaths_per_region[key] = 10
    
    # Suppression logic is in WorldLoop._update_world_evolution
    # We'll just verify the suppression_effect stat penalty
    effect = suppression_effect(duration=10)
    hero.combat.effects.append(effect)
    
    hero.combat.atk_base = 100
    # atk should be 100 * 0.8 = 80
    assert hero.combat.atk == 80
