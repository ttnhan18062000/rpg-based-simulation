from __future__ import annotations

from dataclasses import replace
from typing import TYPE_CHECKING

from src.core.enums import ReasonCode
from src.core.updates import (
    EntityUpdate,
    StrategicUpdate,
    RejectionEvent,
)
from src.core.strategic import BlockerState
from src.core.state import _readonly_mapping
from src.engine.domain_logic import SimulationDomainLogic
from src.engine.legality import LegalityServiceV2
from src.engine.apply import ApplyPath

if TYPE_CHECKING:
    from src.core.state import AuthoritativeState
    from src.core.updates import StateUpdate


class ActionRoutingPhase:
    """
    Routes ENTITY_ACT task intents through authoritative domain logic.

    Must preserve:
        - sliding state awareness
        - task outcome annotation
        - rejection audit
        - deterministic entity ordering
    """

    @staticmethod
    def route(state: AuthoritativeState, update: StateUpdate) -> StateUpdate:
        """
        Law 300: Action Routing.

        Responsibilities:
            - route ENTITY_ACT tasks into authoritative domain logic
            - preserve the original task intent
            - annotate the task with SUCCESS / FAILURE
            - use sliding state so later actions in the same tick see earlier effects

        Critical law:
            If actor A kills target T earlier in this refinement pass, actor B must
            see T as incapacitated later in the same pass and must not receive a
            second kill reward.
        """

        def _normalize_reason(reason):
            """
            Normalize string/enum failure reasons into ReasonCode when possible.
            """
            if reason is None:
                return ReasonCode.UNKNOWN

            if isinstance(reason, ReasonCode):
                return reason

            if hasattr(reason, "value"):
                try:
                    return ReasonCode(reason.value)
                except Exception:
                    return reason

            reason_str = str(reason)

            if reason_str.startswith("ReasonCode."):
                reason_str = reason_str.split(".", 1)[1]

            if reason_str in ReasonCode.__members__:
                return ReasonCode[reason_str]

            try:
                return ReasonCode(reason_str)
            except Exception:
                return reason

        def _reason_key(reason):
            return reason.value if hasattr(reason, "value") else str(reason)

        def _target_for_action(payload):
            return payload.get("target_id") or payload.get("target_pos") or payload.get("target_position")

        refined_entity_updates = dict(update.entity_updates)
        new_world_events_add = list(update.world_events_add)

        # Optimization: Identify actors with ENTITY_ACT tasks early
        actors_with_tasks = [
            (eid, upd) for eid, upd in update.entity_updates.items()
            if upd.task and upd.task.work_kind_set == "ENTITY_ACT"
        ]
        
        if not actors_with_tasks:
            return update

        # Optimization: Use the original state as the base for action routing.
        # Passive logic is handled by the final Fused Apply pass.
        working_entities = dict(state.entities)
        for eid in sorted(update.entity_updates.keys()):
            ent_upd = update.entity_updates[eid]
            if eid in working_entities:
                working_entities[eid] = ApplyPath._apply_entity_update(working_entities[eid], ent_upd)

        # Create a sliding state proxy that updates its entity map.
        sliding_state = replace(state, entities=working_entities)

        for eid, ent_upd in sorted(actors_with_tasks):
            entity = state.entities.get(eid)
            if not entity or not entity.lifecycle.active:
                continue

            task_upd = ent_upd.task
            payload = dict(task_upd.payload_set or {})
            action = payload.get("action")
            if not action:
                continue

            # Survival actions (EAT/REST/SLEEP) bypass combat readiness —
            # biological necessity is never gated by combat cooldown.
            is_survival = action in ("EAT", "REST", "SLEEP")

            working_entity = working_entities.get(eid, entity)

            legal, reason = LegalityServiceV2.verify_action_legality(
                working_entity, action, sliding_state
            )

            if not legal:
                reason_value = reason.value if hasattr(reason, "value") else str(reason)
                failed_task = replace(task_upd, payload_set={**payload, "outcome": "FAILURE", "reason": reason_value})
                refined_entity_updates[eid] = replace(ent_upd, task=failed_task)

                new_rejection_events = list(update.rejection_events)
                new_rejections_delta = dict(update.rejections_delta)
                new_rejections_delta[reason_value] = new_rejections_delta.get(reason_value, 0) + 1
                new_rejection_events.append(RejectionEvent(
                    tick=state.tick, actor_id=eid, action_kind=action, reason=reason,
                    target_id=payload.get("target_id") or payload.get("target_pos")
                ))
                update = replace(update, entity_updates=refined_entity_updates, rejection_events=new_rejection_events, rejections_delta=new_rejections_delta, world_events_add=new_world_events_add)
                continue

            if not is_survival:
                ready, r_reason = LegalityServiceV2.verify_readiness(working_entity)
                if not ready:
                    reason_value = r_reason.value if hasattr(r_reason, "value") else str(r_reason)
                    failed_task = replace(task_upd, payload_set={**payload, "outcome": "FAILURE", "reason": reason_value})
                    new_rejection_events = list(update.rejection_events)
                    new_rejections_delta = dict(update.rejections_delta)
                    new_rejections_delta[reason_value] = new_rejections_delta.get(reason_value, 0) + 1
                    new_rejection_events.append(RejectionEvent(
                        tick=state.tick, actor_id=eid, action_kind=action, reason=r_reason,
                        target_id=payload.get("target_id") or payload.get("target_pos")
                    ))
                    refined_entity_updates[eid] = replace(ent_upd, task=failed_task, strategic=StrategicUpdate(
                        blockers_add_or_update=[BlockerState(id=f"blocker_nav_{reason_value}", kind="capability", subject=reason_value)]
                    ))
                    update = replace(update, entity_updates=refined_entity_updates, rejection_events=new_rejection_events, rejections_delta=new_rejections_delta, world_events_add=new_world_events_add)
                    continue

            action_updates = SimulationDomainLogic.execute_action(
                working_entity, payload=payload, current_tick=state.tick,
                neighbor_view=SimulationDomainLogic.get_neighbor_view(sliding_state, working_entity, radius=10.0),
                context=sliding_state
            )

            # TCK-20260824-CAUSAL-MEMORY-ROUTE-SCORING: emit a COMBAT_LOSS WorldEvent for a
            # defender who survives and takes damage -- deliberately NOT tied to
            # NearDeathHardeningPhase's hp_pct<=10% threshold, which would structurally
            # guarantee hp_pct<0.3 on every firing and starve CausalAttributionService's
            # avoid_enemy fallback branch (see plan.md Step 4).
            if action == "ATTACK":
                from src.domains.world_emergence.schema import WorldEvent, WorldEventCategory
                for action_eid, action_upd in action_updates.items():
                    if action_eid == eid or action_upd.combat is None:
                        continue
                    combat_upd = action_upd.combat
                    if combat_upd.alive_set is not False and combat_upd.damage_taken > 0:
                        defender_entity = state.entities.get(action_eid)
                        defender_region_id = defender_entity.navigation.region_id if defender_entity else None
                        new_world_events_add.append(WorldEvent(
                            category=WorldEventCategory.COMBAT_LOSS,
                            tick=state.tick,
                            region_id=defender_region_id,
                            subject=str(action_eid),
                        ))

            actor_action_upd = action_updates.get(eid)
            outcome = "SUCCESS"
            failure_reason = None
            if actor_action_upd is None:
                outcome, failure_reason = "FAILURE", "NO_ACTION_UPDATE"
            elif actor_action_upd.navigation and actor_action_upd.navigation.failure_reason:
                outcome, failure_reason = "FAILURE", actor_action_upd.navigation.failure_reason
            elif actor_action_upd.combat and actor_action_upd.combat.outcome_kind == "REJECTED":
                outcome, failure_reason = "FAILURE", actor_action_upd.combat.failure_reason
                
            if outcome == "FAILURE":
                audit_reason = _normalize_reason(failure_reason)
                audit_key = _reason_key(audit_reason)
                new_rejection_events = list(update.rejection_events)
                new_rejections_delta = dict(update.rejections_delta)
                new_rejections_delta[audit_key] = new_rejections_delta.get(audit_key, 0) + 1
                new_rejection_events.append(RejectionEvent(
                    tick=state.tick, actor_id=eid, action_kind=action, reason=audit_reason, target_id=_target_for_action(payload)
                ))
                update = replace(update, rejection_events=new_rejection_events, rejections_delta=new_rejections_delta, world_events_add=new_world_events_add)

            reason_value = failure_reason.value if hasattr(failure_reason, "value") else failure_reason
            # Survival actions reset the task to idle on success so the brain
            # can re-evaluate on the next cadence tick (entity stays near tavern).
            #
            # ATTACK + TARGET_INCAPACITATED also resets to idle -- a real, unrecoverable failure
            # (the target is dead/inactive; retrying can never succeed). Without this, the stale
            # target_id in payload keeps the task classified ENTITY_ACT with a non-empty payload,
            # which bypasses scheduler.py's own is_idle_act/brain-cadence gate entirely (that gate
            # only applies when payload is empty) -- the same failing attack gets re-dispatched
            # every tick readiness recovers (readiness regens from execute_attack's own -50.0
            # illegal-target penalty in ~5 real ticks), forever, confirmed via live corpus trace to
            # repeat for 180+ real ticks against the same dead target with no natural end
            # (TCK-20260809-COMBAT-STUCK-ATTACK-TASK-DEAD-TARGET). INSUFFICIENT_READINESS/
            # OUT_OF_RANGE are deliberately NOT reset here -- both are real, recoverable
            # conditions (readiness regens; range may close via a fresh pursuit decision), unlike
            # a dead target which can never become legal again.
            is_unrecoverable_attack_failure = (
                action == "ATTACK" and outcome == "FAILURE"
                and reason_value == ReasonCode.TARGET_INCAPACITATED.value
            )
            if (is_survival and outcome == "SUCCESS") or is_unrecoverable_attack_failure:
                # Wholesale-empty payload_set is required, not merely clearing action/target_id:
                # scheduler.py's own is_idle_act check (`work_kind=="ENTITY_ACT" and not
                # ent.task.payload`) needs a genuinely falsy payload to reclassify this entity
                # back to ENTITY_BRAIN scheduling on the next tick. Confirmed via live corpus
                # trace (TCK-20260810-COMBAT-PURSUIT-STALE-TARGET-SNAPSHOT-NEVER-RETARGETS): a
                # {"outcome":..., "reason":...}-only payload (non-empty but action/target_id-less)
                # still bypasses is_idle_act, and the stuck-retry-forever bug this reset exists to
                # prevent (TCK-20260809-COMBAT-STUCK-ATTACK-TASK-DEAD-TARGET) reoccurs -- one real
                # entity hit TARGET_INCAPACITATED 73 times in a 2000-tick run with a non-empty-but-
                # actionless payload, vs. ~4 with a genuinely empty one.
                annotated_task = replace(task_upd, payload_set={})
            else:
                annotated_task = replace(task_upd, payload_set={**payload, "outcome": outcome, **({"reason": reason_value} if reason_value else {})})

            for action_eid, action_upd in action_updates.items():
                existing_upd = refined_entity_updates.get(action_eid, EntityUpdate(entity_id=action_eid))
                merged = existing_upd.merge(action_upd)
                if action_eid == eid:
                    merged = replace(merged, task=annotated_task)
                refined_entity_updates[action_eid] = merged
                # Update sliding entities for later actors
                if action_eid in working_entities:
                    working_entities[action_eid] = ApplyPath._apply_entity_update(working_entities[action_eid], action_upd)
                    try:
                        object.__setattr__(sliding_state, "entities", _readonly_mapping(working_entities))
                        object.__setattr__(sliding_state, "_spatial_grid_cache", None)
                        object.__setattr__(sliding_state, "_occupancy_map_cache", None)
                        object.__setattr__(sliding_state, "_has_hostiles_or_dead_cache", None)
                        object.__setattr__(sliding_state, "_readonly_entities_cache", None)
                    except AttributeError:
                        pass

            if eid not in action_updates:
                refined_entity_updates[eid] = replace(ent_upd, task=annotated_task)

            update = replace(update, entity_updates=refined_entity_updates, world_events_add=new_world_events_add)

        return replace(
            update,
            entity_updates=refined_entity_updates,
            world_events_add=new_world_events_add,
        )
