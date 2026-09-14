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


# outcome_kind values that never represent a real entity-vs-entity combat resolution, even when
# a CombatUpdate carries an attacker_id. Mirrors src/observability/event_extractor.py's own
# `_NON_COMBAT_OUTCOME_KINDS` check by value, not by import: src/domains/ may not import
# src/observability/ outside a small pinned allowlist neither this module nor this ticket is on
# (tests/architecture/test_phase18_import_boundaries.py) -- the *value* is the real, shared
# contract (both CombatUpdate.outcome_kind values), not the module that first checked it.
_NON_COMBAT_OUTCOME_KINDS = ("HAZARD", "REJECTED")

# Witnessed-combat's own perception radius -- the same 10.0 units Sec 13.1 already establishes
# for passive observation (SimulationDomainLogic.get_neighbor_view()), applied here to a
# real fight's participant positions instead of to the observer's own idle scanning (Sec 13.7).
WITNESSED_COMBAT_RADIUS = 10.0


def _read_through_cognition(
    entity_id: int,
    fallback_cognition,
    entity_updates: Dict[int, EntityUpdate],
    tick_update: Optional[StateUpdate],
):
    """
    TCK-20260914-COMBAT-ENGAGEMENT-PERCEIVED-POWER (real, disclosed cross-phase bug found via
    tests/integration/scenarios/test_causal_memory_route_scoring_e2e.py, not the ticket's own
    unit suite): `EntityUpdate.merge()`'s own `cognition_bundle_set` field is a whole-object
    REPLACE, not a per-subfield merge (src/core/updates.py). `memory_update` runs BEFORE
    `combat_engagement` in the same tick's pipeline (src/engine/pipeline.py) -- if this phase built
    its own updated CognitionModel from `entity.cognition` (the tick-START snapshot) and staged it
    via `cognition_bundle_set`, merging that into the tick's already-accumulated `update` silently
    DISCARDED whatever MemoryUpdatePhase (or any other earlier phase) had already written for that
    same entity this same tick -- e.g. a real `causal.entries` write vanishing the instant
    `ENABLE_COMBAT_ENGAGEMENT` went live, with no error, because "replace" doesn't merge sub-trees.

    Priority order for the base cognition to build on top of: (1) this phase's OWN
    already-accumulated write for this entity this call (`entity_updates` -- covers a witness who
    is also separately evaluated by the main per-actor loop in this same `apply()` invocation),
    (2) an EARLIER pipeline phase's write THIS SAME TICK (`tick_update` -- covers memory_update and
    any other phase that runs before combat_engagement), (3) the tick-start snapshot on the entity
    itself (no prior write this tick at all).
    """
    own_update = entity_updates.get(entity_id)
    if own_update is not None and own_update.cognition_bundle_set is not None:
        return own_update.cognition_bundle_set
    if tick_update is not None:
        prior_update = tick_update.entity_updates.get(entity_id)
        if prior_update is not None and prior_update.cognition_bundle_set is not None:
            return prior_update.cognition_bundle_set
    return fallback_cognition


def _merge_observation_into_updates(
    entity_updates: Dict[int, EntityUpdate],
    observer: EntityState,
    target_id: int,
    estimate,
    state: AuthoritativeState,
    outcome_severity: float,
    tick_update: Optional[StateUpdate] = None,
) -> None:
    """
    Read-through-then-replace `observer`'s own OpponentModel for `target_id`, merging the write
    into `entity_updates[observer.id]` in place -- reads any `cognition_bundle_set` an earlier
    write THIS SAME tick already staged for `observer`, whether from this same phase call (a
    witness who is also, separately, evaluating its own nearest hostile this tick) or from an
    earlier pipeline phase such as memory_update (`_read_through_cognition`'s own docstring).
    """
    subject_key = opponent_subject_key(target_id)
    base_cognition = _read_through_cognition(observer.id, observer.cognition, entity_updates, tick_update)
    prior_memory = base_cognition.memory.combat.opponent_stats.get(subject_key)

    updated_model = OpponentModel(
        subject_key=subject_key,
        estimated_power=estimate.estimated_power,
        uncertainty=estimate.uncertainty,
        confidence=estimate.confidence,
        known_skill_ids=prior_memory.known_skill_ids if prior_memory else (),
        outcomes=prior_memory.outcomes if prior_memory else (),
        last_updated_tick=state.tick,
        salience=compute_salience(prior_memory, estimate.estimated_power, outcome_severity=outcome_severity),
    )
    new_combat_memory = store_opponent_model(base_cognition.memory.combat, updated_model)
    new_memory = dataclass_replace(base_cognition.memory, combat=new_combat_memory)
    new_cognition = dataclass_replace(base_cognition, memory=new_memory)

    existing_update = entity_updates.get(observer.id)
    if existing_update is not None:
        entity_updates[observer.id] = dataclass_replace(existing_update, cognition_bundle_set=new_cognition)
    else:
        entity_updates[observer.id] = EntityUpdate(
            entity_id=observer.id, intent_results=[], cognition_bundle_set=new_cognition,
        )


