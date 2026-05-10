import pytest
from src.core.state import EntityState, IdentityComponent
from src.core.enums import EntityRole
from src.core.strategic import ProjectState
from src.systems.routine import RoutineService

def test_role_identity_biasing():
    """Verify that different roles bias toward different project kinds."""
    from src.core.builder import V2EntityBuilder
    # 1. Shopkeeper bias for Shopkeeping
    shopkeeper = (V2EntityBuilder(1)
        .kind("CITIZEN")
        .location(0.0, 0.0)
        .identity(role=EntityRole.SHOPKEEPER)
        .build())
    
    projects = [
        ProjectState(id="p1", kind="SHOPKEEPING", score=10.0),
        ProjectState(id="p2", kind="QUEST", score=10.0)
    ]
    
    biased_shop = RoutineService.apply_role_based_biasing(shopkeeper, projects, 1200)
    
    # SHOPKEEPING should get +20.0
    p1_shop = next(p for p in biased_shop if p.id == "p1")
    assert p1_shop.score == 30.0
    
    # QUEST should stay 10.0
    p2_shop = next(p for p in biased_shop if p.id == "p2")
    assert p2_shop.score == 10.0
    
    # 2. Hero bias for Quests
    hero = (V2EntityBuilder(2)
        .kind("HERO")
        .location(0.0, 0.0)
        .identity(role=EntityRole.HERO)
        .build())
    
    biased_hero = RoutineService.apply_role_based_biasing(hero, projects, 1200)
    
    # QUEST should get +10.0
    p2_hero = next(p for p in biased_hero if p.id == "p2")
    assert p2_hero.score == 20.0
    
    # SHOPKEEPING should stay 10.0
    p1_hero = next(p for p in biased_hero if p.id == "p1")
    assert p1_hero.score == 10.0
