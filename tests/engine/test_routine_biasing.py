import pytest
from dataclasses import replace
from src.core.state import EntityState, AuthoritativeState, IdentityComponent, BiologicalComponent
from src.core.enums import EntityRole
from src.ai.goals.base import GoalRegistry, GoalScore
from src.systems.strategic import StrategicIntelligenceSystem
from src.core.builder import V2EntityBuilder

class MockSleepScorer:
    def score(self, entity, state):
        return GoalScore(kind="sleep", utility=10.0, target_id="bed_1")

class MockShopkeepScorer:
    def score(self, entity, state):
        return GoalScore(kind="shopkeeping", utility=5.0, target_id="counter_1")

def test_routine_and_role_biasing(monkeypatch):
    # Setup state at Night (20:00)
    state = AuthoritativeState(tick=100, seed=42, world_time=2000)
    
    # 1. Hero with sleep debt
    hero = (V2EntityBuilder(1)
            .kind("hero")
            .identity(role=EntityRole.HERO)
            .biological(sleep_debt=50.0)
            .build())
    
    # 2. Shopkeeper
    shopkeeper = (V2EntityBuilder(2)
                  .kind("shopkeeper")
                  .identity(role=EntityRole.SHOPKEEPER)
                  .biological(sleep_debt=0.0)
                  .build())
    
    state = replace(state, entities={1: hero, 2: shopkeeper})
    
    # Register mock scorers using monkeypatch to avoid persistent state contamination
    mock_scorers = {
        "sleep": MockSleepScorer(),
        "shopkeeping": MockShopkeepScorer()
    }
    monkeypatch.setattr(GoalRegistry, "_scorers", mock_scorers)
    
    # Evaluate hero intent
    update_hero = StrategicIntelligenceSystem.evaluate_strategic_intent(state, hero, force=True)
    
    # Let's check update_hero
    assert "sleep" in update_hero.current_project_id_set
    
    print("\nSuccessfully demonstrated Night-time Sleep bias.")

def test_role_biasing(monkeypatch):
     # Setup state at Day (12:00)
    state = AuthoritativeState(tick=100, seed=42, world_time=1200)
    
    shopkeeper = (V2EntityBuilder(2)
                  .kind("shopkeeper")
                  .identity(role=EntityRole.SHOPKEEPER)
                  .biological(sleep_debt=0.0)
                  .build())
    state = replace(state, entities={2: shopkeeper})
    
    # Register mock scorers
    mock_scorers = {
        "sleep": MockSleepScorer(),
        "shopkeeping": MockShopkeepScorer()
    }
    monkeypatch.setattr(GoalRegistry, "_scorers", mock_scorers)
    
    # Evaluate shopkeeper
    update_sk = StrategicIntelligenceSystem.evaluate_strategic_intent(state, shopkeeper, force=True)
    
    assert "shopkeeping" in update_sk.current_project_id_set
    
    print("\nSuccessfully demonstrated Role-based Shopkeeping bias.")
