"""
tests/unit/domains/adventure/test_phase3_route_generator.py

Phase 3 — AdventureRouteGenerator unit tests.
Verifies dynamic generation of candidate route options from state and opportunities.
"""

import pytest
from src.core.builder import V2EntityBuilder
from src.core.state import CombatComponent, BiologicalComponent
from src.core.self_model import SelfModelBundle, SelfAwarenessComponent, NeedInterpretationComponent, KnowledgeModelComponent, UnknownFact
from src.world.providers.resources import Opportunity
from src.world.providers.requirements import Requirement
from src.domains.adventure.schema import RouteFamily
from src.domains.adventure.generator import AdventureRouteGenerator


def _entity(hp=100, max_hp=100, weaknesses=(), hunger=0.0, unknowns=None):
    from src.core.self_model import NeedInterpretationComponent, InterpretedNeed
    b = V2EntityBuilder(1)
    b.replace_combat(CombatComponent(hp=hp, max_hp=max_hp, atk=10, def_stat=2))
    b.replace_biological(BiologicalComponent(hunger=hunger, sleep_debt=0.0))
    b.identity(evolution_level=1)
    
    # Needs mapping
    active_needs = {}
    dominant_need = None
    if "low_health" in weaknesses:
        active_needs["healing"] = InterpretedNeed(key="healing", urgency=0.9, confidence=1.0, reason="low_hp")
        dominant_need = "healing"
    if "hunger_pressure" in weaknesses:
        active_needs["food"] = InterpretedNeed(key="food", urgency=0.8, confidence=1.0, reason="hunger")
        if not dominant_need:
            dominant_need = "food"
    if "weak_weapon" in weaknesses:
        active_needs["equipment_improvement"] = InterpretedNeed(key="equipment_improvement", urgency=0.6, confidence=1.0, reason="weak")
        if not dominant_need:
            dominant_need = "equipment_improvement"
            
    awareness = SelfAwarenessComponent(
        perceived_condition={"health": hp/max_hp},
        perceived_weaknesses=tuple(weaknesses),
    )
    needs = NeedInterpretationComponent(active_needs=active_needs, dominant_need=dominant_need)
    km = KnowledgeModelComponent(unknowns=unknowns or {})
    bundle = SelfModelBundle(self_awareness=awareness, needs=needs, knowledge=km)
    b.replace_self_model(bundle)
    return b.build()


def test_low_hp_generates_recover_route():
    entity = _entity(hp=20, max_hp=100, weaknesses=["low_health"])
    opps = [
        Opportunity(id="o1", kind="rest_inn", target_id="inn", subject="rest", estimated_reward=50.0, estimated_risk=0.0, requirements=(), confidence=1.0)
    ]
    routes = AdventureRouteGenerator.generate(entity, None, opps)
    
    assert any(r.family == RouteFamily.RECOVER for r in routes)


def test_weak_weapon_and_shop_item_generates_buy_upgrade_route():
    entity = _entity(weaknesses=["weak_weapon"])
    opps = [
        Opportunity(id="o2", kind="buy_item", target_id="shop", subject="iron_sword", estimated_reward=40.0, estimated_risk=0.0, requirements=(), confidence=1.0)
    ]
    routes = AdventureRouteGenerator.generate(entity, None, opps)
    
    assert any(r.family == RouteFamily.BUY_UPGRADE for r in routes)


def test_known_recipe_generates_craft_upgrade_route():
    entity = _entity(weaknesses=["weak_weapon"])
    opps = [
        Opportunity(id="o3", kind="craft_item", target_id="blacksmith", subject="iron_sword", estimated_reward=60.0, estimated_risk=0.1, requirements=(), confidence=1.0)
    ]
    routes = AdventureRouteGenerator.generate(entity, None, opps)
    
    assert any(r.family == RouteFamily.CRAFT_UPGRADE for r in routes)


def test_unknown_material_generates_ask_information_route():
    unknowns = {"material.moon_resin.source": UnknownFact("material.moon_resin.source", "provider_partial")}
    entity = _entity(unknowns=unknowns)
    opps = [
        Opportunity(id="o4", kind="ask_information", target_id="guide", subject="moon_resin", estimated_reward=30.0, estimated_risk=0.0, requirements=(), confidence=0.8)
    ]
    routes = AdventureRouteGenerator.generate(entity, None, opps)
    
    assert any(r.family == RouteFamily.ASK_INFORMATION for r in routes)


def test_not_enough_gold_generates_earn_gold_routes():
    entity = _entity(weaknesses=["weak_weapon"])
    opps = [
        Opportunity(id="o5", kind="gather_resource", target_id="mine", subject="iron_ore", estimated_reward=20.0, estimated_risk=0.2, requirements=(), confidence=0.9)
    ]
    routes = AdventureRouteGenerator.generate(entity, None, opps)
    
    assert any(r.family == RouteFamily.GATHER_RESOURCE for r in routes)


def test_no_valid_route_generates_defer_with_reason():
    entity = _entity()
    routes = AdventureRouteGenerator.generate(entity, None, [])
    
    assert len(routes) == 1
    assert routes[0].family == RouteFamily.DEFER_WITH_REASON
    assert "blocked" in routes[0].reason or "no active opportunities" in routes[0].reason


def test_target_node_id_widened_to_all_int_castable_opportunity_kinds():
    """
    TCK-20260713-SIMQ-ECONOMY-INTENT-GENERATION-GAP Step 2: target_node_id
    capture is no longer scoped to "gather_resource" only — any opportunity
    whose target_id int-casts gets it populated (e.g. a resource-provider
    opportunity keyed by a real node id), while opportunities whose target_id
    is a non-numeric string (e.g. a service id) still degrade safely to None.
    """
    entity = _entity()
    opps = [
        Opportunity(id="o1", kind="gather_resource", target_id="42", subject="iron_ore", estimated_reward=10.0, estimated_risk=0.1, requirements=(), confidence=1.0),
        Opportunity(id="o2", kind="craft_item", target_id="blacksmith_hometown", subject="iron_sword", estimated_reward=60.0, estimated_risk=0.1, requirements=(), confidence=1.0),
    ]
    routes = AdventureRouteGenerator.generate(entity, None, opps)

    gather_route = next(r for r in routes if r.family == RouteFamily.GATHER_RESOURCE)
    assert gather_route.target_node_id == 42

    craft_route = next(r for r in routes if r.family == RouteFamily.CRAFT_UPGRADE)
    assert craft_route.target_node_id is None


def test_generator_caps_result_count():
    entity = _entity()
    opps = [
        Opportunity(id=f"o{i}", kind="gather_resource", target_id="mine", subject="ore", estimated_reward=10.0, estimated_risk=0.1, requirements=(), confidence=1.0)
        for i in range(50)
    ]
    routes = AdventureRouteGenerator.generate(entity, None, opps)
    
    assert len(routes) <= 25  # capped
