from __future__ import annotations
from dataclasses import replace
from typing import TYPE_CHECKING, Dict, List, Tuple

from src_legacy.core.updates import StateUpdate, EntityUpdate, NavigationUpdate

if TYPE_CHECKING:
    from src_legacy.core.state import AuthoritativeState

class AuthoritativeApplyPipeline:
    """
    Unified authoritative refinement pipeline for the V2 Engine.
    Enforces the "Proposal -> Refinement -> Apply" law.
    """

    @staticmethod
    def refine(state: AuthoritativeState, raw_update: StateUpdate) -> StateUpdate:
        """
        Refines a proposed StateUpdate through the authoritative law pipeline.
        Consolidates Town, Shop, Blacksmith, Interaction, and Movement rules.
        """
        from src_legacy.engine.town_resolution import TownResolutionSystem
        from src_legacy.engine.shop import ShopSystem
        from src_legacy.engine.blacksmith import BlacksmithSystem
        from src_legacy.engine.interaction import InteractionSystem
        from src_legacy.systems.strategic import StrategicIntelligenceSystem
        from src_legacy.systems.redirection import StrategicRedirectionSystem
        from src_legacy.systems.biological import BiologicalSystem
        from src_legacy.engine.movement import MovementSystem
        from src_legacy.engine.world_dynamics import WorldDynamicsSystem
        from src_legacy.engine.evolution import EvolutionSystem
        from src_legacy.engine.sabotage import BuildingSabotageSystem
        from src_legacy.engine.combat import CombatResolutionSystem
        from src_legacy.engine.legality import LegalityServiceV2
        from src_legacy.systems.lifecycle import LifecycleSystem
        from src_legacy.systems.groups import GroupSystem
        
        # 1. Territorial & Service Laws (Healing, Shopping, Crafting)
        # These operate on current position (or proposed new position)
        update = TownResolutionSystem.resolve(state, raw_update)
        update = ShopSystem.enforce(state, update)
        update = BlacksmithSystem.enforce(state, update)
        
        # 1.2 Combat Laws (Attack resolution)
        update = AuthoritativeApplyPipeline._route_combat_intent(state, update)
        
        # 1.5 World Dynamics (Regional Hazards, Calamities)
        from src_legacy.systems.generator import EntityGenerator
        generator = EntityGenerator(state.seed + state.tick)
        update = WorldDynamicsSystem.resolve_dynamics(state, update, generator)
        
        # 1.6 Building Sabotage
        update = BuildingSabotageSystem.resolve(state, update)
        
        # 2. Intent Routing (Interaction)
        # Identifies if entity is at a resource node and initiates progress
        update = AuthoritativeApplyPipeline._route_interaction_intent(state, update)
        
        # 3. Interaction Enforcement (Harvesting/Looting)
        # Validates channeling progress, item weights, and node depletion
        update = InteractionSystem.enforce(state, update)
        
        # 4. Strategic Logic
        update = BiologicalSystem.resolve_pressures(state, update)
        update = StrategicIntelligenceSystem.resolve_blockers(state, update)
        update = StrategicIntelligenceSystem.validate_leads(state, update)
        from src_legacy.systems.detour import DetourSuggestionSystem
        # We'll call suppress_exhausted_leads and merge its updates
        # For now, let's just make it part of the strategic evaluation in the brain.
        
        update = StrategicIntelligenceSystem.evaluate_biological_concerns(state, update)
        update = StrategicRedirectionSystem.enforce(state, update)
        
        # 4.5 Social & Group Coordination
        group_update = GroupSystem.update_groups(state)
        update = AuthoritativeApplyPipeline._merge_state_updates(update, group_update)

        # 5. Quest & Progression
        from src_legacy.systems.progression import ProgressionSystem
        from src_legacy.engine.quests import QuestResolutionSystem
        from src_legacy.systems.skills import SkillSystem
        from src_legacy.systems.equipment import EquipmentSystem
        update = EquipmentSystem.resolve_equipment(state, update)
        update = ProgressionSystem.resolve_rewards(state, update)
        update = QuestResolutionSystem.evaluate_state_updates(state, update)
        update = ProgressionSystem.process_progression(state, update)
        update = SkillSystem.process_skill_unlocks(state, update)
        
        # 5. Intent Routing (Movement)
        # Resolves proposed navigation targets into step-wise moves
        update = AuthoritativeApplyPipeline._route_movement_intent(state, update)
        
        # 6. Conflict Resolution (Occupancy)
        # Tie-breaks multiple entities racing for the same tile
        update = AuthoritativeApplyPipeline._resolve_occupancy_conflicts(state, update)
        
        # 7. Evolution & Growth
        update = EvolutionSystem.evaluate(state, update)
        
        # 7.5 Near-Death Hardening (Pillar 2.2)
        update = AuthoritativeApplyPipeline._apply_near_death_hardening(state, update)
        
        # 8. Lifecycle (Aging, Death, Succession)
        update = LifecycleSystem.resolve_lifecycle(state, update)
        
        # 9. World Lifecycle (Resource Recharge, Decay, Cleanup)
        from src_legacy.systems.world_lifecycle import WorldLifecycleSystem
        update = WorldLifecycleSystem.resolve(state, update)
        
        return update

    @staticmethod
    def _route_interaction_intent(state: AuthoritativeState, update: StateUpdate) -> StateUpdate:
        refined_entity_updates = dict(update.entity_updates)
        for e_id, entity in state.entities.items():
            ent_upd = refined_entity_updates.get(e_id, EntityUpdate(entity_id=e_id))
            
            nav_target = entity.navigation.target
            if ent_upd.navigation and ent_upd.navigation.target_set is not None:
                nav_target = ent_upd.navigation.target_set
            
            if nav_target and (entity.position == nav_target):
                target_node = next((n for n in state.resource_nodes.values() if n.position == nav_target), None)
                if target_node and target_node.remaining_charges > 0:
                    from src_legacy.core.updates import InteractionUpdate
                    current_int = ent_upd.interaction or InteractionUpdate()
                    if not current_int.reset:
                         refined_entity_updates[e_id] = replace(ent_upd,
                             interaction=replace(current_int, target_node_id=target_node.id, progress_delta=1)
                         )
        return replace(update, entity_updates=refined_entity_updates)

    @staticmethod
    def _route_movement_intent(state: AuthoritativeState, update: StateUpdate) -> StateUpdate:
        from src_legacy.engine.movement import MovementSystem
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
                    move_updates = MovementSystem.resolve_move(state, entity, nav_target)
                    
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
                                readiness_delta=min(ent_upd.readiness_delta, u_upd.readiness_delta)
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
        from src_legacy.engine.combat import CombatResolutionSystem
        from src_legacy.engine.legality import LegalityServiceV2
        from src_legacy.core.updates import EntityUpdate, IdentityUpdate
        from src_legacy.engine.domain_logic import SimulationDomainLogic
        
        refined_entity_updates = dict(update.entity_updates)
        
        # Phase 9 Fix: Use list(keys) to avoid "dictionary changed size during iteration"
        for e_id in list(refined_entity_updates.keys()):
            ent_upd = refined_entity_updates[e_id]
            entity = state.entities.get(e_id)
            if not entity or not entity.active: continue
            
            task_upd = ent_upd.task
            if not task_upd or task_upd.work_kind_set != "ENTITY_ACT": continue
            
            action_kind = task_upd.payload_set.get("action")
            legal, reason = LegalityServiceV2.verify_action_legality(entity, action_kind, state)
            
            if not legal:
                 # Suppression! Remove the task and record failure
                 refined_entity_updates[e_id] = replace(ent_upd,
                    task=replace(task_upd, payload_set={**task_upd.payload_set, "outcome": "FAILURE", "reason": reason})
                 )
                 continue

            if action_kind == "ATTACK":
                target_id = task_upd.payload_set.get("target_id")
                if target_id is None: continue
                
                target = state.entities.get(target_id)
                if not target: continue
                
                # 1. Legality Check (LoS, Range, Faction)
                is_legal, reason = LegalityServiceV2.verify_attack_legality(entity, target, state)
                if not is_legal:
                     # Mark failure in task payload (Milestone 3 logic)
                     refined_entity_updates[e_id] = replace(ent_upd,
                         task=replace(task_upd, payload_set={**task_upd.payload_set, "failure_reason": reason})
                     )
                     continue
                
                # 2. Execute Action via Domain Logic (Authoritative multi-entity resolution)
                action_updates = SimulationDomainLogic.execute_action(
                    entity, 
                    payload=task_upd.payload_set, 
                    current_tick=state.tick,
                    neighbor_view=SimulationDomainLogic.get_neighbor_view(state, entity, radius=10.0),
                    context=state
                )
                
                # 3. Merge all updates from the action (Attacker + Target)
                for eid, upd in action_updates.items():
                    existing = refined_entity_updates.get(eid, EntityUpdate(entity_id=eid))
                    # Law: Readiness costs do not stack if multiple systems trigger on the same intent.
                    # We take the most restrictive (most negative) delta.
                    merged = existing.merge(upd)
                    refined_entity_updates[eid] = replace(merged, 
                        readiness_delta=min(existing.readiness_delta, upd.readiness_delta)
                    )
                
                # 4. Specific Strategic Overrides (if any)
                # Ensure the task outcome is marked as SUCCESS on the attacker
                final_ent_upd = refined_entity_updates[e_id]
                refined_entity_updates[e_id] = replace(final_ent_upd,
                    task=replace(final_ent_upd.task or task_upd, payload_set={**task_upd.payload_set, "outcome": "SUCCESS"})
                )

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
                
        return replace(update, entity_updates=refined_entity_updates)

    @staticmethod
    def _apply_near_death_hardening(state: AuthoritativeState, update: StateUpdate) -> StateUpdate:
        """
        Pillar 2.2: Near-death hardening. 
        Heroes surviving combat at <10% HP gain permanent +5 max_hp.
        """
        from src_legacy.core.models.enums import EntityRole
        from src_legacy.core.updates import CombatUpdate
        
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
        from src_legacy.core.updates import EntityUpdate
        
        new_entity_updates = dict(base.entity_updates)
        for e_id, extra_ent_upd in extra.entity_updates.items():
            if e_id in new_entity_updates:
                # Merge individual EntityUpdate (simplified)
                base_ent_upd = new_entity_updates[e_id]
                new_entity_updates[e_id] = replace(
                    base_ent_upd,
                    group_id_set=extra_ent_upd.group_id_set if extra_ent_upd.group_id_set is not None else base_ent_upd.group_id_set
                    # Add other fields if necessary
                )
            else:
                new_entity_updates[e_id] = extra_ent_upd
                
        return replace(
            base,
            entity_updates=new_entity_updates,
            groups_add_or_update=base.groups_add_or_update + extra.groups_add_or_update,
            groups_remove=base.groups_remove + extra.groups_remove
        )
