"""
src/domains/combat_engagement/phase.py
───────────────────────────────────────────────────────────────────────────────
Phase 4 — CombatEngagementPhase

Integrates sensor candidate targets with subjective postures.
Bounded overhead per tick via spatial filtering.
"""

from __future__ import annotations
from dataclasses import replace as dataclass_replace
from typing import Dict, List, Optional, Tuple

from src.core.state import AuthoritativeState, EntityState
from src.core.strategic import RiskLevel
from src.core.updates import StateUpdate, EntityUpdate, StrategicUpdate
from src.content_semantics.faction import get_faction_id_str, get_faction_semantics_service
from src.content_semantics.relation import RelationContext
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

        TCK-20260904-COMBAT-RISK-BELIEF-PRODUCER-DESIGN (correction, 2026-09-08): a post-merge
        peer review found the target selection below previously had no hostility filter at all
        (an ally, a villager, or a child could be "evaluated" as the actor's combat threat) and a
        dead `[:3]`-then-`break` pattern that only ever evaluated whichever entity happened to
        come first out of the unordered spatial query -- silently writing `combat_risk` from an
        arbitrary neighbor rather than a real threat. Fixed: candidates are now filtered through
        the same `is_hostile_compat()` faction-relation check `src/engine/legality.py`/
        `tactical.py`/`combat_rewards.py` already use for this exact question, and exactly the
        nearest hostile candidate is evaluated -- still one `evaluate()` call per actor per tick,
        same strategic-budget cost as before, just correctly targeted.
        """
        update = StateUpdate()
        entity_updates: Dict[int, EntityUpdate] = {}

        # 1. Filter actors (alive, active, hero class, etc.)
        actors = [e for e in state.entities.values() if e.combat.alive and e.lifecycle.active]
        if not actors:
            return update

        semantics_service = get_faction_semantics_service()

        # To avoid pairwise NxN comparison, we query the spatial grid or fallback to capped Euclidean range
        for actor in actors:
            # Hostility-filtered (candidate_entity, dist_sq) pairs -- nearest hostile wins below.
            hostile_candidates: List[Tuple[EntityState, float]] = []

            def _consider(e: EntityState) -> None:
                if not (e.combat.alive and e.lifecycle.active):
                    return
                dist_sq = ((e.navigation.position[0] - actor.navigation.position[0]) ** 2 +
                           (e.navigation.position[1] - actor.navigation.position[1]) ** 2)
                actor_faction = get_faction_id_str(actor)
                target_faction = get_faction_id_str(e)
                rel_context = RelationContext(combat_engaged=True)
                if semantics_service.is_hostile_compat(actor_faction, target_faction, rel_context):
                    hostile_candidates.append((e, dist_sq))

            # Utilize the spatial query cache to resolve neighbors within range 10
            # M7/M10 optimization: check if state contains spatial_index or grid
            grid = getattr(state, "spatial_grid", None)
            if grid is not None:
                # Query index with absolute cap
                nearby_ids = grid.query_radius(actor.navigation.position, 10.0)
                for nid in nearby_ids:
                    if nid != actor.id:
                        e = state.entities.get(nid)
                        if e is not None:
                            _consider(e)
            else:
                # Fallback range check
                for e in state.entities.values():
                    if e.id != actor.id:
                        dist_sq = ((e.navigation.position[0] - actor.navigation.position[0]) ** 2 +
                                   (e.navigation.position[1] - actor.navigation.position[1]) ** 2)
                        if dist_sq <= 100.0:
                            _consider(e)

            if not hostile_candidates:
                # TCK-20260904-COMBAT-RISK-BELIEF-PRODUCER-DESIGN (correction, 2026-09-08): the
                # hostility filter above removed the accidental every-tick refresh the old
                # arbitrary-neighbor version relied on to keep this module's own documented
                # invariant true (COMBAT_RISK_BELIEF_ID's docstring: "a *current* assessment
                # that each tick replaces in place"). Without this, the belief only got written
                # while a hostile was in range and then stuck permanently at its last value once
                # the threat left or died -- HelpNeedEvaluator.evaluate() has no staleness check
                # and BeliefCycleSystem.decay_stale_beliefs() only touches `leads`, never
                # `beliefs`, so nothing else would ever clear it. Writing a real no-threat (LOW)
                # assessment restores the invariant at zero added evaluate() cost -- no target
                # means no posture/intent resolution, but it does mean a real, current "no
                # threat" belief.
                #
                # (2nd correction, 2026-09-08, same review round): only write when it actually
                # changes something -- an earlier version wrote this unconditionally for every
                # actor with no hostile nearby, every tick. Since combat_engagement's own output
                # domain is "strategic" (src/engine/phase_graph.py), and this phase runs whenever
                # `movement`/`combat` are dirty (i.e. essentially every tick in a moving world),
                # that meant every living actor got a fresh EntityUpdate.strategic every tick --
                # ds.strategic_entities permanently non-empty, defeating dirty-set short-
                # circuiting for every downstream phase gated on "strategic", and (per
                # apply_plan.py's invalidate_read_model gate) invalidating the read model every
                # tick too. An actor with no existing combat_risk belief (never met a hostile)
                # correctly needs no write at all -- HelpNeedEvaluator already degrades an absent
                # belief to NORMAL, identical to a real LOW belief for its own purposes -- and an
                # actor already sitting at LOW needs no re-write either. Only a stale non-LOW
                # belief (a real threat that has since left) needs downgrading, and only once,
                # on the transition tick -- which is the real event this producer models anyway.
                existing_belief = actor.strategic.beliefs.get(COMBAT_RISK_BELIEF_ID)
                needs_no_threat_write = (
                    existing_belief is not None
                    and getattr(existing_belief, "claim", None) != RiskLevel.LOW.value
                )
                if needs_no_threat_write:
                    no_threat_belief = build_combat_risk_belief(death_risk=0.0, current_tick=state.tick)
                    entity_updates[actor.id] = EntityUpdate(
                        entity_id=actor.id,
                        intent_results=[],
                        strategic=StrategicUpdate(beliefs_add_or_update=[no_threat_belief]),
                    )
                continue

            # Evaluate exactly the nearest hostile candidate -- one evaluate() call per actor
            # per tick, matching the strategic-budget constraint this phase has always had.
            target, _nearest_dist_sq = min(hostile_candidates, key=lambda pair: pair[1])

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

        if entity_updates:
            update = StateUpdate(entity_updates=entity_updates)

        return update
