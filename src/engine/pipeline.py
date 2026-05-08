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
        
        # 0. Trust Boundary: strip raw world-side effects from worker proposals.
        # Workers may propose intents, tasks, interaction progress, inventory requests,
        # etc. They must NOT directly mutate world resources.
        #
        # Authoritative systems inside this pipeline may later add node/building/chest
        # updates, but raw caller-provided world effects are untrusted.
        update = AuthoritativeApplyPipeline._strip_untrusted_world_effects(update)
        
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
        
        # Phase 8: Infrastructure Sabotage (LEG-RPG-006)
        from src.engine.sabotage import BuildingSabotageSystem
        update = BuildingSabotageSystem.resolve(state, update)
        
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

        LAW:
            Worker/raw proposals may express intent, but they may not directly
            submit authoritative outcomes.

        Stripped from raw proposals:
            - direct world mutations:
                node_updates
                building_updates
                chest_updates
                ground_items_remove
                corpses_remove

            - unauthorized quest reward/status effects:
                QuestUpdate.status_set
                worker-submitted QUEST_REWARD resource transfers

        Why:
            Quest status transitions such as COMPLETED, REWARD_PENDING, and
            REWARDED must be produced by the authoritative quest/reward resolver,
            not by workers.

        Fraud this prevents:
            - worker marks quest REWARDED without reward delivery
            - worker injects QUEST_REWARD transfer directly
            - inventory-full quest reward still marks REWARDED
            - stale node/building/chest mutations bypass conservation checks
        """
        from dataclasses import replace

        from src.core.updates import EntityUpdate, QuestUpdate

        sanitized_entity_updates = {}

        for entity_id, entity_update in update.entity_updates.items():
            clean_quest = entity_update.quest

            if clean_quest is not None:
                clean_quest = QuestUpdate(
                    quest_id=clean_quest.quest_id,
                    progress_delta=clean_quest.progress_delta,
                    status_set=None,
                )

            clean_resource_transfers = [
                transfer
                for transfer in entity_update.resource_transfers
                if transfer.transfer_kind not in {
                    "QUEST_REWARD",
                    "REWARD",
                    "KILL_REWARD",
                    "TAX",
                }
            ]

            sanitized_entity_updates[entity_id] = replace(
                entity_update,
                quest=clean_quest,
                resource_transfers=clean_resource_transfers,
            )

        return replace(
            update,
            entity_updates=sanitized_entity_updates,
            node_updates={},
            building_updates={},
            chest_updates={},
            ground_items_remove=[],
            corpses_remove=[],
        )
        
    @staticmethod
    def _resolve_contract_expirations(
        state: AuthoritativeState,
        update: StateUpdate,
    ) -> StateUpdate:
        """
        Expire stale social contracts during authoritative refinement.

        LAW:
            Contracts with expiry_tick <= current tick must not be usable by later
            systems in the same tick.

        Why this exists:
            A contract can be stored on an entity from a previous tick. If the
            pipeline does not expire it before routing social/strategic/movement
            logic, stale consent can still influence the world.

        Examples:
            - expired recruitment offer should not be accepted
            - expired POSITION_SWAP contract should not allow movement
            - expired loan/protection contract should not affect strategy

        This phase is status-only:
            It updates contracts to EXPIRED, but does not remove them, move entities,
            transfer inventory, or mutate world resources.
        """
        from dataclasses import replace

        from src.core.updates import EntityUpdate
        from src.systems.social_contract import SocialContractSystem

        entity_updates = dict(update.entity_updates)

        for entity_id, entity in state.entities.items():
            strategic_update = SocialContractSystem.check_expirations(
                entity,
                state.tick,
            )

            if not strategic_update.contracts_add_or_update:
                continue

            existing = entity_updates.get(
                entity_id,
                EntityUpdate(entity_id=entity_id),
            )

            merged_strategic = (
                existing.strategic.merge(strategic_update)
                if existing.strategic is not None
                else strategic_update
            )

            entity_updates[entity_id] = replace(
                existing,
                strategic=merged_strategic,
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
        Law 300: Action Routing (Milestone E5.7)
        Routes high-level entity tasks to low-level action execution.
        """
        from src.engine.legality import LegalityServiceV2
        from src.engine.domain_logic import SimulationDomainLogic
        from src.core.updates import EntityUpdate, CombatUpdate, StrategicUpdate
        from src.engine.apply import ApplyPath
        
        refined_entity_updates = dict(update.entity_updates)
        
        # Use SLIDING state (Identity + Interaction + Blacksmith already applied in 'update')
        # This ensures combat reflects the very latest state within the tick.
        working_state = ApplyPath.apply_generation(state, update)
        
        for eid, entity in state.entities.items():
            if not entity.lifecycle.active: continue
            
            ent_upd = refined_entity_updates.get(eid, EntityUpdate(entity_id=eid))
            task_upd = ent_upd.task
            if not task_upd or task_upd.work_kind_set != "ENTITY_ACT": continue
            
            payload = task_upd.payload_set
            if not payload: continue
            action = payload.get("action")
            if not action: continue
            
            # 0. General action legality check
            legal, reason = LegalityServiceV2.verify_action_legality(
                entity,
                action,
                working_state,
            )

            if not legal:
                from src.core.updates import RejectionEvent

                failed_payload = dict(task_upd.payload_set or {})
                failed_payload["outcome"] = "FAILURE"
                failed_payload["reason"] = reason.value if hasattr(reason, "value") else reason

                failed_task = replace(
                    task_upd,
                    payload_set=failed_payload,
                )

                refined_entity_updates[eid] = replace(
                    ent_upd,
                    task=failed_task,
                )

                return_update_events = list(update.rejection_events)
                return_update_events.append(
                    RejectionEvent(
                        tick=state.tick,
                        actor_id=eid,
                        action_kind=action,
                        reason=reason,
                        target_id=failed_payload.get("target_id") or failed_payload.get("target_pos"),
                    )
                )

                update = replace(
                    update,
                    rejection_events=return_update_events,
                )
                
                continue

            # 1. Readiness Check (Standard Law)
            ready, r_reason = LegalityServiceV2.verify_readiness(entity)
            if not ready:
                from src.core.strategic import BlockerState
                from src.core.updates import StrategicUpdate
                refined_entity_updates[eid] = replace(ent_upd,
                    strategic=StrategicUpdate(blockers_add_or_update=[
                        BlockerState(id=f"blocker_nav_{r_reason}", kind="capability", subject=str(r_reason))
                    ])
                )
                continue

            # 2. Execute Action via Domain Logic using SLIDING state
            action_updates = SimulationDomainLogic.execute_action(
                entity, 
                payload=task_upd.payload_set, 
                neighbor_view=SimulationDomainLogic.get_neighbor_view(working_state, entity, radius=10.0),
                context=working_state
            )
            
            # 3. Merge all updates from the action (Attacker + Target)
            for action_eid, action_upd in action_updates.items():
                existing_upd = refined_entity_updates.get(action_eid, EntityUpdate(entity_id=action_eid))
                refined_entity_updates[action_eid] = existing_upd.merge(action_upd)

        return replace(update, entity_updates=refined_entity_updates)
    
    @staticmethod
    def _resolve_quest_rewards(
        state: AuthoritativeState,
        update: StateUpdate,
    ) -> StateUpdate:
        """
        Resolve quest completion and reward retry into authoritative reward intents.

        LAW:
            Quest status REWARDED may only be set after reward delivery succeeds.

        Handles:
            1. ACTIVE quest receives enough progress to complete.
            2. REWARD_PENDING quest retries reward delivery every tick.
            3. Full inventory keeps quest in REWARD_PENDING.
            4. Freeing inventory later allows retry to become REWARDED.

        This phase does not directly mutate inventory.
        It only creates ResourceTransferIntent objects and tentative quest status.
        _resolve_resource_transactions(...) decides final success/failure.
        """
        from dataclasses import replace

        from src.core.quests import QuestState, QuestStatus
        from src.core.state import ItemStack
        from src.core.updates import EntityUpdate, QuestUpdate, ResourceTransferIntent

        refined_entity_updates = dict(update.entity_updates)

        for entity_id, entity in state.entities.items():
            existing = refined_entity_updates.get(
                entity_id,
                EntityUpdate(entity_id=entity_id),
            )

            quest_update = existing.quest

            # No quest update from worker/system, but entity may already have
            # REWARD_PENDING quests that need retry.
            pending_quests = [
                q
                for q in entity.strategic.projects.values()
                if isinstance(q, QuestState)
                and q.quest_status == QuestStatus.REWARD_PENDING
            ]

            candidate_quest = None
            progress_delta = 0.0

            if quest_update is not None:
                candidate_quest = entity.strategic.projects.get(
                    quest_update.quest_id,
                )
                progress_delta = quest_update.progress_delta or 0.0

            elif pending_quests:
                candidate_quest = pending_quests[0]
                quest_update = QuestUpdate(
                    quest_id=candidate_quest.id,
                    progress_delta=0.0,
                    status_set=None,
                )

            if not isinstance(candidate_quest, QuestState):
                continue

            quest = candidate_quest

            is_reward_retry = quest.quest_status == QuestStatus.REWARD_PENDING

            would_complete = (
                quest.quest_status == QuestStatus.ACTIVE
                and quest.current_value + progress_delta >= quest.goal_value
            )

            if not is_reward_retry and not would_complete:
                continue

            reward = quest.reward

            reward_items = [
                ItemStack(
                    item_id=item_id,
                    quantity=1,
                )
                for item_id in reward.items
            ]

            reward_intent = ResourceTransferIntent(
                source_id=quest.id,
                source_kind="QUEST",
                items_add=reward_items,
                gold_delta=reward.gold,
                xp_reward=reward.xp,
                transfer_kind="QUEST_REWARD",
                transaction_id=f"quest:{quest.id}:reward",
            )

            refined_entity_updates[entity_id] = replace(
                existing,
                quest=QuestUpdate(
                    quest_id=quest.id,
                    progress_delta=progress_delta,
                    status_set=QuestStatus.REWARD_PENDING,
                ),
                resource_transfers=list(existing.resource_transfers) + [reward_intent],
            )

        return replace(
            update,
            entity_updates=refined_entity_updates,
        )

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

        for entity_id in sorted(rejected_entity_ids):
            entity_update = refined_entity_updates.get(
                entity_id,
                EntityUpdate(entity_id=entity_id),
            )

            current_navigation_update = entity_update.navigation or NavigationUpdate()

            refined_entity_updates[entity_id] = replace(
                entity_update,
                new_position=None,
                moved_this_tick=False,
                navigation=replace(
                    current_navigation_update,
                    failure_reason="OCCUPANCY_CONFLICT",
                ),
            )

        return replace(
            update,
            entity_updates=refined_entity_updates,
        )