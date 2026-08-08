"""
tests/unit/tactical/test_objective_pursuit_coverage.py

Regression coverage for the TCK-20260713-SIMQ-ECONOMY-INTENT-GENERATION-GAP fix:
TacticalDecisionSystem.evaluate_entity_intent's Pillar 5.1 branch previously only
understood ObjectiveKind.REACH_LOCATION (tactical.py:213 hardcoded gate) — every
other ObjectiveKind System A (src/domains/adventure/) or System B
(src/systems/strategic_systems/intelligence.py) could produce silently fell
through to a bare idle EntityUpdate(entity_id=entity.id) at tactical.py:319.

These tests drive the new elif branch that wires ObjectiveIntentResolver +
ActionIntentAdapter.execute() into that Pillar 5.1 branch for every other
ObjectiveKind (excluding REACH_LOCATION, whose existing branch is untouched,
and DEFEAT_ENEMY, handled by the separate hostile-engagement branch).
"""
from __future__ import annotations
from dataclasses import replace

from src.core.builder import V2EntityBuilder
from src.core.state import AuthoritativeState, ResourceNodeState, BuildingState, ItemStack
from src.core.strategic import (
    ProjectKind,
    ProjectState,
    ProjectStatus,
    ObjectiveKind,
    ObjectiveState,
    ObjectiveStatus,
)
from src.core.enums import Faction
from src.core.registries import RecipeRegistry
from src.engine.tactical import TacticalDecisionSystem


def _hero(eid: int, pos: tuple[float, float], **kwargs) -> "EntityState":
    b = V2EntityBuilder(eid)
    b.kind("hero")
    b.location(float(pos[0]), float(pos[1]))
    b.identity(faction=Faction.HERO_GUILD, **kwargs)
    b.combat(hp=100, max_hp=100, alive=True, readiness=100.0)
    b.lifecycle(active=True)
    return b


def _with_project(builder: V2EntityBuilder, project: ProjectState) -> "EntityState":
    builder.strategic(
        projects={project.id: project},
        current_project_id=project.id,
        current_objective_id=project.active_objective_id,
    )
    return builder.build()


def test_objective_kind_acquire_item_produces_executable_action():
    """
    ACQUIRE_ITEM (System A's CRAFT_UPGRADE objective) must reach real execution
    via ObjectiveIntentResolver -> ActionIntentAdapter -> REQUEST_CRAFT dispatch,
    not fall through to the idle EntityUpdate(entity_id=entity.id) fallback.
    """
    recipe_id = "iron_sword"
    recipe = RecipeRegistry.get(recipe_id)

    obj = ObjectiveState(
        id="obj.craft_upgrade.ent1.t10",
        kind=ObjectiveKind.ACQUIRE_ITEM,
        target=f"opp_craft_{recipe_id}",
        status=ObjectiveStatus.ACTIVE,
    )
    project = ProjectState(
        id="proj.craft_upgrade.ent1.t10",
        kind=ProjectKind.CRAFTING,
        status=ProjectStatus.ACTIVE,
        objectives=[obj],
        active_objective_id=obj.id,
        lock_until_tick=0,
    )

    builder = _hero(1, (0.0, 0.0), known_recipes={recipe_id})
    materials = [ItemStack(mat, qty) for mat, qty in recipe.requires_items.items()]
    builder.inventory(gold=recipe.gold_cost, items=materials)
    hero = _with_project(builder, project)

    state = AuthoritativeState(tick=10, seed=1, entities={1: hero})

    update = TacticalDecisionSystem.evaluate_entity_intent(state, hero, neighbors=[])

    assert update.entity_id == 1
    assert update.resource_transfers, (
        "ACQUIRE_ITEM objective did not produce a resource_transfers payload — "
        "fell through to the idle fallback instead of real REQUEST_CRAFT execution"
    )
    transfer = update.resource_transfers[0]
    assert transfer.source_kind == "CRAFTING"
    assert transfer.source_id == recipe_id


