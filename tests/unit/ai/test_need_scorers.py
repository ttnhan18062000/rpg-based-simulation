"""TCK-20261007-BIOLOGICAL-NEEDS-ESCALATE-ABOVE-ORDINARY-GOALS-BEFORE-THE-CONSEQUENCE-LINE-SURV-07:
the hunger and fatigue goals carry the escalation, measured over the walk to the inn."""
from __future__ import annotations

from dataclasses import replace

import pytest

from src.ai.goals.base import NeedAccess
from src.engine.need_pull import HUNGER_LINE, SLEEP_LINE
from src.ai.goals.scorers import EatScorer, SleepScorer
from src.core.builder import V2EntityBuilder
from src.core.movement_modes import MovementMode
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


def test_an_inn_within_reach_is_a_way_to_eat_only_for_a_subject_that_holds_the_price():
    """Decision 73: nothing is free, so an inn is an open way only for a subject holding EAT_PRICE_GOLD."""
    from src.engine.service_prices import EAT_PRICE_GOLD
    hunger = 0.75 * HUNGER_LINE
    broke = EatScorer().score(_hero(gold=EAT_PRICE_GOLD - 1, hunger=hunger), _state((5.0, 0.0)))
    assert broke.target_pos is None and broke.need_access is NeedAccess.NO_AFFORDABLE_WAY
    paying = EatScorer().score(_hero(gold=EAT_PRICE_GOLD, hunger=hunger), _state((5.0, 0.0)))
    assert paying.target_pos == (5.0, 0.0) and paying.utility > BLOCKER_CEILING and paying.need_access is NeedAccess.WAY_WITHIN_REACH


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


def _acting(state, task):
    """`state` with the hostile (entity 2) given `task`."""
    monster = replace(state.entities[2], task=task)
    object.__setattr__(state, "entities", {**state.entities, 2: monster})
    return state


def test_a_hostile_acting_on_the_subject_takes_the_escalation_away_so_a_need_never_outbids_combat():
    """Memo row 88: a hostile holds back an escalated need by an act (its current task attacks or pursues the subject, or it hit the subject), not by standing adjacent."""
    from src.core.state import TaskComponent

    hunger = 0.75 * HUNGER_LINE
    hero, near = _with_hostile(_hero(hunger=hunger), (1.0, 0.0))
    attacking = _acting(near, TaskComponent(work_kind="ENTITY_ACT", payload={"action": "ATTACK", "target_id": hero.id}))
    assert EatScorer().score(hero, attacking).utility == pytest.approx(hunger)  # a targeting attacker: the escalation gives way
    hero, near = _with_hostile(_hero(hunger=hunger), (1.0, 0.0))
    pursuing = _acting(near, TaskComponent(work_kind="ENTITY_MOVE", payload={"target_position": (0.0, 0.0), "target_id": hero.id}))
    object.__setattr__(pursuing, "entities", {**pursuing.entities, 2: replace(pursuing.entities[2], navigation=replace(pursuing.entities[2].navigation, movement_mode=MovementMode.PURSUE))})
    assert EatScorer().score(hero, pursuing).utility == pytest.approx(hunger)
    hero, far = _with_hostile(_hero(hunger=hunger), (9.0, 0.0))   # perceived but not acting
    assert EatScorer().score(hero, far).utility > BLOCKER_CEILING


def test_a_hostile_merely_adjacent_does_not_take_the_escalation_away():
    """Old -> new: an adjacent hostile with no attack or pursuit task used to count as a present threat and drop the escalation to the raw hunger."""
    hunger = 0.75 * HUNGER_LINE
    hero, near = _with_hostile(_hero(hunger=hunger), (1.0, 0.0))
    assert EatScorer().score(hero, near).utility > BLOCKER_CEILING


def test_a_hit_within_the_window_is_an_act_and_a_stale_or_foreign_hit_is_not():
    from src.engine.scheduler import NEED_WAKE_CADENCE

    hunger = 0.75 * HUNGER_LINE

    def scene(last_attacker, hit_tick):
        hero, state = _with_hostile(_hero(hunger=hunger), (1.0, 0.0))
        hero = replace(hero, combat=replace(hero.combat, last_attacker_id=last_attacker, last_hit_tick=hit_tick))
        object.__setattr__(state, "entities", {**state.entities, 1: hero})
        return hero, state

    hero, state = scene(2, 500 - NEED_WAKE_CADENCE)
    assert EatScorer().score(hero, state).utility == pytest.approx(hunger)  # the hostile hit it exactly one cadence ago
    hero, state = scene(2, 500 - NEED_WAKE_CADENCE - 1)
    assert EatScorer().score(hero, state).utility > BLOCKER_CEILING  # one tick past the window
    hero, state = scene(99, 500)
    assert EatScorer().score(hero, state).utility > BLOCKER_CEILING  # the last hit was another body's


def test_a_wound_alone_with_no_hostile_in_view_is_not_a_threat_to_the_need():
    hunger = 0.75 * HUNGER_LINE
    hero = _hero(hunger=hunger)
    hero = replace(hero, combat=replace(hero.combat, hp=30, max_hp=100))
    assert EatScorer().score(hero, _state((5.0, 0.0))).utility > BLOCKER_CEILING
