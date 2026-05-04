"""
Biological needs and routine strategic integration tests.
- RPG-0060: biological_routine_integration
"""
import pytest
from dataclasses import replace
from src.core.state import EntityState, BiologicalComponent, AuthoritativeState
from src.core.updates import StateUpdate, EntityUpdate
from src.systems.routine import RoutineService
from src.systems.strategic import StrategicIntelligenceSystem
from src.engine.apply import ApplyPath

def test_biological_decay_per_tick():
    """Verify that biological needs increase over time (decay)."""
    from src.core.builder import V2EntityBuilder
    ent = (V2EntityBuilder(1)
        .kind("HERO")
        .at((0.0, 0.0))
        .biological(hunger=10.0, sleep_debt=5.0)
        .build())
    state = AuthoritativeState(tick=100, seed=42, entities={1: ent})
    
    update = StateUpdate()
    next_state = ApplyPath.apply_generation(state, update, 101)
    
    new_ent = next_state.entities[1]
    # Hunger: 10.0 + 0.1 = 10.1
    # Sleep Debt: 5.0 + 0.05 = 5.05
    assert new_ent.biological.hunger == pytest.approx(10.1)
    assert new_ent.biological.sleep_debt == pytest.approx(5.05)

def test_hunger_concern_generation():
    """Verify that high hunger generates a strategic concern."""
    from src.core.builder import V2EntityBuilder
    ent = (V2EntityBuilder(1)
        .kind("HERO")
        .at((0.0, 0.0))
        .biological(hunger=60.0)
        .build())
    state = AuthoritativeState(tick=100, seed=42, entities={1: ent}, world_time=1200)
    
    concerns = RoutineService.evaluate_biological_needs(ent, state.world_time)
    assert any(c.id == "concern_hunger" for c in concerns)
    assert concerns[0].urgency == pytest.approx(0.6)

def test_sleep_bias_at_night():
    """Verify that sleep urgency is higher at night."""
    from src.core.builder import V2EntityBuilder
    ent = (V2EntityBuilder(1)
        .kind("HERO")
        .at((0.0, 0.0))
        .biological(sleep_debt=30.0)
        .build())
    
    # Daytime (12:00)
    concerns_day = RoutineService.evaluate_biological_needs(ent, 1200)
    # sleep_urgency = 0.3 (below 0.4 threshold)
    assert not any(c.id == "concern_sleep" for c in concerns_day)
    
    # Nighttime (20:00)
    concerns_night = RoutineService.evaluate_biological_needs(ent, 2000)
    # sleep_urgency = 0.3 + 0.3 = 0.6
    assert any(c.id == "concern_sleep" for c in concerns_night)
    assert concerns_night[0].urgency == pytest.approx(0.6)

def test_routine_utility_boost():
    """Verify that routine-related projects get utility boosts."""
    from src.core.builder import V2EntityBuilder
    ent = (V2EntityBuilder(1)
        .kind("HERO")
        .at((0.0, 0.0))
        .biological(hunger=50.0, sleep_debt=40.0)
        .build())
    
    # Hunger boost: 50.0 / 10.0 = 5.0
    boost_eat = RoutineService.get_routine_utility_boost(ent, "eating", 1200)
    assert boost_eat == pytest.approx(5.0)
    
    # Sleep boost at night: (40.0 / 10.0) * 2.0 = 8.0
    boost_sleep = RoutineService.get_routine_utility_boost(ent, "sleep", 2200)
    assert boost_sleep == pytest.approx(8.0)

def test_pipeline_integrates_biological_concerns():
    """Verify that the AuthoritativeApplyPipeline adds biological concerns."""
    from src.engine.pipeline import AuthoritativeApplyPipeline
    from src.core.builder import V2EntityBuilder
    
    ent = (V2EntityBuilder(1)
        .kind("HERO")
        .at((0.0, 0.0))
        .biological(hunger=80.0)
        .build())
    state = AuthoritativeState(tick=99, seed=42, entities={1: ent}, world_time=1200)
    
    raw_update = StateUpdate()
    refined = AuthoritativeApplyPipeline.refine(state, raw_update)
    
    ent_upd = refined.entity_updates[1]
    assert ent_upd.strategic is not None
    assert any(c.id == "concern_hunger" for c in ent_upd.strategic.concerns_add_or_update)

def test_routine_action_execution():
    """Verify that REST/EAT actions produce correct biological updates."""
    from src.engine.domain_logic import SimulationDomainLogic
    from src.core.builder import V2EntityBuilder
    
    ent = (V2EntityBuilder(1)
        .kind("HERO")
        .at((0.0, 0.0))
        .biological(hunger=50.0, sleep_debt=40.0)
        .readiness(100.0)
        .build())
    
    # 1. Test REST
    upd_sleep = SimulationDomainLogic.execute_action(ent, {"action": "REST"}, current_tick=500)
    assert upd_sleep[1].biological is not None
    assert upd_sleep[1].biological.rest_pressure_delta == -30.0
    
    # 2. Test EAT
    upd_eat = SimulationDomainLogic.execute_action(ent, {"action": "EAT"}, current_tick=600)
    assert upd_eat[1].biological is not None
    assert upd_eat[1].biological.hunger_delta == -40.0
    assert upd_eat[1].biological.last_meal_tick_set == 600
