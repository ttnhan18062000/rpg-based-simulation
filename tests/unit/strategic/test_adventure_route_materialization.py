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
        "src.ai.goals.adventure_scorer._supports_adventure_routing",
        lambda entity, cache: True,
    )


def _fake_decide_factory(raw_score, family, target_node_id=None):
    def _fake_decide(entity, candidates, tick=0, resource_nodes=None, faction_directives=None, factions=None, culture_state=None, legend_fact=None, belief_institutions=None, event_fidelity=None):
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


def test_adventure_route_win_thread_family_into_strategic_update(monkeypatch):
    """TCK-20260813-ADVENTURE-ROUTE-LAST-ROUTING-FAMILY-RESTORE: a winning ADVENTURE_ROUTE
    candidate's materialization must thread the route family into
    StrategicUpdate.last_routing_family_set as the .value STRING (not the raw RouteFamily enum).
    type(...) is str is required, not isinstance -- RouteFamily(str, Enum) means isinstance would
    still pass even if .value were forgotten."""
    _eligible(monkeypatch)
    monkeypatch.setattr(
        AdventureDecisionService, "decide",
        _fake_decide_factory(2.0, family=RouteFamily.TAKE_EASY_QUEST, target_node_id=777),
    )
    entity = _entity()
    state = _state(entities={1: entity}, tick=123)

    result = StrategicIntelligenceSystem.evaluate_strategic_intent(state, entity, force=True)

    assert result is not None
    assert result.last_routing_family_set == "take_easy_quest"
    assert type(result.last_routing_family_set) is str
    assert result.last_routing_tick_set == 123


def test_adventure_route_win_that_loses_project_switch_does_not_set_routing_family(monkeypatch):
    """Reproduces the pre-deletion phase's `if strat_upd is None: continue` semantics: a winning
    best_candidate whose evaluate_project_switch() call is rejected must NOT set
    last_routing_family_set anywhere -- proves the `if switch_up:` gate, not an unconditional set
    inside the ADVENTURE_ROUTE branch."""
    _eligible(monkeypatch)
    monkeypatch.setattr(
        AdventureDecisionService, "decide",
        _fake_decide_factory(2.0, family=RouteFamily.TAKE_EASY_QUEST, target_node_id=777),
    )
    monkeypatch.setattr(
        StrategicIntelligenceSystem, "evaluate_project_switch",
        staticmethod(lambda entity, candidate_proj, current_tick, state=None: None),
    )
    entity = _entity()
    state = _state(entities={1: entity})

    result = StrategicIntelligenceSystem.evaluate_strategic_intent(state, entity, force=True)

    assert result is not None
    assert result.last_routing_family_set is None
    assert result.last_routing_tick_set is None


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


def test_adventure_route_defer_family_does_not_set_routing_family(monkeypatch):
    """TCK-20260813-ADVENTURE-ROUTE-LAST-ROUTING-FAMILY-RESTORE: DEFER_WITH_REASON never reaches
    the switch_up-returning path (mirrored by the (None, None) mapper contract above), so it must
    not set last_routing_family_set/last_routing_tick_set either -- last_routing_family was only
    ever written on the winning-route path, matching the pre-deletion phase's own behavior."""

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
    assert result.last_routing_family_set is None
    assert result.last_routing_tick_set is None


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


# ─────────────────────────────────────────────────────────────────────────────
# Ported from tests/integration/domains/adventure/test_adventure_shadow_migration_parity.py
# (TCK-20260811-DELETE-ADVENTURE-DECISION-PHASE, plan.md Step 6): that file's entire premise
# (diffing two coexisting live decision paths) disappeared once AdventureDecisionPhase was
# deleted, and it was retired in full. This helper + test guard a real, independently-valuable
# regression class -- the raw_score-vs-utility scale-mismatch defect
# TCK-20260811-INTERRUPTION-BYPASS-RETENTION-MARGIN-SCALE-BUG fixed -- that doesn't need two
# live paths to verify, so it survives here rather than disappearing with the rest of the
# shadow-parity suite.
# ─────────────────────────────────────────────────────────────────────────────

def _diff_routes(phase_family, phase_raw_score, scorer_family, scorer_raw_score,
                  phase_utility=None, scorer_utility=None):
    """Itemized diff report -- required by the ticket's own Scope text ("surfacing
    normalization miscalibration as a named itemized diff report, not single pass/fail"),
    not just a standalone unit test. raw_score and utility mismatches are kept in
    separate keys so the design doc's scale-mismatch defect shape (raw_score vs. utility
    getting conflated) is caught by the report's own shape, not just its content."""
    report = {"family_mismatches": [], "raw_score_mismatches": [], "utility_mismatches": []}
    if phase_family != scorer_family:
        report["family_mismatches"].append({"phase": phase_family, "scorer": scorer_family})
    if phase_raw_score != scorer_raw_score:
        report["raw_score_mismatches"].append({"phase": phase_raw_score, "scorer": scorer_raw_score})
    if phase_utility is not None and scorer_utility is not None and phase_utility != scorer_utility:
        report["utility_mismatches"].append({"phase": phase_utility, "scorer": scorer_utility})
    return report


def test_shadow_diff_report_separates_raw_score_from_utility_mismatches():
    """Exercises the shared _diff_routes() definition against 2 synthetic cases, proving the
    report *shape* keeps raw_score and utility mismatches apart -- catching the design doc's
    scale-mismatch bug shape (raw_score/utility conflation) by construction."""
    # Case A: raw_score differs, family matches, no utility args supplied.
    diff_a = _diff_routes(
        phase_family="recover", phase_raw_score=1.5,
        scorer_family="recover", scorer_raw_score=2.0,
    )
    assert len(diff_a["raw_score_mismatches"]) == 1
    assert diff_a["family_mismatches"] == []
    assert diff_a["utility_mismatches"] == []

    # Case B: utility differs (hypothetical -- the old AdventureDecisionPhase path never
    # actually produced a utility value), raw_score and family match.
    diff_b = _diff_routes(
        phase_family="recover", phase_raw_score=1.5,
        scorer_family="recover", scorer_raw_score=1.5,
        phase_utility=40.0, scorer_utility=55.0,
    )
    assert len(diff_b["utility_mismatches"]) == 1
    assert diff_b["raw_score_mismatches"] == []
    assert diff_b["family_mismatches"] == []
