import pytest
from unittest.mock import MagicMock
from src.core.entities.entity import Entity
from src.core.models.enums import AIState, Faction, HeroClass
from src.core.entities.stats import Stats

def test_entity_stats_proxy_delegation():
    # Setup entity with base stats
    entity = Entity(id=1, kind="hero")
    entity.combat.atk = 10
    entity.combat.def_ = 5
    
    # Check base delegation
    assert entity.stats.combat.atk == 10
    assert entity.stats.combat.def_ == 5
    
    # Test setting through stats shim
    entity.stats.combat.atk = 20
    assert entity.combat.atk == 20
    assert entity.stats.combat.atk == 20

def test_effective_stats_with_equipment():
    entity = Entity(id=1, kind="hero")
    entity.combat.atk = 10
    
    # Mock inventory equipment bonus
    entity.aspects["inventory"] = MagicMock()
    entity.aspects["inventory"].equipment_bonus.return_value = 5
    
    # effective_atk should be 10 (base) + 5 (equip) = 15
    assert entity.stats.combat.atk == 15

def test_effective_stats_with_effects():
    entity = Entity(id=1, kind="hero")
    entity.combat.atk = 10
    
    # Mock effect
    mock_effect = MagicMock()
    mock_effect.atk_mult = 1.2
    entity.combat.effects = [mock_effect]
    
    # effective_atk should be 10 * 1.2 = 12
    assert entity.stats.combat.atk == 12

def test_veterancy_multiplier():
    entity = Entity(id=1, kind="hero")
    entity.combat.atk = 10
    
    # Set veterancy to ELITE (rank 3) -> 1.10x multiplier for atk
    entity.progression.veterancy_rank = 3
    
    assert entity.stats.combat.atk == 11
