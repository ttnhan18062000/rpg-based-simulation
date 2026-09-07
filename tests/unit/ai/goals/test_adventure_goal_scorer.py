"""
Unit tests for AdventureGoalScorer (TCK-20260811-ADVENTURE-GOAL-SCORER).

Covers AC1 (registration), AC2 (normalization + metadata), AC5 (ineligible/DEFER never clear
the tier-5 floor), AC6 (deliberate tie-break value), and the Risk #1 target_pos-resolution fix
(RECOVER/ASK_INFORMATION/FORM_PARTY placeholder families) per plan.md Step 5.
"""
from __future__ import annotations

import pytest

from src.ai.goals import GoalRegistry
from src.ai.goals.adventure_scorer import AdventureGoalScorer, _ADVENTURE_ROUTE_TIER5_COMPETITION_MAX
from src.ai.goals.base import GoalScore
from src.core.builder import V2EntityBuilder
from src.core.state import AuthoritativeState, BuildingState
from src.core.strategic import GoalKind
from src.domains.adventure.schema import AdventureDecisionResult, AdventureRouteOption, RouteFamily
from src.domains.adventure.service import AdventureDecisionService


def _entity(eid: int = 1, pos: tuple = (0.0, 0.0)):
    return (
        V2EntityBuilder(eid)
        .kind("hero")
        .location(*pos)
        .build()
    )


def _state(entities=None, buildings=None, town_center=(50.0, 50.0), tick=10):
    return AuthoritativeState(
        tick=tick,
        seed=42,
        entities=entities or {},
        buildings=buildings or {},
        town_center=town_center,
    )


def _fake_decide_factory(raw_score, family=RouteFamily.GATHER_RESOURCE, target_node_id=999):
    """Builds a fake AdventureDecisionService.decide() replacement pinning `selected.score`
    and `selected.family`, so the scorer's normalization/metadata/target-resolution logic can
    be tested in isolation from route-generation nondeterminism (test_plan.md AC2 guidance)."""

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
            selected=selected,
            rejected=(),
            proposed_project=None,
            proposed_objective=None,
            trace={},
        )

    return _fake_decide


def _eligible(monkeypatch):
    monkeypatch.setattr(
        "src.ai.goals.adventure_scorer._supports_adventure_routing",
        lambda entity, cache: True,
    )


# --- AC1 ---------------------------------------------------------------------------------


def test_goal_kind_adventure_route_is_registered_member():
    assert GoalKind("z_adventure_route") == GoalKind.ADVENTURE_ROUTE
    assert isinstance(GoalRegistry._scorers[GoalKind.ADVENTURE_ROUTE], AdventureGoalScorer)


def test_adventure_goal_scorer_implements_goal_scorer_protocol(monkeypatch):
    _eligible(monkeypatch)
    monkeypatch.setattr(
        AdventureDecisionService, "decide",
        _fake_decide_factory(1.0, family=RouteFamily.SCOUT_LOCATION, target_node_id=7),
    )
    entity = _entity()
    state = _state(entities={1: entity})
    score = AdventureGoalScorer().score(entity, state)
    assert isinstance(score, GoalScore)


# --- AC2 ---------------------------------------------------------------------------------


