import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", ".."))


import pytest
from unittest.mock import MagicMock, patch
from src.core.gameplay.attributes import Attributes, check_breakthroughs, recalc_derived_stats
from src.core.aspects.combat import CombatAspect

from src.core.entities.entity import Entity
from src.core.models.vectors import Vector2
from src.core.aspects.identity import IdentityAspect
from src.core.aspects.spatial import SpatialAspect
from src.core.gameplay.attributes import Attributes, check_breakthroughs, recalc_derived_stats

def test_breakthrough_is_added():
    # check_breakthroughs(entity)
    e = Entity(id=1, kind="hero", progression={"attributes": Attributes(str_=25)})
    check_breakthroughs(e)
    assert "str_25" in e.identity.traits

def test_breakthrough_applies_bonus():
    # Use real entity for reliable property testing
    e = Entity(
        id=2, kind="hero",
        identity=IdentityAspect(traits=["str_25"]),
        combat={"hp": 100, "max_hp": 100, "atk": 100},
        spatial=SpatialAspect(pos=Vector2(0, 0))
    )
    
    attrs = Attributes(str_=25)
    recalc_derived_stats(e, attrs)
    
    # 100 base + 12 (str_25 contribution) = 112
    # Then 112 * 1.1 = 123.2
    assert e.combat.atk_base >= 123