def test_objective_kind_reach_resource_produces_executable_action():
    """
    REACH_RESOURCE (System A's GATHER_RESOURCE objective) must reach real
    execution — while still far from the node, the new branch must issue a
    real NavigationUpdate toward the node's position, not the idle fallback.
    """
    node = ResourceNodeState(
        id=501,
        kind="iron_ore",
        position=(50.0, 50.0),
        yields_item="iron_ore",
        remaining_charges=5,
        max_charges=5,
        required_ticks=5,
    )

    obj = ObjectiveState(
        id="obj.gather_resource.ent1.t10",
        kind=ObjectiveKind.REACH_RESOURCE,
        target=str(node.id),
        status=ObjectiveStatus.ACTIVE,
    )
    project = ProjectState(
        id="proj.gather_resource.ent1.t10",
        kind=ProjectKind.HARVESTING,
        status=ProjectStatus.ACTIVE,
        objectives=[obj],
        active_objective_id=obj.id,
        lock_until_tick=0,
    )

    builder = _hero(1, (0.0, 0.0))
    hero = _with_project(builder, project)

    state = AuthoritativeState(tick=10, seed=1, entities={1: hero}, resource_nodes={501: node})

    update = TacticalDecisionSystem.evaluate_entity_intent(state, hero, neighbors=[])

    assert update.entity_id == 1
    assert update.navigation is not None and update.navigation.target_set == node.position, (
        "REACH_RESOURCE objective did not navigate toward the resolved node position — "
        "fell through to the idle fallback instead of real execution"
    )
    assert update.task is None, (
        "REACH_RESOURCE objective fired a harvest/interact task while still > 1.0 away from the node"
    )
    assert update.interaction is None, (
        "REACH_RESOURCE objective fired an interaction update while still > 1.0 away from the node"
    )


def test_objective_kind_reach_resource_arrival_produces_harvest_action():
    """
    REACH_RESOURCE at arrival (dist <= 1.0 from the target node) must transition
    to a harvest/interact action via ActionIntentAdapter's HARVEST_RESOURCE
    dispatch, not re-issue another MOVE_TO through ObjectiveIntentResolver's
    unconditional REACH_RESOURCE -> MOVE_TO mapping.
    """
    node = ResourceNodeState(
        id=501,
        kind="iron_ore",
        position=(50.0, 50.0),
        yields_item="iron_ore",
        remaining_charges=5,
        max_charges=5,
        required_ticks=5,
    )

    obj = ObjectiveState(
        id="obj.gather_resource.ent1.t10",
        kind=ObjectiveKind.REACH_RESOURCE,
        target=str(node.id),
        status=ObjectiveStatus.ACTIVE,
    )
    project = ProjectState(
        id="proj.gather_resource.ent1.t10",
        kind=ProjectKind.HARVESTING,
        status=ProjectStatus.ACTIVE,
        objectives=[obj],
        active_objective_id=obj.id,
        lock_until_tick=0,
    )

    builder = _hero(1, node.position)
    hero = _with_project(builder, project)

    state = AuthoritativeState(tick=10, seed=1, entities={1: hero}, resource_nodes={501: node})

    update = TacticalDecisionSystem.evaluate_entity_intent(state, hero, neighbors=[])

    assert update.entity_id == 1
    assert update.interaction is not None and update.interaction.target_node_id == node.id, (
        "REACH_RESOURCE objective at arrival did not produce an interaction update "
        "targeting the resource node — the arrival-transition fix did not fire"
    )


