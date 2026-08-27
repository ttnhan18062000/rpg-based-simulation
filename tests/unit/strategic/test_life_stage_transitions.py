"""
TCK-20260824-LIFE-STAGE-TRANSITIONS: pure-function coverage for
LifeStageService.get_stage_for_age() and LifeStageService.is_forward_transition().
"""
import pytest
from src.ai.life_stage import LifeStageService
from src.core.state import LifeStage
from src.domains.demographics.cohort import get_age_bracket


def test_get_stage_for_age_boundaries():
    assert LifeStageService.get_stage_for_age(0) == LifeStage.CHILD
    assert LifeStageService.get_stage_for_age(2999) == LifeStage.CHILD
    assert LifeStageService.get_stage_for_age(3000) == LifeStage.ADULT
    assert LifeStageService.get_stage_for_age(6999) == LifeStage.ADULT
    assert LifeStageService.get_stage_for_age(7000) == LifeStage.ELDER
    assert LifeStageService.get_stage_for_age(9000) == LifeStage.ELDER


def test_is_forward_transition_promotes_only_forward():
    assert LifeStageService.is_forward_transition(LifeStage.CHILD, LifeStage.ADULT) is True
    assert LifeStageService.is_forward_transition(LifeStage.ADULT, LifeStage.ELDER) is True
    assert LifeStageService.is_forward_transition(LifeStage.CHILD, LifeStage.ELDER) is True


def test_is_forward_transition_rejects_same_or_backward():
    assert LifeStageService.is_forward_transition(LifeStage.ADULT, LifeStage.ADULT) is False
    assert LifeStageService.is_forward_transition(LifeStage.ELDER, LifeStage.ADULT) is False
    assert LifeStageService.is_forward_transition(LifeStage.ELDER, LifeStage.CHILD) is False
    assert LifeStageService.is_forward_transition(LifeStage.ADULT, LifeStage.CHILD) is False


def test_is_forward_transition_elder_never_regresses_from_recomputed_lower_candidate():
    """An already-ELDER entity fed a re-computed CHILD or ADULT candidate must NOT regress --
    the forward-only monotonicity guard this ticket's trigger depends on."""
    assert LifeStageService.is_forward_transition(LifeStage.ELDER, LifeStage.CHILD) is False
    assert LifeStageService.is_forward_transition(LifeStage.ELDER, LifeStage.ADULT) is False


@pytest.mark.parametrize("age_ticks", [0, 2999, 3000, 6999, 7000, 9000])
def test_get_stage_for_age_matches_get_age_bracket_numeric_boundaries(age_ticks):
    """Regression guard for Design Decision 1 (investigation.md): get_stage_for_age()'s numeric
    boundaries are intentionally duplicated from get_age_bracket() (src/domains/demographics/
    cohort.py, WORLD-DEMO-003) rather than imported. This compares where the transition points
    fall, not the string/enum vocabularies themselves, which are deliberately different."""
    stage = LifeStageService.get_stage_for_age(age_ticks)
    bracket = get_age_bracket(age_ticks)

    stage_to_bracket = {
        LifeStage.CHILD: "young",
        LifeStage.ADULT: "adult",
        LifeStage.ELDER: "elder",
    }
    assert stage_to_bracket[stage] == bracket
