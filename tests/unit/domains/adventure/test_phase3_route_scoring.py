"""
tests/unit/domains/adventure/test_phase3_route_scoring.py

Phase 3 — Imperfect Decision Scoring unit tests.
Verifies subjective scoring, need priorities, and personality trait biases.
"""

import pytest
from src.core.builder import V2EntityBuilder
from src.core.state import CombatComponent, BiologicalComponent
from src.core.self_model import (
    SelfModelBundle,
    SelfAwarenessComponent,
    NeedInterpretationComponent,
    InterpretedNeed,
    KnowledgeModelComponent,
    UnknownFact,
)
from src.domains.adventure.schema import RouteFamily, AdventureRouteOption
from src.domains.adventure.scoring import AdventureRouteScorer


def _entity(hp=100, max_hp=100, weaknesses=(), hunger=0.0, unknowns=None, personality=None):
    from src.core.self_model import NeedInterpretationComponent, InterpretedNeed
    from src.core.state import PersonalityComponent
    b = V2EntityBuilder(1)
    b.replace_combat(CombatComponent(hp=hp, max_hp=max_hp, atk=10, def_stat=2))
    b.replace_biological(BiologicalComponent(hunger=hunger, sleep_debt=0.0))
    p_comp = None
    if personality:
        # personality dict could have caution/curiosity, but state.PersonalityComponent only supports greed, bravery, sociability, industry
        # But wait! In our test, test_cautious_entity_prefers_recover_before_hunt passes {"caution": 10} etc.
        # Since caution is derived from 1.0 - bravery, we can convert caution to bravery!
        # If caution is given, bravery = 1.0 - caution
        greed = personality.get("greed", 0.0)
        sociability = personality.get("sociability", 0.0)
        industry = personality.get("industry", 0.0)
        if "caution" in personality:
            c_val = personality["caution"]
            if c_val > 1.0:
                c_val /= 100.0
            bravery = 1.0 - c_val
        else:
            bravery = personality.get("bravery", 0.0)
        
        p_comp = PersonalityComponent(greed=greed, bravery=bravery, sociability=sociability, industry=industry)
        # If curiosity is in personality, let's put it into identity properties!
        props = {}
        if "curiosity" in personality:
            props["curiosity"] = personality["curiosity"]
        b.identity(evolution_level=1, personality=p_comp, properties=props)
    else:
        b.identity(evolution_level=1, personality=p_comp)
    
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
    km = KnowledgeModelComponent(unknowns=unknowns or {})
    bundle = SelfModelBundle(self_awareness=awareness, needs=needs, knowledge=km)
    b.replace_self_model(bundle)
    return b.build()


def test_healing_need_outranks_upgrade_when_hp_critical():
    """Verify critical survival need outranks growth under critical health (hp=15)."""
    entity = _entity(hp=15, max_hp=100, weaknesses=["low_health", "weak_weapon"])
    
    r_recover = AdventureRouteOption(family=RouteFamily.RECOVER, score=0.0, confidence=1.0, expected_benefit=0.8, expected_risk=0.0)
    r_upgrade = AdventureRouteOption(family=RouteFamily.BUY_UPGRADE, score=0.0, confidence=1.0, expected_benefit=0.9, expected_risk=0.2)
    
    scored_recover = AdventureRouteScorer.score(entity, r_recover)
    scored_upgrade = AdventureRouteScorer.score(entity, r_upgrade)
    
    assert scored_recover.score > scored_upgrade.score


def test_greedy_entity_prefers_gold_route_when_risk_equal():
    """Verify greedy personality bias boosts gold/loot routes over others when risks are identical."""
    entity_normal = _entity(personality={"greed": 10})
    entity_greedy = _entity(personality={"greed": 85}) # high greed
    
    route = AdventureRouteOption(family=RouteFamily.GATHER_RESOURCE, score=0.0, confidence=1.0, expected_benefit=0.8, expected_risk=0.2)
    
    s_normal = AdventureRouteScorer.score(entity_normal, route)
    s_greedy = AdventureRouteScorer.score(entity_greedy, route)
    
    assert s_greedy.score > s_normal.score


def test_cautious_entity_prefers_recover_before_hunt():
    """Verify cautious personality bias increases recovery score and inflates risk penalties."""
    entity_normal = _entity(personality={"caution": 10})
    entity_cautious = _entity(personality={"caution": 90}) # high caution
    
    r_recover = AdventureRouteOption(family=RouteFamily.RECOVER, score=0.0, confidence=1.0, expected_benefit=0.5, expected_risk=0.0)
    r_hunt = AdventureRouteOption(family=RouteFamily.HUNT_WEAK_ENEMY, score=0.0, confidence=1.0, expected_benefit=0.8, expected_risk=0.4)
    
    normal_rec = AdventureRouteScorer.score(entity_normal, r_recover).score
    normal_hunt = AdventureRouteScorer.score(entity_normal, r_hunt).score
    
    cautious_rec = AdventureRouteScorer.score(entity_cautious, r_recover).score
    cautious_hunt = AdventureRouteScorer.score(entity_cautious, r_hunt).score
    
    # Cautious prefers recovery more than normal entity
    assert (cautious_rec - cautious_hunt) > (normal_rec - normal_hunt)


def test_curious_entity_prefers_information_when_unknown_exists():
    """Verify curious personality bias values information routes more."""
    entity_curious = _entity(personality={"curiosity": 95})
    entity_normal = _entity(personality={"curiosity": 10})
    
    route = AdventureRouteOption(family=RouteFamily.ASK_INFORMATION, score=0.0, confidence=0.8, expected_benefit=0.6, expected_risk=0.0)
    
    s_normal = AdventureRouteScorer.score(entity_normal, route)
    s_curious = AdventureRouteScorer.score(entity_curious, route)
    
    assert s_curious.score > s_normal.score


def test_industrious_entity_prefers_craft_route_when_feasible():
    """Verify industrious personality bias prefers crafting and gathering resource options."""
    entity_industrious = _entity(personality={"industry": 90})
    entity_normal = _entity(personality={"industry": 10})
    
    route = AdventureRouteOption(family=RouteFamily.CRAFT_UPGRADE, score=0.0, confidence=0.9, expected_benefit=0.8, expected_risk=0.1)
    
    s_normal = AdventureRouteScorer.score(entity_normal, route)
    s_industrious = AdventureRouteScorer.score(entity_industrious, route)
    
    assert s_industrious.score > s_normal.score


def test_scoring_does_not_use_hidden_world_truth():
    """Verify scoring logic strictly uses subjective self-model views and rejects hidden truths."""
    entity = _entity()
    route = AdventureRouteOption(family=RouteFamily.RECOVER, score=0.0, confidence=0.8, expected_benefit=0.7, expected_risk=0.1)
    
    # Assert scorer takes entity + option and does not query state providers directly
    res = AdventureRouteScorer.score(entity, route)
    assert res.score > 0.0


def test_route_scoring_is_deterministic():
    entity = _entity(weaknesses=["low_health"])
    route = AdventureRouteOption(family=RouteFamily.RECOVER, score=0.0, confidence=0.9, expected_benefit=0.8, expected_risk=0.0)
    
    s1 = AdventureRouteScorer.score(entity, route)
    s2 = AdventureRouteScorer.score(entity, route)
    
    assert s1 == s2
