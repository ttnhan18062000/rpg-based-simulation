import pytest
from src.core.entities.entity import Entity
from src.core.aspects.combat import CombatAspect
from src.core.aspects.progression import ProgressionAspect
from src.core.models.vectors import Vector2

def test_combat_aspect_invariants():
    # Test HP clamping
    c = CombatAspect(hp=100, max_hp=50)
    c.validate()
    assert c.hp == 50
    
    c.hp = -10
    c.validate()
    assert c.hp == 0
    
    # Test base stats bounds
    c.atk_base = 0
    c.spd_base = -5
    c.validate()
    assert c.atk_base == 1
    assert c.spd_base == 1

def test_progression_aspect_invariants():
    # Test stamina clamping
    p = ProgressionAspect(stamina=200, max_stamina=100)
    p.validate()
    assert p.stamina == 100
    
    p.stamina = -20
    p.validate()
    assert p.stamina == 0
    
    # Test other metrics
    p.gold = -100
    p.xp = -50
    p.level = 0
    p.validate()
    assert p.gold == 0
    assert p.xp == 0
    assert p.level == 1

def test_freeze_calls_validate():
    # Verify that calling freeze() triggers validate() automatically
    c = CombatAspect(hp=100, max_hp=50)
    assert c.hp == 100
    c.freeze()
    assert c.hp == 50
    assert getattr(c, "_frozen", False)

def test_nested_freeze_invariants():
    # Entity freeze should recursively validate all aspects
    e = Entity(id=1, kind="hero", combat=CombatAspect(hp=100, max_hp=50))
    # Before freeze
    assert e.combat.hp == 100
    
    e.freeze()
    # After freeze (recursive)
    assert e.combat.hp == 50
    assert getattr(e.combat, "_frozen", False)