# NOTE (TCK-20260813-ADVENTURE-ROUTE-UTILITY-SCALE-NEVER-WINS-TIER5): this test now asserts the
# dedicated _ADVENTURE_ROUTE_TIER5_COMPETITION_MAX=2.4 denominator's own boundary, not the old
# shared _ADVENTURE_ROUTE_SCORE_MAX=2.9 boundary. raw_score==2.9 no longer normalizes to
# utility==100.0 here -- 2.9 is now the Generalized Bypass gate's own, unrelated ceiling (see
# test_score_normalization.py and the architecture-guard test below).
@pytest.mark.parametrize(
    "raw_score,expected_utility",
    [
        (_ADVENTURE_ROUTE_TIER5_COMPETITION_MAX, 100.0),
        (_ADVENTURE_ROUTE_TIER5_COMPETITION_MAX / 2, 50.0),
        (0.0, 0.0),
    ],
)
def test_adventure_goal_scorer_normalizes_raw_score_to_utility_exact_dedicated_denominator(monkeypatch, raw_score, expected_utility):
    _eligible(monkeypatch)
    monkeypatch.setattr(
        AdventureDecisionService, "decide",
        _fake_decide_factory(raw_score, family=RouteFamily.GATHER_RESOURCE, target_node_id=999),
    )
    entity = _entity()
    state = _state(entities={1: entity})
    score = AdventureGoalScorer().score(entity, state)
    assert score.utility == pytest.approx(expected_utility)


def test_adventure_goal_scorer_metadata_carries_route_family_and_raw_score(monkeypatch):
    _eligible(monkeypatch)
    monkeypatch.setattr(
        AdventureDecisionService, "decide",
        _fake_decide_factory(1.8, family=RouteFamily.HUNT_WEAK_ENEMY, target_node_id=42),
    )
    entity = _entity()
    state = _state(entities={1: entity})
    score = AdventureGoalScorer().score(entity, state)
    assert set(score.metadata.keys()) >= {"route_family", "raw_score"}
    assert score.metadata["route_family"] == RouteFamily.HUNT_WEAK_ENEMY
    assert score.metadata["raw_score"] == 1.8


# --- TCK-20260813-ADVENTURE-ROUTE-UTILITY-SCALE-NEVER-WINS-TIER5: dedicated-denominator fix ----


def test_adventure_route_typical_score_produces_meaningfully_higher_utility_than_before_fix(monkeypatch):
    """RECOVER critical-healing-plus-rest_inn example (plan.md Step 1b, corrected ceiling):
    raw_score=2.35 from urgency(0.95, healing CRITICAL) + benefit(1.0, rest_inn at
    sleep_debt=100) + personality_bias(0.25, caution) + confidence_bonus(0.15) - risk_penalty(0).
    Pre-fix, this normalized against the old shared _ADVENTURE_ROUTE_SCORE_MAX=2.9:
    (2.35/2.9)*100 = 81.03. Post-fix, using the dedicated, smaller denominator, utility must be
    measurably higher -- the whole point of decoupling the denominator from a ceiling
    (faction-directive-inclusive, never live in this call path) the real formula rarely reaches.
    """
    _eligible(monkeypatch)
    raw_score = 2.35
    pre_fix_utility = (raw_score / 2.9) * 100.0
    monkeypatch.setattr(
        AdventureDecisionService, "decide",
        _fake_decide_factory(raw_score, family=RouteFamily.RECOVER, target_node_id=999),
    )
    entity = _entity()
    state = _state(entities={1: entity})
    score = AdventureGoalScorer().score(entity, state)
    assert score.utility > pre_fix_utility
    assert score.utility == pytest.approx((raw_score / _ADVENTURE_ROUTE_TIER5_COMPETITION_MAX) * 100.0)


@pytest.mark.parametrize("raw_score", [0.58, 0.6914, 0.75])
def test_adventure_route_sibling_ticket_typical_band_produces_higher_utility_than_before_fix(monkeypatch, raw_score):
    """Sibling ticket's own DEBUG-trace-observed typical raw_score band
    (investigation.md: "~0.58-0.75"), re-confirmed this session's empirical measurement
    (max 0.7439 across all 6 named calibration run_keys). Quantifies the fix's real-world
    magnitude, not just its boundary values."""
    _eligible(monkeypatch)
    pre_fix_utility = (raw_score / 2.9) * 100.0
    monkeypatch.setattr(
        AdventureDecisionService, "decide",
        _fake_decide_factory(raw_score, family=RouteFamily.GATHER_RESOURCE, target_node_id=999),
    )
    entity = _entity()
    state = _state(entities={1: entity})
    score = AdventureGoalScorer().score(entity, state)
    assert score.utility > pre_fix_utility


