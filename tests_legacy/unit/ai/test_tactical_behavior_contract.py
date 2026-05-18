import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", ".."))

import pytest
from unittest.mock import MagicMock
from src_legacy.ai.tactical.contract import TacticalMode, TacticalRole
from src_legacy.ai.tactical.tactical_evaluator import TacticalEvaluator
from src_legacy.core.models.enums import HeroClass, Faction, LifeRole
from src_legacy.core.models.vectors import Vector2
from src_legacy.core.gameplay.items.item_registry import ITEM_REGISTRY

def _make_mock_entity(eid: int, x: int, y: int, hero_class=HeroClass.NONE, faction=Faction.HERO_GUILD, weapon=None, hp=100, max_hp=100):
    e = MagicMock()
    e.id = eid
    e.spatial.pos = Vector2(x, y)
    e.identity.hero_class = hero_class
    e.identity.faction = faction
    e.identity.world_role = LifeRole.NONE
    e.inventory.weapon = weapon
    e.combat.hp = hp
    e.combat.hp_max = max_hp # Some tests might use hp_max
    e.combat.alive = True
    return e

def test_melee_striker_closes_distance():
    actor = _make_mock_entity(1, 0, 0, hero_class=HeroClass.WARRIOR)
    enemy = _make_mock_entity(2, 3, 0, faction=Faction.GOBLIN_HORDE)
    
    ctx = MagicMock(actor=actor, visible=[enemy])
    ctx.nearest_enemy.return_value = enemy
    
    eval = TacticalEvaluator.evaluate_tactics(ctx)
    
    assert eval.role == TacticalRole.MELEE_STRIKER
    assert eval.mode == TacticalMode.CLOSE
    assert eval.target_id == 2

def test_ranged_skirmisher_kites_when_close():
    actor = _make_mock_entity(1, 0, 0, hero_class=HeroClass.RANGER, weapon="bow")
    # Populate registry instead of mocking .get
    ITEM_REGISTRY["bow"] = MagicMock(weapon_range=5)
    
    enemy = _make_mock_entity(2, 1, 0, faction=Faction.GOBLIN_HORDE)
    
    ctx = MagicMock(actor=actor, visible=[enemy])
    ctx.nearest_enemy.return_value = enemy
    
    eval = TacticalEvaluator.evaluate_tactics(ctx)
    
    assert eval.role == TacticalRole.RANGED_SKIRMISHER
    assert eval.mode == TacticalMode.WIDEN
    assert "Widen" in str(eval.reason)

def test_ranged_skirmisher_maintains_distance():
    actor = _make_mock_entity(1, 0, 0, hero_class=HeroClass.RANGER, weapon="bow")
    ITEM_REGISTRY["bow"] = MagicMock(weapon_range=5)
    enemy = _make_mock_entity(2, 4, 0, faction=Faction.GOBLIN_HORDE)
    
    ctx = MagicMock(actor=actor, visible=[enemy])
    ctx.nearest_enemy.return_value = enemy
    
    eval = TacticalEvaluator.evaluate_tactics(ctx)
    
    assert eval.mode == TacticalMode.MAINTAIN
    assert "Maintain" in str(eval.reason)

def test_safe_shot_detection():
    actor = _make_mock_entity(1, 0, 0, hero_class=HeroClass.RANGER, weapon="bow")
    ITEM_REGISTRY["bow"] = MagicMock(weapon_range=5)
    enemy = _make_mock_entity(2, 3, 0, faction=Faction.GOBLIN_HORDE)
    
    ctx = MagicMock(actor=actor, visible=[enemy])
    ctx.nearest_enemy.return_value = enemy
    ctx.faction_reg.is_hostile.return_value = True
    
    eval = TacticalEvaluator.evaluate_tactics(ctx)
    assert eval.is_safe_shot is True
    
    # Now add an adjacent enemy
    enemy2 = _make_mock_entity(3, 1, 0, faction=Faction.GOBLIN_HORDE)
    ctx.visible = [enemy, enemy2]
    
    eval = TacticalEvaluator.evaluate_tactics(ctx)
    assert eval.is_safe_shot is False

def test_tactical_retreat_at_low_hp():
    actor = _make_mock_entity(1, 0, 0, hero_class=HeroClass.WARRIOR, hp=20, max_hp=100)
    enemy = _make_mock_entity(2, 1, 0, faction=Faction.GOBLIN_HORDE)
    
    ctx = MagicMock(actor=actor, visible=[enemy])
    ctx.nearest_enemy.return_value = enemy
    
    eval = TacticalEvaluator.evaluate_tactics(ctx)
    
    assert eval.mode == TacticalMode.RETREAT
    assert "Low HP" in str(eval.reason)

def test_group_spacing_preservation():
    actor = _make_mock_entity(10, 0, 0, hero_class=HeroClass.RANGER, weapon="bow")
    ITEM_REGISTRY["bow"] = MagicMock(weapon_range=5)
    ally = _make_mock_entity(5, 1, 0, hero_class=HeroClass.RANGER, faction=Faction.HERO_GUILD)
    enemy = _make_mock_entity(2, 4, 0, faction=Faction.GOBLIN_HORDE)
    
    ctx = MagicMock(actor=actor, visible=[ally, enemy])
    ctx.faction_reg.is_allied.side_effect = lambda f1, f2: f1 == f2
    ctx.nearest_enemy.return_value = enemy
    
    # Actor 10 is higher ID than Ally 5, so Actor 10 should move away
    eval = TacticalEvaluator.evaluate_tactics(ctx)
    
    assert eval.mode == TacticalMode.WIDEN
    assert "spacing" in str(eval.reason).lower()
    
    # If actor is lower ID, it should NOT move away for spacing (let the other move)
    actor.id = 3
    eval = TacticalEvaluator.evaluate_tactics(ctx)
    assert eval.mode == TacticalMode.MAINTAIN
