"""The hunger pull aims at the nearest open way whose route is not threatened, and holds its choice until reached or threatened (SURV-07, memo row 84).

Pure reads: the perceived hostiles and the open ways are supplied, so each case isolates one clause of the rule.
"""
from __future__ import annotations

from types import SimpleNamespace

import pytest

import src.ai.goals.safe_route as safe_route
from src.ai.goals.safe_route import OpenWay
from src.core.strategic import GoalKind, ObjectiveKind, ObjectiveState, ObjectiveStatus, ProjectState, ProjectStatus

INN = OpenWay("20003", (23.0, 39.0))
FORAGE = OpenWay("10005", (72.0, 20.0))
CARCASS = OpenWay("1000003", (46.0, 40.0))


def _subject(x=54.0, y=40.0):
    return SimpleNamespace(navigation=SimpleNamespace(position=(x, y)))


def _hostile(x, y, reach=1):
    return SimpleNamespace(navigation=SimpleNamespace(position=(x, y)), combat=SimpleNamespace(range=reach))


def _hunger_project(way: OpenWay) -> ProjectState:
    objective = ObjectiveState(id=f"hunger_{way.target_id}", kind=ObjectiveKind.REACH_LOCATION, target=way.target_id, target_position=way.target_pos, status=ObjectiveStatus.ACTIVE)
    return ProjectState(id="proj_hunger_633", kind=GoalKind.HUNGER, status=ProjectStatus.ACTIVE, objectives=[objective], active_objective_id=objective.id, lock_until_tick=0, created_tick=633, score=73.0)


@pytest.fixture
def world(monkeypatch):
    """Patch what the subject perceives and which ways are open; returns the setter."""
    state = {"hostiles": [], "ways": []}
    monkeypatch.setattr(safe_route, "perceived_hostiles", lambda entity, st: list(state["hostiles"]))
    monkeypatch.setattr(safe_route, "open_ways", lambda entity, st: list(state["ways"]))
    return state


def _target(project: ProjectState):
    return next(o for o in project.objectives if o.id == project.active_objective_id).target_position


def test_a_threatened_hunger_objective_is_retargeted_to_the_nearest_open_way_with_a_clear_route(world):
    world["hostiles"] = [_hostile(45.0, 40.0), _hostile(46.0, 41.0)]  # townsfolk on the walk west to the inn
    world["ways"] = [INN, FORAGE, CARCASS]
    project = _hunger_project(INN)
    changed = safe_route.retarget_if_threatened(_subject(), None, project)
    assert changed is not None and changed.id == project.id, "the same project is retargeted, not replaced"
    assert _target(changed) == FORAGE.target_pos
    assert len(changed.objectives) == 1 and changed.active_objective_id == "hunger_10005"


def test_a_re_chosen_objective_is_kept_when_the_old_threat_leaves_view_and_never_flips_back(world):
    world["hostiles"] = [_hostile(45.0, 40.0)]
    world["ways"] = [INN, FORAGE]
    chosen = safe_route.retarget_if_threatened(_subject(), None, _hunger_project(INN))
    assert _target(chosen) == FORAGE.target_pos
    world["hostiles"] = []  # the old threat is out of view: the inn looks clear again
    assert safe_route.retarget_if_threatened(_subject(62.0, 38.0), None, chosen) is None
    world["hostiles"] = [_hostile(45.0, 40.0)]  # and when it is back in view, it is still not on the way to the forage node
    assert safe_route.retarget_if_threatened(_subject(62.0, 38.0), None, chosen) is None


def test_a_re_chosen_objective_that_is_itself_threatened_is_re_chosen_again(world):
    world["ways"] = [INN, FORAGE, CARCASS]
    world["hostiles"] = [_hostile(45.0, 40.0)]
    chosen = safe_route.retarget_if_threatened(_subject(), None, _hunger_project(INN))
    assert _target(chosen) == FORAGE.target_pos
    world["hostiles"] = [_hostile(66.0, 28.0)]  # now the forage walk is the threatened one; the inn walk is clear
    again = safe_route.retarget_if_threatened(_subject(), None, chosen)
    assert again is not None and _target(again) in (INN.target_pos, CARCASS.target_pos)


def test_when_every_open_way_is_threatened_the_objective_stays_where_it_is(world):
    world["hostiles"] = [_hostile(45.0, 40.0), _hostile(66.0, 28.0)]
    world["ways"] = [INN, FORAGE]
    project = _hunger_project(INN)
    assert safe_route.retarget_if_threatened(_subject(), None, project) is None


def test_an_unthreatened_objective_is_never_re_chosen(world):
    world["hostiles"] = [_hostile(40.0, 10.0)]  # perceived, but nowhere near the walk to the inn
    world["ways"] = [INN, FORAGE]
    assert safe_route.retarget_if_threatened(_subject(), None, _hunger_project(INN)) is None
    world["hostiles"] = []
    assert safe_route.retarget_if_threatened(_subject(), None, _hunger_project(INN)) is None


def test_a_hostile_beside_the_route_threatens_it_and_one_off_to_the_side_does_not():
    """Beside = within the hostile's OWN attack reach plus one step of the straight line: melee (reach 1) counts at 2 tiles, a ranged hostile wider."""
    start, end = (54.0, 40.0), (23.0, 39.0)  # the line runs at y of about 39.7 where x is 44
    assert safe_route.route_is_threatened(start, end, [_hostile(44.0, 40.0)])                      # on the walk
    assert safe_route.route_is_threatened(start, end, [_hostile(44.0, 41.0)])                      # melee: 1.3 tiles off the line (inside reach 1 + step 1)
    assert not safe_route.route_is_threatened(start, end, [_hostile(44.0, 42.0)])                  # melee: 2.3 tiles off is out of its reach
    assert not safe_route.route_is_threatened(start, end, [_hostile(44.0, 46.0)])
    assert safe_route.route_is_threatened(start, end, [_hostile(44.0, 45.0, reach=5)])             # ranged (reach 5): 5.3 tiles off still strikes
    assert not safe_route.route_is_threatened(start, end, [_hostile(44.0, 46.0, reach=5)])         # but not 6.3
    assert not safe_route.route_is_threatened(start, end, [])
