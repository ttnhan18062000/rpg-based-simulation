"""
src/domains/combat_engagement/phase.py
───────────────────────────────────────────────────────────────────────────────
Phase 4 — CombatEngagementPhase

Integrates sensor candidate targets with subjective postures.
Bounded overhead per tick via spatial filtering.
"""

from __future__ import annotations
from dataclasses import replace as dataclass_replace
from typing import Dict, List, Optional

from src.core.state import AuthoritativeState, EntityState
from src.core.strategic import RiskLevel
from src.core.updates import StateUpdate, EntityUpdate, StrategicUpdate
from src.domains.combat_engagement.service import CombatEngagementDecisionService
from src.domains.combat_engagement.resolver import PostureIntentResolver
from src.systems.strategic_systems.belief import BeliefEntry


# TCK-20260904-COMBAT-RISK-BELIEF-PRODUCER-DESIGN: the stable belief key this phase writes.
# MUST stay equal to HelpNeedEvaluator.evaluate()'s own lookup key
# (src/domains/cooperation/evaluators.py), because StrategicUpdate.beliefs_add_or_update is
# merged by `res[item.id] = item` (src/engine/patches.py::merge_dict) -- the BeliefEntry's own
# `id` IS the dict key. A stable (non-tick-suffixed) id is deliberate: combat_risk is a *current*
# assessment that each tick replaces in place, not an append-only history like the rumor/
# observation beliefs in BeliefCycleSystem, which would grow the dict without bound.
COMBAT_RISK_BELIEF_ID = "combat_risk"

# death_risk -> RiskLevel cutoffs. NOT invented: derived from constants already live in
# EngagementRiskEvaluator.evaluate() (src/domains/combat_engagement/risk_evaluator.py), which
# computes death_risk = clamp((1.0 / power_ratio) * 0.4, 0.0, 1.0):
#   power_ratio 2.0 (actor twice as strong)  -> death_risk 0.20
#   power_ratio 1.0 (evenly matched)         -> death_risk 0.40
#   death_risk > 0.80                        -> that evaluator's OWN "hp_critical_safety_lock"
#                                               severe-safety cutoff, and where its `near_death`
#                                               floor (max(0.9, ...)) deliberately lands.
# These are a documented, evidence-anchored starting point, tunable if real calibration data
# later says otherwise -- they are not a final tuned answer.
COMBAT_RISK_LOW_MAX = 0.20
COMBAT_RISK_NORMAL_MAX = 0.40
COMBAT_RISK_HIGH_MAX = 0.80


def death_risk_to_level(death_risk: float) -> RiskLevel:
    """Map an EngagementRiskEvaluation.death_risk float to a subjective RiskLevel."""
    if death_risk <= COMBAT_RISK_LOW_MAX:
        return RiskLevel.LOW
    if death_risk <= COMBAT_RISK_NORMAL_MAX:
        return RiskLevel.NORMAL
    if death_risk <= COMBAT_RISK_HIGH_MAX:
        return RiskLevel.HIGH
    return RiskLevel.EXTREME


def build_combat_risk_belief(death_risk: float, current_tick: int) -> BeliefEntry:
    """
    Build the real BeliefEntry this phase writes for an actor's own personal combat danger.

    `claim` carries the RiskLevel value (RiskLevel is a str Enum, so it round-trips losslessly);
    `certainty` carries the raw death_risk that produced it, so the consumer-facing level and the
    underlying continuous signal both survive into durable state.
    """
    level = death_risk_to_level(death_risk)
    return BeliefEntry(
        id=COMBAT_RISK_BELIEF_ID,
        subject=COMBAT_RISK_BELIEF_ID,
        claim=level.value,
        certainty=round(max(0.0, min(1.0, death_risk)), 2),
        source="observation",
        created_tick=current_tick,
        last_refreshed_tick=current_tick,
    )


class CombatEngagementPhase:
    """
    Evaluates dynamic pre-combat engagement postures at strategic cadence.
    """

    @staticmethod
    def apply(
        state: AuthoritativeState,
        context: Optional[dict] = None,
    ) -> StateUpdate:
        """
        Evaluate eligible actors on hostiles entering sensory visibility.
        """
        update = StateUpdate()
        entity_updates: Dict[int, EntityUpdate] = {}

        # 1. Filter actors (alive, active, hero class, etc.)
        actors = [e for e in state.entities.values() if e.combat.alive and e.lifecycle.active]
        if not actors:
            return update

        # To avoid pairwise NxN comparison, we query the spatial grid or fallback to capped Euclidean range
        for actor in actors:
            targets = []
            
            # Utilize the spatial query cache to resolve neighbors within range 10
            # M7/M10 optimization: check if state contains spatial_index or grid
            grid = getattr(state, "spatial_grid", None)
            if grid is not None:
                # Query index with absolute cap
                nearby_ids = grid.query_radius(actor.navigation.position, 10.0)
                for nid in nearby_ids:
                    if nid != actor.id:
                        e = state.entities.get(nid)
                        if e and e.combat.alive and e.lifecycle.active:
                            targets.append(e)
            else:
                # Fallback range check
                for e in state.entities.values():
                    if e.id != actor.id and e.combat.alive and e.lifecycle.active:
                        dist_sq = ((e.navigation.position[0] - actor.navigation.position[0]) ** 2 +
                                   (e.navigation.position[1] - actor.navigation.position[1]) ** 2)
                        if dist_sq <= 100.0:
                            targets.append(e)
            
            if not targets:
                continue

            # Limit candidates evaluated per entity (cap = 3) to strictly stay within strategic budget
            targets_to_evaluate = targets[:3]

            for target in targets_to_evaluate:
                # 2. Subjective Pre-combat evaluation
                result = CombatEngagementDecisionService.evaluate(actor, target, state)
                
                # Apply bridge mappings
                intent, strat_upd = PostureIntentResolver.resolve(
                    actor_id=actor.id,
                    target_id=target.id,
                    posture=result.posture,
                    target_pos=target.navigation.position,
                )
                
                # Update properties with chosen posture
                prop_updates = {
                    "last_combat_posture": result.posture.value,
                    "last_combat_posture_target": target.id,
                }

                # TCK-20260904-COMBAT-RISK-BELIEF-PRODUCER-DESIGN: write the actor's own
                # personal combat-risk belief from the death_risk this evaluation already
                # computed -- the real producer for the previously-unwritten "combat_risk"
                # belief that HelpNeedEvaluator.evaluate() (Phase 7) already consumes.
                # Reuses the existing evaluation only; deliberately does NOT widen target
                # evaluation breadth (the `break` below), which would multiply this phase's
                # own strategic-budget cost.
                risk_belief = build_combat_risk_belief(
                    death_risk=result.risk_evaluation.death_risk,
                    current_tick=state.tick,
                )
                if strat_upd is None:
                    strat_upd = StrategicUpdate(beliefs_add_or_update=[risk_belief])
                else:
                    strat_upd = dataclass_replace(
                        strat_upd,
                        beliefs_add_or_update=list(strat_upd.beliefs_add_or_update) + [risk_belief],
                    )

                entity_updates[actor.id] = EntityUpdate(
                    entity_id=actor.id,
                    intent_results=[],
                    property_updates=prop_updates,
                    strategic=strat_upd,
                )
                break # evaluate first target only


        if entity_updates:
            update = StateUpdate(entity_updates=entity_updates)

        return update
