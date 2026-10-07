"""TCK-20261007-BIOLOGICAL-NEEDS-ESCALATE-ABOVE-ORDINARY-GOALS-BEFORE-THE-CONSEQUENCE-LINE-SURV-07:
the hunger and fatigue goals carry the escalation, measured over the walk to the inn."""
from __future__ import annotations

from dataclasses import replace

import pytest

from src.ai.goals.base import NeedAccess
from src.engine.need_pull import HUNGER_LINE, SLEEP_LINE
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


def _hero(gold=50, **bio):
    hero = V2EntityBuilder(1).kind("hero").location(0.0, 0.0).build()
    hero = replace(hero, biological=replace(hero.biological, **bio))
    return replace(hero, inventory=replace(hero.inventory, gold=gold))


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


def test_without_an_inn_there_is_no_way_to_point_at_so_no_escalation_and_no_target():
    hunger = 0.75 * HUNGER_LINE
    score = EatScorer().score(_hero(hunger=hunger), _state(None))
    assert score.target_pos is None and score.utility == pytest.approx(hunger)
    assert score.need_access is NeedAccess.NO_WAY_WITHIN_REACH


def test_a_meal_is_a_way_to_meet_hunger_only_for_a_subject_that_can_pay():
    from src.engine.service_prices import EAT_PRICE_GOLD

    hunger = 0.75 * HUNGER_LINE
    poor = EatScorer().score(_hero(gold=EAT_PRICE_GOLD - 1, hunger=hunger), _state((5.0, 0.0)))
    assert poor.target_pos is None and poor.utility == pytest.approx(hunger)  # the need stays, with no way to point at
    assert poor.need_access is NeedAccess.NO_AFFORDABLE_WAY
    can_pay = EatScorer().score(_hero(gold=EAT_PRICE_GOLD, hunger=hunger), _state((5.0, 0.0)))
    assert can_pay.target_pos == (5.0, 0.0) and can_pay.utility > BLOCKER_CEILING
    assert can_pay.need_access is NeedAccess.WAY_WITHIN_REACH


def test_the_scorer_and_the_inn_charge_the_same_price():
    import inspect
    import src.engine.town_resolution as tr
    from src.engine.service_prices import EAT_PRICE_GOLD

    assert tr.EAT_PRICE_GOLD == EAT_PRICE_GOLD and "gold_delta=-EAT_PRICE_GOLD" in inspect.getsource(tr)


def _with_hostile(hero, at, hp=100):
    from src.core.enums import Faction

    monster = (V2EntityBuilder(2).kind("monster").location(*at).identity(faction=Faction.MONSTER_HORDE)
               .combat(hp=hp, max_hp=100, alive=True, readiness=100.0).lifecycle(active=True).build())
    hero = replace(hero, identity=replace(hero.identity, faction=Faction.HERO_GUILD))
    state = AuthoritativeState(
        tick=500, seed=1, world_time=1000, entities={1: hero, 2: monster},
        buildings={20003: BuildingState(id=20003, kind="inn", position=(5.0, 0.0), functional=True)},
    )
    return hero, state


def test_a_present_threat_takes_the_escalation_away_so_a_need_never_outbids_combat():
    hunger = 0.75 * HUNGER_LINE
    hero, near = _with_hostile(_hero(hunger=hunger), (1.0, 0.0))  # adjacent: a present threat
    assert EatScorer().score(hero, near).utility == pytest.approx(hunger)
    hero, far = _with_hostile(_hero(hunger=hunger), (9.0, 0.0))   # perceived but not a present threat
    assert EatScorer().score(hero, far).utility > BLOCKER_CEILING


def test_a_wound_alone_with_no_hostile_in_view_is_not_a_threat_to_the_need():
    hunger = 0.75 * HUNGER_LINE
    hero = _hero(hunger=hunger)
    hero = replace(hero, combat=replace(hero.combat, hp=30, max_hp=100))
    assert EatScorer().score(hero, _state((5.0, 0.0))).utility > BLOCKER_CEILING
