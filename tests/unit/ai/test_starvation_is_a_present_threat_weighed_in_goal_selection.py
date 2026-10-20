"""SURV-07 amendment (memo row 83): once hunger is past its consequence line and taking health, starvation is itself a present threat to life.

Goal selection weighs it against the appraised threat (flight against food) instead of dropping the hunger escalation while another threat holds;
neither wins by default, and there is no timer. Below the line the old threat gate stands. The tactical order (engagement and panic before any survival
branch) is unchanged, so a hunter that is really attacking the subject is still dealt with first.
"""
from __future__ import annotations

from dataclasses import replace

import pytest

from src.ai.goals.scorers import EatScorer
from src.core.movement_modes import MovementMode
from src.engine.tactical import TacticalDecisionSystem
from tests.helpers.scenario import compile_world

MERCHANT, HUNTER = 37, 45
INN = (40.0, 31.0)


def _scene(hunger, hp=10, merchant_at=(41.0, 31.0), hunter_at=(41.0, 30.0)):
    """Real frontier_living_world seed-42 merchant 37 (wounded, gold 0) beside inn 20003 with predator_hunter 45 adjacent."""
    state = compile_world("frontier_living_world", 42)
    m, h = state.entities[MERCHANT], state.entities[HUNTER]
    m = replace(m, navigation=replace(m.navigation, position=merchant_at, movement_mode=MovementMode.REGROUP, target=INN),
                combat=replace(m.combat, hp=hp, max_hp=85), biological=replace(m.biological, hunger=hunger, sleep_debt=0.0),
                inventory=replace(m.inventory, gold=0, items=[]))
    h = replace(h, navigation=replace(h.navigation, position=hunter_at))
    object.__setattr__(state, "entities", {MERCHANT: m, HUNTER: h})
    return state, m


def test_a_starving_subject_under_a_present_threat_keeps_its_escalated_hunger_pull():
    state, merchant = _scene(hunger=100.0)
    score = EatScorer().score(merchant, state)
    assert score.utility > 100.0, score  # the escalation (raw 100 plus the pull) is not dropped while a threat holds


def test_a_subject_whose_hunger_is_not_past_its_line_still_has_the_pull_dropped_under_a_threat():
    state, merchant = _scene(hunger=80.0)
    assert EatScorer().score(merchant, state).utility == pytest.approx(80.0)  # raw hunger: only a present threat outranks a need below its line


def test_a_wounded_subject_below_its_line_still_flees_the_predator_beside_it():
    state, merchant = _scene(hunger=80.0, merchant_at=(30.0, 30.0), hunter_at=(30.0, 29.0))  # inside the hometown: a real retreat destination exists
    update = TacticalDecisionSystem.evaluate_entity_intent(state, merchant)
    assert (update.task.payload_set or {}).get("reason") == "PANIC_RETREAT"


def test_a_subject_in_the_desperation_band_with_a_hunter_really_attacking_does_not_stand_and_eat():
    """Weighed, not overridden: the tactical order puts a real tactical hostile (engagement, panic) before any survival branch, hunger project or not."""
    from src.core.builder import V2EntityBuilder
    from src.core.enums import Faction
    from src.core.state import AuthoritativeState, BuildingState
    from src.core.strategic import ObjectiveKind, ObjectiveState, ObjectiveStatus, ProjectState, ProjectStatus

    hero = (V2EntityBuilder(1).kind("HERO").location(39.0, 31.0).identity(faction=Faction.HERO_GUILD)
            .combat(hp=7, max_hp=85, atk=10, def_stat=5, alive=True, readiness=100.0)
            .navigation(movement_mode=MovementMode.WANDER, target=INN).lifecycle(active=True).build())
    hero = replace(hero, biological=replace(hero.biological, hunger=100.0))
    objective = ObjectiveState(id="hunger_20003", kind=ObjectiveKind.REACH_LOCATION, target="20003", status=ObjectiveStatus.ACTIVE)
    project = ProjectState(id="proj_hunger_1", kind="hunger", status=ProjectStatus.ACTIVE, objectives=[objective], active_objective_id=objective.id)
    hero = replace(hero, strategic=replace(hero.strategic, projects={project.id: project}, current_project_id=project.id, current_objective_id=objective.id))
    monster = (V2EntityBuilder(2).kind("MONSTER").location(39.0, 30.0).identity(faction=Faction.MONSTER_HORDE)
               .combat(hp=300, max_hp=300, atk=60, def_stat=5, alive=True, readiness=100.0)
               .navigation(movement_mode=MovementMode.WANDER).lifecycle(active=True).build())
    inn = BuildingState(id=20003, kind="inn", position=INN, functional=True)
    state = AuthoritativeState(tick=1, seed=1, entities={1: hero, 2: monster}, buildings={20003: inn}, blocked_tiles={(40, 31)}, building_tiles={}, terrain={})
    update = TacticalDecisionSystem.evaluate_entity_intent(state, hero)
    assert (update.task.payload_set or {}).get("action") != "EAT"
    assert (update.task.payload_set or {}).get("reason") == "PANIC_RETREAT"