# --- AC5 ---------------------------------------------------------------------------------


def test_adventure_goal_scorer_ineligible_entity_returns_zero_utility_no_target(monkeypatch):
    call_count = {"n": 0}

    def _spy_decide(*args, **kwargs):
        call_count["n"] += 1
        raise AssertionError("AdventureDecisionService.decide() must not be called for an "
                              "ineligible entity (early-return before expensive work).")

    monkeypatch.setattr(
        "src.ai.goals.adventure_scorer._supports_adventure_routing",
        lambda entity, cache: False,
    )
    monkeypatch.setattr(AdventureDecisionService, "decide", _spy_decide)

    entity = _entity()
    state = _state(entities={1: entity})
    score = AdventureGoalScorer().score(entity, state)

    assert score.kind == GoalKind.ADVENTURE_ROUTE
    assert score.utility == 0.0
    assert score.target_id is None
    assert call_count["n"] == 0


def test_adventure_goal_scorer_defer_with_reason_returns_zero_utility_no_target(monkeypatch):
    _eligible(monkeypatch)

    def _fake_decide(entity, candidates, tick=0, resource_nodes=None, faction_directives=None, factions=None, culture_state=None, legend_fact=None, belief_institutions=None, event_fidelity=None):
        selected = AdventureRouteOption(
            family=RouteFamily.DEFER_WITH_REASON,
            score=0.01,
            confidence=1.0,
            expected_benefit=0.0,
            expected_risk=0.0,
            reason="no active opportunities or structural needs identified; deferring.",
        )
        return AdventureDecisionResult(
            selected=selected, rejected=(), proposed_project=None, proposed_objective=None, trace={},
        )

    monkeypatch.setattr(AdventureDecisionService, "decide", _fake_decide)
    entity = _entity()
    state = _state(entities={1: entity})
    score = AdventureGoalScorer().score(entity, state)

    assert score.utility == 0.0
    assert score.target_id is None
    assert score.target_pos is None


# --- Risk #1: target_id/target_pos synthesis for RECOVER/ASK_INFORMATION/FORM_PARTY ------


def test_form_party_winner_has_non_null_target_id_and_resolvable_target_pos(monkeypatch):
    _eligible(monkeypatch)
    entity = _entity(eid=1, pos=(0.0, 0.0))
    ally = _entity(eid=2, pos=(10.0, 10.0))
    monkeypatch.setattr(
        AdventureDecisionService, "decide",
        _fake_decide_factory(2.0, family=RouteFamily.FORM_PARTY, target_node_id=None),
    )
    state = _state(entities={1: entity, 2: ally})
    score = AdventureGoalScorer().score(entity, state)

    assert score.target_id == f"adventure:{RouteFamily.FORM_PARTY.value}"
    assert score.target_pos == ally.navigation.position


def test_forced_recover_winner_target_pos_resolves_to_inn_or_town_center(monkeypatch):
    _eligible(monkeypatch)
    monkeypatch.setattr(
        AdventureDecisionService, "decide",
        _fake_decide_factory(1.2, family=RouteFamily.RECOVER, target_node_id=None),
    )
    entity = _entity(pos=(0.0, 0.0))

    inn = BuildingState(id=500, kind="inn", position=(5.0, 5.0))
    state_with_inn = _state(entities={1: entity}, buildings={500: inn}, town_center=(50.0, 50.0))
    score_with_inn = AdventureGoalScorer().score(entity, state_with_inn)
    assert score_with_inn.target_pos == inn.position

    state_no_inn = _state(entities={1: entity}, town_center=(50.0, 50.0))
    score_no_inn = AdventureGoalScorer().score(entity, state_no_inn)
    assert score_no_inn.target_pos == (50.0, 50.0)


