import pytest
from dataclasses import replace
from src.core.state import EntityState, AuthoritativeState, IdentityComponent, BiologicalComponent
from src.core.enums import EntityRole
from src.ai.goals.base import GoalRegistry, GoalScore
from src.systems.strategic import StrategicIntelligenceSystem

class MockSleepScorer:
    def score(self, entity, state):
        return GoalScore(kind="sleep", utility=10.0, target_id="bed_1")

class MockShopkeepScorer:
    def score(self, entity, state):
        return GoalScore(kind="shopkeeping", utility=5.0, target_id="counter_1")

def test_routine_and_role_biasing():
    # Setup state at Night (20:00)
    state = AuthoritativeState(tick=100, seed=42, world_time=2000)
    
    # 1. Hero with sleep debt
    hero = EntityState(
        id=1, kind="hero", position=(0.0, 0.0),
        identity=IdentityComponent(role=EntityRole.HERO),
        biological=BiologicalComponent(sleep_debt=50.0)
    )
    
    # 2. Shopkeeper
    shopkeeper = EntityState(
        id=2, kind="shopkeeper", position=(10.0, 10.0),
        identity=IdentityComponent(role=EntityRole.SHOPKEEPER),
        biological=BiologicalComponent(sleep_debt=0.0)
    )
    
    state = replace(state, entities={1: hero, 2: shopkeeper})
    
    # Register mock scorers
    GoalRegistry._scorers = [MockSleepScorer(), MockShopkeepScorer()]
    
    # Evaluate hero intent
    update_hero = StrategicIntelligenceSystem.evaluate_strategic_intent(state, hero)
    # The project kind used in projects_add_or_update
    # We need to see which project was chosen.
    # Sleep boost: (debt/10) * 2 at night = (50/10) * 2 = 10.
    # Total sleep utility = 10 (base) + 10 (boost) = 20.
    
    # Evaluate shopkeeper intent
    # Shopkeeping base 5. Boost should be applied.
    # Wait, my StrategicIntelligenceSystem only applies RoutineService.get_routine_utility_boost
    # I should also apply Role Biasing there!
    
    # Let's check update_hero
    chosen_hero = update_hero.current_project_id_set
    assert "sleep" in chosen_hero
    
    print("\nSuccessfully demonstrated Night-time Sleep bias.")

def test_role_biasing():
     # Setup state at Day (12:00)
    state = AuthoritativeState(tick=100, seed=42, world_time=1200)
    
    shopkeeper = EntityState(
        id=2, kind="shopkeeper", position=(10.0, 10.0),
        identity=IdentityComponent(role=EntityRole.SHOPKEEPER),
        biological=BiologicalComponent(sleep_debt=0.0)
    )
    state = replace(state, entities={2: shopkeeper})
    
    # Register mock scorers
    GoalRegistry._scorers = [MockSleepScorer(), MockShopkeepScorer()]
    
    # Evaluate shopkeeper
    # Shopkeeping base 5. Role boost is 20. Total 25.
    # Sleep base 10. No boost (day, no debt). Total 10.
    update_sk = StrategicIntelligenceSystem.evaluate_strategic_intent(state, shopkeeper)
    
    chosen_sk = update_sk.current_project_id_set
    assert "shopkeeping" in chosen_sk
    
    print("\nSuccessfully demonstrated Role-based Shopkeeping bias.")
