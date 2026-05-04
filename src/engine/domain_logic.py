# src/engine/domain_logic.py
from __future__ import annotations
from typing import TYPE_CHECKING, Tuple, Dict, Any, Optional, List
from dataclasses import replace

from src.core.updates import (
    EntityUpdate, IdentityUpdate, CombatUpdate, 
    LifecycleUpdate, StateUpdate, RewardUpdate,
    SocialUpdate
)

if TYPE_CHECKING:
    from src.core.state import EntityState

class SimulationDomainLogic:
    """
    Law: Absolute semantic truth for RPG domain operations.
    Isolated from networking, concurrency, or worker protocols.
    """

    @staticmethod
    def execute_move(
        state: AuthoritativeState,
        entity: EntityState, 
        target_pos: Tuple[float, float]
    ) -> Dict[int, EntityUpdate]:
        """GRID-BASED AUTHORITATIVE MOVEMENT."""
        from src.engine.movement import MovementSystem
        from src.engine.quests import QuestResolutionSystem
        from dataclasses import replace
        
        res = MovementSystem.resolve_move(state, entity, target_pos)
        updates_dict = res if isinstance(res, dict) else {entity.id: res}
        
        # Check EXPLORE quests
        entity_up = updates_dict.get(entity.id)
        if entity_up and entity_up.new_position:
            # Create a temporary entity with the new position for evaluation
            temp_entity = replace(entity, navigation=replace(entity.navigation, position=entity_up.new_position))
            q_updates = QuestResolutionSystem.evaluate_explore(state, temp_entity)
            if q_updates:
                # Merge the first quest update (for simplicity, we assume one at a time or we just take the first)
                updates_dict[entity.id] = replace(entity_up, quest=q_updates[0])
                
        return updates_dict

    @staticmethod
    def execute_brain(
        state: AuthoritativeState,
        entity: EntityState
    ) -> Dict[int, EntityUpdate]:
        """RPG TACTICAL COGNITION."""
        # ... (brain logic remains same, just wrap return in dict)
        # To keep it concise I'll skip re-typing the whole brain logic and just fix the return
        from src.engine.cognition import SensoryFilter, AppraisalSystem
        from src.systems.strategic import StrategicIntelligenceSystem
        from src.engine.tactical import TacticalDecisionSystem
        
        # Phase E5.3: Read-Only Guard (Hardening)
        readonly_state = state.to_readonly()
        
        neighbors = SimulationDomainLogic.get_neighbor_view(readonly_state, entity, radius=10.0)
        salient_neighbors = SensoryFilter.filter_saliency(entity, neighbors)
        
        trauma = SimulationDomainLogic.get_region_trauma(readonly_state, entity.position)
        emotion = AppraisalSystem.evaluate_emotional_state(
            entity, 
            salient_neighbors, 
            region_trauma=trauma,
            social_context=entity.social
        )
        
        # Phase 6: Blocker Inference from recent failures
        current_proj = entity.strategic.projects.get(entity.strategic.current_project_id or "")
        inferred_up = StrategicIntelligenceSystem.infer_blockers(
            entity,
            entity.task.work_kind,
            entity.task.payload,
            navigation_failure=entity.navigation.last_failure_reason,
            current_project=current_proj
        )
        
        temp_entity = entity
        if inferred_up.blockers_add_or_update:
             from src.engine.apply import ApplyPath
             temp_strat = entity.strategic
             for b in inferred_up.blockers_add_or_update:
                  temp_strat = replace(temp_strat, blockers={**temp_strat.blockers, b.id: b})
             temp_entity = replace(entity, strategic=temp_strat)
             
        strat_up = StrategicIntelligenceSystem.evaluate_strategic_intent(readonly_state, temp_entity)
        
        # Merge inferred blockers into strat_up
        if inferred_up.blockers_add_or_update:
            strat_up = replace(
                strat_up,
                blockers_add_or_update=list(set(strat_up.blockers_add_or_update + inferred_up.blockers_add_or_update))
            )
        
        temp_entity = entity
        if strat_up.current_project_id_set is not None:
             from src.engine.apply import ApplyPath
             temp_projects = dict(entity.strategic.projects)
             for p in strat_up.projects_add_or_update:
                 temp_projects[p.id] = p
                 
             temp_strat = replace(
                 entity.strategic,
                 projects=temp_projects,
                 current_project_id=strat_up.current_project_id_set,
                 current_objective_id=strat_up.current_objective_id_set
             )
             temp_entity = replace(entity, strategic=temp_strat)
             
        tactical_up = TacticalDecisionSystem.evaluate_entity_intent(readonly_state, temp_entity)
        
        from src.systems.detour import DetourSuggestionSystem
        bandwidth_up = DetourSuggestionSystem.enforce_bandwidth(temp_entity, state.tick)
        
        final_strat = strat_up
        if (strat_up.current_project_id_set is None and 
            not strat_up.projects_add_or_update and 
            tactical_up.strategic is not None):
             final_strat = tactical_up.strategic
             
        from src.core.updates import StrategicUpdate
        if final_strat is None:
             final_strat = StrategicUpdate()
             
        final_strat = replace(
            final_strat,
            leads_remove=list(set(final_strat.leads_remove + bandwidth_up.leads_remove)),
            concerns_remove=list(set(final_strat.concerns_remove + bandwidth_up.concerns_remove)),
            overload_source_set=bandwidth_up.overload_source_set or final_strat.overload_source_set,
            overload_tick_set=bandwidth_up.overload_tick_set or final_strat.overload_tick_set
        )
        
        return {entity.id: replace(tactical_up, 
            strategic=final_strat, 
            readiness_delta=-100.0
        )}

    @staticmethod
    def execute_action(
        entity: EntityState, 
        payload: Optional[Dict[str, Any]] = None,
        current_tick: int = 0,
        neighbor_view: List[tuple[int, EntityState]] = None,
        context: Any = None
    ) -> Dict[int, EntityUpdate]:
        """
        Standard action cost and routine logic.
        VERIFIED v2: SimulationDomainLogic.execute_action
        """
        action = payload.get("action") if payload else None
        from src.core.updates import (
            BiologicalUpdate, CombatUpdate, RewardUpdate, LifecycleUpdate,
            NavigationUpdate, EntityUpdate, IdentityUpdate, ResourceTransferIntent,
            StaminaUpdate
        )
        
        # 0. Readiness Check
        from src.engine.legality import LegalityServiceV2
        ready, r_reason = LegalityServiceV2.verify_readiness(entity)
        if not ready:
            return {entity.id: EntityUpdate(
                entity_id=entity.id,
                navigation=NavigationUpdate(failure_reason=r_reason)
            )}
            
        if action == "SLEEP":
            return {entity.id: EntityUpdate(
                entity_id=entity.id,
                readiness_delta=-100.0,
                biological=BiologicalUpdate(
                    sleep_debt_delta=-20.0,
                    rest_pressure_delta=-10.0,
                    last_sleep_tick_set=current_tick
                )
            )}
        elif action == "EAT":
            return {entity.id: EntityUpdate(
                entity_id=entity.id,
                readiness_delta=-100.0,
                biological=BiologicalUpdate(
                    hunger_delta=-40.0,
                    last_meal_tick_set=current_tick
                )
            )}
        elif action == "REST":
            return {entity.id: EntityUpdate(
                entity_id=entity.id,
                readiness_delta=-100.0,
                biological=BiologicalUpdate(
                    rest_pressure_delta=-30.0
                )
            )}
        elif action == "RECRUIT":
            target_id = payload.get("target_id")
            payout = payload.get("payout", 100)
            target = None
            if neighbor_view:
                for eid, ent in neighbor_view:
                    if eid == target_id:
                        target = ent
                        break
            if not target and context and hasattr(context, "entities"):
                target = context.entities.get(target_id)
                
            if not target:
                from src.core.updates import NavigationUpdate
                return {entity.id: EntityUpdate(entity_id=entity.id, navigation=NavigationUpdate(failure_reason="TARGET_NOT_FOUND"))}
            
            from src.social.appraisal import SocialAppraisalSystem
            from src.core.strategic import ContractState, ContractKind, ContractStatus
            from src.core.updates import InventoryUpdate, StrategicUpdate
            
            # Evaluate offer using consolidated appraisal logic
            temp_contract = ContractState(
                id="temp_eval",
                kind=ContractKind.RECRUITMENT,
                source_id=entity.id,
                target_id=target.id,
                terms={"daily_pay": payout, "risk_level": "NORMAL"},
                status=ContractStatus.OFFERED,
                created_tick=current_tick
            )
            status, reason, _ = SocialAppraisalSystem.appraise_contract(target, temp_contract, context)
            
            if status == ContractStatus.ACCEPTED:
                contract_id = f"contract_recruit_{entity.id}_{target_id}_{current_tick}"
                contract = ContractState(
                    id=contract_id,
                    kind=ContractKind.RECRUITMENT,
                    source_id=entity.id,
                    target_id=target_id,
                    status=ContractStatus.ACTIVE,
                    terms={"payout": payout}
                )
                
                from src.core.updates import ResourceTransferIntent, SocialUpdate
                group_id = f"recruit_{entity.id}_{target_id}_{current_tick}"
                
                attacker_up = EntityUpdate(
                    entity_id=entity.id,
                    readiness_delta=-100.0,
                    resource_transfers=[ResourceTransferIntent(
                        source_id=target_id,
                        source_kind="RECRUIT",
                        gold_delta=-payout,
                        group_id=group_id,
                        transfer_kind="RECRUITMENT",
                        strategic_upd=StrategicUpdate(contracts_add_or_update=[contract])
                    )]
                )
                target_up = EntityUpdate(
                    entity_id=target_id,
                    social=SocialUpdate(last_offer_tick_set=current_tick),
                    resource_transfers=[ResourceTransferIntent(
                        source_id=entity.id,
                        source_kind="RECRUIT",
                        gold_delta=payout,
                        group_id=group_id,
                        transfer_kind="RECRUITMENT",
                        strategic_upd=StrategicUpdate(contracts_add_or_update=[contract])
                    )]
                )
                return {entity.id: attacker_up, target_id: target_up}
            else:
                from src.core.updates import SocialUpdate
                attacker_up = EntityUpdate(
                    entity_id=entity.id, 
                    readiness_delta=-50.0, 
                    task=replace(entity.task, payload={**payload, "outcome": "FAILURE", "reason": "REJECTED"})
                )
                target_up = EntityUpdate(
                    entity_id=target_id,
                    social=SocialUpdate(rejection_increment={entity.id: 1}, last_offer_tick_set=current_tick)
                )
                return {entity.id: attacker_up, target_id: target_up}
        elif action == "ALLOCATE_AP":
            attr_name = payload.get("attribute")
            amount = payload.get("amount", 1)
            
            if entity.identity.unspent_ap < amount:
                return {entity.id: EntityUpdate(entity_id=entity.id, navigation=NavigationUpdate(failure_reason="INSUFFICIENT_AP"))}
            
            from src.core.updates import AttributeUpdate, IdentityUpdate, CombatUpdate
            attr_up = AttributeUpdate()
            combat_up = CombatUpdate()
            
            if attr_name == "strength":
                attr_up = replace(attr_up, strength_delta=amount)
                combat_up = replace(combat_up, atk_delta=amount * 2) # Strength boosts ATK
            elif attr_name == "vitality":
                attr_up = replace(attr_up, vitality_delta=amount)
                combat_up = replace(combat_up, max_hp_delta=amount * 10, hp_delta=amount * 10)
            # ... add more as needed
            
            return {entity.id: EntityUpdate(
                entity_id=entity.id,
                identity=IdentityUpdate(unspent_ap_delta=-amount),
                attributes=attr_up,
                combat=combat_up
            )}
        elif action == "TRAIN":
            skill_id = payload.get("skill_id")
            if not skill_id:
                from src.core.updates import NavigationUpdate
                return {entity.id: EntityUpdate(entity_id=entity.id, navigation=NavigationUpdate(failure_reason="MISSING_SKILL_ID"))}
            
            # Cost: 50 gold (LEG-RPG-001)
            TRAIN_COST = 50
            
            from src.core.updates import ResourceTransferIntent, IdentityUpdate, StrategicUpdate
            
            # Find matching capability blockers
            resolved_blockers = []
            for b_id, b in entity.strategic.blockers.items():
                if b.kind == "capability" and b.subject == skill_id:
                    resolved_blockers.append(b_id)

            # Transaction Intent with Contingent Updates
            intent = ResourceTransferIntent(
                source_id="CLASS_HALL",
                source_kind="TOWN_SERVICE",
                gold_delta=-TRAIN_COST,
                transfer_kind="TRAIN",
                is_group_required=True,
                identity_upd=IdentityUpdate(recipes_learned=[skill_id]),
                strategic_upd=StrategicUpdate(blockers_remove=resolved_blockers)
            )
            
            return {entity.id: EntityUpdate(
                entity_id=entity.id,
                readiness_delta=-100.0,
                resource_transfers=[intent]
            )}
        elif action == "REPAIR":
            # Repair all equipped items (Phase 8)
            total_cost = 0
            repair_deltas = {}
            for slot, dur in entity.equipment.durability.items():
                if dur < 100.0:
                    cost = int((100.0 - dur) * 0.5) # 0.5 gold per 1 durability point
                    total_cost += cost
                    repair_deltas[slot] = 100.0 # Set to max
            
            if not repair_deltas:
                # Nothing to repair
                return {entity.id: EntityUpdate(entity_id=entity.id, readiness_delta=-10.0)}
                
            from src.core.updates import ResourceTransferIntent, EquipmentUpdate
            intent = ResourceTransferIntent(
                source_id="BLACKSMITH",
                source_kind="TOWN_SERVICE",
                gold_delta=-total_cost,
                gold_cost=total_cost,
                transfer_kind="REPAIR",
                equipment_upd=EquipmentUpdate(durability_set=repair_deltas)
            )
            
            return {entity.id: EntityUpdate(
                entity_id=entity.id,
                readiness_delta=-100.0,
                resource_transfers=[intent]
            )}
        elif action == "INTERACT":
            from src.core.updates import InteractionUpdate
            target_id = payload.get("target_id")
            return {entity.id: EntityUpdate(
                entity_id=entity.id,
                readiness_delta=-100.0,
                interaction=InteractionUpdate(target_node_id=target_id, progress_delta=1)
            )}
        elif action == "ATTACK":
            target_id = payload.get("target_id")
            target = None
            if neighbor_view:
                for eid, ent in neighbor_view:
                    if eid == target_id:
                        target = ent
                        break
            
            if not target and context and hasattr(context, "entities"):
                target = context.entities.get(target_id)
            
            if target and context:
                from src.engine.legality import LegalityServiceV2
                is_legal, reason = LegalityServiceV2.verify_attack_legality(entity, target, context)
                if not is_legal:
                    return {entity.id: EntityUpdate(entity_id=entity.id, readiness_delta=-50.0, navigation=NavigationUpdate(failure_reason=reason))}
                from src.engine.combat import CombatResolutionSystem
                combat_up = CombatResolutionSystem.resolve_attack(entity, target, context)
                
                # Attacker Update: Cost + Rewards
                from src.core.updates import ResourceTransferIntent
                attacker_up = EntityUpdate(
                    entity_id=entity.id,
                    readiness_delta=-100.0,
                    equipment=combat_up.attacker_equipment_upd,
                    resource_transfers=combat_up.resource_transfers
                )
                
                # Check HUNT quests if target was killed
                if combat_up.alive_set is False:
                    from src.engine.quests import QuestResolutionSystem
                    q_updates = QuestResolutionSystem.evaluate_combat_victory(entity, target.kind)
                    if q_updates:
                        attacker_up = replace(attacker_up, quest=q_updates[0])

                
                # Defender Update: Damage + Mortality
                defender_combat_up = combat_up
                
                # Phase 7: Social Consequences & Betrayal Check
                from src.core.updates import StrategicUpdate, SocialUpdate
                social_up = combat_up.social_upd or SocialUpdate()
                strat_up = StrategicUpdate()
                group_dissolve_upd = None
                
                if entity.group_id is not None and entity.group_id == target.group_id:
                    from src.social.appraisal import SocialAppraisalSystem
                    s_up, st_up = SocialAppraisalSystem.process_betrayal(
                        target, entity.id, salience=0.8, current_tick=current_tick
                    )
                    # Merge s_up with social_up
                    social_up = social_up.merge(s_up)
                    strat_up = st_up
                    group_dissolve_upd = -1 # None/Reset
                
                defender_up = EntityUpdate(
                    entity_id=target.id,
                    combat=combat_up,
                    wound_update=combat_up.wound_update,
                    social=social_up,
                    strategic=strat_up if strat_up.directives_add_or_update else None,
                    group_id_set=group_dissolve_upd,
                    lifecycle=LifecycleUpdate(
                        age_delta=0,
                        generation_delta=combat_up.generation_delta,
                        is_permadeath_set=combat_up.is_permadeath_set
                    ) if (combat_up.generation_delta != 0 or combat_up.is_permadeath_set is not None) else None
                )
                
                # Stamina drain on attack (Checklist Part 6 Section E)
                from src.core.updates import StaminaUpdate
                stamina_cost = 5.0 # Standard attack cost
                attacker_up = replace(attacker_up, stamina_update=StaminaUpdate(current_delta=-stamina_cost))
                
                return {entity.id: attacker_up, target.id: defender_up}
        elif action == "SKILL":
            from src.core.skills import SKILL_REGISTRY
            from src.engine.rpg_depth import StaminaService, SkillScalingService
            from src.engine.combat import CombatResolutionSystem
            
            skill_id = payload.get("skill_id")
            target_id = payload.get("target_id")
            skill = SKILL_REGISTRY.get(skill_id)
            
            # 1. Skill Exists and Known?
            if not skill or skill_id not in entity.identity.learned_skills:
                 return {entity.id: EntityUpdate(entity_id=entity.id, readiness_delta=-10.0)}
            
            # 2. Cooldown?
            current_tick = getattr(context, "tick", 0) if context else 0
            if current_tick < entity.identity.cooldowns.get(skill_id, 0):
                 return {entity.id: EntityUpdate(entity_id=entity.id, readiness_delta=-10.0)}
            
            # 3. Stamina?
            if not StaminaService.can_use_skill(entity.stamina, skill.cost):
                 return {entity.id: EntityUpdate(entity_id=entity.id, readiness_delta=-10.0)}
                 
            # 4. Target?
            target = None
            if neighbor_view:
                for eid, ent in neighbor_view:
                    if eid == target_id:
                        target = ent
                        break
            if not target and context and hasattr(context, "entities"):
                target = context.entities.get(target_id)
            
            if not target or not target.combat.alive:
                 return {entity.id: EntityUpdate(entity_id=entity.id, readiness_delta=-10.0)}

            # 5. Resolve
            skill_dmg = SkillScalingService.calculate_skill_damage(
                skill.power, skill.category.name, entity.attributes, base_atk=entity.combat.atk
            )
            
            combat_up = CombatResolutionSystem.resolve_skill_usage(
                entity, target, context, skill_dmg
            )
            
            if combat_up.outcome_kind == "REJECTED":
                return {entity.id: EntityUpdate(entity_id=entity.id, readiness_delta=-10.0)}
            
            # 6. Apply Side Effects
            next_ready_tick = current_tick + skill.cooldown
            stamina_cost = StaminaService.drain_skill(entity.stamina, skill.cost)
            
            attacker_up = EntityUpdate(
                entity_id=entity.id,
                readiness_delta=-100.0,
                identity=IdentityUpdate(cooldown_updates={skill_id: next_ready_tick}),
                stamina_update=StaminaUpdate(current_delta=-stamina_cost),
                equipment=combat_up.attacker_equipment_upd,
                resource_transfers=combat_up.resource_transfers
            )
            
            defender_up = EntityUpdate(
                entity_id=target.id,
                combat=combat_up,
                wound_update=combat_up.wound_update,
                equipment=combat_up.equipment_upd,
                lifecycle=LifecycleUpdate(
                    generation_delta=combat_up.generation_delta,
                    is_permadeath_set=combat_up.is_permadeath_set
                ) if (combat_up.generation_delta != 0 or combat_up.is_permadeath_set is not None) else None
            )
            
            return {entity.id: attacker_up, target.id: defender_up}
        elif action == "AOE_ATTACK":
            from src.engine.combat import CombatResolutionSystem
            target_pos = payload.get("target_pos")
            radius = payload.get("radius", 1)
            
            # Identify primary target (if any) at that position
            defender = None
            for eid, ent in context.entities.items():
                if ent.position == target_pos and ent.combat.alive:
                    defender = ent
                    break
            
            # resolve_aoe_attack returns Dict[int, CombatUpdate] for all affected entities
            combat_updates = CombatResolutionSystem.resolve_aoe_attack(
                entity, target_pos, radius, context, defender=defender
            )
            
            attacker_combat = combat_updates.get(entity.id)
            if attacker_combat and attacker_combat.outcome_kind == "REJECTED":
                return {entity.id: EntityUpdate(entity_id=entity.id, readiness_delta=-10.0)}
            
            updates = {}
            for eid, c_up in combat_updates.items():
                if eid == entity.id:
                    # Attacker Update: Readiness + Rewards
                    updates[eid] = EntityUpdate(
                        entity_id=eid,
                        readiness_delta=-100.0,
                        combat=c_up, # Holds simultaneous_intents
                        resource_transfers=c_up.resource_transfers
                    )
                else:
                    # Victim Update: Damage + Mortality + Durability
                    updates[eid] = EntityUpdate(
                        entity_id=eid,
                        combat=c_up,
                        wound_update=c_up.wound_update,
                        equipment=c_up.equipment_upd,
                        lifecycle=LifecycleUpdate(
                            generation_delta=c_up.generation_delta,
                            is_permadeath_set=c_up.is_permadeath_set
                        ) if (c_up.generation_delta != 0 or c_up.is_permadeath_set is not None) else None
                    )
            
            # Stamina drain on AOE attack
            from src.core.updates import StaminaUpdate
            stamina_cost = 10.0 # AOE cost
            updates[entity.id] = replace(updates[entity.id], stamina_update=StaminaUpdate(current_delta=-stamina_cost))
            
            return updates

        return {entity.id: EntityUpdate(
            entity_id=entity.id,
            readiness_delta=-100.0
        )}
    @staticmethod
    def drain_debt(owner_id: str, profile) -> int:
        """
        Milestone C Law: Authoritative Drain Logic.
        Determines how much work debt is cleared in a single execution unit.
        """
        # owner_id is the subsystem name (e.g. "REPLAY", "KERNEL")
        return -profile.max_worker_count

    @staticmethod
    def get_neighbor_view(
        state: AuthoritativeState,
        subject: EntityState, 
        radius: float
    ) -> List[tuple[int, EntityState]]:
        """
        Produce a deterministic, ID-sorted view of nearby entities.
        Uses a spatial grid to optimize O(N^2) lookups.
        VERIFIED v2: spatial_query_optimization
        """
        grid = SimulationDomainLogic._get_cached_spatial_grid(state)
        candidate_ids = grid.get_neighbors(subject.position, radius)
        
        neighbors = []
        sx, sy = subject.position
        for e_id in candidate_ids:
            if e_id == subject.id:
                continue
            
            ent = state.entities[e_id]
            ex, ey = ent.position
            dist = ((ex - sx)**2 + (ey - sy)**2)**0.5
            if dist <= radius:
                neighbors.append((e_id, ent))
                
        # Sort by ID for determinism
        neighbors.sort(key=lambda x: x[0])
        return neighbors

    @staticmethod
    def _get_cached_spatial_grid(state: AuthoritativeState):
        """Internal helper to cache grid per tick."""
        if not hasattr(SimulationDomainLogic, "_grid_cache"):
            SimulationDomainLogic._grid_cache = (None, None) # (state_id, grid)
            
        state_id = id(state)
        if SimulationDomainLogic._grid_cache[0] != state_id:
            from src.engine.spatial import SpatialGrid
            SimulationDomainLogic._grid_cache = (state_id, SpatialGrid(state.entities))
            
        return SimulationDomainLogic._grid_cache[1]

    @staticmethod
    def get_region_trauma(
        state: AuthoritativeState,
        pos: Tuple[float, float]
    ) -> float:
        """
        Pillar 4.2: Environmental Dread.
        Finds the trauma score of the region containing the given position.
        """
        px, py = pos
        for region in state.regions.values():
            xmin, ymin, xmax, ymax = region.bounds
            if xmin <= px <= xmax and ymin <= py <= ymax:
                return region.trauma_score
        return 0.0
