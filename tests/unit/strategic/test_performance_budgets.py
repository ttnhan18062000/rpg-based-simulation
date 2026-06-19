import pytest
from src.core.builder import V2EntityBuilder
from src.world.providers.requirements import Requirement, RequirementEvaluator, PerformanceBudgets
from src.world.providers.resources import ResourceOpportunityProvider
from src.world.providers.services import ServiceOpportunityProvider


def test_performance_budget_counters():
    """Verify that PerformanceBudgets increments counters on provider and requirement calls."""
    PerformanceBudgets.reset()
    assert PerformanceBudgets.provider_calls_total == 0
    assert PerformanceBudgets.requirements_evaluated_total == 0

    ent = (V2EntityBuilder(1)
        .kind("hero")
        .build())
    object.__setattr__(ent.navigation, "region_id", "hometown")

    # Call service provider (increments calls and opportunities returned count)
    opps = ServiceOpportunityProvider.get_opportunities(ent, None)
    assert PerformanceBudgets.provider_calls_total == 1
    assert PerformanceBudgets.provider_calls_by_kind["services"] == 1
    assert PerformanceBudgets.opportunities_returned_total == len(opps)

    # Call evaluator
    req = Requirement(kind="has_gold", quantity=10)
    res = RequirementEvaluator.evaluate(ent, None, req)
    assert PerformanceBudgets.requirements_evaluated_total == 1


def test_performance_budget_gate_enforcement():
    """Verify requirement evaluator and providers throttle queries past budget thresholds."""
    # 1. Test requirement evaluator throttling
    PerformanceBudgets.reset()
    PerformanceBudgets.requirements_evaluated_total = PerformanceBudgets.MAX_REQUIREMENTS_BUDGET + 1

    ent = (V2EntityBuilder(1)
        .kind("hero")
        .build())
    req = Requirement(kind="has_gold", quantity=10)
    res = RequirementEvaluator.evaluate(ent, None, req)
    
    assert not res.passed
    assert res.blocker_kind == "budget_exceeded"

    # 2. Test provider throttling
    PerformanceBudgets.reset()
    PerformanceBudgets.provider_calls_total = 501

    opps = ResourceOpportunityProvider.get_opportunities(ent, None)
    assert len(opps) == 0


def test_per_tick_reset_prevents_cap_accumulation():
    """Reset once per simulated tick: counter stays at per-tick count, never accumulates."""
    num_entities = 20

    for _tick in range(2):
        PerformanceBudgets.reset()
        for _ in range(num_entities):
            PerformanceBudgets.provider_calls_total += 1
        # End of each tick: count equals entities this tick only
        assert PerformanceBudgets.provider_calls_total == num_entities
        assert PerformanceBudgets.provider_calls_total <= 500
