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
from src.domains.combat_engagement.schema import OpponentModel
from src.domains.combat_engagement.memory_store import compute_salience, store_opponent_model
from src.systems.strategic_systems.belief import BeliefEntry


def opponent_subject_key(target_id: int) -> str:
    """
    The per-individual OpponentModel key for a target entity (docs/mechanics/
    04_strategic_cognition.md Sec 13.6: "keyed per individual, not per kind, for now").
    """
    return f"entity.{target_id}"


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
                # ReadModelCache's own dirty_set.all_dirty_entities check,
                # src/api/read_model_cache.py -- NOT apply_plan.py's `invalidate_read_model` field,
                # confirmed dead code, never read anywhere outside its own definition; correction
                # from TCK-20260908-DIRTY-SET-PASSIVE-DECAY-CONSUMER-INVESTIGATION) invalidating
                # the read model every tick too. An actor with no existing combat_risk belief (never met a hostile)
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

            # TCK-20260914-COMBAT-ENGAGEMENT-PERCEIVED-POWER: read this actor's real, durable
            # OpponentModel for `target` before evaluating -- previously always None (confirmed
            # via repo-wide grep: no real caller anywhere ever passed memory=), which meant
            # OpponentPerceptionService.estimate()'s own memory-blending logic was correct code
            # that never actually ran on a real memory. `subject_key` is per-individual (Sec 13.6).
            subject_key = opponent_subject_key(target.id)
            prior_memory = actor.cognition.memory.combat.opponent_stats.get(subject_key)

            # 2. Subjective Pre-combat evaluation
            result = CombatEngagementDecisionService.evaluate(actor, target, state, memory=prior_memory)

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

            # TCK-20260914-COMBAT-ENGAGEMENT-PERCEIVED-POWER: persist this tick's passive
            # observation into the actor's own durable OpponentModel collection -- read-through-
            # then-replace, following MemoryUpdatePhase.apply()'s own precedent
            # (src/domains/memory/phase.py) for writing a nested cognition sub-model via
            # EntityUpdate.cognition_bundle_set. Salience uses outcome_severity=0.0 here: no
            # combat occurred this tick, only observation (Sec 13.6's own combat-vs-observation
            # distinction; a real combat outcome's higher severity is Step 5's own concern).
            updated_model = OpponentModel(
                subject_key=subject_key,
                estimated_power=result.opponent_estimate.estimated_power,
                uncertainty=result.opponent_estimate.uncertainty,
                confidence=result.opponent_estimate.confidence,
                known_skill_ids=prior_memory.known_skill_ids if prior_memory else (),
                outcomes=prior_memory.outcomes if prior_memory else (),
                last_updated_tick=state.tick,
                salience=compute_salience(
                    prior_memory, result.opponent_estimate.estimated_power, outcome_severity=0.0
                ),
            )
            new_combat_memory = store_opponent_model(actor.cognition.memory.combat, updated_model)
            new_memory = dataclass_replace(actor.cognition.memory, combat=new_combat_memory)
            new_cognition = dataclass_replace(actor.cognition, memory=new_memory)

            entity_updates[actor.id] = EntityUpdate(
                entity_id=actor.id,
                intent_results=[],
                property_updates=prop_updates,
                strategic=strat_upd,
                cognition_bundle_set=new_cognition,
            )

        if entity_updates:
            update = StateUpdate(entity_updates=entity_updates)

        return update
