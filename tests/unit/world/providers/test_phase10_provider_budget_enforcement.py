# TDD tests for ProviderBudgetEnforcement
import pytest
from src.domains.optimization.provider_enforcement import ProviderBudgetEnforcement, ScopedContext

def test_provider_requires_scoped_context():
    pe = ProviderBudgetEnforcement(max_calls=5, max_results=3)
    ctx = ScopedContext(entity_id=1, tick=10, region_id="forest")
    assert ctx.entity_id == 1
    assert ctx.tick == 10

def test_provider_caps_results():
    pe = ProviderBudgetEnforcement(max_calls=5, max_results=2)
    ctx = ScopedContext(entity_id=1, tick=10, region_id="forest")
    # Ask provider to enforce limits on raw list
    raw_results = ["ore_1", "ore_2", "ore_3"]
    limited = pe.enforce_results(ctx, raw_results)
    assert len(limited) == 2
    assert limited == ["ore_1", "ore_2"]

def test_provider_budget_exhaustion_returns_partial_result_with_reason():
    pe = ProviderBudgetEnforcement(max_calls=1, max_results=5)
    ctx = ScopedContext(entity_id=1, tick=10, region_id="forest")
    
    # First call is fine
    res1, reason1 = pe.execute_call(ctx, "resource_provider", lambda: ["gold", "iron"])
    assert len(res1) == 2
    assert reason1 is None
    
    # Second call should exceed and return partial/empty with reason
    res2, reason2 = pe.execute_call(ctx, "resource_provider", lambda: ["wood"])
    assert len(res2) == 0
    assert "Provider budget exhausted" in reason2

def test_global_scan_attempt_is_rejected_without_debug_flag():
    pe = ProviderBudgetEnforcement(max_calls=5, max_results=5, debug_global_scan=False)
    ctx = ScopedContext(entity_id=None, tick=10, region_id=None) # Global scan attempt
    
    res, reason = pe.execute_call(ctx, "resource_provider", lambda: ["everything"])
    assert len(res) == 0
    assert "Global scan attempt rejected" in reason

def test_provider_output_order_is_deterministic():
    pe = ProviderBudgetEnforcement(max_calls=5, max_results=5)
    ctx = ScopedContext(entity_id=1, tick=10, region_id="forest")
    
    raw = ["cherry", "banana", "apple"]
    res = pe.enforce_results(ctx, raw)
    # Output must be sorted/deterministic
    assert res == ["apple", "banana", "cherry"]