def _apply_witnessed_combat(
    state: AuthoritativeState,
    tick_update: Optional[StateUpdate],
    entity_updates: Dict[int, EntityUpdate],
) -> None:
    """
    Sec 13.7: a witness is any other entity within perception radius of a real fight's own
    participants at the tick it happened -- updates the witness's own OpponentModel for BOTH
    participants directly (mutates `entity_updates` in place), a lesser-quality but real
    information source, better than nothing and worse than personal combat (Sec 13.5).
    """
    real_fights = _real_combat_this_tick(tick_update)
    if not real_fights:
        return

    living_active = [e for e in state.entities.values() if e.combat.alive and e.lifecycle.active]

    for defender_id, attacker_id in real_fights:
        defender = state.entities.get(defender_id)
        attacker = state.entities.get(attacker_id)
        if defender is None or attacker is None:
            continue

        participant_ids = {defender_id, attacker_id}
        for witness in living_active:
            if witness.id in participant_ids:
                continue
            near_defender = _within_radius(witness.navigation.position, defender.navigation.position, WITNESSED_COMBAT_RADIUS)
            near_attacker = _within_radius(witness.navigation.position, attacker.navigation.position, WITNESSED_COMBAT_RADIUS)
            if not (near_defender or near_attacker):
                continue

            from src.domains.combat_engagement.perception import OpponentPerceptionService

            for target in (defender, attacker):
                subject_key = opponent_subject_key(target.id)
                base_cognition = _read_through_cognition(witness.id, witness.cognition, entity_updates, tick_update)
                prior_memory = base_cognition.memory.combat.opponent_stats.get(subject_key)
                estimate = OpponentPerceptionService.estimate(witness, target, memory=prior_memory, state=state)
                _merge_observation_into_updates(
                    entity_updates, witness, target.id, estimate, state, outcome_severity=0.3,
                    tick_update=tick_update,
                )


def _within_radius(pos_a: Tuple[float, float], pos_b: Tuple[float, float], radius: float) -> bool:
    dist_sq = (pos_a[0] - pos_b[0]) ** 2 + (pos_a[1] - pos_b[1]) ** 2
    return dist_sq <= radius * radius


def _real_combat_this_tick(tick_update: Optional[StateUpdate]) -> List[Tuple[int, int]]:
    """
    Real (defender_id, attacker_id) pairs from this tick's own combat resolution, per Sec 13.7:
    "combat-resolution SimulationEvents already carry participant entity_id/target_id and a tick"
    -- read directly from the real CombatUpdate this tick's action_routing already produced,
    rather than waiting for a downstream event (no new event field, matching the spec's own
    citation that positions and participant ids already exist on state the phase already has).
    """
    pairs: List[Tuple[int, int]] = []
    if tick_update is None:
        return pairs
    for defender_id, e_upd in tick_update.entity_updates.items():
        combat_upd = getattr(e_upd, "combat", None)
        if combat_upd is None:
            continue
        attacker_id = getattr(combat_upd, "attacker_id", None)
        outcome_kind = getattr(combat_upd, "outcome_kind", None)
        if attacker_id is None or outcome_kind in _NON_COMBAT_OUTCOME_KINDS:
            continue
        pairs.append((defender_id, attacker_id))
    return pairs