def test_reach_location_arrival_behavior_unchanged():
    """
    Anti-drift pin for REACH_LOCATION's pre-existing arrival branch
    (tactical.py:214-259), added alongside TCK-20260714-SIMQ-HARVEST-RESOURCE-
    ARRIVAL-TRANSITION's new REACH_RESOURCE arrival branch in the same elif
    block, to catch any accidental control-flow bleed between the two.
    """
    node = ResourceNodeState(
        id=601,
        kind="iron_ore",
        position=(10.0, 10.0),
        yields_item="iron_ore",
        remaining_charges=5,
        max_charges=5,
        required_ticks=5,
    )
    obj_node = ObjectiveState(
        id="obj.reach_location.node.ent1.t10",
        kind=ObjectiveKind.REACH_LOCATION,
        target=str(node.id),
        status=ObjectiveStatus.ACTIVE,
    )
    project_node = ProjectState(
        id="proj.reach_location.node.ent1.t10",
        kind=ProjectKind.EXPLORATION,
        status=ProjectStatus.ACTIVE,
        objectives=[obj_node],
        active_objective_id=obj_node.id,
        lock_until_tick=0,
    )
    hero_node = _with_project(_hero(1, node.position), project_node)
    state_node = AuthoritativeState(tick=10, seed=1, entities={1: hero_node}, resource_nodes={601: node})

    update_node = TacticalDecisionSystem.evaluate_entity_intent(state_node, hero_node, neighbors=[])

    assert update_node.entity_id == 1
    assert update_node.navigation is None
    assert update_node.task is not None
    assert update_node.task.work_kind_set == "ENTITY_ACT"
    assert update_node.task.payload_set == {"action": "INTERACT", "target_id": node.id}
    assert update_node.interaction is not None
    assert update_node.interaction.target_node_id == node.id
    assert update_node.interaction.progress_delta == 1

    tavern = BuildingState(id=701, kind="tavern", position=(20.0, 20.0))
    obj_eat = ObjectiveState(
        id="obj.reach_location.eat.ent2.t10",
        kind=ObjectiveKind.REACH_LOCATION,
        target=str(tavern.id),
        status=ObjectiveStatus.ACTIVE,
    )
    project_eat = ProjectState(
        id="proj.reach_location.eat.ent2.t10",
        kind="hunger",
        status=ProjectStatus.ACTIVE,
        objectives=[obj_eat],
        active_objective_id=obj_eat.id,
        lock_until_tick=0,
    )
    hero_eat = _with_project(_hero(2, tavern.position), project_eat)
    state_eat = AuthoritativeState(tick=10, seed=1, entities={2: hero_eat}, buildings={701: tavern})

    update_eat = TacticalDecisionSystem.evaluate_entity_intent(state_eat, hero_eat, neighbors=[])

    assert update_eat.entity_id == 2
    assert update_eat.navigation is None
    assert update_eat.interaction is None
    assert update_eat.task is not None
    assert update_eat.task.work_kind_set == "ENTITY_ACT"
    assert update_eat.task.payload_set == {"action": "EAT", "target_id": tavern.id}

    inn = BuildingState(id=702, kind="inn", position=(30.0, 30.0))
    obj_rest = ObjectiveState(
        id="obj.reach_location.rest.ent3.t10",
        kind=ObjectiveKind.REACH_LOCATION,
        target=str(inn.id),
        status=ObjectiveStatus.ACTIVE,
    )
    project_rest = ProjectState(
        id="proj.reach_location.rest.ent3.t10",
        kind="fatigue",
        status=ProjectStatus.ACTIVE,
        objectives=[obj_rest],
        active_objective_id=obj_rest.id,
        lock_until_tick=0,
    )
    hero_rest = _with_project(_hero(3, inn.position), project_rest)
    state_rest = AuthoritativeState(tick=10, seed=1, entities={3: hero_rest}, buildings={702: inn})

    update_rest = TacticalDecisionSystem.evaluate_entity_intent(state_rest, hero_rest, neighbors=[])

    assert update_rest.entity_id == 3
    assert update_rest.navigation is None
    assert update_rest.interaction is None
    assert update_rest.task is not None
    assert update_rest.task.work_kind_set == "ENTITY_ACT"
    assert update_rest.task.payload_set == {"action": "REST", "target_id": inn.id}


# ── target_position fallback (TCK-20260807-TOWN-RETURN-TARGET-RESOLUTION-BUG) ──────────────
# TownScorer/RecoverScorer set target="town_center" (not int-castable, not a coordinate
# string) but target_position=state.town_center (a real tuple). Prior to this fix,
# _resolve_target_position only ever looked at `target`, so these objectives never resolved a
# position and the entity never navigated toward it.

