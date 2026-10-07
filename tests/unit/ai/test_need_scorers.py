"""TCK-20261007-BIOLOGICAL-NEEDS-ESCALATE-ABOVE-ORDINARY-GOALS-BEFORE-THE-CONSEQUENCE-LINE-SURV-07:
the hunger and fatigue goals carry the escalation, measured over the walk to the inn."""
from __future__ import annotations

from dataclasses import replace

import pytest

from src.ai.goals.need_pull import HUNGER_LINE, SLEEP_LINE
from src.ai.goals.scorers import EatScorer, SleepScorer
from src.core.builder import V2EntityBuilder
from src.core.state import AuthoritativeState, BuildingState

BLOCKER_CEILING = 103.8


@pytest.fixture(scope="module", autouse=True)
def _consumers():
    from src.content.repository import CatalogRepository
    from src.engine.behavior_consumers import configure_behavior_consumers, reset_behavior_consumers

    repo = CatalogRepository("data/content")
    repo.load_all()
    configure_behavior_consumers(repo)
    yield
    reset_behavior_consumers()


def _hero(**bio):
    hero = V2EntityBuilder(1).kind("hero").location(0.0, 0.0).build()
    return replace(hero, biological=replace(hero.biological, **bio))


def _state(inn):
    buildings = {20003: BuildingState(id=20003, kind="inn", position=inn, functional=True)} if inn else {}
    return AuthoritativeState(tick=500, seed=1, world_time=1000, buildings=buildings)


def test_a_mild_need_scores_its_raw_value():
    assert EatScorer().score(_hero(hunger=40.0), _state((10.0, 0.0))).utility == pytest.approx(40.0)
    assert SleepScorer().score(_hero(sleep_debt=30.0), _state((10.0, 0.0))).utility == pytest.approx(30.0)


def test_a_pressing_hunger_outranks_the_highest_ordinary_goal_before_the_line():
    hunger = 0.75 * HUNGER_LINE
    score = EatScorer().score(_hero(hunger=hunger), _state((5.0, 0.0)))
    assert hunger < HUNGER_LINE and score.utility > BLOCKER_CEILING
    assert score.target_pos == (5.0, 0.0)


def test_a_pressing_sleep_debt_outranks_the_highest_ordinary_goal_before_the_line():
    sleep_debt = 0.75 * SLEEP_LINE
    assert SleepScorer().score(_hero(sleep_debt=sleep_debt), _state((5.0, 0.0))).utility > BLOCKER_CEILING


def test_a_far_inn_escalates_the_pull_earlier_than_a_near_one():
    near = EatScorer().score(_hero(hunger=60.0), _state((2.0, 0.0))).utility
    far = EatScorer().score(_hero(hunger=60.0), _state((190.0, 0.0))).utility
    assert far > near


def test_without_an_inn_the_need_still_escalates_with_no_walk():
    hunger = 0.75 * HUNGER_LINE
    score = EatScorer().score(_hero(hunger=hunger), _state(None))
    assert score.target_pos is None and score.utility > BLOCKER_CEILING
