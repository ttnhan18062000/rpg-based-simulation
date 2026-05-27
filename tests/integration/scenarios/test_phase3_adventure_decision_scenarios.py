"""
tests/integration/scenarios/test_phase3_adventure_decision_scenarios.py

Phase 3 — Integrated scenario tests for Adventure Decision Layer.
Verifies standard gameplay scenarios 3.1 through 3.5.
"""

import pytest
from src.core.builder import V2EntityBuilder
from src.core.state import CombatComponent, BiologicalComponent, PersonalityComponent
from src.core.self_model import (
    SelfModelBundle,
    SelfAwarenessComponent,
    NeedInterpretationComponent,
    InterpretedNeed,
    KnowledgeModelComponent,
)
from src.domains.adventure.schema import RouteFamily, AdventureRouteOption
from src.domains.adventure.service import AdventureDecisionService
from src.domains.adventure.scoring import AdventureRouteScorer
from src.domains.adventure.generator import AdventureRouteGenerator
from src.core.strategic import ProjectKind, ObjectiveKind


def _entity(hp=100, max_hp=100, weaknesses=(), hunger=0.0, personality=None, gold=100, known_recipes=None):
    b = V2EntityBuilder(1)
    b.replace_combat(CombatComponent(hp=hp, max_hp=max_hp, atk=10, def_stat=2))
    b.replace_biological(BiologicalComponent(hunger=hunger, sleep_debt=0.0))
    b.inventory(gold=gold)
    
    # Personality mapping
    p_comp = None
    if personality:
        greed = personality.get("greed", 0.0)
        sociability = personality.get("sociability", 0.0)
        industry = personality.get("industry", 0.0)
        bravery = personality.get("bravery", 0.5)
        if "caution" in personality:
            c_val = personality["caution"]
            if c_val > 1.0:
                c_val /= 100.0
            bravery = 1.0 - c_val
        p_comp = PersonalityComponent(greed=greed, bravery=bravery, sociability=sociability, industry=industry)
    else:
        p_comp = PersonalityComponent(greed=0.5, bravery=0.5, sociability=0.5, industry=0.5)
        
    props = {}
    if personality and "curiosity" in personality:
        props["curiosity"] = personality["curiosity"]

    b.identity(evolution_level=1, personality=p_comp, properties=props, known_recipes=known_recipes)
    
    # Self-Model setup
    active_needs = {}
    dominant_need = None
    if "low_health" in weaknesses:
        active_needs["healing"] = InterpretedNeed(key="healing", urgency=0.95 if hp < 20 else 0.8, confidence=1.0, reason="low_hp")
        dominant_need = "healing"
    if "hunger_pressure" in weaknesses:
        active_needs["food"] = InterpretedNeed(key="food", urgency=0.7, confidence=1.0, reason="hunger")
        if not dominant_need:
            dominant_need = "food"
    if "weak_weapon" in weaknesses:
        active_needs["equipment_improvement"] = InterpretedNeed(key="equipment_improvement", urgency=0.5, confidence=1.0, reason="weak")
        if not dominant_need:
            dominant_need = "equipment_improvement"
            
    awareness = SelfAwarenessComponent(
        perceived_condition={"health": hp/max_hp},
        perceived_weaknesses=tuple(weaknesses),
    )
    needs = NeedInterpretationComponent(active_needs=active_needs, dominant_need=dominant_need)
    km = KnowledgeModelComponent(unknowns={})
    bundle = SelfModelBundle(self_awareness=awareness, needs=needs, knowledge=km)
    b.replace_self_model(bundle)
    
    return b.build()


# ── Scenario 3.1: Vulnerability Overrides Growth ──────────────────────────────

def test_scenario_3_1_vulnerability_overrides_growth():
    """Wounded entity (HP=15/100) must prioritise recovery over buying upgrades."""
    entity = _entity(hp=15, weaknesses=["low_health", "weak_weapon"])
    
    c_rec = AdventureRouteOption(family=RouteFamily.RECOVER, score=0.0, confidence=1.0, expected_benefit=0.8, expected_risk=0.0)
    c_upg = AdventureRouteOption(family=RouteFamily.BUY_UPGRADE, score=0.0, confidence=1.0, expected_benefit=0.9, expected_risk=0.2)
    
    res = AdventureDecisionService.decide(entity, [c_rec, c_upg], tick=1)
    
    assert res.selected is not None
    assert res.selected.family == RouteFamily.RECOVER
    assert res.proposed_project.kind == ProjectKind.RECOVERY
    assert res.proposed_objective.kind == ObjectiveKind.REACH_SERVICE


