"""A range-bound subject judges its ways to eat inside its range (owner decision D57, the designer's range rule).

A subject with a leash above 0 (a leashed animal or monster) only targets a way within its leash radius of home; one with nothing
in range has no open step and stays honestly hungry (SURV-06). A subject with no range-bound home (people) has every way in range.
Staging asserts the verdicts, never a death count.
"""
from __future__ import annotations

from dataclasses import replace

import pytest

from src.ai.goals.base import NeedAccess, OpeningStepKind
from src.ai.goals.opening_steps import first_open_step
from src.ai.goals.scorers import EatScorer
from src.core.builder import V2EntityBuilder
from src.core.state import AuthoritativeState, BuildingState, ResourceNodeState
from src.engine.need_pull import HUNGER_LINE
from src.engine.rpg_depth import LeashService

HOME = (50.0, 50.0)
RADIUS = 10.0


@pytest.fixture(scope="module", autouse=True)
def _consumers():
    from src.content.repository import CatalogRepository
    from src.engine.behavior_consumers import configure_behavior_consumers, reset_behavior_consumers

    repo = CatalogRepository("data/content")
    repo.load_all()
    configure_behavior_consumers(repo)
    yield
    reset_behavior_consumers()


def _subject(leash=RADIUS):
    e = V2EntityBuilder(1).kind("goblin_warrior").location(*HOME).navigation(home_position=HOME, leash_radius=leash).build()
    return replace(e, biological=replace(e.biological, hunger=0.75 * HUNGER_LINE))


def _node(node_id, pos):
    return ResourceNodeState(id=node_id, kind="berry_thicket", position=pos, yields_item="wild_berries", remaining_charges=4,
                             max_charges=8, required_ticks=8, cooldown_remaining=0)


def _state(inn=None, nodes=()):
    buildings = {20003: BuildingState(id=20003, kind="inn", position=inn, functional=True)} if inn else {}
    return AuthoritativeState(tick=500, seed=1, world_time=1000, buildings=buildings, resource_nodes={n.id: n for n in nodes})


def test_the_range_is_the_manhattan_distance_from_home_within_the_leash_radius():
    e = _subject()
    assert LeashService.way_in_range(e, (55.0, 55.0))       # 10 away: on the line, inside
    assert not LeashService.way_in_range(e, (56.0, 55.0))   # 11 away: outside
    assert LeashService.way_in_range(e, None)


def test_a_subject_with_no_range_bound_home_has_every_way_in_range():
    assert LeashService.way_in_range(_subject(leash=0.0), (500.0, 500.0))


def test_a_range_bound_subject_does_not_target_an_inn_outside_its_range():
    score = EatScorer().score(_subject(), _state(inn=(90.0, 50.0)))
    assert score.target_pos is None and score.no_open_step and score.need_access is NeedAccess.NO_WAY_WITHIN_REACH


def test_a_person_targets_the_same_inn():
    person = _subject(leash=0.0)
    score = EatScorer().score(replace(person, inventory=replace(person.inventory, gold=5)), _state(inn=(90.0, 50.0)))
    assert score.target_pos == (90.0, 50.0) and not score.no_open_step


def test_a_range_bound_subject_forages_a_node_inside_its_range_and_not_a_nearer_one_outside():
    inside, outside = _node(10, (58.0, 50.0)), _node(11, (51.0, 62.0))  # 8 away; 13 away
    step = first_open_step(_subject(), _state(nodes=[outside, inside]))
    assert step.kind is OpeningStepKind.FORAGE and step.target_id == "10"
    assert first_open_step(_subject(), _state(nodes=[outside])) is None
