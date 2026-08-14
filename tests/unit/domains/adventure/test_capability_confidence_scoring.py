"""Tests for capability-driven confidence_bonus in AdventureRouteScorer.score()
(TCK-20260811-CAPABILITY-CONFIDENCE-ADVENTURE-SCORING).

For GATHER_RESOURCE routes with a resolvable target_node_id and a real tool
requirement, and for CRAFT_UPGRADE routes with a resolvable recipe_known
requirement, confidence_bonus is computed from an ad-hoc
CapabilityEstimateService.estimate() call instead of the flat
route.confidence x 0.15 constant. All other routes -- and mapped routes whose
key cannot be resolved -- keep the flat term unchanged.

This is a scorer-local, throwaway read: entity.self_model.capabilities.estimates
is never populated or mutated by this call (see Design Decision 6 in plan.md).
"""

from src.core.builder import V2EntityBuilder
from src.core.models.inventory import InventoryComponent, ItemStack
from src.core.self_model import (
    KnowledgeModelComponent,
    NeedInterpretationComponent,
    SelfAwarenessComponent,
    SelfModelBundle,
)
from src.core.state import (
    BiologicalComponent,
    CombatComponent,
    EquipmentComponent,
    ResourceNodeState,
)
from src.domains.adventure.schema import AdventureRouteOption, RouteFamily
from src.domains.adventure.scoring import AdventureRouteScorer
from src.world.providers.requirements import Requirement


# ── Helpers ───────────────────────────────────────────────────────────────────

def _build_entity(
    inventory: InventoryComponent = None,
    equipment: EquipmentComponent = None,
) -> object:
    b = V2EntityBuilder(1)
    b.replace_combat(CombatComponent(hp=100, max_hp=100, atk=10, def_stat=2))
    b.replace_biological(BiologicalComponent(hunger=0.0, sleep_debt=0.0))
    b.identity(evolution_level=1)
    b.replace_self_model(SelfModelBundle(
        self_awareness=SelfAwarenessComponent(perceived_condition={}, perceived_weaknesses=()),
        needs=NeedInterpretationComponent(active_needs={}, dominant_need=None),
        knowledge=KnowledgeModelComponent(unknowns={}),
    ))
    if inventory is not None:
        b.replace_inventory(inventory)
    if equipment is not None:
        b.replace_equipment(equipment)
    return b.build()


def _node(node_id: int, kind: str = "iron_ore") -> ResourceNodeState:
    return ResourceNodeState(
        id=node_id,
        kind=kind,
        position=(10.0, 10.0),
        yields_item="iron_ingot",
        remaining_charges=10,
        max_charges=10,
        required_ticks=5,
    )


def _gather_route(
    node_id,
    requirements=(),
    confidence: float = 0.5,
) -> AdventureRouteOption:
    return AdventureRouteOption(
        family=RouteFamily.GATHER_RESOURCE,
        score=0.0,
        confidence=confidence,
        expected_benefit=0.5,
        expected_risk=0.1,
        target_node_id=node_id,
        requirements=requirements,
    )


def _craft_route(requirements=(), confidence: float = 0.5) -> AdventureRouteOption:
    return AdventureRouteOption(
        family=RouteFamily.CRAFT_UPGRADE,
        score=0.0,
        confidence=confidence,
        expected_benefit=0.5,
        expected_risk=0.1,
        requirements=requirements,
    )


# ── Test 1: GATHER_RESOURCE reflects capability estimate ──────────────────────