class CombatEngagementPhase:
    """
    Evaluates dynamic pre-combat engagement postures at strategic cadence.
    """

    @staticmethod
    def apply(
        state: AuthoritativeState,
        context: Optional[dict] = None,
        tick_update: Optional[StateUpdate] = None,
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

        # Lazy import matching RoleModelSelectionPhase's own precedent for the identical query
        # shape (src/strategy/role_model_phase.py) -- avoids a module-level import cycle risk
        # between src.engine and src.domains.combat_engagement.
        from src.engine.spatial_query import SpatialQueryService

        # Real spatial index query -- see the TCK-20260914-COMBAT-ENGAGEMENT-PERCEIVED-POWER
        # comment below for why this replaced a dead hand-rolled grid check.
        for actor in actors:
            # Hostility-filtered (candidate_entity, dist_sq) pairs -- nearest hostile wins below.
            hostile_candidates: List[Tuple[EntityState, float]] = []

            # TCK-20260914-COMBAT-ENGAGEMENT-PERCEIVED-POWER: hoisted out of _consider() -- both
            # are actor-invariant (same value for every candidate `e` this actor considers) but
            # were being recomputed on every single call, found via profiling the O(n^2) spatial-
            # grid fix above (get_faction_id_str/is_hostile_compat were the real hot path, not the
            # neighbor lookup itself, once that was fixed).
            actor_faction = get_faction_id_str(actor)
            rel_context = RelationContext(combat_engaged=True)

            def _consider(e: EntityState) -> None:
                if not (e.combat.alive and e.lifecycle.active):
                    return
                dist_sq = ((e.navigation.position[0] - actor.navigation.position[0]) ** 2 +
                           (e.navigation.position[1] - actor.navigation.position[1]) ** 2)
                target_faction = get_faction_id_str(e)
                if semantics_service.is_hostile_compat(actor_faction, target_faction, rel_context):
                    hostile_candidates.append((e, dist_sq))

            # TCK-20260914-COMBAT-ENGAGEMENT-PERCEIVED-POWER: this block previously checked
            # `getattr(state, "spatial_grid", None)` for a real spatial index before falling back
            # to an O(n) full-entity scan per actor -- but `spatial_grid` was never a real
            # AuthoritativeState attribute (confirmed: only an unrelated, likewise-unpopulated
            # `_spatial_grid_cache` field exists), so `grid` was always `None` and every actor,
            # every tick, silently took the "fallback" path -- an O(n^2) scan for the whole loop,
            # present since 2026-05-30 (git blame), dormant only because ENABLE_COMBAT_ENGAGEMENT
            # defaulted OFF until this ticket's own Step 6. A real, disclosed defect: a construct
            # whose failure mode is silence -- no error, no warning, an optimization that simply
            # never engaged. Measured directly: ~1.9s per CombatEngagementPhase.apply() call at
            # 1000 entities before this fix (flat regardless of real combat-event count, ruling out
            # witnessed-combat as the cost driver). Fixed by using the same real, populated,
            # cached spatial index (`SpatialQueryService.nearby_entities()`,
            # `src/engine/spatial_query.py`, backed by `WorldIndexService.get_indexes()`) that
            # `RoleModelSelectionPhase` already uses for an identical radius-query shape
            # (`src/strategy/role_model_phase.py`) -- not a design choice, a working replacement
            # for a check that was never wired to anything real.
            nearby_ids = SpatialQueryService.nearby_entities(state, actor.navigation.position, 10.0)
            for nid in nearby_ids:
                if nid != actor.id:
                    e = state.entities.get(nid)
                    if e is not None:
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
            base_cognition = _read_through_cognition(actor.id, actor.cognition, entity_updates, tick_update)
            prior_memory = base_cognition.memory.combat.opponent_stats.get(subject_key)

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
            new_combat_memory = store_opponent_model(base_cognition.memory.combat, updated_model)
            new_memory = dataclass_replace(base_cognition.memory, combat=new_combat_memory)
            new_cognition = dataclass_replace(base_cognition, memory=new_memory)

            entity_updates[actor.id] = EntityUpdate(
                entity_id=actor.id,
                intent_results=[],
                property_updates=prop_updates,
                strategic=strat_upd,
                cognition_bundle_set=new_cognition,
            )

        # TCK-20260914-COMBAT-ENGAGEMENT-PERCEIVED-POWER (Sec 13.7): witnessed-combat third tier.
        # Runs after the main per-actor loop above so a witness who is also itself evaluating its
        # own nearest hostile this tick gets both writes merged, not overwritten.
        _apply_witnessed_combat(state, tick_update, entity_updates)

        if entity_updates:
            update = StateUpdate(entity_updates=entity_updates)

        return update
