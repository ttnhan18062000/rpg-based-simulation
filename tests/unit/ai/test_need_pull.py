"""TCK-20261007-BIOLOGICAL-NEEDS-ESCALATE-ABOVE-ORDINARY-GOALS-BEFORE-THE-CONSEQUENCE-LINE-SURV-07: the SURV-07 pull curve.

The ordinary-goal ceilings below are the measured maxima of the corpus (crowded_frontier and frontier_living_world, seed 42,
1500 ticks): region_stabilization 100.0 (flat), resolve_blocker 103.8, harvesting 95, town_return 134.8.
"""
from __future__ import annotations

import pytest

from src.ai.goals.need_pull import (
    ESCALATION_AMPLITUDE, ESCALATION_FULL, ESCALATION_ONSET, HUNGER_LINE, SLEEP_LINE,
    arrival_fraction, hunger_pull, need_pull, sleep_pull, smoothstep,
)

STABILIZE_CEILING = 100.0
BLOCKER_CEILING = 103.8
TOWN_RETURN_CEILING = 134.8


def test_smoothstep_is_zero_below_one_above_and_half_at_the_middle():
    assert smoothstep(0.6, 0.85, 0.5) == 0.0
    assert smoothstep(0.6, 0.85, 0.9) == 1.0
    assert smoothstep(0.6, 0.85, 0.725) == pytest.approx(0.5)


def test_below_the_onset_the_pull_is_exactly_the_raw_utility():
    for hunger in (0.0, 30.0, 0.59 * HUNGER_LINE):
        assert hunger_pull(hunger, hunger, 0.0) == hunger


def test_the_pull_never_decreases_as_the_need_grows():
    pulls = [hunger_pull(h, h, 0.0) for h in range(0, 100)]
    assert pulls == sorted(pulls)


def test_a_pressing_need_outranks_stabilization_and_blocker_goals_before_its_line():
    # about 75% of the line: above the highest ordinary goal, with a quarter of the line still to go
    hunger = 0.75 * HUNGER_LINE
    assert hunger_pull(hunger, hunger, 0.0) > BLOCKER_CEILING
    assert hunger < HUNGER_LINE
    sleep_debt = 0.75 * SLEEP_LINE
    assert sleep_pull(sleep_debt, sleep_debt, 0.0) > BLOCKER_CEILING


def test_a_need_near_its_line_outranks_even_the_highest_corpus_goal_below_combat():
    hunger = 0.85 * HUNGER_LINE
    assert hunger_pull(hunger, hunger, 0.0) > TOWN_RETURN_CEILING
    assert ESCALATION_AMPLITUDE == 60.0 and ESCALATION_FULL == 0.85 and ESCALATION_ONSET == 0.6


def test_a_mild_need_is_still_one_wish_among_many():
    assert hunger_pull(40.0, 40.0, 0.0) < STABILIZE_CEILING
    assert sleep_pull(30.0, 30.0, 0.0) < STABILIZE_CEILING


def test_a_longer_walk_escalates_the_pull_earlier():
    near = hunger_pull(60.0, 60.0, 0.0)
    far = hunger_pull(60.0, 60.0, 190.0)
    assert far > near
    assert arrival_fraction(60.0, 0.1, 190.0, HUNGER_LINE) == pytest.approx((60.0 + 19.0) / HUNGER_LINE)


def test_the_helper_adds_the_escalation_on_top_of_whatever_raw_utility_it_is_given():
    assert need_pull(10.0, 80.0, 0.1, 0.0, HUNGER_LINE) - need_pull(0.0, 80.0, 0.1, 0.0, HUNGER_LINE) == pytest.approx(10.0)
