"""Tests for PlanRevisionService — initial plan generation and blocker revision (E61D)."""

from src.domains.campaigns.plan_revision import PlanRevisionService
from src.domains.campaigns.progression_plan import (
    BuildGoal,
    MilestoneCheck,
    ProgressionPlan,
    RevisionTrigger,
)
from src.domains.campaigns.social_memory import SocialMemoryRecord
from src.domains.campaigns.state import EntityCarryForward


def _carry(entity_id: int = 1, level: int = 1, alive: bool = True) -> EntityCarryForward:
    return EntityCarryForward(
        entity_id=entity_id,
        level=level,
        xp=0,
        equipment={"slots": {}, "durability": {}},
        reputation=1.0,
        alive=alive,
    )


def _plan_with_trigger(trigger_kind: str, subject: str = "2", target_item_id=None) -> ProgressionPlan:
    return ProgressionPlan(
        entity_id=1,
        goal_queue=(
            BuildGoal(
                goal_id="g1",
                target_route_family="craft_upgrade",
                target_item_id=target_item_id,
                target_level=5,
                status="pending",
            ),
            BuildGoal(
                goal_id="g2",
                target_route_family="quest_opportunity",
                target_item_id=None,
                target_level=10,
                status="pending",
            ),
        ),
        milestone_checks=(),
        revision_triggers=(
            RevisionTrigger(
                trigger_id="t1",
                kind=trigger_kind,
                subject=subject,
                fired=False,
            ),
        ),
        created_episode=0,
        last_revised_episode=0,
    )


def _social_memory(relationship_scores: dict) -> SocialMemoryRecord:
    return SocialMemoryRecord(entity_id=1, relationship_scores=relationship_scores)


# ── generate_initial_plan ─────────────────────────────────────────────────────

def test_generate_initial_plan_level_1_hero():
    cf = _carry(level=1)
    plan = PlanRevisionService.generate_initial_plan(1, cf, episode_index=0)
    assert plan.goal_queue[0].target_route_family == "craft_upgrade"
    assert len(plan.goal_queue) == 3
    assert all(g.status == "pending" for g in plan.goal_queue)


def test_generate_initial_plan_level_5_hero():
    cf = _carry(level=5)
    plan = PlanRevisionService.generate_initial_plan(1, cf, episode_index=0)
    assert plan.goal_queue[0].target_route_family == "quest_opportunity"


def test_generate_initial_plan_level_10_hero():
    cf = _carry(level=10)
    plan = PlanRevisionService.generate_initial_plan(1, cf, episode_index=0)
    assert plan.goal_queue[0].target_route_family == "gather_resource"


# ── detect_and_revise — mentor_dead ──────────────────────────────────────────

def test_detect_mentor_dead_fires_trigger():
    plan = _plan_with_trigger("mentor_dead", subject="2")
    sm = _social_memory({2: 0.8})  # entity 2 is a mentor (positive score)
    persistent = {2: _carry(entity_id=2, alive=False)}  # entity 2 is dead

    revised, entry = PlanRevisionService.detect_and_revise(1, plan, _carry(), sm, 1, persistent)

    assert revised is not plan
    assert revised.goal_queue[0].goal_id == "g2"  # g2 promoted to head
    assert revised.goal_queue[-1].status == "blocked"  # g1 moved to tail as blocked
    assert revised.revision_triggers[0].fired is True
    assert entry is not None
    assert entry.event_type == "plan_revision"


def test_detect_mentor_alive_no_trigger():
    plan = _plan_with_trigger("mentor_dead", subject="2")
    sm = _social_memory({2: 0.8})
    persistent = {2: _carry(entity_id=2, alive=True)}  # mentor still alive

    revised, entry = PlanRevisionService.detect_and_revise(1, plan, _carry(), sm, 1, persistent)

    assert revised is plan
    assert entry is None


def test_detect_no_social_memory_no_revision():
    plan = _plan_with_trigger("mentor_dead", subject="2")
    persistent = {2: _carry(entity_id=2, alive=False)}

    revised, entry = PlanRevisionService.detect_and_revise(1, plan, _carry(), None, 1, persistent)

    assert revised is plan
    assert entry is None


# ── detect_and_revise — item_unavailable ─────────────────────────────────────

def test_detect_item_unavailable_fires_trigger():
    plan = _plan_with_trigger("item_unavailable", target_item_id="iron_sword")
    # Equipment does NOT contain iron_sword
    cf = EntityCarryForward(
        entity_id=1, level=1, xp=0,
        equipment={"slots": {"MAIN_HAND": "wooden_stick"}, "durability": {}},
        reputation=1.0, alive=True,
    )
    revised, entry = PlanRevisionService.detect_and_revise(1, plan, cf, None, 1, {})

    assert revised.goal_queue[0].goal_id == "g2"
    assert entry is not None


# ── NarrativeLedgerEntry format ───────────────────────────────────────────────

def test_revision_emits_narrative_ledger_entry():
    plan = _plan_with_trigger("mentor_dead")
    sm = _social_memory({2: 0.5})
    persistent = {2: _carry(entity_id=2, alive=False)}

    _, entry = PlanRevisionService.detect_and_revise(1, plan, _carry(), sm, 3, persistent)

    assert entry is not None
    assert entry.event_type == "plan_revision"
    assert entry.subject_id == "1"
    assert entry.significance == 0.6
    assert entry.payload["blocked_goal"] == "g1"
    assert entry.payload["new_head"] == "g2"


def test_revision_entry_id_dedup_format():
    plan = _plan_with_trigger("mentor_dead")
    sm = _social_memory({2: 0.5})
    persistent = {2: _carry(entity_id=2, alive=False)}

    _, entry = PlanRevisionService.detect_and_revise(1, plan, _carry(), sm, 5, persistent)

    assert entry.entry_id == "5:0:plan_revision:1"


def test_no_trigger_fired_returns_original_plan():
    plan = _plan_with_trigger("mentor_dead")
    # No social memory → no mentor check possible
    revised, entry = PlanRevisionService.detect_and_revise(1, plan, _carry(), None, 1, {})

    assert revised is plan
    assert entry is None
