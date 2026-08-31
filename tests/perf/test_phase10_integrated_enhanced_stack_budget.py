# Integrated performance scenario tests for Phase 10
import pytest
import time
from dataclasses import dataclass
from src.domains.optimization.feature_flags import FeatureFlagManager, FeatureMode
from src.domains.optimization.budget_manager import PhaseBudgetManager, PhaseBudget
from tests.tools.perf_assertions import assert_perf_threshold

# Inlined from the now-removed RolloutProfileManager (TCK-20260824-ROLLOUT-FLAG-DECISIONS --
# confirmed dead production code, zero real callers; this test only ever used its tick_budget_ms/
# max_trace_events numbers as convenient test parameters, not the class itself).
@dataclass(frozen=True)
class _HardwareBudget:
    tick_budget_ms: float
    max_trace_events: int

_CLASS_A_BUDGET = _HardwareBudget(tick_budget_ms=10.0, max_trace_events=1000)
_CLASS_B_BUDGET = _HardwareBudget(tick_budget_ms=25.0, max_trace_events=5000)
_CLASS_C_BUDGET = _HardwareBudget(tick_budget_ms=50.0, max_trace_events=20000)

def run_performance_ticks(entities_count: int, ticks: int, profile: _HardwareBudget):
    ff = FeatureFlagManager()

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
    elapsed_ms = run_performance_ticks(entities_count=30, ticks=10, profile=_CLASS_B_BUDGET)
    assert_perf_threshold(elapsed_ms, 1000.0, "Scenario 10.1 (30 entities, 10 ticks) elapsed time", op="<")

def test_scenario_10_2_medium_selected_stack():
    # 100 entities, 10 ticks
    elapsed_ms = run_performance_ticks(entities_count=100, ticks=10, profile=_CLASS_B_BUDGET)
    assert_perf_threshold(elapsed_ms, 1000.0, "Scenario 10.2 (100 entities, 10 ticks) elapsed time", op="<")

def test_scenario_10_3_large_conservative():
    # 500 entities, 5 ticks
    elapsed_ms = run_performance_ticks(entities_count=500, ticks=5, profile=_CLASS_A_BUDGET)
    assert_perf_threshold(elapsed_ms, 1500.0, "Scenario 10.3 (500 entities, 5 ticks) elapsed time", op="<")

def test_scenario_10_4_event_heavy_emergence():
    # 100 entities, 10 ticks
    elapsed_ms = run_performance_ticks(entities_count=100, ticks=10, profile=_CLASS_C_BUDGET)
    assert_perf_threshold(elapsed_ms, 1000.0, "Scenario 10.4 (100 entities, 10 ticks) elapsed time", op="<")

def test_scenario_10_5_cooperation_candidate_explosion():
    # 200 entities, 10 ticks
    elapsed_ms = run_performance_ticks(entities_count=200, ticks=10, profile=_CLASS_C_BUDGET)
    assert_perf_threshold(elapsed_ms, 1000.0, "Scenario 10.5 (200 entities, 10 ticks) elapsed time", op="<")
