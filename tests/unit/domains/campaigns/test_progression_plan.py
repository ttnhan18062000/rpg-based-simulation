"""Tests for ProgressionPlan model and CampaignState.progression_plans field (E61A)."""

from src.domains.campaigns.progression_plan import (
    BuildGoal,
    MilestoneCheck,
    ProgressionPlan,
    RevisionTrigger,
)
from src.domains.campaigns.state import CampaignState


def _make_plan() -> ProgressionPlan:
    return ProgressionPlan(
        entity_id=42,
        goal_queue=(
            BuildGoal(
                goal_id="g1",
                target_route_family="GATHER_RESOURCE",
                target_item_id="iron_ore",
                target_level=None,
                status="pending",
            ),
            BuildGoal(
                goal_id="g2",
                target_route_family="QUEST_OPPORTUNITY",
                target_item_id=None,
                target_level=5,
                status="in_progress",
            ),
        ),
        milestone_checks=(
            MilestoneCheck(
                milestone_id="m1",
                target_level=5,
                episode_index=2,
                achieved=False,
            ),
        ),
        revision_triggers=(
            RevisionTrigger(
                trigger_id="t1",
                kind="goal_completed",
                subject="g1",
                fired=False,
            ),
        ),
        created_episode=0,
        last_revised_episode=0,
    )


def test_progression_plan_round_trip():
    plan = _make_plan()
    restored = ProgressionPlan.from_dict(plan.to_dict())
    assert restored == plan
    assert restored.goal_queue[0].target_item_id == "iron_ore"
    assert restored.goal_queue[1].target_level == 5
    assert restored.milestone_checks[0].achieved is False
    assert restored.revision_triggers[0].kind == "goal_completed"


def test_progression_plan_empty_queue_round_trip():
    plan = ProgressionPlan(
        entity_id=1,
        goal_queue=(),
        milestone_checks=(),
        revision_triggers=(),
        created_episode=3,
        last_revised_episode=3,
    )
    restored = ProgressionPlan.from_dict(plan.to_dict())
    assert restored == plan
    assert isinstance(restored.goal_queue, tuple)
    assert isinstance(restored.milestone_checks, tuple)
    assert isinstance(restored.revision_triggers, tuple)
    assert len(restored.goal_queue) == 0


def test_campaign_state_with_plans_round_trip():
    plan = _make_plan()
    state = CampaignState(
        campaign_id="test_campaign",
        episode_index=1,
        progression_plans={42: plan},
    )
    d = state.to_dict()
    assert "42" in d["progression_plans"]
    restored = CampaignState.from_dict(d)
    assert 42 in restored.progression_plans
    assert restored.progression_plans[42] == plan


def test_campaign_state_missing_plans_key_backward_compat():
    d = {
        "campaign_id": "old_campaign",
        "episode_index": 0,
    }
    state = CampaignState.from_dict(d)
    assert state.progression_plans == {}
