"""
src/domains/campaigns/progression_plan.py
───────────────────────────────────────────────────────────────────────────────
ProgressionPlan model — long-term build-goal planner for HERO entities.

Design constraints (same as state.py / social_memory.py):
  - MUST NOT import from src.engine or src.core.state at module level.
  - All sub-records are frozen (immutable after construction).
  - to_dict() / from_dict() provide JSON-safe round-trip.
  - Tuple fields serialize as lists in JSON; reconstructed as tuples on load.
  - Sorted dict keys for determinism.

Populated by: E61B ProgressionPlanExporter (end-of-episode hook).
Consumed by:  E61B ProgressionPlanImporter (start-of-episode hook).
Stored in:    CampaignState.progression_plans (Dict[int, ProgressionPlan]).
"""

from __future__ import annotations

from dataclasses import dataclass, replace as dc_replace
from typing import Optional, Tuple


@dataclass(frozen=True)
class BuildGoal:
    """One step in an entity's build queue.

    target_route_family is stored as str (RouteFamily.value) to avoid a
    circular import between this module and src/domains/adventure/schema.py.

    status values: "pending" | "in_progress" | "completed" | "blocked"
    """

    goal_id: str
    target_route_family: str
    target_item_id: Optional[str]
    target_level: Optional[int]
    status: str

    def to_dict(self) -> dict:
        return {
            "goal_id": self.goal_id,
            "target_route_family": self.target_route_family,
            "target_item_id": self.target_item_id,
            "target_level": self.target_level,
            "status": self.status,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "BuildGoal":
        return cls(
            goal_id=d["goal_id"],
            target_route_family=d["target_route_family"],
            target_item_id=d.get("target_item_id"),
            target_level=d.get("target_level"),
            status=d["status"],
        )


@dataclass(frozen=True)
class MilestoneCheck:
    """A level threshold check tied to a specific episode.

    episode_index — episode by which target_level should be reached.
    achieved      — True once the entity reached target_level in that episode.
    """

    milestone_id: str
    target_level: int
    episode_index: int
    achieved: bool

    def to_dict(self) -> dict:
        return {
            "milestone_id": self.milestone_id,
            "target_level": self.target_level,
            "episode_index": self.episode_index,
            "achieved": self.achieved,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "MilestoneCheck":
        return cls(
            milestone_id=d["milestone_id"],
            target_level=d["target_level"],
            episode_index=d["episode_index"],
            achieved=d["achieved"],
        )


@dataclass(frozen=True)
class RevisionTrigger:
    """Condition that signals the plan should be revised.

    kind values: "mentor_dead" | "item_unavailable" | "goal_completed"
    subject     — entity_id (str), item_id, or goal_id depending on kind.
    fired       — True once the trigger has been evaluated and acted upon.
    """

    trigger_id: str
    kind: str
    subject: str
    fired: bool

    def to_dict(self) -> dict:
        return {
            "trigger_id": self.trigger_id,
            "kind": self.kind,
            "subject": self.subject,
            "fired": self.fired,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "RevisionTrigger":
        return cls(
            trigger_id=d["trigger_id"],
            kind=d["kind"],
            subject=d["subject"],
            fired=d["fired"],
        )


@dataclass(frozen=True)
class ProgressionPlan:
    """Long-term build-goal plan for a single HERO entity.

    Immutable — mutations are applied via dataclasses.replace().

    goal_queue          — ordered build goals; first item is the active goal.
    milestone_checks    — level thresholds to verify at episode boundaries.
    revision_triggers   — conditions that indicate the plan needs revision (E61D).
    created_episode     — episode index when the plan was first written.
    last_revised_episode — episode index of the most recent revision (0 = never revised).
    """

    entity_id: int
    goal_queue: Tuple[BuildGoal, ...]
    milestone_checks: Tuple[MilestoneCheck, ...]
    revision_triggers: Tuple[RevisionTrigger, ...]
    created_episode: int
    last_revised_episode: int

    def to_dict(self) -> dict:
        return {
            "entity_id": self.entity_id,
            "goal_queue": [g.to_dict() for g in self.goal_queue],
            "milestone_checks": [m.to_dict() for m in self.milestone_checks],
            "revision_triggers": [r.to_dict() for r in self.revision_triggers],
            "created_episode": self.created_episode,
            "last_revised_episode": self.last_revised_episode,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "ProgressionPlan":
        return cls(
            entity_id=d["entity_id"],
            goal_queue=tuple(BuildGoal.from_dict(g) for g in d.get("goal_queue", [])),
            milestone_checks=tuple(
                MilestoneCheck.from_dict(m) for m in d.get("milestone_checks", [])
            ),
            revision_triggers=tuple(
                RevisionTrigger.from_dict(r) for r in d.get("revision_triggers", [])
            ),
            created_episode=d["created_episode"],
            last_revised_episode=d["last_revised_episode"],
        )


# ---------------------------------------------------------------------------
# ProgressionPlanExporter
# ---------------------------------------------------------------------------


class ProgressionPlanExporter:
    """Export a ProgressionPlan at episode end for carry-forward.

    Called by CampaignOrchestrator._advance_state() after entity carry-forwards
    are extracted. Returns None for dead entities or entities with no plan.
    """

    @staticmethod
    def export(
        entity_id: int,
        current_plan: Optional[ProgressionPlan],
        alive: bool,
    ) -> Optional[ProgressionPlan]:
        """Return plan for carry-forward, or None if the plan should be dropped.

        Rules:
        - No current plan → None
        - Entity is dead (alive=False) → None (dead entities do not carry plans)
        - Entity is alive and goal_queue non-empty → return plan unchanged
        - Entity is alive but goal_queue is empty → return plan unchanged
          (an empty queue is a valid completed-plan state; do not drop it)
        """
        if current_plan is None:
            return None
        if not alive:
            return None
        return current_plan


# ---------------------------------------------------------------------------
# ProgressionPlanImporter
# ---------------------------------------------------------------------------


class ProgressionPlanImporter:
    """Import and update a ProgressionPlan at the start of a new episode.

    Called by CampaignOrchestrator._build_initial_state() for every entity
    that has a plan in CampaignState.progression_plans. Updates milestone
    achieved flags based on the entity's carried level; returns a new plan
    via dataclasses.replace() — the original is unchanged (frozen).
    """

    @staticmethod
    def import_plan(
        entity_id: int,
        plan: ProgressionPlan,
        new_episode_index: int,
        entity_level: int,
    ) -> ProgressionPlan:
        """Return a new ProgressionPlan with milestones updated for entity_level.

        MilestoneCheck.achieved is set to True when target_level <= entity_level.
        Already-achieved milestones are left True.
        """
        if not plan.milestone_checks:
            return plan

        updated_checks = tuple(
            dc_replace(check, achieved=True)
            if (not check.achieved and entity_level >= check.target_level)
            else check
            for check in plan.milestone_checks
        )

        if updated_checks == plan.milestone_checks:
            return plan

        return dc_replace(plan, milestone_checks=updated_checks)
