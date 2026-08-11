"""
Integration tests for the tier-5 ADVENTURE_ROUTE materialization branch
(TCK-20260811-ADVENTURE-GOAL-SCORER, plan.md Step 4/Step 6).

Covers AC3/AC4 (materialization uses metadata["raw_score"], never best_candidate.utility,
preserving RouteToProjectMapper's (None, None) contract for DEFER_WITH_REASON) and the
architecture-reviewer's Risk #1 "wins but stalls" regression: a materialized FORM_PARTY winner
must be genuinely resolvable by TacticalDecisionSystem._resolve_target_position(), not just
carry a non-None target_id.
"""
from __future__ import annotations

from dataclasses import replace as dc_replace

from src.ai.goals import GoalRegistry
from src.ai.goals.base import GoalScore
from src.core.builder import V2EntityBuilder
from src.core.state import AuthoritativeState
from src.core.strategic import GoalKind, ProjectKind
from src.domains.adventure.schema import AdventureDecisionResult, AdventureRouteOption, RouteFamily
from src.domains.adventure.service import AdventureDecisionService
from src.engine.tactical import TacticalDecisionSystem
from src.systems.strategic import StrategicIntelligenceSystem


def _entity(eid: int = 1, pos: tuple = (0.0, 0.0)):
    return (
        V2EntityBuilder(eid)
        .kind("hero")
        .location(*pos)
        .build()
    )


def _state(entities=None, tick=10):
    return AuthoritativeState(
        tick=tick,
        seed=42,
        entities=entities or {},
        town_center=(50.0, 50.0),
    )


def _eligible(monkeypatch):
    monkeypatch.setattr(
        "src.domains.adventure.phase._supports_adventure_routing",
        lambda entity, cache: True,
    )


def _fake_decide_factory(raw_score, family, target_node_id=None):
    def _fake_decide(entity, candidates, tick=0, resource_nodes=None, faction_directives=None, factions=None):
        selected = AdventureRouteOption(
            family=family,
            score=raw_score,
            confidence=1.0,
            expected_benefit=0.5,
            expected_risk=0.0,
            target_node_id=target_node_id,
        )
        return AdventureDecisionResult(
            selected=selected, rejected=(), proposed_project=None, proposed_objective=None, trace={},
        )

    return _fake_decide


def test_adventure_route_winner_materializes_with_raw_score_not_utility(monkeypatch):
    """AC3/AC4: with raw_score=2.0, utility = (2.0/2.9)*100.0 ~= 68.9655. The materialized
    ProjectState.score must equal the RAW score (2.0), never the normalized utility -- a
    regression here silently reproduces
    TCK-20260811-INTERRUPTION-BYPASS-RETENTION-MARGIN-SCALE-BUG's defect class (design doc
    Sec 4)."""
    _eligible(monkeypatch)
    monkeypatch.setattr(
        AdventureDecisionService, "decide",
        _fake_decide_factory(2.0, family=RouteFamily.TAKE_EASY_QUEST, target_node_id=777),
    )
    entity = _entity()
    state = _state(entities={1: entity})

    result = StrategicIntelligenceSystem.evaluate_strategic_intent(state, entity, force=True)

    assert result is not None
    assert len(result.projects_add_or_update) == 1
    project = result.projects_add_or_update[0]

    expected_utility = (2.0 / 2.9) * 100.0
    assert project.score == 2.0
    assert project.score != expected_utility
    # Materialization ran RouteToProjectMapper, not the generic best_candidate.kind path --
    # confirms project.kind is the real mapped ProjectKind, never GoalKind.ADVENTURE_ROUTE.
    assert project.kind == ProjectKind.QUEST
    assert project.kind != GoalKind.ADVENTURE_ROUTE


def test_adventure_route_winner_preserves_none_none_handling_for_defer_family(monkeypatch):
    """Defensive case (test_plan.md): if a winning GoalScore's metadata["route_family"] is
    somehow RouteFamily.DEFER_WITH_REASON, the materialization branch must no-op (mirroring
    RouteToProjectMapper.map_to_states()'s existing (None, None) contract) rather than raise or
    construct a garbage ProjectState. Bypasses AdventureGoalScorer.score() itself (which never
    produces a non-zero-utility DEFER_WITH_REASON result) by patching GoalRegistry.get_all_scores
    directly, exercising intelligence.py's branch in isolation."""

    def _fake_get_all_scores(entity, state):
        return [
            GoalScore(
                kind=GoalKind.ADVENTURE_ROUTE,
                utility=99.0,
                target_id="adventure:defer_with_reason",
                target_pos=(1.0, 1.0),
                metadata={"route_family": RouteFamily.DEFER_WITH_REASON, "raw_score": 0.0},
            )
        ]

    monkeypatch.setattr(GoalRegistry, "get_all_scores", _fake_get_all_scores)

    entity = _entity()
    state = _state(entities={1: entity})

    result = StrategicIntelligenceSystem.evaluate_strategic_intent(state, entity, force=True)

    assert result is not None
    assert result.projects_add_or_update == []
    assert result.current_project_id_set is None


def test_form_party_materialized_objective_is_tactically_resolvable_not_a_stall(monkeypatch):
    """Reviewer regression guard: a materialized FORM_PARTY winner must be genuinely
    tactically resolvable (via TacticalDecisionSystem._resolve_target_position()'s existing,
    unmodified target_position fallback), not merely carry a non-None target_id. Also
    demonstrates, as a negative check, that the ORIGINAL (rejected) plan version -- target_id
    synthesized alone, target_pos left None -- would have produced (None, None, None), i.e. the
    "wins but stalls forever" failure mode this fix prevents."""
    _eligible(monkeypatch)
    entity = _entity(eid=1, pos=(0.0, 0.0))
    ally = _entity(eid=2, pos=(15.0, 20.0))
    monkeypatch.setattr(
        AdventureDecisionService, "decide",
        _fake_decide_factory(2.1, family=RouteFamily.FORM_PARTY, target_node_id=None),
    )
    state = _state(entities={1: entity, 2: ally})

    result = StrategicIntelligenceSystem.evaluate_strategic_intent(state, entity, force=True)

    assert result is not None
    assert len(result.projects_add_or_update) == 1
    project = result.projects_add_or_update[0]
    materialized_obj = project.objectives[0]

    # 1. The committed ObjectiveState itself carries a real position, not None.
    assert materialized_obj.target_position is not None
    assert materialized_obj.target_position == ally.navigation.position

    # 2. _resolve_target_position() resolves it via the documented target_position fallback
    #    (tactical.py:751-752) -- both int() and ast.literal_eval() must fail first for
    #    "adventure:form_party", confirming the fallback path (not an accidental parse) is
    #    what resolves it.
    resolved_pos, node_id, building_id = TacticalDecisionSystem._resolve_target_position(state, materialized_obj)
    assert resolved_pos == ally.navigation.position
    assert node_id is None
    assert building_id is None

    # 3. Negative check: reconstruct what the ORIGINAL (rejected) plan version would have
    #    produced -- an ObjectiveState with target_position=None -- and confirm it stalls.
    stalled_obj = dc_replace(materialized_obj, target_position=None)
    stalled_resolved = TacticalDecisionSystem._resolve_target_position(state, stalled_obj)
    assert stalled_resolved == (None, None, None)
