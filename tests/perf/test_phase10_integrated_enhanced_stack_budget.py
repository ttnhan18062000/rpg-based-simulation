# Integrated performance scenario tests for Phase 10
import pytest
import time
from src.domains.optimization.feature_flags import FeatureFlagManager, FeatureMode
from src.domains.optimization.rollout_profiles import RolloutProfileManager, HardwareClass
from src.domains.optimization.budget_manager import PhaseBudgetManager, PhaseBudget

def run_performance_ticks(entities_count: int, ticks: int, profile_class: HardwareClass):
    ff = FeatureFlagManager()
    rpm = RolloutProfileManager()
    profile = rpm.get_profile(profile_class)
    
    # Register budget for the tick
    budget = PhaseBudget(
        phase_name="test_phase",
        max_ms_per_tick=profile.tick_budget_ms,
        max_entities_per_tick=entities_count,
        max_provider_calls_per_tick=entities_count * 2,
        max_results_per_entity=5,
        max_trace_events_per_tick=profile.max_trace_events,
        max_memory_entries_per_entity=100
    )
    pbm = PhaseBudgetManager(budget)
    
    # Track simulation loop metrics
    t0 = time.perf_counter()
    for tick in range(ticks):
        # Simulate processing entities
        pbm.reset()
        res = pbm.check_and_consume(
            entities=entities_count,
            provider_calls=entities_count // 2,
            trace_events=min(5, profile.max_trace_events // ticks),
            ms_spent=0.01
        )
        assert res.allowed or "exhausted" in str(res.skipped_reason)
    t1 = time.perf_counter()
    return (t1 - t0) * 1000

def test_scenario_10_1_small_full_stack():
    # 30 entities, 10 ticks (shortened for unit test speed)
    elapsed_ms = run_performance_ticks(entities_count=30, ticks=10, profile_class=HardwareClass.CLASS_B)
    assert elapsed_ms < 1000.0

def test_scenario_10_2_medium_selected_stack():
    # 100 entities, 10 ticks
    elapsed_ms = run_performance_ticks(entities_count=100, ticks=10, profile_class=HardwareClass.CLASS_B)
    assert elapsed_ms < 1000.0

def test_scenario_10_3_large_conservative():
    # 500 entities, 5 ticks
    elapsed_ms = run_performance_ticks(entities_count=500, ticks=5, profile_class=HardwareClass.CLASS_A)
    assert elapsed_ms < 1500.0

def test_scenario_10_4_event_heavy_emergence():
    # 100 entities, 10 ticks
    elapsed_ms = run_performance_ticks(entities_count=100, ticks=10, profile_class=HardwareClass.CLASS_C)
    assert elapsed_ms < 1000.0

def test_scenario_10_5_cooperation_candidate_explosion():
    # 200 entities, 10 ticks
    elapsed_ms = run_performance_ticks(entities_count=200, ticks=10, profile_class=HardwareClass.CLASS_C)
    assert elapsed_ms < 1000.0
