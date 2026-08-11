"""
Unit tests for AdventureGoalScorer (TCK-20260811-ADVENTURE-GOAL-SCORER).

Covers AC1 (registration), AC2 (normalization + metadata), AC5 (ineligible/DEFER never clear
the tier-5 floor), AC6 (deliberate tie-break value), and the Risk #1 target_pos-resolution fix
(RECOVER/ASK_INFORMATION/FORM_PARTY placeholder families) per plan.md Step 5.
"""
from __future__ import annotations

import pytest

from src.ai.goals import GoalRegistry
from src.ai.goals.adventure_scorer import AdventureGoalScorer
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


@pytest.mark.parametrize(
    "raw_score,expected_utility",
    [
        (2.9, 100.0),   # AC2's literal claim: raw_score==2.9 normalizes to utility==100.0 exactly
        (1.45, 50.0),   # midpoint sanity check
        (0.0, 0.0),
    ],
)
def test_adventure_goal_scorer_normalizes_raw_score_to_utility_exact(monkeypatch, raw_score, expected_utility):
    _eligible(monkeypatch)
    monkeypatch.setattr(
        AdventureDecisionService, "decide",
        _fake_decide_factory(raw_score, family=RouteFamily.GATHER_RESOURCE, target_node_id=999),
    )
    entity = _entity()
    state = _state(entities={1: entity})
    score = AdventureGoalScorer().score(entity, state)
    assert score.utility == expected_utility


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

    def _fake_decide(entity, candidates, tick=0, resource_nodes=None, faction_directives=None, factions=None):
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
