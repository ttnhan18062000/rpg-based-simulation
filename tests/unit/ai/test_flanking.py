import pytest
from unittest.mock import MagicMock
from src.core.models import Vector2, Entity
from src.actions.damage import PhysicalDamageCalculator

def test_flanking_bonus():
    calc = PhysicalDamageCalculator()
    
    attacker = MagicMock(spec=Entity)
    attacker.spatial.pos = Vector2(0, 0)
    attacker.stats.combat.atk = 10
    attacker.attributes = None
    
    defender = MagicMock(spec=Entity)
    defender.spatial.pos = Vector2(0, 1)
    defender.spatial.facing = Vector2(0, 1) # Facing South
    defender.stats.combat.def_ = 0
    defender.attributes = None
    
    # Attacker is at (0,0), Defender at (0,1).
    # Defender faces (0,1) [South]. 
    # Attacker is BEHIND the defender.
    
    ctx = calc.resolve(attacker, defender)
    
    # atk_mult should be 1.3
    assert ctx.combat.atk_mult == pytest.approx(1.3)

def test_no_flanking_bonus_when_facing_attacker():
    calc = PhysicalDamageCalculator()
    
    attacker = MagicMock(spec=Entity)
    attacker.spatial.pos = Vector2(0, 0)
    attacker.stats.combat.atk = 10
    attacker.attributes = None
    
    defender = MagicMock(spec=Entity)
    defender.spatial.pos = Vector2(0, 1)
    defender.spatial.facing = Vector2(0, -1) # Facing North (toward attacker)
    defender.stats.combat.def_ = 0
    defender.attributes = None
    
    ctx = calc.resolve(attacker, defender)
    
    # atk_mult should be 1.0
    assert ctx.combat.atk_mult == pytest.approx(1.0)
