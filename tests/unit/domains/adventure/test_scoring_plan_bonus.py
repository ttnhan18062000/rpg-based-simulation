"""Tests for AdventureRouteScorer plan-advance bonus (E61C)."""

from unittest.mock import MagicMock

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

def _build_entity(role: EntityRole = EntityRole.HERO) -> object:
    b = V2EntityBuilder(1)
    b.replace_combat(CombatComponent(hp=100, max_hp=100, atk=10, def_stat=2))
    b.replace_biological(BiologicalComponent(hunger=0.0, sleep_debt=0.0))
    b.identity(role=role, traits=set())
    b.replace_self_model(SelfModelBundle(
        self_awareness=SelfAwarenessComponent(perceived_condition={"health": 1.0}, perceived_weaknesses=()),
        needs=NeedInterpretationComponent(active_needs={}, dominant_need=None),
        knowledge=KnowledgeModelComponent(unknowns={}),
    ))
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

def test_plan_advance_bonus_applied_when_route_matches_head_goal():
    entity = _build_entity()
    route = _route(RouteFamily.CRAFT_UPGRADE)
    plan = _plan_with_head("craft_upgrade", "pending")

    result = AdventureRouteScorer.score(entity, route, progression_plan=plan)

    assert result.plan_advance_bonus == 1.5
    # Score with bonus must be 1.5 higher than without
    baseline = AdventureRouteScorer.score(entity, route)
    assert abs(result.score - (baseline.score + 1.5)) < 0.01


def test_plan_advance_bonus_not_applied_when_goal_completed():
    entity = _build_entity()
    route = _route(RouteFamily.CRAFT_UPGRADE)
    plan = _plan_with_head("craft_upgrade", "completed")

    result = AdventureRouteScorer.score(entity, route, progression_plan=plan)

    assert result.plan_advance_bonus == 0.0


def test_plan_advance_bonus_not_applied_when_goal_blocked():
    entity = _build_entity()
    route = _route(RouteFamily.CRAFT_UPGRADE)
    plan = _plan_with_head("craft_upgrade", "blocked")

    result = AdventureRouteScorer.score(entity, route, progression_plan=plan)

    assert result.plan_advance_bonus == 0.0


def test_plan_advance_bonus_not_applied_when_queue_empty():
    entity = _build_entity()
    route = _route(RouteFamily.CRAFT_UPGRADE)
    plan = ProgressionPlan(
        entity_id=1,
        goal_queue=(),
        milestone_checks=(),
        revision_triggers=(),
        created_episode=0,
        last_revised_episode=0,
    )

    result = AdventureRouteScorer.score(entity, route, progression_plan=plan)

    assert result.plan_advance_bonus == 0.0


def test_plan_advance_bonus_not_applied_when_route_family_mismatch():
    entity = _build_entity()
    route = _route(RouteFamily.GATHER_RESOURCE)
    plan = _plan_with_head("craft_upgrade", "pending")

    result = AdventureRouteScorer.score(entity, route, progression_plan=plan)

    assert result.plan_advance_bonus == 0.0


def test_plan_advance_bonus_zero_when_no_plan():
    entity = _build_entity()
    route = _route(RouteFamily.CRAFT_UPGRADE)

    result = AdventureRouteScorer.score(entity, route, progression_plan=None)

    assert result.plan_advance_bonus == 0.0


def test_existing_hero_quest_bonus_still_applies():
    """Regression: HERO quest bonus via group context still works after E61C changes."""
    from src.core.state import GroupRecord

    entity = _build_entity(role=EntityRole.HERO)
    route = _route(RouteFamily.QUEST_OPPORTUNITY, benefit=0.5)
    group = MagicMock(spec=GroupRecord)
    group.roles = {1: "HERO"}
    group.escort_target_id = None

    result_with_group = AdventureRouteScorer.score(entity, route, group=group)
    result_no_group = AdventureRouteScorer.score(entity, route)

    # HERO +10% group multiplier must still apply
    assert result_with_group.score > result_no_group.score


def test_existing_warrior_mage_bonus_still_applies():
    """Regression: WARRIOR+MAGE group bonus on HUNT_WEAK_ENEMY still works."""
    from src.core.state import GroupRecord

    entity = _build_entity(role=EntityRole.GUARD)
    route = _route(RouteFamily.HUNT_WEAK_ENEMY, benefit=0.5)

    group_with_mage = MagicMock(spec=GroupRecord)
    group_with_mage.roles = {1: "WARRIOR", 2: "MAGE"}
    group_with_mage.escort_target_id = None

    group_no_mage = MagicMock(spec=GroupRecord)
    group_no_mage.roles = {1: "WARRIOR"}
    group_no_mage.escort_target_id = None

    result_with_mage = AdventureRouteScorer.score(entity, route, group=group_with_mage)
    result_no_mage = AdventureRouteScorer.score(entity, route, group=group_no_mage)

    assert result_with_mage.score > result_no_mage.score
