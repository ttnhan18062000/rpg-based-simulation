import pytest
from src.domains.commitment.abandonment import AbandonmentEvaluator

def test_abandonment_evaluator():
    # Valid abandonment: near death
    eval_res_valid = AbandonmentEvaluator.evaluate_abandonment(
        hp=5, max_hp=100, is_party_in_combat=True, is_greed_driven=False
    )
    assert eval_res_valid["is_betrayal"] is False
    assert eval_res_valid["penalty"] == 0.0

    # Bad abandonment: greed driven leaving party in combat
    eval_res_bad = AbandonmentEvaluator.evaluate_abandonment(
        hp=90, max_hp=100, is_party_in_combat=True, is_greed_driven=True
    )
    assert eval_res_bad["is_betrayal"] is True
    assert eval_res_bad["penalty"] > 0.5
