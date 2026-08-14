from __future__ import annotations
from typing import Optional, Tuple

from src.ai.goals.base import GoalScorer, GoalScore
from src.core.state import EntityState, AuthoritativeState
from src.core.strategic import GoalKind, ProjectKind, ObjectiveKind


class RegionStabilizationGoalScorer(GoalScorer):
    """
    GoalScorer wrapper around EventInterpreter.compute_danger_urgency() (src/systems/
    world_systems/events.py), registered under GoalKind.REGION_STABILIZATION as one candidate
    among many in tier 5 of StrategicIntelligenceSystem.evaluate_strategic_intent()
    (src/systems/strategic_systems/intelligence.py). See plan.md
    TCK-20260811-REGION-STABILIZATION-GOAL-SCORER, Design Decision #1: unlike
    SocialContractGoalScorer (live-reachable via an independent existing production writer),
    this scorer is the FIRST live-reachable path for LEG-RPG-116 (regional-danger-driven
    stabilization) -- interpret_regional_danger() itself has no production caller, before or
    after this ticket. Registering this scorer makes the mechanic live for the first time; this
    is a disclosed, intentional behavior-availability change, not a bypass-closure on an
    already-live path.
    """

    def score(self, entity: EntityState, state: AuthoritativeState) -> GoalScore:
        from src.engine.legality import LegalityServiceV2

        # Same "entity's current region" resolution this codebase already uses in 7+ other call
        # sites (src/world/ecology.py, regional_sovereignty.py, boss.py, spawn.py, calamity.py,
        # influence.py, camp.py -- all read directly, confirmed identical call shape) -- not a
        # bespoke lookup invented for this scorer.
        region = LegalityServiceV2.get_region_for_position(entity.navigation.position, state)
        if region is None:
            return GoalScore(kind=GoalKind.REGION_STABILIZATION, utility=0.0, target_id=None)

        from src.systems.world_systems.events import EventInterpreter

        urgency = EventInterpreter.compute_danger_urgency(region)
        if urgency is None:
            return GoalScore(kind=GoalKind.REGION_STABILIZATION, utility=0.0, target_id=None)

        # MUST be a lazy (function-local) import: mirrors AdventureGoalScorer's/
        # SocialContractGoalScorer's own documented reason -- intelligence.py's own top-level
        # `from src.ai.goals import GoalRegistry` creates a transitive module-load-order
        # dependency once this module is registered in src/ai/goals/__init__.py.
        from src.systems.strategic_systems.intelligence import (
            _ADVENTURE_ROUTE_SCORE_MAX,
            _GOAL_UTILITY_SCORE_MAX,
        )

        # New Finding #7: the ORIGINAL interpret_regional_danger() set
        # stabilize_project.score = urgency * 100 -- valid only while kind="stabilize" was a bare
        # string that fell through _score_scale_max()'s isinstance(kind, ProjectKind) check to
        # the 100-ceiling scale. Now that ProjectKind.STABILIZE is a real ProjectKind (AC1/AC5),
        # that check reclassifies the materialized project onto the 2.9-ceiling scale --
        # committing urgency*100 there would make it always trivially clear
        # evaluate_project_switch()'s lock-bypass gate, reproducing the
        # TCK-20260811-INTERRUPTION-BYPASS-RETENTION-MARGIN-SCALE-BUG defect class a third time.
        # Recalibrated to the SAME 0-2.9 ceiling ADVENTURE_ROUTE/SOCIAL_CONTRACT already share
        # (never modify _score_scale_max()/_ADVENTURE_ROUTE_SCORE_MAX itself -- see Scope Guards).
        raw_score = urgency * _ADVENTURE_ROUTE_SCORE_MAX
        utility = (raw_score / _ADVENTURE_ROUTE_SCORE_MAX) * _GOAL_UTILITY_SCORE_MAX

        # New Finding #8: real target_pos (region centroid), fixing the ORIGINAL, inherited
        # "wins but stalls" defect -- TacticalDecisionSystem._resolve_target_position()
        # (tactical.py:702-753) can never resolve a bare region id string (not int-castable, not
        # a coordinate tuple) and the original ObjectiveState never set target_position either.
        # Centroid formula mirrors src/world/influence.py:90-93's own "Center of region"
        # precedent exactly.
        target_pos: Tuple[float, float] = (
            (region.bounds[0] + region.bounds[2]) / 2.0,
            (region.bounds[1] + region.bounds[3]) / 2.0,
        )

        return GoalScore(
            kind=GoalKind.REGION_STABILIZATION,
            utility=utility,
            target_id=region.id,
            target_pos=target_pos,
            metadata={
                "region_id": region.id,
                "raw_score": raw_score,
                # New Finding #11: proj_kind/obj_kind resolved HERE, not in intelligence.py --
                # keeps intelligence.py's materialization branch a "dumb" consumer needing zero
                # new top-level imports, mirroring SocialContractGoalScorer's identical pattern.
                "proj_kind": ProjectKind.STABILIZE,
                "obj_kind": ObjectiveKind.INVESTIGATE,
            },
        )
