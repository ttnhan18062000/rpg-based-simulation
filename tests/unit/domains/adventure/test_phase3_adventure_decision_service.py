"""
tests/unit/domains/adventure/test_phase3_adventure_decision_service.py

Phase 3 — AdventureDecisionService unit tests.
Verifies decision service logic, rejections tracking, and strategic bridge creation.
"""

import pytest
from src.core.builder import V2EntityBuilder
from src.core.state import CombatComponent, BiologicalComponent, PersonalityComponent
from src.domains.adventure.schema import RouteFamily, AdventureRouteOption, RejectedRoute
from src.domains.adventure.service import AdventureDecisionService
from src.core.strategic import ProjectKind, ObjectiveKind


def _entity():
    b = V2EntityBuilder(1)
    b.replace_combat(CombatComponent(hp=100, max_hp=100, atk=10, def_stat=2))
    b.replace_biological(BiologicalComponent(hunger=0.0, sleep_debt=0.0))
    p = PersonalityComponent(greed=0.5, bravery=0.5, sociability=0.5, industry=0.5)
    b.identity(evolution_level=1, personality=p)
    return b.build()


def test_selects_highest_scoring_route():
    entity = _entity()
    c1 = AdventureRouteOption(family=RouteFamily.RECOVER, score=0.0, confidence=1.0, expected_benefit=0.5, expected_risk=0.0)
    c2 = AdventureRouteOption(family=RouteFamily.BUY_UPGRADE, score=0.0, confidence=1.0, expected_benefit=0.9, expected_risk=0.0)
    
    # We want c2 to score higher, let's trigger decision which scores candidates
    result = AdventureDecisionService.decide(entity, [c1, c2], tick=10)
    
    assert result.selected is not None
    assert result.selected.family in (RouteFamily.RECOVER, RouteFamily.BUY_UPGRADE)
    # Validate strategic objects are generated
    assert result.proposed_project is not None
    assert result.proposed_objective is not None
    assert result.proposed_project.created_tick == 10
    assert result.proposed_project.active_objective_id == result.proposed_objective.id


def test_rejects_blocked_routes():
    entity = _entity()
    c_blocked = AdventureRouteOption(family=RouteFamily.RECOVER, score=0.0, confidence=1.0, expected_benefit=0.8, expected_risk=0.0, blockers=("no_tavern",))
    c_valid = AdventureRouteOption(family=RouteFamily.GATHER_RESOURCE, score=0.0, confidence=1.0, expected_benefit=0.4, expected_risk=0.0)
    
    result = AdventureDecisionService.decide(entity, [c_blocked, c_valid], tick=5)
    
    assert result.selected is not None
    assert result.selected.family == RouteFamily.GATHER_RESOURCE
    
    # Blocked route must be inside rejected with reason
    rejected_families = [r.family for r in result.rejected]
    assert RouteFamily.RECOVER in rejected_families
    
    # Verify blocker text is present in the reason
    recover_rej = [r for r in result.rejected if r.family == RouteFamily.RECOVER][0]
    assert "no_tavern" in recover_rej.reason


def test_defers_when_no_candidates():
    entity = _entity()
    result = AdventureDecisionService.decide(entity, [], tick=1)

    assert result.selected is not None
    assert result.selected.family == RouteFamily.DEFER_WITH_REASON
    assert result.proposed_project is None
    assert result.proposed_objective is None


def test_resolved_target_node_id_preferred_over_opportunity_id():
    """
    TCK-20260713-SIMQ-ECONOMY-INTENT-GENERATION-GAP Step 3: when the selected
    route's target_node_id was resolved (Step 2), ObjectiveState.target must be
    the stringified ref id, not the raw opportunity id — so tactical.py's
    existing int-cast + resource_nodes/buildings lookup can resolve a real
    position for it, the same way REACH_LOCATION already does.
    """
    entity = _entity()
    route = AdventureRouteOption(
        family=RouteFamily.GATHER_RESOURCE,
        score=0.9,
        confidence=1.0,
        expected_benefit=0.8,
        expected_risk=0.1,
        source_opportunity_ids=("opp_resource_42",),
        target_node_id=42,
    )

    result = AdventureDecisionService.decide(entity, [route], tick=7)

    assert result.proposed_objective is not None
    assert result.proposed_objective.target == "42"


def test_opportunity_id_used_when_target_node_id_unresolved():
    entity = _entity()
    route = AdventureRouteOption(
        family=RouteFamily.CRAFT_UPGRADE,
        score=0.9,
        confidence=1.0,
        expected_benefit=0.8,
        expected_risk=0.1,
        source_opportunity_ids=("opp_craft_iron_sword",),
        target_node_id=None,
    )

    result = AdventureDecisionService.decide(entity, [route], tick=7)

    assert result.proposed_objective is not None
    assert result.proposed_objective.target == "opp_craft_iron_sword"
