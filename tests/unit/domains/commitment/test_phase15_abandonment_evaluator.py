import pytest
from src.domains.commitment.abandonment import (
    AbandonmentEvaluator,
    AbandonmentClassification,
    AbandonmentCategory,
)

def test_abandonment_evaluator():
    # Valid abandonment: near death
    eval_res_valid = AbandonmentEvaluator.evaluate_abandonment(
        hp=5, max_hp=100, is_party_in_combat=True, is_greed_driven=False
    )
    assert eval_res_valid.is_betrayal is False
    assert eval_res_valid.penalty == 0.0

    # Bad abandonment: greed driven leaving party in combat
    eval_res_bad = AbandonmentEvaluator.evaluate_abandonment(
        hp=90, max_hp=100, is_party_in_combat=True, is_greed_driven=True
    )
    assert eval_res_bad.is_betrayal is True
    assert eval_res_bad.penalty > 0.5


def test_evaluate_abandonment_returns_typed_classification():
    """Parity: evaluate_abandonment must return AbandonmentClassification for every branch."""
    # SURVIVAL branch
    result_survival = AbandonmentEvaluator.evaluate_abandonment(
        hp=10, max_hp=100, is_party_in_combat=True, is_greed_driven=False
    )
    assert isinstance(result_survival, AbandonmentClassification)
    assert result_survival.category == AbandonmentCategory.SURVIVAL
    assert result_survival.is_betrayal is False
    assert result_survival.penalty == 0.0

    # GREEDY_DESERTION branch
    result_greedy = AbandonmentEvaluator.evaluate_abandonment(
        hp=90, max_hp=100, is_party_in_combat=True, is_greed_driven=True
    )
    assert isinstance(result_greedy, AbandonmentClassification)
    assert result_greedy.category == AbandonmentCategory.GREEDY_DESERTION
    assert result_greedy.is_betrayal is True
    assert result_greedy.penalty == 0.8

    # VOLUNTARY_QUIT branch
    result_quit = AbandonmentEvaluator.evaluate_abandonment(
        hp=90, max_hp=100, is_party_in_combat=False, is_greed_driven=False
    )
    assert isinstance(result_quit, AbandonmentClassification)
    assert result_quit.category == AbandonmentCategory.VOLUNTARY_QUIT
    assert result_quit.is_betrayal is False
    assert result_quit.penalty == 0.2