def test_gather_resource_confidence_reflects_capability_estimate():
    node_id = 1
    resource_nodes = {node_id: _node(node_id, kind="iron_ore")}
    route = _gather_route(
        node_id,
        requirements=(Requirement(kind="has_item", subject="pickaxe", quantity=1),),
        confidence=0.5,
    )

    entity_with_tool = _build_entity(
        inventory=InventoryComponent(items=[ItemStack(item_id="pickaxe", quantity=1)])
    )
    entity_without_tool = _build_entity()

    result_with = AdventureRouteScorer.score(entity_with_tool, route, resource_nodes=resource_nodes)
    result_without = AdventureRouteScorer.score(entity_without_tool, route, resource_nodes=resource_nodes)

    flat_term = round(route.confidence * 0.15, 4)

    assert result_with.confidence_bonus > result_without.confidence_bonus
    assert result_with.confidence_bonus != flat_term
    assert result_without.confidence_bonus != flat_term


# ── Test 2: CRAFT_UPGRADE reflects capability estimate ─────────────────────────

def test_craft_upgrade_confidence_reflects_capability_estimate():
    requirements = (
        Requirement(kind="recipe_known", subject="iron_sword"),
        Requirement(kind="has_gold", quantity=50),
        Requirement(kind="has_item", subject="iron_ingot", quantity=2),
    )
    route = _craft_route(requirements=requirements, confidence=0.5)

    entity_with_materials = _build_entity(
        inventory=InventoryComponent(
            gold=100,
            items=[ItemStack(item_id="iron_ingot", quantity=5)],
        )
    )
    entity_without_materials = _build_entity(
        inventory=InventoryComponent(gold=0, items=[])
    )

    result_with = AdventureRouteScorer.score(entity_with_materials, route)
    result_without = AdventureRouteScorer.score(entity_without_materials, route)

    flat_term = round(route.confidence * 0.15, 4)

    assert result_with.confidence_bonus > result_without.confidence_bonus
    assert result_with.confidence_bonus != flat_term
    assert result_without.confidence_bonus != flat_term


# ── Test 3: unmapped families keep the flat term ────────────────────────────────

def test_capability_confidence_falls_back_to_flat_term_for_unmapped_families():
    entity = _build_entity()

    for family in (
        RouteFamily.RECOVER,
        RouteFamily.BUY_UPGRADE,
        RouteFamily.ASK_INFORMATION,
        RouteFamily.FORM_PARTY,
    ):
        route = AdventureRouteOption(
            family=family,
            score=0.0,
            confidence=0.6,
            expected_benefit=0.5,
            expected_risk=0.1,
        )
        result = AdventureRouteScorer.score(entity, route)
        assert result.confidence_bonus == round(route.confidence * 0.15, 4)


# ── Test 4: extraction-failure fallback (4 sub-cases) ───────────────────────────

def test_capability_confidence_extraction_failure_falls_back_safely():
    entity = _build_entity()

    # (a) CRAFT_UPGRADE with no recipe_known requirement.
    craft_route = _craft_route(requirements=(), confidence=0.4)
    craft_result = AdventureRouteScorer.score(entity, craft_route)
    assert craft_result.confidence_bonus == round(craft_route.confidence * 0.15, 4)

    # (b) GATHER_RESOURCE with target_node_id=None.
    route_no_node_id = _gather_route(
        None,
        requirements=(Requirement(kind="has_item", subject="pickaxe", quantity=1),),
        confidence=0.4,
    )
    result_no_node_id = AdventureRouteScorer.score(entity, route_no_node_id, resource_nodes={1: _node(1)})
    assert result_no_node_id.confidence_bonus == round(route_no_node_id.confidence * 0.15, 4)

    # (b) GATHER_RESOURCE with target_node_id not present in resource_nodes.
    route_missing_node = _gather_route(
        999,
        requirements=(Requirement(kind="has_item", subject="pickaxe", quantity=1),),
        confidence=0.4,
    )
    result_missing_node = AdventureRouteScorer.score(entity, route_missing_node, resource_nodes={1: _node(1)})
    assert result_missing_node.confidence_bonus == round(route_missing_node.confidence * 0.15, 4)

    # (c) Review round-1 fix guard: resolvable GATHER_RESOURCE node but no tool
    # requirement at all -- this is test_depletion_scoring.py's _gather_route()
    # fixture shape (no requirements set, resource_nodes IS provided) and must
    # fall back to the flat term, not a capability-estimate-derived value.
    node_id = 7
    route_no_requirements = _gather_route(node_id, requirements=(), confidence=0.4)
    result_no_requirements = AdventureRouteScorer.score(
        entity, route_no_requirements, resource_nodes={node_id: _node(node_id)}
    )
    assert result_no_requirements.confidence_bonus == round(route_no_requirements.confidence * 0.15, 4)