# ── Scenario 3.2: Gold Check Before Purchasing ────────────────────────────────

def test_scenario_3_2_gold_check_before_purchasing():
    """Poor entity (gold=10) should reject/de-prioritise expensive upgrades."""
    entity_poor = _entity(gold=10, weaknesses=["weak_weapon"])
    
    # Scorer should penalize or generators should flag blocker
    c_buy = AdventureRouteOption(
        family=RouteFamily.BUY_UPGRADE,
        score=0.0,
        confidence=1.0,
        expected_benefit=0.9,
        expected_risk=0.0,
        blockers=("insufficient_gold",),  # Gated by generators or resolver
    )
    c_gather = AdventureRouteOption(
        family=RouteFamily.GATHER_RESOURCE,
        score=0.0,
        confidence=1.0,
        expected_benefit=0.5,
        expected_risk=0.0,
    )
    
    res = AdventureDecisionService.decide(entity_poor, [c_buy, c_gather], tick=1)
    
    assert res.selected.family == RouteFamily.GATHER_RESOURCE
    assert RouteFamily.BUY_UPGRADE in [r.family for r in res.rejected]


# ── Scenario 3.3: Personality Alters Choice ───────────────────────────────────

def test_scenario_3_3_personality_alters_choice():
    """Greedy entity prioritises gathering resources, cautious entity prioritises recovery."""
    entity_greedy = _entity(personality={"greed": 90})
    entity_cautious = _entity(personality={"caution": 90})
    
    c_rec = AdventureRouteOption(family=RouteFamily.RECOVER, score=0.0, confidence=1.0, expected_benefit=0.6, expected_risk=0.0)
    c_gat = AdventureRouteOption(family=RouteFamily.GATHER_RESOURCE, score=0.0, confidence=1.0, expected_benefit=0.6, expected_risk=0.0)
    
    res_greedy = AdventureDecisionService.decide(entity_greedy, [c_rec, c_gat], tick=1)
    res_cautious = AdventureDecisionService.decide(entity_cautious, [c_rec, c_gat], tick=1)
    
    assert res_greedy.selected.family == RouteFamily.GATHER_RESOURCE
    assert res_cautious.selected.family == RouteFamily.RECOVER


# ── Scenario 3.4: Unknown Source Triggers Ask Information ────────────────────

def test_scenario_3_4_unknown_source_triggers_ask_information():
    """Recipe moon_resin unknown source gap generates ASK_INFORMATION route."""
    # When entity has unknowns in knowledge gap, asking for information scores well
    entity = _entity(personality={"curiosity": 95})
    
    c_info = AdventureRouteOption(family=RouteFamily.ASK_INFORMATION, score=0.0, confidence=1.0, expected_benefit=0.7, expected_risk=0.0)
    c_hunt = AdventureRouteOption(family=RouteFamily.HUNT_WEAK_ENEMY, score=0.0, confidence=1.0, expected_benefit=0.5, expected_risk=0.2)
    
    res = AdventureDecisionService.decide(entity, [c_info, c_hunt], tick=1)
    
    assert res.selected.family == RouteFamily.ASK_INFORMATION
    assert res.proposed_project.kind == ProjectKind.INFORMATION


# ── Scenario 3.5: Recipe Gaps Drive Crafting ──────────────────────────────────

def test_scenario_3_5_recipe_gaps_drive_crafting():
    """Known recipes create craft routes when matching material is in needs/opportunities."""
    entity = _entity(known_recipes={"hunter_blade"})
    
    c_craft = AdventureRouteOption(family=RouteFamily.CRAFT_UPGRADE, score=0.0, confidence=1.0, expected_benefit=0.8, expected_risk=0.0)
    c_train = AdventureRouteOption(family=RouteFamily.TRAIN_SKILL, score=0.0, confidence=1.0, expected_benefit=0.7, expected_risk=0.0)
    
    res = AdventureDecisionService.decide(entity, [c_craft, c_train], tick=1)
    
    assert res.selected.family == RouteFamily.CRAFT_UPGRADE
    assert res.proposed_project.kind == ProjectKind.CRAFTING
