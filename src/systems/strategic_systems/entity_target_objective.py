"""Lifecycle of an objective whose subject is a specific moving entity (typed ``target_entity_id``).

TCK-20261002-COMBAT-OBJECTIVE-TARGETS-ENTITY-VIA-FIXED-POINT-AND-NEVER-TERMINATES. Pure, read-only: the
caller (``StrategicIntelligenceSystem.evaluate_strategic_intent``) emits the ``StrategicUpdate`` and the
strategic work queue (``StrategicWorkQueue``) uses the same predicate to schedule the evaluation, so the two
can never disagree about when an objective has ended.
"""
from __future__ import annotations

from typing import TYPE_CHECKING, Optional

from src.core.strategic import ObjectiveStatus, ProjectStatus

if TYPE_CHECKING:
    from src.core.state import AuthoritativeState, EntityState
    from src.core.strategic import ObjectiveState

# Perception radius an entity-targeted objective is held to: the radius CombatEngageScorer chooses its
# target within (get_neighbor_view radius), so an objective ends when its target leaves the neighbourhood
# the scorer would have chosen it from.
ENTITY_TARGET_PERCEPTION_RADIUS = 10.0


def entity_target_outcome(
    hero: "EntityState", state: "AuthoritativeState", objective: "ObjectiveState"
) -> Optional[tuple[ObjectiveStatus, ProjectStatus]]:
    """Terminal (objective, project) status for an entity-targeted objective, or None while it holds.

      - target dead            -> RESOLVED / COMPLETED
      - target gone from state -> FAILED / ABANDONED
      - target outside ENTITY_TARGET_PERCEPTION_RADIUS (Manhattan) -> FAILED / ABANDONED
    """
    if objective.target_entity_id is None:
        return None
    target = state.entities.get(objective.target_entity_id)
    if target is None:
        return ObjectiveStatus.FAILED, ProjectStatus.ABANDONED
    if not target.combat.alive:
        return ObjectiveStatus.RESOLVED, ProjectStatus.COMPLETED
    hx, hy = hero.navigation.position
    tx, ty = target.navigation.position
    if abs(tx - hx) + abs(ty - hy) > ENTITY_TARGET_PERCEPTION_RADIUS:
        return ObjectiveStatus.FAILED, ProjectStatus.ABANDONED
    return None