def test_reach_location_with_unparseable_target_id_falls_back_to_target_position():
    """
    An objective whose `target` field is neither int-castable nor a coordinate string (e.g.
    TownScorer's "town_center") must still navigate using `target_position` when it's set,
    instead of silently resolving to no position at all.
    """
    town_center = (0.0, 0.0)
    obj = ObjectiveState(
        id="obj.reach_location.town_return.ent1.t10",
        kind=ObjectiveKind.REACH_LOCATION,
        target="town_center",
        target_position=town_center,
        status=ObjectiveStatus.ACTIVE,
    )
    project = ProjectState(
        id="proj.town_return.ent1.t10",
        kind="town_return",
        status=ProjectStatus.ACTIVE,
        objectives=[obj],
        active_objective_id=obj.id,
        lock_until_tick=0,
    )
    hero = _with_project(_hero(1, (50.0, 50.0)), project)
    state = AuthoritativeState(tick=10, seed=1, entities={1: hero})

    update = TacticalDecisionSystem.evaluate_entity_intent(state, hero, neighbors=[])

    assert update.entity_id == 1
    assert update.navigation is not None and update.navigation.target_set == town_center, (
        "town_return objective with an unparseable target id did not fall back to "
        "target_position — the entity never received a real navigation target"
    )


def test_reach_location_with_unparseable_target_id_and_no_target_position_stays_unresolved():
    """
    If neither `target` parses nor `target_position` is set, the objective must resolve to no
    position at all (same behavior as before this fix) -- not silently invent a fallback.
    """
    obj = ObjectiveState(
        id="obj.reach_location.nowhere.ent1.t10",
        kind=ObjectiveKind.REACH_LOCATION,
        target="nowhere",
        target_position=None,
        status=ObjectiveStatus.ACTIVE,
    )
    project = ProjectState(
        id="proj.nowhere.ent1.t10",
        kind="town_return",
        status=ProjectStatus.ACTIVE,
        objectives=[obj],
        active_objective_id=obj.id,
        lock_until_tick=0,
    )
    hero = _with_project(_hero(1, (50.0, 50.0)), project)
    state = AuthoritativeState(tick=10, seed=1, entities={1: hero})

    update = TacticalDecisionSystem.evaluate_entity_intent(state, hero, neighbors=[])

    assert update.entity_id == 1
    assert update.navigation is None


def test_reach_location_target_position_fallback_does_not_override_resolvable_node_id():
    """
    Anti-regression: when `target` DOES parse to a real resource-node id, the int-parse branch
    must still win and populate node_id -- the target_position fallback must never short-circuit
    the currently-working int-castable path (which needs node_id/building_id for the
    INTERACT/EAT/REST arrival-dispatch branches, not just a bare position).
    """
    node = ResourceNodeState(
        id=901,
        kind="iron_ore",
        position=(10.0, 10.0),
        yields_item="iron_ore",
        remaining_charges=5,
        max_charges=5,
        required_ticks=5,
    )
    # Deliberately set a target_position that does NOT match the node's real position, to prove
    # the int-parse branch (which yields the node's real position) took priority and the
    # fallback was never consulted.
    obj = ObjectiveState(
        id="obj.reach_location.node.ent1.t10",
        kind=ObjectiveKind.REACH_LOCATION,
        target=str(node.id),
        target_position=(999.0, 999.0),
        status=ObjectiveStatus.ACTIVE,
    )
    project = ProjectState(
        id="proj.reach_location.node.ent1.t10",
        kind=ProjectKind.EXPLORATION,
        status=ProjectStatus.ACTIVE,
        objectives=[obj],
        active_objective_id=obj.id,
        lock_until_tick=0,
    )
    hero = _with_project(_hero(1, node.position), project)
    state = AuthoritativeState(tick=10, seed=1, entities={1: hero}, resource_nodes={901: node})

    update = TacticalDecisionSystem.evaluate_entity_intent(state, hero, neighbors=[])

    assert update.entity_id == 1
    assert update.interaction is not None and update.interaction.target_node_id == node.id, (
        "target_position fallback incorrectly overrode a resolvable int-castable target id"
    )
