"""
tests/unit/domains/adventure/test_depletion_scoring.py

TCK-20260619-E21C-SCORING-WIRE — Depletion-Aware Adventure Route Scoring

Verifies that AdventureRouteScorer.score() applies a depletion_fraction multiplier
to the benefit term for GATHER_RESOURCE routes when resource_nodes is provided.
"""

import pytest
from src.core.builder import V2EntityBuilder
from src.core.state import CombatComponent, BiologicalComponent, ResourceNodeState
from src.core.self_model import (
    SelfModelBundle,
    SelfAwarenessComponent,
    NeedInterpretationComponent,
    KnowledgeModelComponent,
)
from src.domains.adventure.schema import RouteFamily, AdventureRouteOption
from src.domains.adventure.scoring import AdventureRouteScorer


def _make_entity():
    """Minimal entity with no needs, no personality bias — isolates benefit term."""
    b = V2EntityBuilder(1)
    b.replace_combat(CombatComponent(hp=100, max_hp=100, atk=10, def_stat=2))
    b.replace_biological(BiologicalComponent(hunger=0.0, sleep_debt=0.0))
    b.identity(evolution_level=1)
    bundle = SelfModelBundle(
        self_awareness=SelfAwarenessComponent(perceived_condition={}, perceived_weaknesses=()),
        needs=NeedInterpretationComponent(active_needs={}, dominant_need=None),
        knowledge=KnowledgeModelComponent(unknowns={}),
    )
    b.replace_self_model(bundle)
    return b.build()


def _node(node_id: int, remaining: int, max_charges: int) -> ResourceNodeState:
    return ResourceNodeState(
        id=node_id,
        kind="iron_ore",
        position=(10.0, 10.0),
        yields_item="iron_ingot",
        remaining_charges=remaining,
        max_charges=max_charges,
        required_ticks=5,
    )


def _gather_route(node_id: int, benefit: float = 0.8) -> AdventureRouteOption:
    return AdventureRouteOption(
        family=RouteFamily.GATHER_RESOURCE,
        score=0.0,
        confidence=0.0,   # zero confidence_bonus to isolate benefit term
        expected_benefit=benefit,
        expected_risk=0.0,
        target_node_id=node_id,
    )


# ── AC1: depleted node scores <= full node ────────────────────────────────────

def test_gather_route_depleted_node_scores_lower_than_full():
    """GATHER_RESOURCE to depleted node (remaining=0) scores <= full node."""
    entity = _make_entity()
    route_id = 42

    full_node = _node(route_id, remaining=10, max_charges=10)
    depleted_node = _node(route_id, remaining=0, max_charges=10)

    route = _gather_route(route_id, benefit=0.8)

    score_full = AdventureRouteScorer.score(entity, route, resource_nodes={route_id: full_node}).score
    score_depleted = AdventureRouteScorer.score(entity, route, resource_nodes={route_id: depleted_node}).score

    assert score_depleted <= score_full


# ── AC2: half-depleted → benefit scaled by 0.5 ───────────────────────────────

def test_gather_route_half_depleted_scores_half_benefit():
    """
    With no urgency, no personality bias, zero confidence and risk,
    a half-depleted node yields score == expected_benefit × 0.5.
    """
    entity = _make_entity()
    node_id = 7

    full_node = _node(node_id, remaining=10, max_charges=10)
    half_node = _node(node_id, remaining=5, max_charges=10)

    route = _gather_route(node_id, benefit=0.8)

    score_full = AdventureRouteScorer.score(entity, route, resource_nodes={node_id: full_node}).score
    score_half = AdventureRouteScorer.score(entity, route, resource_nodes={node_id: half_node}).score

    # half score must be <= 0.5 × full score (ticket AC)
    assert score_half <= 0.5 * score_full + 1e-9
    # Also verify the value is approximately correct: benefit=0.8, depletion=0.5 → score≈0.4
    assert abs(score_half - 0.4) < 1e-4


# ── AC3: non-GATHER routes unaffected ────────────────────────────────────────

def test_non_gather_routes_unaffected_by_resource_nodes():
    """RECOVER and BUY_UPGRADE scores are identical with or without resource_nodes."""
    entity = _make_entity()
    node_id = 99
    nodes = {node_id: _node(node_id, remaining=0, max_charges=10)}

    for family in (RouteFamily.RECOVER, RouteFamily.BUY_UPGRADE):
        route = AdventureRouteOption(
            family=family,
            score=0.0,
            confidence=0.0,
            expected_benefit=0.8,
            expected_risk=0.0,
            target_node_id=node_id,
        )
        score_with = AdventureRouteScorer.score(entity, route, resource_nodes=nodes).score
        score_without = AdventureRouteScorer.score(entity, route, resource_nodes=None).score
        assert score_with == score_without, f"Score for {family} changed with resource_nodes"


# ── AC4: missing node → no crash, no scaling applied ─────────────────────────

def test_gather_route_missing_node_no_scaling():
    """GATHER_RESOURCE with unknown target_node_id falls back to unscaled benefit."""
    entity = _make_entity()
    node_id = 999

    route = _gather_route(node_id, benefit=0.5)

    # Empty resource_nodes dict — node not found
    score_missing = AdventureRouteScorer.score(entity, route, resource_nodes={}).score
    # Without resource_nodes at all — same no-scaling path
    score_none = AdventureRouteScorer.score(entity, route, resource_nodes=None).score

    assert score_missing == score_none


# ── AC5: max_charges=0 → no division by zero ─────────────────────────────────

def test_gather_route_zero_max_charges_no_crash():
    """GATHER_RESOURCE with max_charges=0 does not raise; depletion guard prevents division."""
    entity = _make_entity()
    node_id = 3

    zero_max_node = _node(node_id, remaining=0, max_charges=0)
    route = _gather_route(node_id, benefit=0.6)

    # Must not raise ZeroDivisionError
    result = AdventureRouteScorer.score(entity, route, resource_nodes={node_id: zero_max_node})
    # Score is deterministic (benefit unscaled because guard skips when max_charges==0)
    score_again = AdventureRouteScorer.score(entity, route, resource_nodes={node_id: zero_max_node})
    assert result.score == score_again.score


# ── AC6: resource_nodes=None → backward-compatible ───────────────────────────

def test_scorer_no_resource_nodes_backward_compatible():
    """Calling score() without resource_nodes is identical to current behavior."""
    entity = _make_entity()
    route = _gather_route(node_id=5, benefit=0.7)

    # Explicit None
    score_none = AdventureRouteScorer.score(entity, route, resource_nodes=None).score
    # Omitted (default)
    score_default = AdventureRouteScorer.score(entity, route).score

    assert score_none == score_default
    # With no depletion scaling, benefit term == 0.7 directly
    # Score = 0 + 0.7 + 0 + 0 - risk_penalty - 0 (confidence=0 → bonus=0)
    # risk_penalty = 0.0 * risk_multiplier * 0.5 = 0
    # So score should equal 0.7
    assert abs(score_default - 0.7) < 1e-4
