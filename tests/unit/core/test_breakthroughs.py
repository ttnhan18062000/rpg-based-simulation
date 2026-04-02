import pytest
from unittest.mock import MagicMock, patch
from src.core.gameplay.attributes import Attributes, check_breakthroughs, recalc_derived_stats
from src.core.aspects.combat import CombatAspect

def test_breakthrough_is_added():
    attrs = Attributes(str_=25)
    traits = []
    check_breakthroughs(attrs, traits)
    assert "str_25" in traits

def test_breakthrough_applies_bonus():
    # Use a real entity or a very simple mock structure
    entity = MagicMock()
    # Ensure identity is a mock and has traits
    entity.identity = MagicMock()
    entity.identity.traits = ["str_25"]
    entity.progression.progression.stamina = 100
    entity.progression.max_stamina = 100
    
    stats = CombatAspect()
    stats.on_attach(entity)
    stats.combat.atk_base = 100
    
    attrs = Attributes(str_=25)
    recalc_derived_stats(stats, attrs)
    
    # Base 112 * 1.1 = 123
    assert stats.combat.atk_base >= 123
