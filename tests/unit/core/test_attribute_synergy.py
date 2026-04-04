import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", ".."))


"""Tests for attribute synergy and secondary stat impacts."""

import pytest
from src.core.gameplay.attributes import derive_crit_rate
# derive_loot_modifier might not exist yet, we'll try to import it and let it fail if needed
# or just test against the module it SHOULD be in.

from src.core.entities.entity import Entity
from src.core.aspects.progression import ProgressionAspect
from src.core.aspects.spatial import SpatialAspect
from src.core.models.vectors import Vector2
from src.core.gameplay.attributes import Attributes, derive_loot_bonus

def test_luck_impacts_crit_rate_significantly():
    """Verify that Luck has a meaningful impact on critical hit rate."""
    # base 0.05, agi 10, luck 20
    # Expected formula: base + agi*0.004 + luck*0.01
    # 0.05 + 0.04 + 0.20 = 0.29
    luck = 20
    agi = 10
    base = 0.05
    result = derive_crit_rate(base, agi, luck=luck)
    assert abs(result - 0.29) < 0.0001

def test_luck_impacts_loot_modifier():
    """Verify that Luck/Perception provides a loot rarity multiplier."""
    # derive_loot_bonus(per, wis) -> 1.0 + per * 0.008 + wis * 0.003
    assert derive_loot_bonus(0, 0) == 1.0
    # per 50, wis 0 -> 1.0 + 0.4 = 1.4
    assert abs(derive_loot_bonus(50, 0) - 1.4) < 0.001

def test_per_based_hidden_discovery():
    """Verify that hidden entities are only visible with sufficient Perception."""
    from src.ai.perception import Perception
    from unittest.mock import MagicMock

    # Actor with low PER (5)
    actor_low = Entity(
        id=1, kind="hero",
        progression=ProgressionAspect(attributes=Attributes(per=5)),
        spatial=SpatialAspect(pos=Vector2(0, 0))
    )

    # Actor with high PER (25)
    actor_high = Entity(
        id=2, kind="hero",
        progression=ProgressionAspect(attributes=Attributes(per=25)),
        spatial=SpatialAspect(pos=Vector2(0, 0))
    )

    # Hidden entity
    hidden_e = Entity(id=3, kind="cache", spatial=SpatialAspect(pos=Vector2(1, 1)))
    # AOA Stabilization: is_hidden is often a spatial attribute or getattr flag
    hidden_e.is_hidden = True 
    
    snapshot = MagicMock()
    # Mock entities dict and nearby_entity_ids helper
    snapshot.entities = {1: actor_low, 2: actor_high, 3: hidden_e}
    snapshot.nearby_entity_ids.return_value = [1, 2, 3]

    # Low PER should NOT see it (requires PER >= 20)
    visible_low = Perception.visible_entities(actor_low, snapshot, 10)
    assert 3 not in [e.id for e in visible_low]

    # High PER SHOULD see it
    visible_high = Perception.visible_entities(actor_high, snapshot, 10)
    assert 3 in [e.id for e in visible_high]