def test_forced_ask_information_winner_target_pos_resolves_to_town_center(monkeypatch):
    _eligible(monkeypatch)
    monkeypatch.setattr(
        AdventureDecisionService, "decide",
        _fake_decide_factory(0.9, family=RouteFamily.ASK_INFORMATION, target_node_id=None),
    )
    entity = _entity()
    state = _state(entities={1: entity}, town_center=(33.0, 44.0))
    score = AdventureGoalScorer().score(entity, state)
    assert score.target_pos == (33.0, 44.0)


def test_form_party_target_pos_falls_back_to_entity_own_position_when_no_ally_candidates(monkeypatch):
    _eligible(monkeypatch)
    entity = _entity(pos=(7.0, 8.0))
    monkeypatch.setattr(
        AdventureDecisionService, "decide",
        _fake_decide_factory(2.1, family=RouteFamily.FORM_PARTY, target_node_id=None),
    )
    state = _state(entities={1: entity})
    score = AdventureGoalScorer().score(entity, state)
    assert score.target_pos == (7.0, 8.0)


# --- TCK-20260907-ROUTE-BIAS-SCORING-INFRASTRUCTURE: region_culture_states bridge ---------


def test_adventure_goal_scorer_threads_bridged_culture_state_for_entity_own_region(monkeypatch):
    import dataclasses
    from src.domains.culture.model import CultureState

    _eligible(monkeypatch)
    seen = {}

    def _spy_decide(entity, candidates, tick=0, resource_nodes=None, faction_directives=None, factions=None, culture_state=None, legend_fact=None, belief_institutions=None, event_fidelity=None):
        seen["culture_state"] = culture_state
        return AdventureDecisionResult(
            selected=AdventureRouteOption(
                family=RouteFamily.RECOVER, score=0.5, confidence=1.0,
                expected_benefit=0.5, expected_risk=0.0,
            ),
            rejected=(), proposed_project=None, proposed_objective=None, trace={},
        )

    monkeypatch.setattr(AdventureDecisionService, "decide", _spy_decide)

    entity = _entity()
    entity = dataclasses.replace(
        entity, navigation=dataclasses.replace(entity.navigation, region_id="hostile_region")
    )
    culture = CultureState(fatalism=0.8)
    state = _state(entities={1: entity})
    state.region_culture_states["hostile_region"] = culture

    AdventureGoalScorer().score(entity, state)

    assert seen["culture_state"] is culture


def test_adventure_goal_scorer_culture_state_none_safe_when_region_or_entry_missing(monkeypatch):
    import dataclasses

    _eligible(monkeypatch)
    seen = {}

    def _spy_decide(entity, candidates, tick=0, resource_nodes=None, faction_directives=None, factions=None, culture_state=None, legend_fact=None, belief_institutions=None, event_fidelity=None):
        seen["culture_state"] = culture_state
        return AdventureDecisionResult(
            selected=AdventureRouteOption(
                family=RouteFamily.RECOVER, score=0.5, confidence=1.0,
                expected_benefit=0.5, expected_risk=0.0,
            ),
            rejected=(), proposed_project=None, proposed_objective=None, trace={},
        )

    monkeypatch.setattr(AdventureDecisionService, "decide", _spy_decide)

    # Entity with no region_id yet (default None) -- must not raise.
    entity = _entity()
    state = _state(entities={1: entity})
    AdventureGoalScorer().score(entity, state)
    assert seen["culture_state"] is None

    # Entity resolved to a region with no bridged entry -- must fall back to None, not KeyError.
    entity2 = _entity(eid=2)
    entity2 = dataclasses.replace(
        entity2, navigation=dataclasses.replace(entity2.navigation, region_id="unbridged_region")
    )
    state2 = _state(entities={2: entity2})
    AdventureGoalScorer().score(entity2, state2)
    assert seen["culture_state"] is None


# --- TCK-20260907-LEGEND-FACT-ROUTE-BIAS-WIRING: entity_legend_facts bridge --------------


