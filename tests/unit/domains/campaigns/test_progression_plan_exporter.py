"""Tests for ProgressionPlanExporter (E61B)."""

from src.domains.campaigns.progression_plan import (
    BuildGoal,
    ProgressionPlan,
    ProgressionPlanExporter,
)


def _make_plan(entity_id: int = 1) -> ProgressionPlan:
    return ProgressionPlan(
        entity_id=entity_id,
        goal_queue=(
            BuildGoal(
                goal_id="g1",
                target_route_family="QUEST_OPPORTUNITY",
                target_item_id=None,
                target_level=5,
                status="pending",
            ),
        ),
        milestone_checks=(),
        revision_triggers=(),
        created_episode=0,
        last_revised_episode=0,
    )


def test_exporter_carries_live_entity_plan():
    plan = _make_plan(entity_id=7)
    result = ProgressionPlanExporter.export(7, plan, alive=True)
    assert result is plan


def test_exporter_drops_dead_entity_plan():
    plan = _make_plan(entity_id=7)
    result = ProgressionPlanExporter.export(7, plan, alive=False)
    assert result is None


def test_exporter_no_plan_returns_none():
    result = ProgressionPlanExporter.export(99, None, alive=True)
    assert result is None
