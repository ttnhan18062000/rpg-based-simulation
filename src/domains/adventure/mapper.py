"""
src/domains/adventure/mapper.py
───────────────────────────────────────────────────────────────────────────────
Phase 3 — RouteToProjectMapper

Maps RouteFamily to strategic ProjectKind and ObjectiveKind.
Generates deterministic ProjectState and ObjectiveState instances.
"""

from __future__ import annotations
from typing import Tuple, Optional

from src.core.strategic import (
    ProjectKind,
    ObjectiveKind,
    ProjectState,
    ObjectiveState,
    ProjectStatus,
    ObjectiveStatus,
)
from src.domains.adventure.schema import RouteFamily


class RouteToProjectMapper:
    """
    Data-driven bridge connecting an Adventure RouteFamily to standard
    strategic projects and objectives.
    """

    # Static data-driven mapping
    _MAP = {
        RouteFamily.RECOVER: (ProjectKind.RECOVERY, ObjectiveKind.REACH_SERVICE),
        RouteFamily.BUY_UPGRADE: (ProjectKind.PREPARATION, ObjectiveKind.BUY_ITEM),
        RouteFamily.CRAFT_UPGRADE: (ProjectKind.CRAFTING, ObjectiveKind.ACQUIRE_ITEM),
        RouteFamily.TRAIN_SKILL: (ProjectKind.TRAINING, ObjectiveKind.REACH_LOCATION),
        RouteFamily.TAKE_EASY_QUEST: (ProjectKind.QUEST, ObjectiveKind.ACCEPT_QUEST),
        RouteFamily.HUNT_WEAK_ENEMY: (ProjectKind.COMBAT, ObjectiveKind.DEFEAT_ENEMY),
        RouteFamily.GATHER_RESOURCE: (ProjectKind.HARVESTING, ObjectiveKind.REACH_RESOURCE),
        RouteFamily.SELL_LOOT_FOR_GOLD: (ProjectKind.PREPARATION, ObjectiveKind.REACH_SERVICE),
        RouteFamily.ASK_INFORMATION: (ProjectKind.INFORMATION, ObjectiveKind.ASK_INFORMATION),
        RouteFamily.SCOUT_LOCATION: (ProjectKind.EXPLORATION, ObjectiveKind.REACH_LOCATION),
        RouteFamily.FORM_PARTY: (ProjectKind.SOCIAL, ObjectiveKind.REACH_LOCATION),
        RouteFamily.RETURN_TOWN: (ProjectKind.TRAVEL, ObjectiveKind.RETURN_TOWN),
        RouteFamily.QUEST_OPPORTUNITY: (ProjectKind.QUEST, ObjectiveKind.ACCEPT_QUEST),
    }

    @classmethod
    def get_kinds(cls, family: str) -> Tuple[Optional[ProjectKind], Optional[ObjectiveKind]]:
        """
        Return the ProjectKind and ObjectiveKind for the given RouteFamily.
        Raises ValueError if family is unknown.
        """
        # Ensure it is a valid RouteFamily member/value
        try:
            route_enum = RouteFamily(family)
        except ValueError:
            raise ValueError(f"Unknown route family string: {family}")

        if route_enum == RouteFamily.DEFER_WITH_REASON:
            return None, None

        return cls._MAP[route_enum]

    @classmethod
    def map_to_states(
        self,
        family: RouteFamily,
        entity_id: int,
        target: Optional[str] = None,
        target_pos: Optional[Tuple[float, float]] = None,
        tick: int = 0,
    ) -> Tuple[Optional[ProjectState], Optional[ObjectiveState]]:
        """
        Produce deterministic ProjectState and ObjectiveState instances based
        on the selected route family.
        """
        p_kind, o_kind = self.get_kinds(family)
        if p_kind is None or o_kind is None:
            return None, None

        # Deterministic IDs
        project_id = f"proj.{family.value}.ent{entity_id}.t{tick}"
        objective_id = f"obj.{family.value}.ent{entity_id}.t{tick}"

        obj = ObjectiveState(
            id=objective_id,
            kind=o_kind,
            target=target,
            target_position=target_pos,
            status=ObjectiveStatus.UNRESOLVED,
            blocker_ids=[],
        )

        project = ProjectState(
            id=project_id,
            kind=p_kind,
            status=ProjectStatus.ACTIVE,
            score=1.0,
            lock_until_tick=tick + 10,  # default strategic project lock duration
            objectives=[obj],
            active_objective_id=objective_id,
            created_tick=tick,
        )

        return project, obj