def test_adventure_goal_scorer_threads_bridged_legend_fact_for_entity_own_subject_id(monkeypatch):
    from src.domains.fame.legend import LegendFact

    _eligible(monkeypatch)
    seen = {}

    def _spy_decide(entity, candidates, tick=0, resource_nodes=None, faction_directives=None, factions=None, culture_state=None, legend_fact=None, belief_institutions=None, event_fidelity=None):
        seen["legend_fact"] = legend_fact
        return AdventureDecisionResult(
            selected=AdventureRouteOption(
                family=RouteFamily.RECOVER, score=0.5, confidence=1.0,
                expected_benefit=0.5, expected_risk=0.0,
            ),
            rejected=(), proposed_project=None, proposed_objective=None, trace={},
        )

    monkeypatch.setattr(AdventureDecisionService, "decide", _spy_decide)

    entity = _entity(eid=7)
    fact = LegendFact(subject_id="7", fame=0.8)
    state = _state(entities={7: entity})
    state.entity_legend_facts["7"] = fact

    AdventureGoalScorer().score(entity, state)

    assert seen["legend_fact"] is fact


def test_adventure_goal_scorer_legend_fact_none_safe_when_subject_id_missing(monkeypatch):
    _eligible(monkeypatch)
    seen = {}

    def _spy_decide(entity, candidates, tick=0, resource_nodes=None, faction_directives=None, factions=None, culture_state=None, legend_fact=None, belief_institutions=None, event_fidelity=None):
        seen["legend_fact"] = legend_fact
        return AdventureDecisionResult(
            selected=AdventureRouteOption(
                family=RouteFamily.RECOVER, score=0.5, confidence=1.0,
                expected_benefit=0.5, expected_risk=0.0,
            ),
            rejected=(), proposed_project=None, proposed_objective=None, trace={},
        )

    monkeypatch.setattr(AdventureDecisionService, "decide", _spy_decide)

    # Entity whose subject_id has no bridged entry -- must fall back to None, not KeyError.
    entity = _entity(eid=99)
    state = _state(entities={99: entity})
    AdventureGoalScorer().score(entity, state)
    assert seen["legend_fact"] is None


# --- AC6 ---------------------------------------------------------------------------------


def test_adventure_route_kind_value_sorts_after_all_existing_goal_kinds():
    existing_values = [
        GoalKind.HARVESTING.value, GoalKind.FATIGUE.value, GoalKind.HUNGER.value,
        GoalKind.SOCIAL.value, GoalKind.TOWN_RETURN.value, GoalKind.COMBAT_ENGAGE.value,
        GoalKind.COMBAT_RETREAT.value, GoalKind.RECOVER.value, GoalKind.RESOLVE_BLOCKER.value,
        GoalKind.GUILD.value,
    ]
    for v in existing_values:
        assert GoalKind.ADVENTURE_ROUTE.value > v, (
            f"GoalKind.ADVENTURE_ROUTE.value={GoalKind.ADVENTURE_ROUTE.value!r} must sort "
            f"after {v!r} so an exact-utility tie never lets adventure routing win over "
            f"existing survival/urgency-tier scorers (investigation.md Risk #5)."
        )
    # town_return is today's alphabetical maximum among the 10 existing values -- pin that
    # assumption explicitly so this test fails loudly if a future ticket adds an 11th/12th
    # existing GoalKind whose value would also need checking here.
    assert max(existing_values) == GoalKind.TOWN_RETURN.value


def test_adventure_route_loses_exact_utility_tie_against_existing_kind():
    scores = [
        GoalScore(kind=GoalKind.ADVENTURE_ROUTE, utility=50.0, target_id="t", target_pos=(0, 0)),
        GoalScore(kind=GoalKind.RECOVER, utility=50.0, target_id="t", target_pos=(0, 0)),
    ]
    scores.sort(key=lambda x: (-x.utility, x.kind))
    assert scores[0].kind == GoalKind.RECOVER  # recover (survival-urgency) wins the tie
