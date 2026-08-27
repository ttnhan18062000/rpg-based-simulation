from __future__ import annotations
from typing import Optional, Tuple

from src.ai.goals.base import GoalScorer, GoalScore
from src.core.state import EntityState, AuthoritativeState
from src.core.enums import EntityRole
from src.core.strategic import GoalKind, ProjectKind, ObjectiveKind
from src.world.occupation_config import BASE_OCCUPATION_DENSITY, MIN_OCCUPATION_SLOTS

# TCK-20260824-OCCUPATION-CHANGE-TRIGGER, Design Decision #2: role -> attribute family mapping,
# chosen to align with RoleSemanticsService's existing family groupings (is_civilian groups
# CITIZEN+SHOPKEEPER, is_worker is WORKER-only, GUARD is in the is_combatant family) rather than
# an arbitrary pairing. Fixed evaluation order also doubles as the destination-role priority order.
_CANDIDATE_ROLES: Tuple[int, ...] = (EntityRole.SHOPKEEPER, EntityRole.WORKER, EntityRole.GUARD)
_ROLE_APTITUDE_ATTR = {
    EntityRole.SHOPKEEPER: "charisma",
    EntityRole.WORKER: "endurance",
    EntityRole.GUARD: "strength",
}


class OccupationChangeGoalScorer(GoalScorer):
    """
    GoalScorer for a CITIZEN entity taking an open, skill-matched civilian job
    (SHOPKEEPER/WORKER/GUARD), registered under GoalKind.OCCUPATION_CHANGE as one candidate among
    many in tier 5 of StrategicIntelligenceSystem.evaluate_strategic_intent()
    (src/systems/strategic_systems/intelligence.py). Structured to mirror
    RegionStabilizationGoalScorer exactly -- see plan.md TCK-20260824-OCCUPATION-CHANGE-TRIGGER,
    Design Decisions 1-3.
    """

    def score(self, entity: EntityState, state: AuthoritativeState) -> GoalScore:
        if entity.identity.role != EntityRole.CITIZEN:
            return GoalScore(kind=GoalKind.OCCUPATION_CHANGE, utility=0.0, target_id=None)

        from src.engine.legality import LegalityServiceV2

        region = LegalityServiceV2.get_region_for_position(entity.navigation.position, state)
        if region is None:
            return GoalScore(kind=GoalKind.OCCUPATION_CHANGE, utility=0.0, target_id=None)

        # Single pass over all entities, tallying live headcount per candidate role whose own
        # region matches this entity's region -- bounds the scan to one pass regardless of how
        # many of the 3 roles are checked (same per-entity-per-tick cost class as
        # RegionStabilizationGoalScorer/spawn.py's own region lookups).
        counts = {role: 0 for role in _CANDIDATE_ROLES}
        for other in state.entities.values():
            if not other.combat.alive or other.identity.role not in counts:
                continue
            other_region = LegalityServiceV2.get_region_for_position(other.navigation.position, state)
            if other_region is not None and other_region.id == region.id:
                counts[other.identity.role] += 1

        xmin, ymin, xmax, ymax = region.bounds
        area = (xmax - xmin) * (ymax - ymin)

        dest_role: Optional[int] = None
        for role in _CANDIDATE_ROLES:
            target_count = max(
                MIN_OCCUPATION_SLOTS,
                int((area / 10000.0) * BASE_OCCUPATION_DENSITY[role]),
            )
            skill_ok = getattr(entity.attributes, _ROLE_APTITUDE_ATTR[role]) >= 5
            if counts[role] < target_count and skill_ok:
                dest_role = role
                break

        if dest_role is None:
            return GoalScore(kind=GoalKind.OCCUPATION_CHANGE, utility=0.0, target_id=None)

        from src.systems.strategic_systems.intelligence import (
            _ADVENTURE_ROUTE_SCORE_MAX,
            _GOAL_UTILITY_SCORE_MAX,
        )

        # Design Decision: unlike RegionStabilizationGoalScorer's urgency-proportional score, this
        # trigger is a binary match/no-match condition, not a graduated signal -- a flat
        # near-ceiling constant honestly represents "conditions met, fire now" without inventing
        # a fake continuous metric.
        raw_score = _ADVENTURE_ROUTE_SCORE_MAX * 0.9
        utility = (raw_score / _ADVENTURE_ROUTE_SCORE_MAX) * _GOAL_UTILITY_SCORE_MAX

        target_pos: Tuple[float, float] = (
            (region.bounds[0] + region.bounds[2]) / 2.0,
            (region.bounds[1] + region.bounds[3]) / 2.0,
        )

        return GoalScore(
            kind=GoalKind.OCCUPATION_CHANGE,
            utility=utility,
            target_id=region.id,
            target_pos=target_pos,
            metadata={
                "region_id": region.id,
                "dest_role": int(dest_role),
                "raw_score": raw_score,
                "proj_kind": ProjectKind.CAREER_CHANGE,
                "obj_kind": ObjectiveKind.CHANGE_OCCUPATION,
            },
        )
