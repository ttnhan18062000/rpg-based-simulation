"""TCK-20261007-BIOLOGICAL-NEEDS-ESCALATE-ABOVE-ORDINARY-GOALS-BEFORE-THE-CONSEQUENCE-LINE-SURV-07: rest in place (SURV-06, SURV-07).

A fatigue project that cannot reach a bed before the sleep debt crosses 85% of its line, or that has no bed to walk to, sleeps
where it stands unless a present threat holds (AGENCY-07's predicate); otherwise the walk to the inn continues as before.
"""
from __future__ import annotations

from dataclasses import replace

import pytest

from src.core.builder import V2EntityBuilder
from src.core.enums import Faction
from src.core.state import AuthoritativeState, BuildingState
from src.core.strategic import GoalKind, ObjectiveKind, ObjectiveState, ObjectiveStatus, ProjectState, ProjectStatus
from src.engine.behavior_consumers import configure_behavior_consumers, reset_behavior_consumers
from src.engine.tactical import TacticalDecisionSystem
from src.engine.tactical_rest import rest_in_place_update

INN_ID = 20003


@pytest.fixture(scope="module", autouse=True)
def _consumers():
    from src.content.repository import CatalogRepository

    repo = CatalogRepository("data/content")
    repo.load_all()
    configure_behavior_consumers(repo)
    yield
    reset_behavior_consumers()


def _hero(pos=(0, 0), sleep_debt=50.0, target="20003", with_project=True, project_kind=GoalKind.FATIGUE):
    hero = (V2EntityBuilder(1).kind("hero").location(float(pos[0]), float(pos[1])).identity(faction=Faction.HERO_GUILD)
            .combat(hp=100, max_hp=100, alive=True, readiness=100.0).lifecycle(active=True).build())
    hero = replace(hero, biological=replace(hero.biological, sleep_debt=sleep_debt))
    if not with_project:
        return hero
    objective = ObjectiveState(id="o1", kind=ObjectiveKind.REACH_LOCATION, target=target, status=ObjectiveStatus.ACTIVE)
    project = ProjectState(id="p1", kind=project_kind, status=ProjectStatus.ACTIVE, objectives=[objective], active_objective_id="o1")
    return replace(hero, strategic=replace(hero.strategic, projects={"p1": project}, current_project_id="p1", current_objective_id="o1"))


def _state(*entities, inn=(200.0, 0.0)):
    buildings = {INN_ID: BuildingState(id=INN_ID, kind="inn", position=inn, functional=True)}
    return AuthoritativeState(tick=500, seed=1, entities={e.id: e for e in entities}, buildings=buildings)


def _monster(pos, targeting=None):
    m = (V2EntityBuilder(2).kind("monster").location(float(pos[0]), float(pos[1])).identity(faction=Faction.MONSTER_HORDE)
         .combat(hp=100, max_hp=100, alive=True, readiness=100.0).lifecycle(active=True).build())
    if targeting is not None:
        m = replace(m, task=replace(m.task, payload={"target_id": targeting}))
    return m


def _action(update):
    return (update.task.payload_set or {}).get("action") if update is not None and update.task is not None else None


def test_a_bed_too_far_to_reach_in_time_means_resting_where_it_stands():
    hero = _hero(sleep_debt=75.0)  # inn 200 tiles away: (75 + 0.05 * 200) / 98 = 0.867, past 0.85
    update = rest_in_place_update(_state(hero), hero, [])
    assert _action(update) == "SLEEP" and update.task.payload_set["reason"] == "REST_IN_PLACE"
    assert update.navigation.target_clear


def test_a_bed_reachable_in_time_keeps_the_walk_going():
    hero = _hero(sleep_debt=50.0)  # (50 + 10) / 98 = 0.61
    assert rest_in_place_update(_state(hero), hero, []) is None


def test_a_near_bed_can_still_be_too_late_for_a_very_tired_subject():
    hero = _hero(pos=(190, 0), sleep_debt=84.0)  # inn 10 tiles away: (84 + 0.5) / 98 = 0.862
    assert _action(rest_in_place_update(_state(hero), hero, [])) == "SLEEP"


def test_at_the_bed_the_building_branch_decides_not_this_one():
    hero = _hero(pos=(199, 0), sleep_debt=90.0)
    assert rest_in_place_update(_state(hero), hero, []) is None


def test_a_fatigue_project_that_names_no_place_rests_in_place():
    hero = _hero(sleep_debt=30.0, target="not_a_building")
    assert _action(rest_in_place_update(_state(hero), hero, [])) == "SLEEP"


def test_a_present_threat_means_no_rest():
    hero = _hero(sleep_debt=90.0)
    assert rest_in_place_update(_state(hero), hero, [_monster((1, 0))]) is None  # adjacent
    assert rest_in_place_update(_state(hero), hero, [_monster((9, 0), targeting=1)]) is None  # targeting it


def test_a_hostile_merely_seen_is_not_a_threat_so_the_subject_still_rests():
    hero = _hero(sleep_debt=90.0)
    assert _action(rest_in_place_update(_state(hero), hero, [_monster((12, 0))])) == "SLEEP"


def test_no_fatigue_project_or_little_sleep_debt_means_no_rest():
    assert rest_in_place_update(_state(_hero(with_project=False, sleep_debt=90.0)), _hero(with_project=False, sleep_debt=90.0), []) is None
    assert rest_in_place_update(_state(_hero(sleep_debt=10.0)), _hero(sleep_debt=10.0), []) is None
    other = _hero(sleep_debt=90.0, project_kind=GoalKind.HARVESTING)
    assert rest_in_place_update(_state(other), other, []) is None


def test_the_tactical_pass_dispatches_the_rest():
    hero = _hero(sleep_debt=80.0)
    update = TacticalDecisionSystem.evaluate_entity_intent(_state(hero), hero)
    assert _action(update) == "SLEEP" and update.task.payload_set["reason"] == "REST_IN_PLACE"
