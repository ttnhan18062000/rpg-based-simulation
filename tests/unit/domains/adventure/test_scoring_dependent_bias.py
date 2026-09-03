"""Tests for AdventureRouteScorer personal-dependents route bias (SOC-262)."""

from src.core.builder import V2EntityBuilder
from src.core.enums import EntityRole
from src.core.self_model import (
    KnowledgeModelComponent,
    NeedInterpretationComponent,
    SelfAwarenessComponent,
    SelfModelBundle,
)
from src.core.state import BiologicalComponent, CombatComponent
from src.domains.adventure.schema import AdventureRouteOption, RouteFamily
from src.domains.adventure.scoring import AdventureRouteScorer
from src.domains.campaigns.progression_plan import BuildGoal, ProgressionPlan


# ── Helpers ───────────────────────────────────────────────────────────────────

def _build_entity(role: EntityRole = EntityRole.HERO, dependent_entity_ids=None) -> object:
    b = V2EntityBuilder(1)
    b.replace_combat(CombatComponent(hp=100, max_hp=100, atk=10, def_stat=2))
    b.replace_biological(BiologicalComponent(hunger=0.0, sleep_debt=0.0))
    b.identity(role=role, traits=set())
    b.replace_self_model(SelfModelBundle(
        self_awareness=SelfAwarenessComponent(perceived_condition={"health": 1.0}, perceived_weaknesses=()),
        needs=NeedInterpretationComponent(active_needs={}, dominant_need=None),
        knowledge=KnowledgeModelComponent(unknowns={}),
    ))
    if dependent_entity_ids is not None:
        b.lifecycle(dependent_entity_ids=dependent_entity_ids)
    return b.build()


def _route(family: RouteFamily, benefit: float = 0.5) -> AdventureRouteOption:
    return AdventureRouteOption(
        family=family,
        score=0.0,
        confidence=0.8,
        expected_benefit=benefit,
        expected_risk=0.1,
    )


def _plan_with_head(target_route_family: str, status: str) -> ProgressionPlan:
    return ProgressionPlan(
        entity_id=1,
        goal_queue=(
            BuildGoal(
                goal_id="g1",
                target_route_family=target_route_family,
                target_item_id=None,
                target_level=None,
                status=status,
            ),
        ),
        milestone_checks=(),
        revision_triggers=(),
        created_episode=0,
        last_revised_episode=0,
    )


# ── Tests ─────────────────────────────────────────────────────────────────────

def test_dependent_route_bias_lowers_risky_route_score():
    entity_with_dependent = _build_entity(dependent_entity_ids=[2])
    entity_without_dependent = _build_entity()
    route = _route(RouteFamily.HUNT_WEAK_ENEMY)

    result_with_dependent = AdventureRouteScorer.score(entity_with_dependent, route)
    result_without_dependent = AdventureRouteScorer.score(entity_without_dependent, route)

    assert result_with_dependent.dependent_bias == -2.0
    assert result_with_dependent.score < result_without_dependent.score


def test_dependent_route_bias_raises_recovery_route_score():
    entity_with_dependent = _build_entity(dependent_entity_ids=[2])
    entity_without_dependent = _build_entity()

    for family in (RouteFamily.RECOVER, RouteFamily.RETURN_TOWN):
        route = _route(family)
        result_with_dependent = AdventureRouteScorer.score(entity_with_dependent, route)
        result_without_dependent = AdventureRouteScorer.score(entity_without_dependent, route)

        assert result_with_dependent.dependent_bias == 1.0
        assert result_with_dependent.score > result_without_dependent.score


def test_dependent_route_bias_zero_when_no_dependent():
    entity = _build_entity(dependent_entity_ids=[])
    route = _route(RouteFamily.HUNT_WEAK_ENEMY)

    result = AdventureRouteScorer.score(entity, route)

    assert result.dependent_bias == 0.0


def test_dependent_bias_independent_of_other_additive_terms():
    entity_with_dependent = _build_entity(dependent_entity_ids=[2])
    entity_without_dependent = _build_entity()
    route = _route(RouteFamily.RECOVER)
    plan = _plan_with_head("recover", "pending")

    baseline = AdventureRouteScorer.score(entity_without_dependent, route)
    result = AdventureRouteScorer.score(entity_with_dependent, route, progression_plan=plan)

    dependent_delta = result.dependent_bias
    plan_advance_bonus = result.plan_advance_bonus

    assert abs(result.score - (baseline.score + dependent_delta + plan_advance_bonus)) < 0.01
