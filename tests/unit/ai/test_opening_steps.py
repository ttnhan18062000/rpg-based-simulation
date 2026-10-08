"""TCK-20261007-A-NEED-WITH-NO-OPEN-WAY-PULLS-TOWARD-THE-STEP-THAT-OPENS-ONE-SURV-07-AMENDMENT (decision 27):
when no way to eat is open, the hungry subject's pull goes to the step that opens one, and a subject with no step stays honestly hungry."""
from __future__ import annotations

from dataclasses import replace

import pytest

from src.ai.goals.base import NeedAccess, OpeningStepKind
from src.engine.need_pull import HUNGER_LINE
from src.ai.goals.opening_steps import first_open_step, opening_steps
from src.ai.goals.scorers import EatScorer
from src.core.builder import V2EntityBuilder
from src.core.state import AuthoritativeState, BuildingState, ItemStack, ResourceNodeState

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


def _hero(gold=0, hunger=0.75 * HUNGER_LINE, items=()):
    hero = V2EntityBuilder(1).kind("hero").location(0.0, 0.0).build()
    hero = replace(hero, biological=replace(hero.biological, hunger=hunger))
    return replace(hero, inventory=replace(hero.inventory, gold=gold, items=list(items)))


def _node(node_id, pos, item="wild_berries", charges=4, cooldown=0):
    return ResourceNodeState(
        id=node_id, kind="berry_thicket", position=pos, yields_item=item, remaining_charges=charges, max_charges=8,
        required_ticks=8, cooldown_remaining=cooldown)


def _state(nodes=(), inn=(5.0, 0.0)):
    buildings = {20003: BuildingState(id=20003, kind="inn", position=inn, functional=True)} if inn else {}
    return AuthoritativeState(tick=500, seed=1, world_time=1000, buildings=buildings, resource_nodes={n.id: n for n in nodes})


def test_the_corpus_food_item_is_declared_edible_and_herb_is_not():
    from src.core.items import food_hunger_recovery
    assert food_hunger_recovery("wild_berries") > 0.0
    assert food_hunger_recovery("herb") == 0.0 and food_hunger_recovery("healing_flower") == 0.0


def test_forage_picks_the_nearest_food_node_with_charges():
    near, far = _node(10, (3.0, 0.0)), _node(11, (9.0, 0.0))
    step = first_open_step(_hero(), _state([far, near]))
    assert step.kind is OpeningStepKind.FORAGE and step.target_id == "10" and step.target_pos == (3.0, 0.0)


@pytest.mark.parametrize("node", [
    _node(10, (3.0, 0.0), charges=0), _node(10, (3.0, 0.0), cooldown=5), _node(10, (3.0, 0.0), item="herb"),
], ids=["depleted", "on_cooldown", "yields_inedible_item"])
def test_forage_is_not_open_without_a_usable_food_node(node):
    forage = opening_steps(_hero(), _state([node]))[0]
    assert forage.kind is OpeningStepKind.FORAGE and not forage.available and forage.reason


def test_forage_is_not_open_without_room_to_carry():
    hero = _hero()
    full = replace(hero, inventory=replace(hero.inventory, max_slots=1, items=[ItemStack("wood", 1)]))
    forage = opening_steps(full, _state([_node(10, (3.0, 0.0))]))[0]
    assert not forage.available and "room" in forage.reason


def test_the_steps_without_content_report_unavailable_with_a_reason():
    steps = {s.kind: s for s in opening_steps(_hero(), _state([_node(10, (3.0, 0.0))]))}
    for kind in (OpeningStepKind.EARN_THEN_BUY, OpeningStepKind.ASK):
        assert not steps[kind].available and steps[kind].reason


def test_a_subject_with_no_inn_within_reach_is_pulled_to_the_food_node_above_the_ordinary_ceiling():
    score = EatScorer().score(_hero(gold=0), _state([_node(10, (3.0, 0.0))], inn=None))
    assert score.need_access is NeedAccess.NO_WAY_WITHIN_REACH and score.opening_step is OpeningStepKind.FORAGE
    assert score.target_id == "10" and score.target_pos == (3.0, 0.0) and not score.no_open_step
    assert score.utility > BLOCKER_CEILING


def test_a_subject_with_no_inn_and_a_food_node_forages_too():
    score = EatScorer().score(_hero(gold=50), _state([_node(10, (3.0, 0.0))], inn=None))
    assert score.need_access is NeedAccess.NO_WAY_WITHIN_REACH and score.opening_step is OpeningStepKind.FORAGE


def test_with_free_meals_on_a_subject_with_an_inn_within_reach_goes_to_the_inn_not_the_node_whatever_it_holds():
    score = EatScorer().score(_hero(gold=0), _state([_node(10, (3.0, 0.0))]))
    assert score.need_access is NeedAccess.WAY_WITHIN_REACH and score.target_pos == (5.0, 0.0) and score.opening_step is None


def test_no_step_the_subject_can_take_is_a_typed_state_and_keeps_the_raw_hunger():
    hunger = 0.75 * HUNGER_LINE
    score = EatScorer().score(_hero(gold=0, hunger=hunger), _state([_node(10, (3.0, 0.0), charges=0)], inn=None))
    assert score.no_open_step and score.opening_step is None and score.target_id is None
    assert score.need_access is NeedAccess.NO_WAY_WITHIN_REACH and score.utility == pytest.approx(hunger)


def test_a_present_threat_outranks_the_pull_to_the_node(monkeypatch):
    import src.ai.goals.scorers as scorers
    monkeypatch.setattr(scorers, "present_threat_to", lambda entity, state: True)
    hunger = 0.75 * HUNGER_LINE
    score = EatScorer().score(_hero(gold=0, hunger=hunger), _state([_node(10, (3.0, 0.0))], inn=None))
    assert score.opening_step is OpeningStepKind.FORAGE and score.utility == pytest.approx(hunger)
