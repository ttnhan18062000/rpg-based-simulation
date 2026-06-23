"""
src/domains/campaigns/plan_revision.py
───────────────────────────────────────────────────────────────────────────────
PlanRevisionService — initial plan generation and blocker-triggered revision
for cross-episode HERO progression plans.

Wired into CampaignOrchestrator._build_initial_state() after
ProgressionPlanImporter runs.
"""

from __future__ import annotations

from dataclasses import replace as dc_replace
from typing import TYPE_CHECKING, Dict, Optional, Tuple

from src.domains.campaigns.progression_plan import (
    BuildGoal,
    MilestoneCheck,
    ProgressionPlan,
    RevisionTrigger,
)
from src.domains.campaigns.state import EntityCarryForward, NarrativeLedgerEntry

if TYPE_CHECKING:
    from src.domains.campaigns.social_memory import SocialMemoryRecord


# Level-bracket → (head_family, fallback_1, fallback_2)
_LEVEL_BRACKETS: list[tuple[str, str, str]] = [
    # Level 1–4
    ("craft_upgrade", "quest_opportunity", "gather_resource"),
    # Level 5–9
    ("quest_opportunity", "craft_upgrade", "gather_resource"),
    # Level 10+
    ("gather_resource", "quest_opportunity", "craft_upgrade"),
]

# Milestone unlock thresholds aligned to bracket boundaries
_MILESTONE_THRESHOLDS: dict[str, int] = {
    "craft_upgrade": 5,
    "quest_opportunity": 10,
    "gather_resource": 15,
}


class PlanRevisionService:
    """Generate and revise ProgressionPlans at episode boundaries.

    All methods are static — no mutable state, pure functions.

    Called from CampaignOrchestrator._build_initial_state() in two passes:
      1. generate_initial_plan() for each alive entity without an existing plan.
      2. detect_and_revise() for each alive entity that has a plan.
    """

    @staticmethod
    def generate_initial_plan(
        entity_id: int,
        carry_forward: EntityCarryForward,
        episode_index: int,
    ) -> ProgressionPlan:
        """Generate a 3-goal initial ProgressionPlan based on entity level.

        Level brackets:
          1–4  → head = craft_upgrade
          5–9  → head = quest_opportunity
          10+  → head = gather_resource

        Each bracket includes 3 goals (head + 2 fallbacks), one MilestoneCheck
        per goal at the corresponding unlock threshold, and one mentor_dead
        RevisionTrigger per goal (subject="0" placeholder — detection uses
        relationship_scores at runtime).
        """
        level = carry_forward.level
        if level <= 4:
            families = _LEVEL_BRACKETS[0]
        elif level <= 9:
            families = _LEVEL_BRACKETS[1]
        else:
            families = _LEVEL_BRACKETS[2]

        goal_queue = tuple(
            BuildGoal(
                goal_id=f"g{i + 1}",
                target_route_family=fam,
                target_item_id=None,
                target_level=_MILESTONE_THRESHOLDS[fam],
                status="pending",
            )
            for i, fam in enumerate(families)
        )
        milestone_checks = tuple(
            MilestoneCheck(
                milestone_id=f"m{i + 1}",
                target_level=_MILESTONE_THRESHOLDS[fam],
                episode_index=episode_index,
                achieved=False,
            )
            for i, fam in enumerate(families)
        )
        revision_triggers = tuple(
            RevisionTrigger(
                trigger_id=f"t{i + 1}",
                kind="mentor_dead",
                subject="0",  # placeholder; detection scans relationship_scores
                fired=False,
            )
            for i in range(3)
        )
        return ProgressionPlan(
            entity_id=entity_id,
            goal_queue=goal_queue,
            milestone_checks=milestone_checks,
            revision_triggers=revision_triggers,
            created_episode=episode_index,
            last_revised_episode=episode_index,
        )

    @staticmethod
    def detect_and_revise(
        entity_id: int,
        plan: ProgressionPlan,
        carry_forward: EntityCarryForward,
        social_memory: Optional["SocialMemoryRecord"],
        episode_index: int,
        persistent_entities: Dict[int, EntityCarryForward],
    ) -> Tuple[ProgressionPlan, Optional[NarrativeLedgerEntry]]:
        """Check revision triggers and rotate the goal_queue if one fires.

        Returns (revised_plan, NarrativeLedgerEntry) if a trigger fires, or
        (original_plan, None) if no trigger fires.  Only the first firing
        trigger is processed per call (one revision per episode per entity).

        Trigger kinds:
          mentor_dead      — any entity in social_memory.relationship_scores with
                             a positive score is dead (alive=False) in
                             persistent_entities. Detection requires social_memory.
          item_unavailable — plan.goal_queue[0].target_item_id is not present
                             in carry_forward.equipment["slots"].values().

        On fire:
          - Head goal moved to tail with status="blocked".
          - Next goal (index 1) becomes new head (unchanged).
          - Trigger marked fired=True.
          - NarrativeLedgerEntry emitted with event_type="plan_revision".
        """
        if not plan.goal_queue:
            return plan, None

        head = plan.goal_queue[0]
        if head.status in ("blocked", "completed"):
            return plan, None

        triggers = list(plan.revision_triggers)
        fired_index: Optional[int] = None

        for i, trigger in enumerate(triggers):
            if trigger.fired:
                continue

            if trigger.kind == "mentor_dead":
                if social_memory is None:
                    continue
                for mentor_id, score in social_memory.relationship_scores.items():
                    if score > 0:
                        cf = persistent_entities.get(mentor_id)
                        if cf is not None and not cf.alive:
                            fired_index = i
                            break

            elif trigger.kind == "item_unavailable":
                target_item = head.target_item_id
                if target_item is not None:
                    equipment = carry_forward.equipment
                    slots = (
                        equipment.get("slots", {})
                        if isinstance(equipment, dict)
                        else {}
                    )
                    if target_item not in slots.values():
                        fired_index = i

            if fired_index is not None:
                break

        if fired_index is None:
            return plan, None

        # Mark trigger as fired.
        triggers[fired_index] = dc_replace(triggers[fired_index], fired=True)

        # Rotate goal_queue: blocked head moves to tail.
        blocked_head = dc_replace(head, status="blocked")
        new_queue = plan.goal_queue[1:] + (blocked_head,)
        new_head_id = new_queue[0].goal_id if new_queue else ""

        revised_plan = dc_replace(
            plan,
            goal_queue=new_queue,
            revision_triggers=tuple(triggers),
            last_revised_episode=episode_index,
        )

        entry_id = f"{episode_index}:0:plan_revision:{entity_id}"
        entry = NarrativeLedgerEntry(
            episode=episode_index,
            tick=0,
            event_type="plan_revision",
            subject_id=str(entity_id),
            payload={"blocked_goal": head.goal_id, "new_head": new_head_id},
            significance=0.6,
            entry_id=entry_id,
        )

        return revised_plan, entry
