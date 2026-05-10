from __future__ import annotations
from typing import TYPE_CHECKING, List, Dict, Optional, Any, Set
from dataclasses import replace
import logging

if TYPE_CHECKING:
    from src.core.state import AuthoritativeState
    from src.core.updates import StateUpdate, EntityUpdate

logger = logging.getLogger(__name__)

class AuthoritativeApplyPipeline:
    """
    Law: The pipeline is the singular bottleneck for authoritative truth.
    Proof: All mutations must pass through refine() and be bit-identical.
    VERIFIED v2: AuthoritativeApplyPipeline (Milestone D)
    """

    @staticmethod
    def refine(state: AuthoritativeState, update: StateUpdate) -> StateUpdate:
        """
        Singular entry point for authoritative state transition refinement.
        Orchestrates systems in the correct causal order.
        """
        # 1. Identity & Lifecycle (High Priority)
        # 2. Strategic Intents (Evaluating long-term projects)
        from src.systems.strategic import StrategicIntelligenceSystem
        from src.systems.redirection import StrategicRedirectionSystem
        from src.systems.navigation import NavigationSystem
        from src.engine.interaction import InteractionSystem
        from src.engine.blacksmith import BlacksmithSystem
        from src.systems.groups import GroupSystem
        from src.systems.lifecycle import LifecycleSystem
        from src.engine.legality import LegalityServiceV2
        from src.core.updates import EntityUpdate
        
        # 0. Trust Boundary: strip raw world-side effects from worker proposals.
        update = AuthoritativeApplyPipeline._strip_untrusted_world_effects(update)
        
        # 0.1 Actor Validity
        # Reject proposals from dead/inactive/incapacitated actors before any subsystem
        # can route their movement, actions, resource intents, or interaction progress.
        #
        # This must run after trust-boundary stripping because raw worker rewards/world
        # mutations should already be removed, but before contract/quest/action/movement
        # routing because invalid actors must not participate in the tick.
        update = AuthoritativeApplyPipeline._resolve_actor_validity(state, update)

        # 0.05 Actor Validity Enforcement (Status: Stunned, Frozen, Dead)
        update = AuthoritativeApplyPipeline._resolve_actor_validity(state, update)
        
        # 0.1 Contract Lifecycle
        # Expire stale social contracts before any later system can consume them.
        #
        # Why this must run early:
        #   - expired recruitment offers should not be accepted
        #   - expired POSITION_SWAP contracts should not move entities
        #   - expired loan/protection/merchant contracts should not affect strategy
        #
        # This phase only updates contract statuses. It should not move entities,
        # transfer inventory, or mutate world resources.
        update = AuthoritativeApplyPipeline._resolve_contract_expirations(state, update)
        
        # 1. Apply Blacksmith/Crafting Laws (Milestone 3)
        update = BlacksmithSystem.enforce(state, update)
        
        # 2. Task/Intent Routing (Converting high-level tasks to low-level intents)
        update = AuthoritativeApplyPipeline._route_interaction_intent(state, update)
        
        # 3. Interaction Enforcement (Harvesting, Chests)
        update = InteractionSystem.enforce(state, update)
        
        # 4. Action Enforcement (Combat, Abilities)
        update = AuthoritativeApplyPipeline._route_action_intent(state, update)
        
        # 4.1 Near-Death Hardening
        # Must run after action/combat routing, because it depends on CombatUpdate.hp_delta.
        # Must run before lifecycle/evolution finalization so the hardened combat update
        # is part of the same authoritative tick.
        update = AuthoritativeApplyPipeline._apply_near_death_hardening(state, update)
        
        # Phase 8: Infrastructure Sabotage (LEG-RPG-006)
        from src.engine.sabotage import BuildingSabotageSystem
        from src.engine.town_resolution import TownResolutionSystem
        update = BuildingSabotageSystem.resolve(state, update)
        update = TownResolutionSystem.resolve(state, update)
        
        # Phase 7 Implementation: World Dynamics (Hazards, Spawns, Decays)
        # VERIFIED v2: passive_world_progression
        from src.systems.generator import EntityGenerator
        from src.engine.world_dynamics import WorldDynamicsSystem
        generator = EntityGenerator(state.seed + state.tick)
        generator._last_id = state.next_entity_id - 1
        update = WorldDynamicsSystem.resolve_dynamics(state, update, generator)
        
        # 4.5 Quest Reward Authority
        # Converts quest completion / reward retry into ResourceTransferIntent.
        # This must run before _resolve_resource_transactions so reward delivery is
        # capacity-checked atomically.
        update = AuthoritativeApplyPipeline._resolve_quest_rewards(state, update)
        
        # 5. Resource Transaction Laws (Transfers, Drops)
        # Atomic Resource Transactions
        from src.engine.shop import ShopSystem
        update = ShopSystem.enforce(state, update)
        update = AuthoritativeApplyPipeline._resolve_resource_transactions(state, update)
        
        # Phase 8: Evolution & Leveling (LEG-RPG-143)
        from src.engine.evolution import EvolutionSystem
        update = EvolutionSystem.evaluate(state, update)
        
        # 6. Strategic Evaluation (Blockers, Projects, Concerns)
        update = StrategicIntelligenceSystem.resolve_blockers(state, update)
        update = StrategicIntelligenceSystem.evaluate_all_concerns(state, update)
        update = StrategicIntelligenceSystem.evaluate_all_strategic_intents(state, update)
        update = StrategicRedirectionSystem.enforce(state, update)
        
        # 7.0 Position Swap Contracts / Mutual Corridor Passing
        # This must run before normal movement routing. Otherwise MovementSystem sees
        # the target tile as occupied and may choose sidestep/yield/failure instead of
        # the explicit consensual adjacent swap.
        update = AuthoritativeApplyPipeline._resolve_position_swaps(state, update)
        
        # 7.1 Navigation & Movement (Pathfinding, Obstacles)
        update = AuthoritativeApplyPipeline._route_movement_intent(state, update)

        # 7.5 Final Occupancy Conflict Resolution
        # This protects the authoritative apply path from invalid worker proposals
        # that directly set EntityUpdate.new_position.
        update = AuthoritativeApplyPipeline._resolve_occupancy_conflicts(state, update)
        
        # 8. Lifecycle Enforcement (Death, Respawn)
        update = LifecycleSystem.resolve_lifecycle(state, update)
        
        # 9. Group Logic (Formation & Coordination)
        from src.engine.apply import ApplyPath
        # VERIFIED v2: GroupSystem (RPG-SOC-200)
        working_state_for_groups = ApplyPath.apply_generation(state, update)
        group_update = GroupSystem.update_groups(working_state_for_groups, update)
        
        # Merge group updates back into main update
        new_groups_add = list(update.groups_add_or_update)
        group_ids = {g.id for g in new_groups_add}
        for g in group_update.groups_add_or_update:
            if g.id in group_ids:
                new_groups_add = [gr if gr.id != g.id else g for gr in new_groups_add]
            else:
                new_groups_add.append(g)

        new_groups_remove = list(set(list(update.groups_remove) + list(group_update.groups_remove)))
        
        refined_entity_updates = dict(update.entity_updates)
        for eid, eupd in group_update.entity_updates.items():
             existing = refined_entity_updates.get(eid, EntityUpdate(entity_id=eid))
             refined_entity_updates[eid] = existing.merge(eupd)

        update = replace(update, 
            groups_add_or_update=new_groups_add,
            groups_remove=new_groups_remove,
            entity_updates=refined_entity_updates
        )

        return update
    
    @staticmethod
    def _strip_untrusted_world_effects(update: StateUpdate) -> StateUpdate:
        """
        Trust-boundary hardening.

        LAW 300.2:
            Worker/raw proposals may express intent, but they may NOT directly
            submit authoritative economy, reward, quest-status, or world mutations.

        Raw worker proposals are allowed to carry:
            - movement/navigation intent
            - task intent
            - interaction intent/progress
            - combat result fields, if produced by the combat/action route

        Raw worker proposals are NOT allowed to carry:
            - direct InventoryUpdate gold/items
            - direct RewardUpdate XP/evolution
            - QUEST_REWARD / KILL_REWARD / TAX ResourceTransferIntent
            - QuestUpdate.status_set
            - direct node/building/chest/corpse/ground-item mutations

        Why combat is preserved:
            This boundary strips reward/economy payloads attached to combat, not the
            combat damage itself. Combat reward must flow through authoritative
            ResourceTransferIntent processing, but damage_taken can remain a combat
            result.
        """
        from dataclasses import replace

        from src.core.updates import QuestUpdate

        sanitized_entity_updates = {}

        blocked_transfer_kinds = {
            "QUEST_REWARD",
            "REWARD",
            "KILL_REWARD",
            "TAX",
        }

        for entity_id, entity_update in update.entity_updates.items():
            clean_quest = entity_update.quest

            if clean_quest is not None:
                clean_quest = QuestUpdate(
                    quest_id=clean_quest.quest_id,
                    progress_delta=clean_quest.progress_delta,
                    status_set=None,
                    multi_updates=getattr(clean_quest, "multi_updates", []),
                )

            clean_resource_transfers = [
                transfer
                for transfer in entity_update.resource_transfers
                if transfer.transfer_kind not in blocked_transfer_kinds
            ]

            sanitized_entity_updates[entity_id] = replace(
                entity_update,

                # Direct economy/reward mutation is never trusted from raw workers.
                inventory=None,
                reward=None,

                # Direct readiness/biological mutation is also not trusted.
                readiness_delta=0.0,
                biological=None,

                # Preserve combat damage/effects, but strip attached rewards via
                # clean_resource_transfers above.
                combat=entity_update.combat,

                quest=clean_quest,
                resource_transfers=clean_resource_transfers,
            )

        return replace(
            update,
            entity_updates=sanitized_entity_updates,

            # Direct world-side effects are generated only by authoritative systems.
            node_updates={},
            building_updates={},
            chest_updates={},
            ground_items_remove=[],
            corpses_remove=[],
        )
        
    @staticmethod
    def _resolve_actor_validity(
        state: AuthoritativeState,
        update: StateUpdate,
    ) -> StateUpdate:
        """
        Law 300.1: Actor Validity.

        Invalid actors may not submit authoritative proposals.

        Invalid means:
            - missing actor
            - lifecycle inactive
            - combat not alive
            - frozen/stunned if legality service reports it

        Effects:
            - strip navigation target
            - strip new_position
            - strip task/action
            - strip resource transfers
            - preserve interaction reset visibility if needed
            - emit GLOBAL_PROPOSAL RejectionEvent

        Fraud this catches:
            - dead actors move
            - dead actors harvest/loot
            - dead actors attack
            - invalid proposals are silently stripped without audit
        """
        from dataclasses import replace

        from src.core.updates import EntityUpdate, NavigationUpdate, RejectionEvent
        from src.engine.legality import LegalityServiceV2

        refined_entity_updates = dict(update.entity_updates)
        new_rejections_delta = dict(update.rejections_delta)
        new_rejection_events = list(update.rejection_events)

        for entity_id, entity_update in sorted(update.entity_updates.items()):
            actor = state.entities.get(entity_id)

            if actor is None:
                continue

            legal, reason = LegalityServiceV2.verify_action_legality(
                actor,
                "GLOBAL_PROPOSAL",
                state,
            )

            if legal:
                continue

            reason_value = reason.value if hasattr(reason, "value") else str(reason)

            current_navigation = entity_update.navigation or NavigationUpdate()

            refined_entity_updates[entity_id] = replace(
                entity_update,
                task=None,
                navigation=replace(
                    current_navigation,
                    target_set=None,
                    clear_target=True,
                    failure_reason=reason,
                ),
                new_position=None,
                moved_this_tick=False,
                resource_transfers=[],
                readiness_delta=0.0,
            )

            new_rejections_delta[reason_value] = new_rejections_delta.get(reason_value, 0) + 1

            new_rejection_events.append(
                RejectionEvent(
                    tick=state.tick,
                    actor_id=entity_id,
                    action_kind="GLOBAL_PROPOSAL",
                    reason=reason,
                )
            )

        return replace(
            update,
            entity_updates=refined_entity_updates,
            rejections_delta=new_rejections_delta,
            rejection_events=new_rejection_events,
        )

    @staticmethod
    def _resolve_actor_validity(
        state: AuthoritativeState,
        update: StateUpdate,
    ) -> StateUpdate:
        """
        Law 300.1: Actor Validity.

        Invalid actors may not submit any authoritative proposal.

        Invalid means:
            - combat.alive is False
            - lifecycle.active is False
            - status_stunned is True
            - status_frozen is True

        Important:
            Navigation intent is also a proposal. A dead actor may not submit
            NavigationUpdate(target_set=...), even if EntityUpdate.new_position is
            still None.

        Effects:
            - strip task
            - strip navigation target / direct movement
            - strip resource transfers
            - strip interaction progress
            - emit one GLOBAL_PROPOSAL RejectionEvent
        """
        from dataclasses import replace

        from src.core.enums import ReasonCode
        from src.core.updates import (
            EntityUpdate,
            NavigationUpdate,
            InteractionUpdate,
            RejectionEvent,
        )

        refined_entity_updates = dict(update.entity_updates)
        new_rejections_delta = dict(update.rejections_delta)
        new_rejection_events = list(update.rejection_events)

        for entity_id, entity_update in sorted(update.entity_updates.items()):
            entity = state.entities.get(entity_id)

            if entity is None:
                continue

            is_stunned = entity.identity.properties.get("status_stunned", False)
            is_frozen = entity.identity.properties.get("status_frozen", False)
            is_dead = not entity.combat.alive
            is_inactive = not entity.lifecycle.active

            if not (is_stunned or is_frozen or is_dead or is_inactive):
                continue

            reason = ReasonCode.ATTACKER_STATUS_BLOCKED

            has_navigation_proposal = (
                entity_update.navigation is not None
                and (
                    entity_update.navigation.target_set is not None
                    or entity_update.navigation.path_set is not None
                    or entity_update.navigation.movement_mode_set is not None
                    or entity_update.navigation.clear_target
                    or entity_update.navigation.clear_path
                )
            )

            has_direct_movement = (
                entity_update.new_position is not None
                or entity_update.moved_this_tick
            )

            has_task = entity_update.task is not None
            has_resource_transfer = bool(entity_update.resource_transfers)
            has_interaction = entity_update.interaction is not None

            has_any_proposal = (
                has_navigation_proposal
                or has_direct_movement
                or has_task
                or has_resource_transfer
                or has_interaction
            )

            if not has_any_proposal:
                continue

            current_navigation = entity_update.navigation or NavigationUpdate()

            clean_navigation = replace(
                current_navigation,
                target_set=None,
                path_set=None,
                movement_mode_set=None,
                clear_target=True,
                clear_path=True,
                failure_reason=reason,
            )

            clean_interaction = None
            if entity_update.interaction is not None:
                clean_interaction = InteractionUpdate(
                    reset=True,
                )

            refined_entity_updates[entity_id] = replace(
                entity_update,
                task=None,
                navigation=clean_navigation,
                new_position=None,
                moved_this_tick=False,
                resource_transfers=[],
                interaction=clean_interaction,
                readiness_delta=0.0,
            )

            reason_key = reason.value if hasattr(reason, "value") else str(reason)
            new_rejections_delta[reason_key] = new_rejections_delta.get(reason_key, 0) + 1

            new_rejection_events.append(
                RejectionEvent(
                    tick=state.tick,
                    actor_id=entity_id,
                    action_kind="GLOBAL_PROPOSAL",
                    reason=reason,
                )
            )

        return replace(
            update,
            entity_updates=refined_entity_updates,
            rejections_delta=new_rejections_delta,
            rejection_events=new_rejection_events,
        )
        
    @staticmethod
    def _resolve_contract_expirations(
        state: AuthoritativeState,
        update: StateUpdate,
    ) -> StateUpdate:
        """
        Resolve stale social contracts during authoritative refinement.

        LAW:
            OFFERED / COUNTERED contracts that expire are EXPIRED.

            ACTIVE contracts that reach expiry_tick are treated as successfully
            completed duration contracts and become FULFILLED / COMPLETED.

        Why:
            An ACTIVE recruitment/protection/merchant contract reaching its end date
            is not the same as an unanswered offer expiring. The active obligation
            was honored until its duration ended.

        Effects:
            - ACTIVE -> FULFILLED may create social reputation updates.
            - OFFERED / COUNTERED -> EXPIRED is status-only.
            - No movement, inventory transfer, or world mutation happens here.
        """
        from dataclasses import replace

        from src.core.strategic import ContractStatus
        from src.core.updates import EntityUpdate, StrategicUpdate, SocialUpdate
        from src.systems.social_contract import SocialContractSystem

        entity_updates = dict(update.entity_updates)

        def _merge_entity_update(entity_id: int, strategic_upd=None, social_upd=None):
            existing = entity_updates.get(
                entity_id,
                EntityUpdate(entity_id=entity_id),
            )

            merged_strategic = existing.strategic
            if strategic_upd is not None:
                merged_strategic = (
                    merged_strategic.merge(strategic_upd)
                    if merged_strategic is not None
                    else strategic_upd
                )

            merged_social = existing.social
            if social_upd is not None:
                merged_social = (
                    merged_social.merge(social_upd)
                    if merged_social is not None
                    else social_upd
                )

            entity_updates[entity_id] = replace(
                existing,
                strategic=merged_strategic,
                social=merged_social,
            )

        for entity_id, entity in state.entities.items():
            for contract in entity.strategic.contracts.values():
                if contract.expiry_tick == -1:
                    continue

                if state.tick < contract.expiry_tick:
                    continue

                if contract.status == ContractStatus.ACTIVE:
                    # Active duration completed successfully.
                    strat_upd, social_upd = SocialContractSystem.transition_contract(
                        entity,
                        contract.id,
                        ContractStatus.FULFILLED,
                        state.tick,
                    )

                    if strat_upd.contracts_add_or_update:
                        _merge_entity_update(
                            entity_id,
                            strategic_upd=strat_upd,
                            social_upd=social_upd,
                        )

                elif contract.status in (
                    ContractStatus.OFFERED,
                    ContractStatus.COUNTERED,
                ):
                    expired_contract = replace(
                        contract,
                        status=ContractStatus.EXPIRED,
                    )

                    _merge_entity_update(
                        entity_id,
                        strategic_upd=StrategicUpdate(
                            contracts_add_or_update=[expired_contract],
                        ),
                    )

        return replace(
            update,
            entity_updates=entity_updates,
        )

    @staticmethod
    def _route_interaction_intent(state: AuthoritativeState, update: StateUpdate) -> StateUpdate:
        from src.core.updates import InteractionUpdate, EntityUpdate
        refined_entity_updates = dict(update.entity_updates)
        for e_id, entity in state.entities.items():
            if not entity.lifecycle.active: continue
            
            # Identify if entity is at a location that triggers automatic interaction
            # Or if they have an explicit target set
            ent_upd = refined_entity_updates.get(e_id, EntityUpdate(entity_id=e_id))
            target_pos = entity.navigation.target
            if ent_upd.navigation and ent_upd.navigation.target_set:
                target_pos = ent_upd.navigation.target_set
            
            if target_pos:
                # Find if any node is at the target
                target_node = next((n for n in state.resource_nodes.values() if n.position == target_pos), None)
                target_ground = next((g for g in state.ground_items.values() if g.position == target_pos), None)
                target_corpse = next((c for c in state.corpses.values() if c.position == target_pos), None)
                
                final_target_id = None
                if target_node: final_target_id = target_node.id
                elif target_ground: final_target_id = target_ground.id
                elif target_corpse: final_target_id = target_corpse.id
                
                if final_target_id is not None:
                    from src.core.updates import InteractionUpdate
                    current_int = ent_upd.interaction or InteractionUpdate()
                    if not current_int.reset:
                         p_delta = current_int.progress_delta if current_int.progress_delta > 0 else 1
                         refined_entity_updates[e_id] = replace(ent_upd,
                             interaction=replace(current_int, target_node_id=final_target_id, progress_delta=p_delta)
                         )
        return replace(update, entity_updates=refined_entity_updates)

    @staticmethod
    def _route_action_intent(state: AuthoritativeState, update: StateUpdate) -> StateUpdate:
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
        from dataclasses import replace

        from src.engine.legality import LegalityServiceV2
        from src.engine.domain_logic import SimulationDomainLogic
        from src.core.updates import (
            EntityUpdate,
            TaskUpdate,
            NavigationUpdate,
            RejectionEvent,
            StrategicUpdate,
        )
        from src.core.strategic import BlockerState
        from src.engine.apply import ApplyPath
        
        from src.core.enums import ReasonCode
        from src.core.updates import RejectionEvent


        def _normalize_reason(reason):
            """
            Normalize string/enum failure reasons into ReasonCode when possible.

            Tests compare ev.reason == ReasonCode.OUT_OF_RANGE, so storing plain
            'OUT_OF_RANGE' can make the audit look missing even when the event exists.
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

        # Initial sliding state includes previous authoritative phases from update.
        working_update = replace(update, entity_updates=refined_entity_updates)
        working_state = ApplyPath.apply_generation(state, working_update)

        # Deterministic action order.
        for eid in sorted(state.entities.keys()):
            entity = state.entities[eid]

            if not entity.lifecycle.active:
                continue

            ent_upd = refined_entity_updates.get(
                eid,
                EntityUpdate(entity_id=eid),
            )

            task_upd = ent_upd.task

            if not task_upd or task_upd.work_kind_set != "ENTITY_ACT":
                continue

            payload = dict(task_upd.payload_set or {})
            action = payload.get("action")

            if not action:
                continue

            # Use the latest sliding version of this actor.
            working_entity = working_state.entities.get(eid, entity)

            # 0. General action legality check.
            legal, reason = LegalityServiceV2.verify_action_legality(
                working_entity,
                action,
                working_state,
            )

            if not legal:
                reason_value = reason.value if hasattr(reason, "value") else str(reason)

                failed_task = replace(
                    task_upd,
                    payload_set={
                        **payload,
                        "outcome": "FAILURE",
                        "reason": reason_value,
                    },
                )

                refined_entity_updates[eid] = replace(
                    ent_upd,
                    task=failed_task,
                )

                new_rejection_events = list(update.rejection_events)
                new_rejections_delta = dict(update.rejections_delta)
                new_rejections_delta[reason_value] = new_rejections_delta.get(reason_value, 0) + 1

                new_rejection_events.append(
                    RejectionEvent(
                        tick=state.tick,
                        actor_id=eid,
                        action_kind=action,
                        reason=reason,
                        target_id=payload.get("target_id") or payload.get("target_pos"),
                    )
                )

                update = replace(
                    update,
                    entity_updates=refined_entity_updates,
                    rejection_events=new_rejection_events,
                    rejections_delta=new_rejections_delta,
                )

                working_update = replace(update, entity_updates=refined_entity_updates)
                working_state = ApplyPath.apply_generation(state, working_update)
                continue

            # 1. Readiness check.
            ready, r_reason = LegalityServiceV2.verify_readiness(working_entity)

            if not ready:
                reason_value = r_reason.value if hasattr(r_reason, "value") else str(r_reason)

                failed_task = replace(
                    task_upd,
                    payload_set={
                        **payload,
                        "outcome": "FAILURE",
                        "reason": reason_value,
                    },
                )

                new_rejection_events = list(update.rejection_events)
                new_rejections_delta = dict(update.rejections_delta)
                new_rejections_delta[reason_value] = new_rejections_delta.get(reason_value, 0) + 1

                new_rejection_events.append(
                    RejectionEvent(
                        tick=state.tick,
                        actor_id=eid,
                        action_kind=action,
                        reason=r_reason,
                        target_id=payload.get("target_id") or payload.get("target_pos"),
                    )
                )

                refined_entity_updates[eid] = replace(
                    ent_upd,
                    task=failed_task,
                    strategic=StrategicUpdate(
                        blockers_add_or_update=[
                            BlockerState(
                                id=f"blocker_nav_{reason_value}",
                                kind="capability",
                                subject=reason_value,
                            )
                        ]
                    ),
                )

                update = replace(
                    update,
                    entity_updates=refined_entity_updates,
                    rejection_events=new_rejection_events,
                    rejections_delta=new_rejections_delta,
                )

                working_update = replace(update, entity_updates=refined_entity_updates)
                working_state = ApplyPath.apply_generation(state, working_update)
                continue

            # 2. Execute action against the latest sliding state.
            action_updates = SimulationDomainLogic.execute_action(
                working_entity,
                payload=payload,
                current_tick=state.tick,
                neighbor_view=SimulationDomainLogic.get_neighbor_view(
                    working_state,
                    working_entity,
                    radius=10.0,
                ),
                context=working_state,
            )

            actor_action_upd = action_updates.get(eid)
            outcome = "SUCCESS"
            failure_reason = None

            if actor_action_upd is None:
                outcome = "FAILURE"
                failure_reason = "NO_ACTION_UPDATE"
            elif actor_action_upd.navigation and actor_action_upd.navigation.failure_reason:
                outcome = "FAILURE"
                failure_reason = actor_action_upd.navigation.failure_reason
            elif actor_action_upd.combat and actor_action_upd.combat.outcome_kind == "REJECTED":
                outcome = "FAILURE"
                failure_reason = actor_action_upd.combat.failure_reason
                
            if outcome == "FAILURE":
                audit_reason = _normalize_reason(failure_reason)
                audit_key = _reason_key(audit_reason)

                new_rejection_events = list(update.rejection_events)
                new_rejections_delta = dict(update.rejections_delta)

                new_rejections_delta[audit_key] = new_rejections_delta.get(audit_key, 0) + 1

                new_rejection_events.append(
                    RejectionEvent(
                        tick=state.tick,
                        actor_id=eid,
                        action_kind=action,
                        reason=audit_reason,
                        target_id=_target_for_action(payload),
                    )
                )

                update = replace(
                    update,
                    rejection_events=new_rejection_events,
                    rejections_delta=new_rejections_delta,
                )

            reason_value = (
                failure_reason.value
                if hasattr(failure_reason, "value")
                else failure_reason
            )

            annotated_task = replace(
                task_upd,
                payload_set={
                    **payload,
                    "outcome": outcome,
                    **({"reason": reason_value} if reason_value else {}),
                },
            )

            # 3. Merge all action updates.
            for action_eid, action_upd in action_updates.items():
                existing_upd = refined_entity_updates.get(
                    action_eid,
                    EntityUpdate(entity_id=action_eid),
                )

                merged = existing_upd.merge(action_upd)

                if action_eid == eid:
                    merged = replace(
                        merged,
                        task=annotated_task,
                    )

                refined_entity_updates[action_eid] = merged

            if eid not in action_updates:
                refined_entity_updates[eid] = replace(
                    ent_upd,
                    task=annotated_task,
                )

            # 4. Refresh sliding state after each action.
            # This is the important anti-double-kill step.
            update = replace(
                update,
                entity_updates=refined_entity_updates,
            )

            working_update = replace(
                update,
                entity_updates=refined_entity_updates,
            )

            working_state = ApplyPath.apply_generation(
                state,
                working_update,
            )

        return replace(
            update,
            entity_updates=refined_entity_updates,
        )
        
    @staticmethod
    def _apply_near_death_hardening(
        state: AuthoritativeState,
        update: StateUpdate,
    ) -> StateUpdate:
        """
        Apply near-death hardening after authoritative combat resolution.

        LAW:
            If an entity survives a hit with critically low remaining HP, it gains
            a small permanent max-HP increase in the same authoritative tick.

        Trigger:
            - entity has a CombatUpdate
            - combat update is not REJECTED
            - entity survives the hit
            - projected HP is > 0
            - projected HP is <= 10% of current max HP

        Effect:
            - CombatUpdate.max_hp_delta += 5

        Why this runs in the pipeline:
            This is not a worker reward. It is an authoritative consequence of
            surviving a near-death combat event.
        """
        from dataclasses import replace

        from src.core.updates import EntityUpdate, CombatUpdate

        refined_entity_updates = dict(update.entity_updates)

        for entity_id, entity_update in list(refined_entity_updates.items()):
            entity = state.entities.get(entity_id)

            if entity is None:
                continue

            combat_update = entity_update.combat

            if combat_update is None:
                continue

            if combat_update.outcome_kind == "REJECTED":
                continue

            current_hp = entity.combat.hp
            current_max_hp = entity.combat.max_hp

            projected_hp = current_hp + combat_update.hp_delta

            survived = (
                projected_hp > 0
                and combat_update.alive_set is not False
            )

            if not survived:
                continue

            near_death_threshold = max(1, int(current_max_hp * 0.10))

            if projected_hp > near_death_threshold:
                continue

            hardened_combat = combat_update.merge(
                CombatUpdate(
                    max_hp_delta=5,
                    trace={
                        "NEAR_DEATH_HARDENING": 5.0,
                        "NEAR_DEATH_PROJECTED_HP": float(projected_hp),
                        "NEAR_DEATH_THRESHOLD": float(near_death_threshold),
                    },
                )
            )

            refined_entity_updates[entity_id] = replace(
                entity_update,
                combat=hardened_combat,
            )

        return replace(
            update,
            entity_updates=refined_entity_updates,
        )
    
    @staticmethod
    def _resolve_quest_rewards(
        state: AuthoritativeState,
        update: StateUpdate,
    ) -> StateUpdate:
        from src.engine.quests import QuestResolutionSystem
        return QuestResolutionSystem.enforce(state, update)

    @staticmethod
    def _resolve_resource_transactions(state: AuthoritativeState, update: StateUpdate) -> StateUpdate:
        """
        Law 400: Resource Conservation (Milestone E5.8)
        Processes all ResourceTransferIntents into final inventory/gold updates.
        """
        from src.engine.economy import ResourceTransactionSystem
        return ResourceTransactionSystem.resolve_all(state, update)

    @staticmethod
    def _resolve_position_swaps(
        state: AuthoritativeState,
        update: StateUpdate,
    ) -> StateUpdate:
        """
        Resolve adjacent position swaps before normal movement routing.

        LAW:
            Two adjacent entities may exchange positions atomically when either:

                1. Mutual same-tick intent exists:
                    A's next step is B's current tile, and
                    B's next step is A's current tile.

                2. A valid accepted/active POSITION_SWAP contract exists:
                    One side wants the other side's tile, and the other side has
                    accepted a short-lived swap contract.

        Safety:
            - no overlap
            - no swap with inactive/dead entities
            - no swap with HOLD entities
            - no swap into blocked terrain/buildings
            - no third-party destination claim
            - consumed swap contract is marked FULFILLED

        Why this exists:
            A one-tile-wide corridor has no sidestep space. Without atomic swap,
            two entities can remain blocked even though the best human-like
            behavior is simply to exchange places.
        """
        from dataclasses import replace
        from src.core.enums import ReasonCode
        from src.core.movement_modes import MovementMode
        from src.core.strategic import ContractKind, ContractStatus
        from src.core.updates import EntityUpdate, NavigationUpdate, StrategicUpdate

        refined_entity_updates = dict(update.entity_updates)
        consumed_entities: set[int] = set()

        entity_ids = sorted(state.entities.keys())

        for i, a_id in enumerate(entity_ids):
            if a_id in consumed_entities:
                continue

            a = state.entities[a_id]

            for b_id in entity_ids[i + 1:]:
                if b_id in consumed_entities:
                    continue

                b = state.entities[b_id]

                if not AuthoritativeApplyPipeline._can_attempt_position_swap_pair(
                    state,
                    a,
                    b,
                ):
                    continue

                a_old = a.navigation.position
                b_old = b.navigation.position

                a_next = AuthoritativeApplyPipeline._desired_next_step_for_swap(
                    state,
                    update,
                    a,
                )
                b_next = AuthoritativeApplyPipeline._desired_next_step_for_swap(
                    state,
                    update,
                    b,
                )

                mutual_swap = (
                    a_next == b_old
                    and b_next == a_old
                )

                active_contract = None

                if not mutual_swap:
                    if a_next == b_old:
                        active_contract = AuthoritativeApplyPipeline._find_valid_position_swap_contract(
                            state=state,
                            requester_id=a_id,
                            responder_id=b_id,
                        )
                    elif b_next == a_old:
                        active_contract = AuthoritativeApplyPipeline._find_valid_position_swap_contract(
                            state=state,
                            requester_id=b_id,
                            responder_id=a_id,
                        )

                if not mutual_swap and active_contract is None:
                    continue

                if not AuthoritativeApplyPipeline._position_swap_destinations_are_safe(
                    state,
                    a_old,
                    b_old,
                ):
                    continue

                # Apply atomic swap. Use merge() so we preserve any earlier updates
                # from blacksmith/action/interaction phases.
                a_existing = refined_entity_updates.get(
                    a_id,
                    EntityUpdate(entity_id=a_id),
                )
                b_existing = refined_entity_updates.get(
                    b_id,
                    EntityUpdate(entity_id=b_id),
                )

                a_swap = AuthoritativeApplyPipeline._build_position_swap_entity_update(
                    entity=a,
                    new_position=b_old,
                    reason=ReasonCode.POSITION_SWAP,
                )

                b_swap = AuthoritativeApplyPipeline._build_position_swap_entity_update(
                    entity=b,
                    new_position=a_old,
                    reason=ReasonCode.POSITION_SWAP,
                )

                refined_entity_updates[a_id] = a_existing.merge(a_swap)
                refined_entity_updates[b_id] = b_existing.merge(b_swap)

                if active_contract is not None:
                    AuthoritativeApplyPipeline._mark_position_swap_contract_fulfilled(
                        refined_entity_updates,
                        active_contract,
                    )

                consumed_entities.add(a_id)
                consumed_entities.add(b_id)
                break

        return replace(
            update,
            entity_updates=refined_entity_updates,
        )


    @staticmethod
    def _can_attempt_position_swap_pair(
        state: AuthoritativeState,
        a: EntityState,
        b: EntityState,
    ) -> bool:
        """
        Validate invariant conditions before considering a swap.

        This does not check intent or contract. It only verifies that the pair is
        physically eligible to swap.
        """
        from src.core.movement_modes import MovementMode

        if not a.lifecycle.active or not b.lifecycle.active:
            return False

        if not a.combat.alive or not b.combat.alive:
            return False

        if a.navigation.movement_mode == MovementMode.HOLD:
            return False

        if b.navigation.movement_mode == MovementMode.HOLD:
            return False

        a_pos = a.navigation.position
        b_pos = b.navigation.position

        dist = abs(a_pos[0] - b_pos[0]) + abs(a_pos[1] - b_pos[1])
        return dist == 1


    @staticmethod
    def _desired_next_step_for_swap(
        state: AuthoritativeState,
        update: StateUpdate,
        entity: EntityState,
    ) -> tuple[float, float] | None:
        """
        Resolve the entity's immediate desired next step for swap detection.

        Sources, in priority order:
            1. already-proposed EntityUpdate.new_position
            2. NavigationUpdate.target_set
            3. TaskUpdate.payload_set["target_position"]
            4. existing entity.navigation.target

        If the target is more than one tile away, this computes the next one-tile
        step using the same Manhattan stepping rule as MovementSystem.
        """
        ent_upd = update.entity_updates.get(entity.id)

        if ent_upd and ent_upd.new_position is not None:
            return tuple(ent_upd.new_position)

        target_pos = None

        if ent_upd and ent_upd.navigation and ent_upd.navigation.target_set is not None:
            target_pos = ent_upd.navigation.target_set

        if target_pos is None and ent_upd and ent_upd.task and ent_upd.task.payload_set:
            payload = ent_upd.task.payload_set
            if "target_position" in payload:
                target_pos = payload["target_position"]

        if target_pos is None:
            target_pos = entity.navigation.target

        if target_pos is None:
            return None

        return AuthoritativeApplyPipeline._next_manhattan_step(
            entity.navigation.position,
            tuple(target_pos),
        )


    @staticmethod
    def _next_manhattan_step(
        current_pos: tuple[float, float],
        target_pos: tuple[float, float],
    ) -> tuple[float, float] | None:
        """
        Compute the next one-tile Manhattan step toward a target.

        This mirrors MovementSystem's effective-target logic so swap detection works
        even when the entity's target is beyond the adjacent blocker.
        """
        if current_pos == target_pos:
            return None

        dx = target_pos[0] - current_pos[0]
        dy = target_pos[1] - current_pos[1]

        if abs(dx) + abs(dy) <= 1:
            return target_pos

        if abs(dx) > abs(dy):
            return (
                current_pos[0] + (1.0 if dx > 0 else -1.0),
                current_pos[1],
            )

        return (
            current_pos[0],
            current_pos[1] + (1.0 if dy > 0 else -1.0),
        )


    @staticmethod
    def _find_valid_position_swap_contract(
        state: AuthoritativeState,
        requester_id: int,
        responder_id: int,
    ):
        """
        Find an accepted/active POSITION_SWAP contract between requester/responder.

        The contract may be stored on either entity. Terms are optional, but when
        present they must match the current positions exactly to prevent stale
        movement contracts from moving entities after the world has changed.
        """
        from src.core.strategic import ContractKind, ContractStatus

        requester = state.entities.get(requester_id)
        responder = state.entities.get(responder_id)

        if requester is None or responder is None:
            return None

        candidates = []

        for owner in (requester, responder):
            candidates.extend(owner.strategic.contracts.values())

        for contract in candidates:
            if contract.kind != ContractKind.POSITION_SWAP:
                continue

            if contract.status not in (ContractStatus.ACCEPTED, ContractStatus.ACTIVE):
                continue

            if contract.expiry_tick != -1 and state.tick > contract.expiry_tick:
                continue

            contract_pair = {contract.source_id, contract.target_id}
            if contract_pair != {requester_id, responder_id}:
                continue

            if not AuthoritativeApplyPipeline._position_swap_contract_terms_match(
                state,
                contract,
            ):
                continue

            return contract

        return None


    @staticmethod
    def _position_swap_contract_terms_match(
        state: AuthoritativeState,
        contract,
    ) -> bool:
        """
        Validate optional source/target position terms on a POSITION_SWAP contract.

        If a term is absent, it is treated as unconstrained. If present, it must
        match the current authoritative positions.
        """
        source = state.entities.get(contract.source_id)
        target = state.entities.get(contract.target_id)

        if source is None or target is None:
            return False

        expected = {
            "source_from": source.navigation.position,
            "source_to": target.navigation.position,
            "target_from": target.navigation.position,
            "target_to": source.navigation.position,
        }

        for key, expected_pos in expected.items():
            if key not in contract.terms:
                continue

            actual_pos = tuple(contract.terms[key])
            if actual_pos != expected_pos:
                return False

        return True


    @staticmethod
    def _position_swap_destinations_are_safe(
        state: AuthoritativeState,
        a_old: tuple[float, float],
        b_old: tuple[float, float],
    ) -> bool:
        """
        Verify that both swap destinations are physically valid.

        Occupancy by the two swapping entities is allowed. Static terrain/building
        obstruction is not allowed.
        """
        return (
            not AuthoritativeApplyPipeline._is_static_position_blocked(state, a_old)
            and not AuthoritativeApplyPipeline._is_static_position_blocked(state, b_old)
        )


    @staticmethod
    def _is_static_position_blocked(
        state: AuthoritativeState,
        pos: tuple[float, float],
    ) -> bool:
        """
        Check terrain/building/blocklist obstruction, ignoring entity occupancy.

        This is intentionally not LegalityServiceV2.verify_occupancy(...), because
        the two swap tiles are currently occupied by the swap participants.
        """
        tile = (int(pos[0]), int(pos[1]))

        if getattr(state, "terrain", {}).get(tile) == "WALL":
            return True

        if tile in getattr(state, "blocked_tiles", set()):
            return True

        for building in getattr(state, "buildings", {}).values():
            if tuple(building.position) == tile:
                return True

        return False


    @staticmethod
    def _build_position_swap_entity_update(
        entity: EntityState,
        new_position: tuple[float, float],
        reason,
    ) -> EntityUpdate:
        """
        Build the movement update for one participant of an atomic position swap.

        The target is not cleared. In a corridor-passing case, the entity may still
        have a farther navigation target and should continue moving next tick.
        The path is cleared because the previous path was calculated from the old
        position and may no longer be valid after the swap.
        """
        from src.core.updates import EntityUpdate, NavigationUpdate, StaminaUpdate

        return EntityUpdate(
            entity_id=entity.id,
            new_position=new_position,
            moved_this_tick=True,
            readiness_delta=-entity.combat.move_cost,
            navigation=NavigationUpdate(
                moved_recently_set=True,
                failure_reason=reason,
                wait_count_delta=-entity.navigation.wait_count,
                oscillation_count_delta=-entity.navigation.oscillation_count,
                last_position_set=entity.navigation.position,
                clear_path=True,
            ),
            stamina_update=StaminaUpdate(
                current_delta=-entity.stamina.MOVE_COST,
            ),
            property_updates={
                "movement_resolution": "POSITION_SWAP",
            },
        )


    @staticmethod
    def _mark_position_swap_contract_fulfilled(
        refined_entity_updates: dict[int, EntityUpdate],
        contract,
    ) -> None:
        """
        Mark a consumed POSITION_SWAP contract as FULFILLED for both parties.

        This prevents the same accepted swap contract from being reused next tick
        and causing an infinite swap-back loop.
        """
        from dataclasses import replace
        from src.core.strategic import ContractStatus
        from src.core.updates import EntityUpdate, StrategicUpdate

        fulfilled_contract = replace(
            contract,
            status=ContractStatus.FULFILLED,
        )

        for entity_id in (contract.source_id, contract.target_id):
            existing = refined_entity_updates.get(
                entity_id,
                EntityUpdate(entity_id=entity_id),
            )

            current_strategic = existing.strategic or StrategicUpdate()
            contract_update = StrategicUpdate(
                contracts_add_or_update=[fulfilled_contract],
            )

            refined_entity_updates[entity_id] = replace(
                existing,
                strategic=current_strategic.merge(contract_update),
            )

    @staticmethod
    def _route_movement_intent(state: AuthoritativeState, update: StateUpdate) -> StateUpdate:
        from src.engine.movement import MovementSystem
        from src.core.updates import EntityUpdate, NavigationUpdate
        refined_entity_updates = dict(update.entity_updates)
        for e_id, entity in state.entities.items():
            ent_upd = refined_entity_updates.get(e_id, EntityUpdate(entity_id=e_id))
            
            nav_target = entity.navigation.target
            if ent_upd.navigation and ent_upd.navigation.target_set is not None:
                nav_target = ent_upd.navigation.target_set
            
            if nav_target and (entity.navigation.position != nav_target):
                # Only move if not already moved and not currently interacting (harvesting)
                is_interacting = (ent_upd.interaction and ent_upd.interaction.progress_delta > 0)
                if not ent_upd.moved_this_tick and not is_interacting:
                    mode = entity.navigation.movement_mode
                    if ent_upd.navigation and ent_upd.navigation.movement_mode_set is not None:
                        mode = ent_upd.navigation.movement_mode_set
                    move_updates = MovementSystem.resolve_move(state, entity, nav_target, mode=mode)
                    
                    for u_id, u_upd in move_updates.items():
                        if u_id == e_id:
                            # Use full merge for subject to preserve combat/readiness (Phase E5.9 Fix)
                            merged = ent_upd.merge(u_upd)
                            refined_entity_updates[e_id] = merged
                        else:
                            # Neighbor collision updates (usually just navigation stats)
                            neighbor_upd = refined_entity_updates.get(u_id, EntityUpdate(entity_id=u_id))
                            refined_entity_updates[u_id] = neighbor_upd.merge(u_upd)
                            
        return replace(update, entity_updates=refined_entity_updates)

    @staticmethod
    def _resolve_occupancy_conflicts(
        state: AuthoritativeState,
        update: StateUpdate,
    ) -> StateUpdate:
        """
        LAW:
            Final movement results must not place two active entities on the same
            tile, and must not allow movement into a tile occupied by a static
            non-moving entity.

        Why this exists:
            MovementSystem handles normal navigation-intent movement, but worker
            proposals or tests may directly provide EntityUpdate.new_position.
            The authoritative pipeline must still validate final positions before
            ApplyPath commits them.

        Determinism:
            If multiple entities claim the same destination tile, the lowest entity
            id wins. All other claimants are rejected with OCCUPANCY_CONFLICT.

        Static occupancy:
            If the destination is occupied by an entity that is not moving away in
            this same update, the move is rejected.
        """
        from dataclasses import replace
        from src.core.updates import EntityUpdate, NavigationUpdate

        refined_entity_updates = dict(update.entity_updates)

        # Moving entities are entities that propose a concrete final position.
        moving_entity_ids = {
            entity_id
            for entity_id, entity_update in refined_entity_updates.items()
            if entity_update.new_position is not None
        }

        if not moving_entity_ids:
            return update

        # Current occupied tiles in authoritative state.
        current_occupied: dict[tuple[int, int], int] = {}

        for entity_id, entity in state.entities.items():
            if not entity.lifecycle.active:
                continue

            current_occupied[
                (
                    int(entity.navigation.position[0]),
                    int(entity.navigation.position[1]),
                )
            ] = entity_id

        # Destination claims from proposed movement results.
        claims_by_tile: dict[tuple[int, int], list[int]] = {}

        for entity_id, entity_update in refined_entity_updates.items():
            if entity_update.new_position is None:
                continue

            tile = (
                int(entity_update.new_position[0]),
                int(entity_update.new_position[1]),
            )

            claims_by_tile.setdefault(tile, []).append(entity_id)

        rejected_entity_ids: set[int] = set()

        for tile in sorted(claims_by_tile):
            contenders = sorted(claims_by_tile[tile])

            existing_occupant_id = current_occupied.get(tile)

            # If the tile is occupied by an entity that is not moving away, nobody
            # may move into that tile.
            if (
                existing_occupant_id is not None
                and existing_occupant_id not in moving_entity_ids
            ):
                rejected_entity_ids.update(contenders)
                continue

            # If multiple entities claim the same destination, lowest id wins.
            winner_id = contenders[0]
            for loser_id in contenders[1:]:
                rejected_entity_ids.add(loser_id)

        from src.core.updates import RejectionEvent
        new_rejections_delta = dict(update.rejections_delta)
        new_rejection_events = list(update.rejection_events)

        for entity_id in sorted(rejected_entity_ids):
            entity_update = refined_entity_updates.get(
                entity_id,
                EntityUpdate(entity_id=entity_id),
            )

            current_navigation_update = entity_update.navigation or NavigationUpdate()
            reason = "OCCUPANCY_CONFLICT"
            
            new_rejections_delta[reason] = new_rejections_delta.get(reason, 0) + 1
            new_rejection_events.append(RejectionEvent(
                tick=state.tick,
                actor_id=entity_id,
                action_kind="MOVE",
                reason=reason
            ))

            refined_entity_updates[entity_id] = replace(
                entity_update,
                new_position=None,
                moved_this_tick=False,
                navigation=replace(
                    current_navigation_update,
                    failure_reason=reason,
                ),
            )

        return replace(
            update,
            entity_updates=refined_entity_updates,
            rejections_delta=new_rejections_delta,
            rejection_events=new_rejection_events
        )