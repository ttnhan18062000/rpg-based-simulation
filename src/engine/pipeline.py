from __future__ import annotations
from dataclasses import replace
from typing import TYPE_CHECKING, Dict, List, Tuple

from src.core.updates import StateUpdate, EntityUpdate, NavigationUpdate, IdentityUpdate, RejectionEvent
from src.core.enums import ReasonCode

if TYPE_CHECKING:
    from src.core.state import AuthoritativeState

class AuthoritativeApplyPipeline:
    @staticmethod
    def refine(state: AuthoritativeState, raw_update: StateUpdate) -> StateUpdate:
        """
        Refines a proposed StateUpdate through the authoritative law pipeline.
        Consolidates Town, Shop, Blacksmith, Interaction, and Movement rules.
        VERIFIED v2: authoritative_refinement_pipeline
        VERIFIED v2: partial_rejection_support
        VERIFIED v2: world_mutation_after_proposal
        """
        from src.engine.town_resolution import TownResolutionSystem
        from src.engine.shop import ShopSystem
        from src.engine.interaction import InteractionSystem
        from src.engine.blacksmith import BlacksmithSystem
        from src.systems.strategic import StrategicIntelligenceSystem
        from src.systems.redirection import StrategicRedirectionSystem
        from src.engine.movement import MovementSystem
        from src.engine.world_dynamics import WorldDynamicsSystem
        from src.engine.evolution import EvolutionSystem
        from src.engine.sabotage import BuildingSabotageSystem
        from src.engine.combat import CombatResolutionSystem
        from src.engine.legality import LegalityServiceV2
        from src.systems.lifecycle import LifecycleSystem
        from src.systems.groups import GroupSystem
        
        # 0. Sanitize Worker Proposals (Milestone 13 Law)
        # The worker results are only proposals. We preserve the INTENTS (task, navigation, etc.)
        # but strip calculated results (identity_delta, combat results, etc.) to avoid 
        # double-counting during authoritative re-execution in the Kernel.
        sanitized_entity_updates = {}
        for e_id, ent_upd in raw_update.entity_updates.items():
            # Phase E5.1: Actor Validity Enforcement (Hardening)
            # VERIFIED v2: actor_validity_enforcement
            actor = state.entities.get(e_id)
            if actor:
                legal, reason = LegalityServiceV2.verify_action_legality(actor, "GLOBAL_PROPOSAL", state)
                if not legal:
                    # Strip all world-mutating proposals from incapacitated actors
                    sanitized_entity_updates[e_id] = EntityUpdate(
                        entity_id=e_id,
                        navigation=NavigationUpdate(failure_reason=reason),
                        task=replace(ent_upd.task, payload_set={**ent_upd.task.payload_set, "outcome": "FAILURE", "reason": reason}) if ent_upd.task else None
                    )
                    # Global rejection tracking (Phase E5.4)
                    raw_update.rejection_events.append(RejectionEvent(
                        tick=state.tick, actor_id=e_id, action_kind="GLOBAL_PROPOSAL", reason=reason
                    ))
                    continue

            # Stripping unauthorized fields:
            # - inventory (gold/items)
            # - reward (XP)
            # - identity (role/faction/veterancy)
            # - attributes (str/agi/etc)
            # - stamina/wound updates (handled by RPG Depth System)
            
            sanitized_transfers = [
                t for t in ent_upd.resource_transfers 
                if t.transfer_kind not in ("QUEST_REWARD", "KILL_REWARD", "REWARD", "TAX")
            ]
            
            # Sanitizing CombatUpdate: Strip direct rewards (Handled by model change)
            clean_combat = ent_upd.combat

            # Sanitizing QuestUpdate: Strip status_set (Authority Only)
            clean_quest = None
            if ent_upd.quest:
                from src.core.updates import QuestUpdate
                clean_quest = QuestUpdate(
                    quest_id=ent_upd.quest.quest_id,
                    progress_delta=ent_upd.quest.progress_delta,
                    status_set=None 
                )

            sanitized_entity_updates[e_id] = EntityUpdate(
                entity_id=e_id,
                task=ent_upd.task,
                navigation=ent_upd.navigation,
                interaction=ent_upd.interaction,
                quest=clean_quest,
                property_updates=ent_upd.property_updates,
                new_position=ent_upd.new_position,
                moved_this_tick=ent_upd.moved_this_tick,
                readiness_delta=ent_upd.readiness_delta,
                combat=clean_combat,
                resource_transfers=sanitized_transfers,
                group_id_set=ent_upd.group_id_set,
                social=ent_upd.social
            )
        update = replace(raw_update, entity_updates=sanitized_entity_updates)
        
        # 1. Territorial & Service Laws (Healing, Shopping, Crafting)
        # VERIFIED v2: TownResolutionSystem
        update = TownResolutionSystem.resolve(state, update)
        # VERIFIED v2: ShopSystem
        update = ShopSystem.enforce(state, update)
        # VERIFIED v2: BlacksmithSystem
        update = BlacksmithSystem.enforce(state, update)
        
        # 1.1 Strategic Logic (Pre-Tactical Cognition)
        from src.social.contracts import ContractService
        # VERIFIED v2: ContractService
        update = ContractService.reap_expired_offers(state, update)
        update = ContractService.process_active_contracts(state, update)
        
        # VERIFIED v2: StrategicIntelligenceSystem (RPG-STRAT-200)
        update = StrategicIntelligenceSystem.resolve_blockers(state, update)
        update = StrategicIntelligenceSystem.evaluate_all_concerns(state, update)
        # VERIFIED v2: StrategicRedirectionSystem
        update = StrategicRedirectionSystem.enforce(state, update)

        # 1.2 Combat Laws (Attack resolution)
        # VERIFIED v2: CombatResolutionSystem
        update = AuthoritativeApplyPipeline._route_combat_intent(state, update)
        update = AuthoritativeApplyPipeline._apply_near_death_hardening(state, update)
        
        # 1.5 World Dynamics
        from src.systems.generator import EntityGenerator
        generator = EntityGenerator(state.seed + state.tick)
        # VERIFIED v2: WorldDynamicsSystem
        update = WorldDynamicsSystem.resolve_dynamics(state, update, generator)
        
        # 1.6 Building Sabotage (De-simulation)
        # VERIFIED v2: BuildingSabotageSystem
        update = BuildingSabotageSystem.resolve(state, update)
        
        # 2. Intent Routing (Interaction)
        update = AuthoritativeApplyPipeline._route_interaction_intent(state, update)
        
        # 3. Interaction Enforcement
        # VERIFIED v2: InteractionSystem
        update = InteractionSystem.enforce(state, update)
        
        # 5. Intent Routing (Movement)
        update = AuthoritativeApplyPipeline._route_movement_intent(state, update)
        
        # 6. Occupancy Conflicts (Milestone 3 Law)
        update = AuthoritativeApplyPipeline._resolve_occupancy_conflicts(state, update)
        
        # 7. Lifecycle
        from src.systems.lifecycle import LifecycleSystem
        # VERIFIED v2: LifecycleSystem
        update = LifecycleSystem.resolve_lifecycle(state, update)
        # 8. Quest Completions & Rewards
        from src.engine.quests import QuestResolutionSystem
        # VERIFIED v2: QuestResolutionSystem
        update = QuestResolutionSystem.enforce(state, update)

        # 9. Atomic Resource Transactions (Consolidated)
        update = AuthoritativeApplyPipeline._resolve_resource_transactions(state, update)
        
        

        
        # 10. Evolution & Growth (Captures XP from all sources above)
        from src.engine.evolution import EvolutionSystem
        # VERIFIED v2: EvolutionSystem
        update = EvolutionSystem.evaluate(state, update)
        
        # 11. Group Logic (Formation & Coordination)
        from src.engine.apply import ApplyPath
        # VERIFIED v2: GroupSystem (RPG-SOC-200)
        working_state_for_groups = ApplyPath.apply_generation(state, update)
        group_update = GroupSystem.update_groups(working_state_for_groups, update)
        update = AuthoritativeApplyPipeline._merge_state_updates(update, group_update)
        
        # 12. Global Readiness Recovery (+10.0 per tick for all active entities)
        # 12. Global Readiness Recovery (+10.0 per tick for all active entities)
        update = AuthoritativeApplyPipeline._apply_readiness_recovery(state, update)

        # 13. Transaction Trace Pruning (Hardening)
        # VERIFIED v2: transaction_trace_pruning
        if len(update.transaction_trace) > 200:
            update = replace(update, transaction_trace=update.transaction_trace[-200:])
            
        return update

    @staticmethod
    def _apply_readiness_recovery(state: AuthoritativeState, update: StateUpdate) -> StateUpdate:
        refined_entity_updates = dict(update.entity_updates)
        for e_id, entity in state.entities.items():
            if not entity.active: continue
            ent_upd = refined_entity_updates.get(e_id, EntityUpdate(entity_id=e_id))
            
            passive_gain = 10.0
            if entity.biological.sleep_debt > 80.0:
                passive_gain *= 0.5
                
            # Environmental Penalties (Aura of Despair)
            from src.world.environment import EnvironmentService
            from src.engine.legality import LegalityServiceV2
            region = LegalityServiceV2.get_region_for_position(entity.position, state)
            if region:
                aura_mults = EnvironmentService.get_aura_multipliers(state, entity)
                passive_gain *= aura_mults.get("readiness_regen", 1.0)

            refined_entity_updates[e_id] = replace(ent_upd, 
                readiness_delta=ent_upd.readiness_delta + passive_gain
            )

        return replace(update, entity_updates=refined_entity_updates)

    @staticmethod
    def _route_interaction_intent(state: AuthoritativeState, update: StateUpdate) -> StateUpdate:
        refined_entity_updates = dict(update.entity_updates)
        for e_id, entity in state.entities.items():
            ent_upd = refined_entity_updates.get(e_id, EntityUpdate(entity_id=e_id))
            
            nav_target = entity.navigation.target
            if ent_upd.navigation and ent_upd.navigation.target_set is not None:
                nav_target = ent_upd.navigation.target_set
            
            if nav_target and (entity.position == nav_target):
                # Search for interaction targets at the destination
                target_node = next((n for n in state.resource_nodes.values() if n.position == nav_target and n.remaining_charges > 0), None)
                target_ground = next((g for g in state.ground_items.values() if g.position == nav_target), None) if not target_node else None
                target_corpse = next((c for c in state.corpses.values() if c.position == nav_target), None) if not target_node and not target_ground else None
                
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
    def _route_movement_intent(state: AuthoritativeState, update: StateUpdate) -> StateUpdate:
        from src.engine.movement import MovementSystem
        refined_entity_updates = dict(update.entity_updates)
        for e_id, entity in state.entities.items():
            ent_upd = refined_entity_updates.get(e_id, EntityUpdate(entity_id=e_id))
            
            nav_target = entity.navigation.target
            if ent_upd.navigation and ent_upd.navigation.target_set is not None:
                nav_target = ent_upd.navigation.target_set
            
            if nav_target and (entity.position != nav_target):
                # Only move if not already moved and not currently interacting (harvesting)
                # Note: ent_upd.interaction might have been added in _route_interaction_intent
                is_interacting = (ent_upd.interaction and ent_upd.interaction.progress_delta > 0)
                if not ent_upd.moved_this_tick and not is_interacting:
                    mode = entity.navigation.movement_mode
                    if ent_upd.navigation and ent_upd.navigation.movement_mode_set is not None:
                        mode = ent_upd.navigation.movement_mode_set
                    move_updates = MovementSystem.resolve_move(state, entity, nav_target, mode=mode)
                    
                    for u_id, u_upd in move_updates.items():
                        if u_id == e_id:
                            # Merge hero's navigation and combat
                            base_nav = ent_upd.navigation or NavigationUpdate()
                            move_nav = u_upd.navigation or NavigationUpdate()
                            merged_nav = replace(base_nav,
                                target_set=move_nav.target_set if move_nav.target_set is not None else base_nav.target_set,
                                path_set=move_nav.path_set if move_nav.path_set is not None else base_nav.path_set,
                                moved_recently_set=move_nav.moved_recently_set if move_nav.moved_recently_set is not None else base_nav.moved_recently_set,
                                failure_reason=move_nav.failure_reason if move_nav.failure_reason is not None else base_nav.failure_reason
                            )
                            
                            refined_entity_updates[e_id] = replace(ent_upd, 
                                new_position=u_upd.new_position,
                                moved_this_tick=u_upd.moved_this_tick,
                                combat=u_upd.combat or ent_upd.combat,
                                navigation=merged_nav,
                                # Phase E5.8 Hardening: Readiness costs must stack across phases
                                readiness_delta=ent_upd.readiness_delta + u_upd.readiness_delta
                            )
                            
                            # Phase 6: Navigation Blocker Inference
                            if merged_nav.failure_reason:
                                from src.core.strategic import BlockerState
                                from src.core.updates import StrategicUpdate
                                curr_upd = refined_entity_updates[e_id]
                                strat_up = curr_upd.strategic or StrategicUpdate()
                                block_id = f"blocker_nav_{merged_nav.failure_reason}"
                                nav_blocker = BlockerState(
                                    id=block_id,
                                    kind="access",
                                    subject=merged_nav.failure_reason,
                                    severity=0.8
                                )
                                refined_entity_updates[e_id] = replace(curr_upd,
                                    strategic=replace(strat_up, blockers_add_or_update=[nav_blocker])
                                )
                                # Global rejection tracking (Phase E4.7)
                                rej_delta = dict(update.rejections_delta)
                                rej_key = f"MOVE_{merged_nav.failure_reason}"
                                rej_delta[rej_key] = rej_delta.get(rej_key, 0) + 1
                                update = replace(update, 
                                    rejections_delta=rej_delta,
                                    rejection_events=update.rejection_events + [RejectionEvent(
                                        tick=state.tick, actor_id=e_id, action_kind="MOVE", reason=merged_nav.failure_reason
                                    )]
                                )
                        else:
                            # Merge other entities' updates (e.g. attackers in OA)
                            if u_id in refined_entity_updates:
                                refined_entity_updates[u_id] = refined_entity_updates[u_id].merge(u_upd)
                            else:
                                refined_entity_updates[u_id] = u_upd
        return replace(update, entity_updates=refined_entity_updates)

    @staticmethod
    def _route_combat_intent(state: AuthoritativeState, update: StateUpdate) -> StateUpdate:
        """
        Processes ATTACK intents and resolves them through CombatResolutionSystem.
        Includes legality checks and position-sensitive bonuses (Milestone 4).
        """
        from src.engine.combat import CombatResolutionSystem
        from src.engine.legality import LegalityServiceV2
        from src.core.updates import EntityUpdate, IdentityUpdate
        from src.engine.domain_logic import SimulationDomainLogic
        
        refined_entity_updates = dict(update.entity_updates)
        working_state = state
        from src.engine.apply import ApplyPath
        
        # Phase 9 Fix: Use list(keys) to avoid "dictionary changed size during iteration"
        for e_id in sorted(list(refined_entity_updates.keys())):
            ent_upd = refined_entity_updates[e_id]
            entity = working_state.entities.get(e_id)
            if not entity or not entity.active: continue
            
            task_upd = ent_upd.task
            if not task_upd or task_upd.work_kind_set != "ENTITY_ACT": continue
            
            action_kind = task_upd.payload_set.get("action")
            
            # 1. Readiness Check (Standard Law)
            ready, r_reason = LegalityServiceV2.verify_readiness(entity)
            if not ready:
                from src.core.strategic import BlockerState
                from src.core.updates import StrategicUpdate
                refined_entity_updates[e_id] = replace(ent_upd,
                     task=replace(task_upd, payload_set={**task_upd.payload_set, "outcome": "FAILURE", "reason": r_reason}),
                     strategic=replace(ent_upd.strategic or StrategicUpdate(), 
                         blockers_add_or_update=[BlockerState(id=f"blocker_act_{r_reason}", kind="access", subject=r_reason)]
                     )
                )
                # Global rejection tracking (Phase E4.7)
                rej_delta = dict(update.rejections_delta)
                rej_delta["READINESS_NOT_READY"] = rej_delta.get("READINESS_NOT_READY", 0) + 1
                update = replace(update, 
                    rejections_delta=rej_delta,
                    rejection_events=update.rejection_events + [RejectionEvent(
                        tick=state.tick, actor_id=e_id, action_kind="ENTITY_ACT", reason=r_reason
                    )]
                )
                continue

            legal, reason = LegalityServiceV2.verify_action_legality(entity, action_kind, working_state)
            
            if not legal:
                 # Suppression! Remove the task and record failure
                 from src.core.strategic import BlockerState
                 from src.core.updates import StrategicUpdate
                 refined_entity_updates[e_id] = replace(ent_upd,
                    task=replace(task_upd, payload_set={**task_upd.payload_set, "outcome": "FAILURE", "reason": reason}),
                    strategic=replace(ent_upd.strategic or StrategicUpdate(), 
                        blockers_add_or_update=[BlockerState(id=f"blocker_act_{reason}", kind="access", subject=reason)]
                    )
                 )
                 # Global rejection tracking (Phase E4.7)
                 rej_delta = dict(update.rejections_delta)
                 rej_delta["ACTION_ILLEGAL"] = rej_delta.get("ACTION_ILLEGAL", 0) + 1
                 update = replace(update, 
                     rejections_delta=rej_delta,
                     rejection_events=update.rejection_events + [RejectionEvent(
                         tick=state.tick, actor_id=e_id, action_kind=action_kind, reason=reason
                     )]
                 )
                 continue

            if action_kind in ("ATTACK", "SKILL", "AOE_ATTACK"):
                is_legal = False
                reason = "UNKNOWN"
                
                if action_kind in ("ATTACK", "SKILL"):
                    target_id = task_upd.payload_set.get("target_id")
                    if target_id is None: continue
                    target = working_state.entities.get(target_id)
                    if not target: continue
                    
                    is_legal, reason = LegalityServiceV2.verify_attack_legality(entity, target, working_state)
                    if is_legal and action_kind == "SKILL":
                        skill_id = task_upd.payload_set.get("skill_id")
                        if not skill_id:
                            is_legal, reason = False, "MISSING_SKILL_ID"
                        else:
                            is_legal, reason = LegalityServiceV2.verify_skill_legality(entity, skill_id, working_state)
                elif action_kind == "AOE_ATTACK":
                    target_pos = task_upd.payload_set.get("target_pos")
                    if target_pos is None: continue
                    is_legal, reason = LegalityServiceV2.verify_aoe_legality(entity, target_pos, working_state)

                if not is_legal:
                     # Mark failure in task payload (Milestone 3 logic)
                     from src.core.strategic import BlockerState
                     from src.core.updates import StrategicUpdate
                     refined_entity_updates[e_id] = replace(ent_upd,
                         task=replace(task_upd, payload_set={**task_upd.payload_set, "outcome": "FAILURE", "reason": reason}),
                         strategic=replace(ent_upd.strategic or StrategicUpdate(), 
                             blockers_add_or_update=[BlockerState(id=f"blocker_{action_kind.lower()}_{reason}", kind="access", subject=reason)]
                         )
                     )
                     # Global rejection tracking (Phase E4.7)
                     rej_delta = dict(update.rejections_delta)
                     rej_delta["ATTACK_ILLEGAL"] = rej_delta.get("ATTACK_ILLEGAL", 0) + 1
                     update = replace(update, 
                         rejections_delta=rej_delta,
                         rejection_events=update.rejection_events + [RejectionEvent(
                             tick=state.tick, actor_id=e_id, action_kind=action_kind, reason=reason, target_id=target_id if action_kind != "AOE_ATTACK" else str(target_pos)
                         )]
                     )
                     continue
                
                # 2. Execute Action via Domain Logic using SLIDING state
                action_updates = SimulationDomainLogic.execute_action(
                    entity, 
                    payload=task_upd.payload_set, 
                    current_tick=working_state.tick,
                    neighbor_view=SimulationDomainLogic.get_neighbor_view(working_state, entity, radius=10.0),
                    context=working_state
                )
                
                # 3. Merge all updates from the action (Attacker + Target)
                new_entities_to_sync = []
                for eid, upd in action_updates.items():
                    existing = refined_entity_updates.get(eid, EntityUpdate(entity_id=eid))
                    merged = existing.merge(upd)
                    # Phase E5.8 Hardening: Readiness costs must stack across phases
                    refined_entity_updates[eid] = replace(merged, 
                        readiness_delta=existing.readiness_delta + upd.readiness_delta
                    )
                    new_entities_to_sync.append(eid)
                
                # 4. Mark SUCCESS
                final_ent_upd = refined_entity_updates[e_id]
                refined_entity_updates[e_id] = replace(final_ent_upd,
                    task=replace(final_ent_upd.task or task_upd, payload_set={**task_upd.payload_set, "outcome": "SUCCESS"})
                )
                
                # 5. UPDATE WORKING STATE for next entity in same tick (Sliding State)
                new_working_entities = dict(working_state.entities)
                for eid, upd in action_updates.items():
                    if eid in new_working_entities:
                        new_working_entities[eid] = ApplyPath._apply_entity_update(
                            new_working_entities[eid], upd
                        )
                working_state = replace(working_state, entities=new_working_entities)

        return replace(update, entity_updates=refined_entity_updates)

    @staticmethod
    def _resolve_occupancy_conflicts(state: AuthoritativeState, update: StateUpdate) -> StateUpdate:
        """
        Milestone 3 Law: Conflict resolution must be deterministic.
        Priority: Class Priority > Local Priority > Entity ID.
        """
        # 1. Collect all proposals for position changes
        proposals: Dict[tuple[int, int], List[int]] = {} # (x, y) -> List of EntityIDs
        
        # Include current positions of entities that are NOT moving to block tiles
        # (Actually, only entities that ARE active block tiles)
        current_occupied = { (int(e.position[0]), int(e.position[1])): e.id 
                             for e in state.entities.values() if e.active }
        
        # entities_moving tracks who is proposing a NEW position
        entities_moving = []
        for e_id, ent_upd in update.entity_updates.items():
            if ent_upd.new_position:
                entities_moving.append(e_id)
                target = (int(ent_upd.new_position[0]), int(ent_upd.new_position[1]))
                if target not in proposals: proposals[target] = []
                proposals[target].append(e_id)
        
        if not proposals:
            return update

        refined_entity_updates = dict(update.entity_updates)
        transaction_trace = list(update.transaction_trace)
        
        # 2. Sort targets and contenders for determinism
        sorted_targets = sorted(proposals.keys())
        
        for target in sorted_targets:
            contenders = proposals[target]
            
            # Tie-breaking logic
            # We need to look up priorities. For now we use EntityID (lower is better)
            # as a simple deterministic proxy for Class/Local priority.
            contenders.sort() # Lowest ID wins
            
            winner_id = contenders[0]
            losers = contenders[1:]
            
            # Check if target is already occupied by someone who ISN'T moving
            existing_occupant = current_occupied.get(target)
            if existing_occupant and existing_occupant not in entities_moving:
                # Winner also loses because the tile is blocked by a static entity
                winner_id = None
                losers = contenders
            
            if winner_id is not None:
                # Winner keeps their position
                pass
                
            for loser_id in losers:
                # Revert move for losers
                ent_upd = refined_entity_updates[loser_id]
                refined_entity_updates[loser_id] = replace(
                    ent_upd,
                    new_position=None,
                    moved_this_tick=False,
                    # We might want to refund readiness, but legacy says move "started" then failed
                    navigation=replace(ent_upd.navigation or NavigationUpdate(), 
                                      failure_reason="OCCUPANCY_CONFLICT")
                )
                transaction_trace.append(f"MOVE_FAIL: Entity {loser_id} - OCCUPANCY_CONFLICT")
                
                # Global rejection tracking (Phase E4.7)
                rej_delta = dict(update.rejections_delta)
                rej_delta["OCCUPANCY_CONFLICT"] = rej_delta.get("OCCUPANCY_CONFLICT", 0) + 1
                update = replace(update, 
                    rejections_delta=rej_delta,
                    rejection_events=update.rejection_events + [RejectionEvent(
                        tick=state.tick, actor_id=loser_id, action_kind="MOVE", reason=ReasonCode.OCCUPANCY_VIOLATION
                    )]
                )
                
        return replace(update, entity_updates=refined_entity_updates, transaction_trace=transaction_trace)

    @staticmethod
    def _apply_near_death_hardening(state: AuthoritativeState, update: StateUpdate) -> StateUpdate:
        """
        Pillar 2.2: Near-death hardening. 
        Heroes surviving combat at <10% HP gain permanent +5 max_hp.
        """
        from src.core.enums import EntityRole
        from src.core.updates import CombatUpdate
        
        refined_entity_updates = dict(update.entity_updates)
        for e_id, ent_upd in refined_entity_updates.items():
            if ent_upd.combat and ent_upd.combat.hp_delta < 0:
                entity = state.entities.get(e_id)
                if not entity or not entity.active: continue
                if entity.identity.role != EntityRole.HERO: continue
                
                # Check if survival is below 10%
                new_hp = entity.combat.hp + ent_upd.combat.hp_delta
                # Must be alive and below threshold
                if 0 < new_hp <= (entity.combat.max_hp * 0.1):
                    cb_upd = ent_upd.combat
                    refined_entity_updates[e_id] = replace(ent_upd,
                        combat=replace(cb_upd, max_hp_delta=cb_upd.max_hp_delta + 5)
                    )
        return replace(update, entity_updates=refined_entity_updates)

    @staticmethod
    def _merge_state_updates(base: StateUpdate, extra: StateUpdate) -> StateUpdate:
        """Helper to merge two StateUpdate instances."""
        from src.core.updates import EntityUpdate
        
        new_entity_updates = dict(base.entity_updates)
        for e_id, extra_ent_upd in extra.entity_updates.items():
            if e_id in new_entity_updates:
                new_entity_updates[e_id] = new_entity_updates[e_id].merge(extra_ent_upd)
            else:
                new_entity_updates[e_id] = extra_ent_upd
                
        return replace(
            base,
            entity_updates=new_entity_updates,
            groups_add_or_update=base.groups_add_or_update + extra.groups_add_or_update,
            groups_remove=base.groups_remove + extra.groups_remove
        )

    @staticmethod
    def _resolve_resource_transactions(state: AuthoritativeState, update: StateUpdate) -> StateUpdate:
        """
        Final authority for all resource transfers.
        Resolves any ResourceTransferIntent that wasn't handled by specific systems.
        """
        from src.core.conservation import ResourceTransactionResolver
        from src.core.updates import InventoryUpdate, IdentityUpdate
        
        refined_entity_updates = dict(update.entity_updates)
        refined_node_updates = dict(update.node_updates)
        ground_items_remove = list(update.ground_items_remove)
        corpses_remove = list(update.corpses_remove)
        resource_updates = dict(update.resource_updates)
        current_home_storage_upds = dict(update.home_storage_updates)
        refined_building_updates = dict(update.building_updates)
        transaction_trace = list(update.transaction_trace)
        accepted_transaction_ids = set(update.processed_transaction_ids)
        
        # P0.2 Refinement: Global source reservation map for the tick
        source_reservations: Dict[tuple[str, str|int], int] = {}
        
        # Phase 9 Fix: Use sorted(list(keys)) to ensure deterministic resolution order.
        # Milestone 13 Law: Conflict resolution must be deterministic (Lowest ID wins).
        for e_id in sorted(list(refined_entity_updates.keys())):
            ent_upd = refined_entity_updates[e_id]
            if not ent_upd.resource_transfers:
                continue
                
            entity = state.entities.get(e_id)
            if not entity: continue
            
            from src.core.inventory import InventoryService
            # Compute pending inventory state (updates as we process each intent)
            current_inv_upd = ent_upd.inventory or InventoryUpdate()
            current_id_upd = ent_upd.identity or IdentityUpdate()
            current_bio_upd = ent_upd.biological
            current_attr_upd = ent_upd.attributes
            current_combat_upd = ent_upd.combat
            current_strat_upd = ent_upd.strategic
            current_interaction_upd = ent_upd.interaction
            current_equip_upd = ent_upd.equipment
            current_reward_upd = ent_upd.reward
            
            intent_results = []
            
            has_any_accepted = False
            
            # P0.3 Refinement: Group intents by group_id using OrderedDict for stability
            from collections import OrderedDict
            intent_groups = OrderedDict()
            for intent in ent_upd.resource_transfers:
                gid = intent.group_id
                if gid is None:
                    # Single-intent independent group
                    gid = f"IND_{intent.transaction_id or id(intent)}"
                if gid not in intent_groups:
                    intent_groups[gid] = []
                intent_groups[gid].append(intent)

            for group_id, group_intents in intent_groups.items():
                # Checkpoint for potential rollback
                cp_inv = current_inv_upd
                cp_id = current_id_upd
                cp_bio = current_bio_upd
                cp_attr = current_attr_upd
                cp_combat = current_combat_upd
                cp_strat = current_strat_upd
                cp_home_stor = dict(current_home_storage_upds)
                cp_equip = current_equip_upd
                cp_reward = current_reward_upd
                cp_node_upds = dict(refined_node_updates)
                cp_ground_rem = list(ground_items_remove)
                cp_corpse_rem = list(corpses_remove)
                cp_quest_upd = refined_entity_updates[e_id].quest
                cp_build_upds = dict(refined_building_updates)
                
                group_success = True
                group_source_reservations = {}
                for intent in group_intents:
                    # Phase E5.3: In-tick Idempotency check
                    if intent.transaction_id and intent.transaction_id in accepted_transaction_ids:
                        from src.core.state import IntentResult
                        intent_results.append(IntentResult(
                            transaction_id=intent.transaction_id,
                            accepted=False,
                            reason=ReasonCode.IDEMPOTENCY_VIOLATION,
                            source_kind=intent.source_kind,
                            source_id=intent.source_id
                        ))
                        transaction_trace.append(f"TRANS_REJECT: Entity {e_id} {intent.transfer_kind} {intent.source_kind}:{intent.source_id} - {ReasonCode.IDEMPOTENCY_VIOLATION} (In-tick)")
                        continue

                    pending_inv = InventoryService.apply_update(entity.inventory, current_inv_upd)
                    
                    # Merge global and group reservations for validation
                    temp_reservations = {**source_reservations}
                    for k, v in group_source_reservations.items():
                        temp_reservations[k] = temp_reservations.get(k, 0) + v

                    result = ResourceTransactionResolver.resolve(
                        state, entity, intent, 
                        inventory_override=pending_inv,
                        node_overrides=refined_node_updates,
                        reservations=temp_reservations
                    )
                    
                    if result.accepted:
                        transaction_trace.append(f"TRANS_ACCEPT: Entity {e_id} {intent.transfer_kind} {intent.source_kind}:{intent.source_id}")
                    else:
                        transaction_trace.append(f"TRANS_FAIL: Entity {e_id} {intent.transfer_kind} {intent.source_kind}:{intent.source_id} - {result.reason}")
                        update = replace(update, rejection_events=update.rejection_events + [RejectionEvent(
                            tick=state.tick, actor_id=e_id, action_kind=intent.transfer_kind, reason=result.reason, target_id=f"{intent.source_kind}:{intent.source_id}"
                        )])
                    
                    from src.core.state import IntentResult
                    intent_results.append(IntentResult(
                        transaction_id=intent.transaction_id,
                        accepted=result.accepted,
                        reason=result.reason,
                        source_kind=intent.source_kind,
                        source_id=intent.source_id
                    ))
                    
                    if result.accepted:
                        if intent.transaction_id:
                            accepted_transaction_ids.add(intent.transaction_id)
                        
                        # P0.2 Refinement: Update local group reservations
                        s_key = (intent.source_kind, intent.source_id)
                        requested = 0
                        if intent.source_kind == "NODE":
                            requested = 1 # charges
                        elif intent.source_kind in ("GROUND_ITEM", "CORPSE", "COMBAT", "QUEST"):
                            requested = 1 # lock
                        group_source_reservations[s_key] = group_source_reservations.get(s_key, 0) + requested

                        # Accumulate updates within the group
                        current_inv_upd = replace(current_inv_upd,
                            items_add=list(current_inv_upd.items_add) + (result.inventory_update.items_add if result.inventory_update else []),
                            items_remove=list(current_inv_upd.items_remove) + (result.inventory_update.items_remove if result.inventory_update else []),
                            gold_delta=current_inv_upd.gold_delta + (result.inventory_update.gold_delta if result.inventory_update else 0)
                        )
                        
                        if result.biological_update:
                             if current_bio_upd:
                                  # Simple merge (set values from result over existing)
                                  current_bio_upd = replace(current_bio_upd,
                                       sleep_debt_delta=current_bio_upd.sleep_debt_delta + result.biological_update.sleep_debt_delta,
                                       sleep_debt_set=result.biological_update.sleep_debt_set if result.biological_update.sleep_debt_set is not None else current_bio_upd.sleep_debt_set,
                                       hunger_delta=current_bio_upd.hunger_delta + result.biological_update.hunger_delta,
                                       hunger_set=result.biological_update.hunger_set if result.biological_update.hunger_set is not None else current_bio_upd.hunger_set,
                                       well_rested_until_set=result.biological_update.well_rested_until_set if result.biological_update.well_rested_until_set is not None else current_bio_upd.well_rested_until_set
                                  )
                             else:
                                  current_bio_upd = result.biological_update
                                  
                        if result.attributes_update:
                             if current_attr_upd:
                                  current_attr_upd = replace(current_attr_upd,
                                       strength_delta=current_attr_upd.strength_delta + result.attributes_update.strength_delta,
                                       agility_delta=current_attr_upd.agility_delta + result.attributes_update.agility_delta,
                                       vitality_delta=current_attr_upd.vitality_delta + result.attributes_update.vitality_delta
                                       # ... add more as needed
                                  )
                             else:
                                  current_attr_upd = result.attributes_update
                                  
                        if result.equipment_update:
                             if current_equip_upd:
                                  current_equip_upd = current_equip_upd.merge(result.equipment_update)
                             else:
                                  current_equip_upd = result.equipment_update
                                   
                        if result.identity_update:
                             current_id_upd = replace(current_id_upd,
                                  recipes_learned=list(current_id_upd.recipes_learned) + list(result.identity_update.recipes_learned),
                                  evolution_points_delta=current_id_upd.evolution_points_delta + result.identity_update.evolution_points_delta,
                                  unspent_ap_delta=current_id_upd.unspent_ap_delta + result.identity_update.unspent_ap_delta
                             )
                                  
                        if result.combat_update:
                             if current_combat_upd:
                                  current_combat_upd = replace(current_combat_upd,
                                       hp_delta=current_combat_upd.hp_delta + result.combat_update.hp_delta,
                                       damage_taken=current_combat_upd.damage_taken + result.combat_update.damage_taken
                                  )
                             else:
                                  current_combat_upd = result.combat_update
                                  
                        if result.strategic_update:
                             if current_strat_upd:
                                  # Merge StrategicUpdate
                                  current_strat_upd = replace(current_strat_upd,
                                       blockers_add_or_update=current_strat_upd.blockers_add_or_update + result.strategic_update.blockers_add_or_update,
                                       blockers_remove=current_strat_upd.blockers_remove + result.strategic_update.blockers_remove,
                                       leads_add_or_update=current_strat_upd.leads_add_or_update + result.strategic_update.leads_add_or_update,
                                       leads_remove=current_strat_upd.leads_remove + result.strategic_update.leads_remove
                                       # ... add more as needed
                                  )
                             else:
                                  current_strat_upd = result.strategic_update
                                  
                        if result.reward_update:
                             if current_reward_upd:
                                  current_reward_upd = replace(current_reward_upd,
                                       xp_gain=current_reward_upd.xp_gain + result.reward_update.xp_gain,
                                       evolution_points_delta=current_reward_upd.evolution_points_delta + result.reward_update.evolution_points_delta
                                  )
                             else:
                                  current_reward_upd = result.reward_update
                                  
                        if result.home_storage_update:
                             existing = current_home_storage_upds.get(e_id)
                             if existing:
                                  current_home_storage_upds[e_id] = replace(existing,
                                       items_add=list(existing.items_add) + list(result.home_storage_update.items_add),
                                       items_remove=list(existing.items_remove) + list(result.home_storage_update.items_remove)
                                  )
                             else:
                                  current_home_storage_upds[e_id] = result.home_storage_update
                        
                        if result.node_update:
                            n_id = result.node_update.node_id
                            existing_node = refined_node_updates.get(n_id)
                            if existing_node:
                                refined_node_updates[n_id] = replace(existing_node,
                                    charges_delta=existing_node.charges_delta + result.node_update.charges_delta
                                )
                            else:
                                refined_node_updates[n_id] = result.node_update
                        
                        if result.building_update:
                             b_id = result.building_update.building_id
                             existing_build = refined_building_updates.get(b_id)
                             if existing_build:
                                 from src.core.updates import BuildingUpdate
                                 # Minimal merge for building updates
                                 merged_inv = existing_build.inventory
                                 if result.building_update.inventory:
                                      if merged_inv:
                                           merged_inv = replace(merged_inv,
                                                items_add=list(merged_inv.items_add) + list(result.building_update.inventory.items_add),
                                                items_remove=list(merged_inv.items_remove) + list(result.building_update.inventory.items_remove),
                                                gold_delta=merged_inv.gold_delta + result.building_update.inventory.gold_delta
                                           )
                                      else:
                                           merged_inv = result.building_update.inventory
                                           
                                 refined_building_updates[b_id] = replace(existing_build,
                                     hp_delta=existing_build.hp_delta + result.building_update.hp_delta,
                                     inventory=merged_inv,
                                     price_modifiers_set=result.building_update.price_modifiers_set if result.building_update.price_modifiers_set is not None else existing_build.price_modifiers_set
                                 )
                             else:
                                 refined_building_updates[b_id] = result.building_update
                        
                        if result.ground_item_remove is not None:
                            ground_items_remove.append(result.ground_item_remove)
                        if result.corpse_remove is not None:
                            corpses_remove.append(result.corpse_remove)
                        
                        # Handle Quest Status (Matching Phase 3 Task 3.1)
                        if intent.transfer_kind == "QUEST_REWARD":
                            from src.core.updates import QuestUpdate
                            from src.core.quests import QuestStatus
                            q_id = str(intent.source_id)
                            curr_q_upd = refined_entity_updates[e_id].quest
                            if curr_q_upd and curr_q_upd.quest_id == q_id:
                                refined_entity_updates[e_id] = replace(refined_entity_updates[e_id],
                                    quest=replace(curr_q_upd, status_set=QuestStatus.REWARDED)
                                )
                        
                        # Handle Interaction Reset (Phase 1 Law)
                        if intent.transfer_kind in ("HARVEST", "LOOT", "AUTO"):
                            from src.core.updates import InteractionUpdate
                            current_interaction_upd = InteractionUpdate(reset=True)
                        
                        # Handle Crafting Reset (Phase 1 Law)
                        if intent.transfer_kind == "CRAFT":
                            current_id_upd = replace(current_id_upd, craft_target="")
                        
                        # Handle Faction Gold Side-Effects (e.g. TAX)
                        if intent.source_kind == "TAX" and intent.gold_delta != 0:
                            f_key = f"{intent.source_id}_gold"
                            resource_updates[f_key] = resource_updates.get(f_key, 0.0) - intent.gold_delta
                            
                        # Conservation Metrics (Phase 10)
                        if result.accepted:
                            # 1. Gold Conservation
                            g_delta = (result.inventory_update.gold_delta if result.inventory_update else 0)
                            if g_delta != 0:
                                resource_updates["metric_total_gold"] = resource_updates.get("metric_total_gold", 0.0) + g_delta
                            
                            # 2. Item Conservation
                            if result.inventory_update:
                                for item in result.inventory_update.items_add:
                                    m_key = f"metric_total_{item.item_id}"
                                    resource_updates[m_key] = resource_updates.get(m_key, 0.0) + item.quantity
                                for item in result.inventory_update.items_remove:
                                    m_key = f"metric_total_{item.item_id}"
                                    resource_updates[m_key] = resource_updates.get(m_key, 0.0) - item.quantity
                    else:
                        # Global rejection tracking (Phase E4.7)
                        rej_delta = dict(update.rejections_delta)
                        rej_key = result.reason if result.reason else "UNKNOWN_REJECTION"
                        rej_delta[rej_key] = rej_delta.get(rej_key, 0) + 1
                        update = replace(update, rejections_delta=rej_delta)
                        
                        # If any intent in the group fails, and it's required, fail the group
                        if intent.is_group_required:
                            group_success = False
                            
                            # Phase E5: Update previously accepted intents in THIS group to REJECTED
                            for prev_intent in group_intents:
                                # Find its result in the list (it might be the current one or a previous one)
                                for idx, res in enumerate(intent_results):
                                    if res.transaction_id == prev_intent.transaction_id:
                                        if res.accepted:
                                            intent_results[idx] = replace(res, accepted=False, reason="GROUP_ROLLBACK")
                            
                            # Phase E5: Record remaining intents as SKIPPED
                            remaining_index = group_intents.index(intent) + 1
                            for skipped_intent in group_intents[remaining_index:]:
                                from src.core.state import IntentResult
                                intent_results.append(IntentResult(
                                    transaction_id=skipped_intent.transaction_id,
                                    accepted=False,
                                    reason="SKIPPED_DUE_TO_GROUP_FAILURE",
                                    source_kind=skipped_intent.source_kind,
                                    source_id=skipped_intent.source_id
                                ))
                                transaction_trace.append(f"TRANS_SKIP: Entity {e_id} {skipped_intent.transfer_kind} {skipped_intent.source_kind}:{skipped_intent.source_id} - GROUP_FAILED")
                            break
                
                if group_success:
                    has_any_accepted = True
                    # P0.2 Refinement: Commit group reservations to global tick reservations
                    for k, v in group_source_reservations.items():
                        source_reservations[k] = source_reservations.get(k, 0) + v
                else:
                    # Rollback group changes
                    current_inv_upd = cp_inv
                    current_id_upd = cp_id
                    current_bio_upd = cp_bio
                    current_attr_upd = cp_attr
                    current_combat_upd = cp_combat
                    current_equip_upd = cp_equip
                    current_reward_upd = cp_reward
                    current_strat_upd = cp_strat
                    current_home_storage_upds = cp_home_stor
                    refined_node_updates = cp_node_upds
                    refined_building_updates = cp_build_upds
                    ground_items_remove = cp_ground_rem
                    corpses_remove = cp_corpse_rem
                    refined_entity_updates[e_id] = replace(refined_entity_updates[e_id], quest=cp_quest_upd)
                    
                    # Phase 1 Law: Reset interaction progress if harvest/loot fails due to capacity
                    for intent in group_intents:
                        if intent.transfer_kind in ("HARVEST", "LOOT", "AUTO"):
                            from src.core.updates import InteractionUpdate
                            current_interaction_upd = InteractionUpdate(reset=True)
                            
                            # Law of Conservation: Proactively strip any node updates for this source
                            # if it failed, to ensure no "ghost" depletions happen.
                            if intent.source_kind == "NODE" and intent.source_id in refined_node_updates:
                                del refined_node_updates[intent.source_id]
                            break
                
                # P0.3: No i = j needed with iterator loop
                
            # Update entity and CLEAR intents
            if has_any_accepted:
                refined_entity_updates[e_id] = replace(refined_entity_updates[e_id], 
                    inventory=current_inv_upd,
                    identity=current_id_upd,
                    biological=current_bio_upd,
                    attributes=current_attr_upd,
                    combat=current_combat_upd,
                    equipment=current_equip_upd,
                    strategic=current_strat_upd,
                    interaction=current_interaction_upd,
                    reward=current_reward_upd,
                    resource_transfers=[],
                    intent_results=intent_results
                )
            else:
                refined_entity_updates[e_id] = replace(refined_entity_updates[e_id], 
                    reward=current_reward_upd, # Preserve rewards even if other intents failed (e.g. QUEST reward vs failed TRADE)
                    interaction=current_interaction_upd if current_interaction_upd else refined_entity_updates[e_id].interaction,
                    resource_transfers=[],
                    intent_results=intent_results
                )

        return replace(
            update,
            entity_updates=refined_entity_updates,
            node_updates=refined_node_updates,
            building_updates=refined_building_updates,
            transaction_trace=transaction_trace,
            ground_items_remove=ground_items_remove,
            corpses_remove=corpses_remove,
            resource_updates=resource_updates,
            home_storage_updates=current_home_storage_upds,
            processed_transaction_ids=accepted_transaction_ids
        )