# ── Test 5: no mutation of entity.self_model ────────────────────────────────────

def test_capability_confidence_does_not_mutate_entity_self_model():
    node_id = 1
    resource_nodes = {node_id: _node(node_id)}
    gather_route = _gather_route(
        node_id,
        requirements=(Requirement(kind="has_item", subject="pickaxe", quantity=1),),
    )
    craft_route = _craft_route(
        requirements=(
            Requirement(kind="recipe_known", subject="iron_sword"),
            Requirement(kind="has_gold", quantity=50),
        )
    )

    entity = _build_entity(
        inventory=InventoryComponent(gold=100, items=[ItemStack(item_id="pickaxe", quantity=1)])
    )
    self_model_before = entity.self_model

    AdventureRouteScorer.score(entity, gather_route, resource_nodes=resource_nodes)
    AdventureRouteScorer.score(entity, craft_route)

    assert entity.self_model is self_model_before


# ── Test 6: reads only entity-owned fields ──────────────────────────────────────

def test_capability_confidence_reads_only_entity_owned_fields():
    node_id = 1
    resource_nodes = {node_id: _node(node_id)}
    route = _gather_route(
        node_id,
        requirements=(Requirement(kind="has_item", subject="pickaxe", quantity=1),),
        confidence=0.5,
    )

    entity_with_tool = _build_entity(
        inventory=InventoryComponent(items=[ItemStack(item_id="pickaxe", quantity=1)])
    )
    entity_without_tool = _build_entity()

    result_with = AdventureRouteScorer.score(entity_with_tool, route, resource_nodes=resource_nodes)
    result_without = AdventureRouteScorer.score(entity_without_tool, route, resource_nodes=resource_nodes)
    assert result_with.confidence_bonus != result_without.confidence_bonus

    # An unrelated node in resource_nodes that the route doesn't reference has no effect.
    unrelated_nodes = dict(resource_nodes)
    unrelated_nodes[42] = _node(42, kind="copper_ore")
    result_with_unrelated = AdventureRouteScorer.score(
        entity_with_tool, route, resource_nodes=unrelated_nodes
    )
    assert result_with_unrelated.confidence_bonus == result_with.confidence_bonus


# ── Test 7: determinism ─────────────────────────────────────────────────────────

def test_capability_confidence_is_deterministic():
    node_id = 1
    resource_nodes = {node_id: _node(node_id)}
    gather_route = _gather_route(
        node_id,
        requirements=(Requirement(kind="has_item", subject="pickaxe", quantity=1),),
    )
    craft_route = _craft_route(
        requirements=(
            Requirement(kind="recipe_known", subject="iron_sword"),
            Requirement(kind="has_gold", quantity=50),
        )
    )
    entity = _build_entity(
        inventory=InventoryComponent(gold=100, items=[ItemStack(item_id="pickaxe", quantity=1)])
    )

    gather_result_1 = AdventureRouteScorer.score(entity, gather_route, resource_nodes=resource_nodes)
    gather_result_2 = AdventureRouteScorer.score(entity, gather_route, resource_nodes=resource_nodes)
    assert gather_result_1.confidence_bonus == gather_result_2.confidence_bonus
    assert gather_result_1.score == gather_result_2.score

    craft_result_1 = AdventureRouteScorer.score(entity, craft_route)
    craft_result_2 = AdventureRouteScorer.score(entity, craft_route)
    assert craft_result_1.confidence_bonus == craft_result_2.confidence_bonus
    assert craft_result_1.score == craft_result_2.score
