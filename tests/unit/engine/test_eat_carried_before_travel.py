"""TCK-20261007-EAT-BESIDE-THE-INN-FEEDS-A-SUBJECT-THAT-CANNOT-PAY-FREE-MEAL (scope 1) with decision 27: a hungry subject that holds
food eats it where it stands, through the tactical pass, before travelling to another node or to the inn.

The case that motivated it: a gatherer released from a node that ran dry (TCK-20261008-A-HELD-INTERACT-ON-A-DEPLETED-OR-MISSING-NODE-IS-NEVER-RE-DECIDED)
used to walk off to another node with berries in its pocket. Eating carried food needs no building and no payment (SURV-06)."""
from __future__ import annotations

from dataclasses import replace

import pytest

from src.core.builder import V2EntityBuilder
from src.core.enums import Faction
from src.core.state import AuthoritativeState, ItemStack, ResourceNodeState
from src.core.strategic import GoalKind, ObjectiveKind, ObjectiveState, ObjectiveStatus, ProjectState, ProjectStatus
from src.engine.behavior_consumers import configure_behavior_consumers, reset_behavior_consumers
from src.engine.tactical import TacticalDecisionSystem
from src.engine.tactical_rest import EAT_CARRIED_MIN_HUNGER

FAR_NODE_ID = 10003


@pytest.fixture(scope="module", autouse=True)
def _consumers():
    from src.content.repository import CatalogRepository

    repo = CatalogRepository("data/content")
    repo.load_all()
    configure_behavior_consumers(repo)
    yield
    reset_behavior_consumers()


def _gatherer(hunger, berries=1, walking_to_node=False):
    hero = (V2EntityBuilder(1).kind("hero").location(0.0, 0.0).identity(faction=Faction.HERO_GUILD)
            .combat(hp=100, max_hp=100, alive=True, readiness=100.0).lifecycle(active=True).build())
    hero = replace(hero, biological=replace(hero.biological, hunger=hunger))
    hero = replace(hero, inventory=replace(hero.inventory, gold=0, items=[ItemStack("wild_berries", berries)] if berries else []))
    if not walking_to_node:
        return hero
    objective = ObjectiveState(id="o1", kind=ObjectiveKind.REACH_LOCATION, target=str(FAR_NODE_ID), status=ObjectiveStatus.ACTIVE)
    project = ProjectState(id="p1", kind=GoalKind.HARVESTING, status=ProjectStatus.ACTIVE, objectives=[objective], active_objective_id="o1")
    return replace(hero, strategic=replace(hero.strategic, projects={"p1": project}, current_project_id="p1", current_objective_id="o1"))


def _state(hero):
    far = ResourceNodeState(
        id=FAR_NODE_ID, kind="berry_thicket", position=(40.0, 0.0), yields_item="wild_berries", remaining_charges=5, max_charges=8, required_ticks=8)
    return AuthoritativeState(tick=500, seed=1, entities={hero.id: hero}, resource_nodes={FAR_NODE_ID: far})


def _action(update):
    return (update.task.payload_set or {}).get("action") if update.task is not None else None


def test_a_released_hungry_gatherer_with_food_eats_before_walking_to_another_node():
    hero = _gatherer(hunger=EAT_CARRIED_MIN_HUNGER + 20.0, walking_to_node=True)
    update = TacticalDecisionSystem.evaluate_entity_intent(_state(hero), hero, [], 0.0)
    assert _action(update) == "EAT" and update.task.payload_set["reason"] == "EAT_CARRIED"
    assert update.navigation.target_clear  # the walk to the far node is dropped for this tick


def test_the_same_gatherer_without_food_keeps_walking_to_the_node():
    hero = _gatherer(hunger=EAT_CARRIED_MIN_HUNGER + 20.0, berries=0, walking_to_node=True)
    update = TacticalDecisionSystem.evaluate_entity_intent(_state(hero), hero, [], 0.0)
    assert _action(update) != "EAT"  # no engine charity: with nothing in its pocket it gets no relief from EAT


def test_a_gatherer_that_is_not_hungry_enough_keeps_its_food_and_its_walk():
    hero = _gatherer(hunger=EAT_CARRIED_MIN_HUNGER - 5.0, walking_to_node=True)
    update = TacticalDecisionSystem.evaluate_entity_intent(_state(hero), hero, [], 0.0)
    assert _action(update) != "EAT"
