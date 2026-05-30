import pytest
from src.domains.emotion.opportunity_cost import OpportunityCostEvaluator

def test_opportunity_cost_evaluator():
    # Selling highly needed materials has high opportunity cost
    cost_high = OpportunityCostEvaluator.evaluate_cost(
        action_kind="sell_material",
        is_needed_for_upgrade=True,
        has_alternative=False
    )
    assert cost_high > 0.5
    
    # Selling extra materials has low opportunity cost
    cost_low = OpportunityCostEvaluator.evaluate_cost(
        action_kind="sell_material",
        is_needed_for_upgrade=False,
        has_alternative=True
    )
    assert cost_low < 0.2
