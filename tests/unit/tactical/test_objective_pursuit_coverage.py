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
from src.core.state import AuthoritativeState, ResourceNodeState, ItemStack
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
