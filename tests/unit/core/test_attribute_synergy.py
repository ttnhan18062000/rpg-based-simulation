"""Tests for attribute synergy and secondary stat impacts."""

import pytest
from src.core.gameplay.attributes import derive_crit_rate
# derive_loot_modifier might not exist yet, we'll try to import it and let it fail if needed
# or just test against the module it SHOULD be in.

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
    """Verify that Luck provides a loot rarity multiplier."""
    # Expected: 1.0 + (Luck / 100)
    from src.core.gameplay.attributes import derive_loot_modifier
    assert derive_loot_modifier(0) == 1.0
    assert derive_loot_modifier(50) == 1.5
    assert derive_loot_modifier(100) == 2.0

def test_per_based_hidden_discovery():
    """Verify that hidden entities are only visible with sufficient Perception."""
    from src.ai.perception import Perception
    from src.core.models import Vector2
    from unittest.mock import MagicMock

    # Actor with low PER (5)
    actor_low = MagicMock()
    actor_low.spatial.pos = Vector2(0, 0)
    actor_low.id = 1
    actor_low.stats.per = 5
    actor_low.stats.spatial.vision_range = 10

    # Actor with high PER (25)
    actor_high = MagicMock()
    actor_high.spatial.pos = Vector2(0, 0)
    actor_high.id = 2
    actor_high.stats.per = 25
    actor_high.stats.spatial.vision_range = 10

    # Hidden entity
    hidden_e = MagicMock()
    hidden_e.spatial.pos = Vector2(1, 1)
    hidden_e.id = 3
    # We will add is_hidden to the actual implementation, for now mock it
    hidden_e.spatial.is_hidden = True 
    
    snapshot = MagicMock()
    snapshot.entities = {1: actor_low, 2: actor_high, 3: hidden_e}
    snapshot.nearby_entity_ids.return_value = [1, 2, 3]

    # Low PER should NOT see it
    visible_low = Perception.visible_entities(actor_low, snapshot, 10)
    assert 3 not in [e.id for e in visible_low]

    # High PER SHOULD see it
    visible_high = Perception.visible_entities(actor_high, snapshot, 10)
    assert 3 in [e.id for e in visible_high]
