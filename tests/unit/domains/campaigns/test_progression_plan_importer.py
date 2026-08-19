"""Tests for ProgressionPlanImporter (E61B)."""

from src.domains.campaigns.progression_plan import (
    MilestoneCheck,
    ProgressionPlan,
    ProgressionPlanImporter,
)


def _make_plan(milestone_checks=()) -> ProgressionPlan:
    return ProgressionPlan(
        entity_id=1,
        goal_queue=(),
        milestone_checks=milestone_checks,
        revision_triggers=(),
        created_episode=0,
        last_revised_episode=0,
    )


def test_importer_achieves_met_milestone():
    plan = _make_plan(
        milestone_checks=(
            MilestoneCheck(
                milestone_id="m1", target_level=3, episode_index=1, achieved=False
            ),
        )
    )
    result = ProgressionPlanImporter.import_plan(1, plan, new_episode_index=1, entity_level=5)
    assert result.milestone_checks[0].achieved is True


def test_importer_skips_unmet_milestone():
    plan = _make_plan(
        milestone_checks=(
            MilestoneCheck(
                milestone_id="m1", target_level=10, episode_index=2, achieved=False
            ),
        )
    )
    result = ProgressionPlanImporter.import_plan(1, plan, new_episode_index=1, entity_level=5)
    assert result.milestone_checks[0].achieved is False


def test_importer_empty_milestones_no_op():
    plan = _make_plan(milestone_checks=())
    result = ProgressionPlanImporter.import_plan(1, plan, new_episode_index=1, entity_level=99)
    assert result is plan
