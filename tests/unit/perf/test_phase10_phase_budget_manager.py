# TDD tests for Phase 10 budget manager
import pytest
import time
from src.domains.optimization.budget_manager import PhaseBudgetManager, PhaseBudget, PhaseBudgetResult

def test_budget_allows_phase_when_under_limit():
    budget = PhaseBudget(
        phase_name="test_phase",
        max_ms_per_tick=50.0,
        max_entities_per_tick=10,
        max_provider_calls_per_tick=5,
        max_results_per_entity=3,
        max_trace_events_per_tick=100,
        max_memory_entries_per_entity=10
    )
    manager = PhaseBudgetManager(budget)
    res = manager.check_and_consume(entities=5, provider_calls=2, trace_events=10, ms_spent=5.0)
    assert res.allowed
    assert res.consumed_entities == 5
    assert res.consumed_provider_calls == 2

def test_budget_skips_phase_when_ms_limit_exceeded():
    budget = PhaseBudget(
        phase_name="test_phase",
        max_ms_per_tick=1.0,
        max_entities_per_tick=10,
        max_provider_calls_per_tick=5,
        max_results_per_entity=3,
        max_trace_events_per_tick=100,
        max_memory_entries_per_entity=10
    )
    manager = PhaseBudgetManager(budget)
    # Let's first consume under the limit
    res1 = manager.check_and_consume(entities=1, provider_calls=1, trace_events=1, ms_spent=0.8)
    assert res1.allowed
    # Next call should exceed and fail
    res2 = manager.check_and_consume(entities=1, provider_calls=1, trace_events=1, ms_spent=0.3)
    assert not res2.allowed
    assert "Time budget exhausted" in res2.skipped_reason

def test_budget_caps_entities_processed():
    budget = PhaseBudget(
        phase_name="test_phase",
        max_ms_per_tick=50.0,
        max_entities_per_tick=5,
        max_provider_calls_per_tick=10,
        max_results_per_entity=3,
        max_trace_events_per_tick=100,
        max_memory_entries_per_entity=10
    )
    manager = PhaseBudgetManager(budget)
    res = manager.check_and_consume(entities=6, provider_calls=1, trace_events=1, ms_spent=1.0)
    assert not res.allowed
    assert "Entity limit exhausted" in res.skipped_reason

def test_budget_caps_provider_calls():
    budget = PhaseBudget(
        phase_name="test_phase",
        max_ms_per_tick=50.0,
        max_entities_per_tick=5,
        max_provider_calls_per_tick=3,
        max_results_per_entity=3,
        max_trace_events_per_tick=100,
        max_memory_entries_per_entity=10
    )
    manager = PhaseBudgetManager(budget)
    res = manager.check_and_consume(entities=1, provider_calls=4, trace_events=1, ms_spent=1.0)
    assert not res.allowed
    assert "Provider calls limit exhausted" in res.skipped_reason

def test_budget_exhaustion_records_honest_reason():
    budget = PhaseBudget(
        phase_name="test_phase",
        max_ms_per_tick=50.0,
        max_entities_per_tick=5,
        max_provider_calls_per_tick=5,
        max_results_per_entity=3,
        max_trace_events_per_tick=10,
        max_memory_entries_per_entity=10
    )
    manager = PhaseBudgetManager(budget)
    res = manager.check_and_consume(entities=1, provider_calls=1, trace_events=11, ms_spent=1.0)
    assert not res.allowed
    assert "Trace events limit exhausted" in res.skipped_reason

def test_budget_skip_does_not_mutate_state():
    budget = PhaseBudget(
        phase_name="test_phase",
        max_ms_per_tick=50.0,
        max_entities_per_tick=5,
        max_provider_calls_per_tick=5,
        max_results_per_entity=3,
        max_trace_events_per_tick=10,
        max_memory_entries_per_entity=10
    )
    manager = PhaseBudgetManager(budget)
    manager.check_and_consume(entities=6, provider_calls=1, trace_events=1, ms_spent=1.0)
    # The counts should still be 0 if the call was rejected/not processed
    assert manager.current_entities == 0
