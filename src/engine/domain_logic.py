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
            temp_entity = replace(entity, position=entity_up.new_position)
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
        
        neighbors = SimulationDomainLogic.get_neighbor_view(state, entity, radius=10.0)
        salient_neighbors = SensoryFilter.filter_saliency(entity, neighbors)
        
        trauma = SimulationDomainLogic.get_region_trauma(state, entity.position)
        emotion = AppraisalSystem.evaluate_emotional_state(
            entity, 
            salient_neighbors, 
            region_trauma=trauma,
            social_context=entity.social
        )
        
        strat_up = StrategicIntelligenceSystem.evaluate_strategic_intent(state, entity)
        
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
             
        tactical_up = TacticalDecisionSystem.evaluate_entity_intent(state, temp_entity)
        
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
        
        return {entity.id: replace(tactical_up, strategic=final_strat, readiness_delta=-100.0)}

    @staticmethod
    def execute_action(
        entity: EntityState, 
        payload: Optional[Dict[str, Any]] = None,
        current_tick: int = 0,
        neighbor_view: List[tuple[int, EntityState]] = None,
        context: Any = None
    ) -> Dict[int, EntityUpdate]:
        """Standard action cost and routine logic."""
        action = payload.get("action") if payload else None
        from src.core.updates import (
            BiologicalUpdate, CombatUpdate, RewardUpdate, LifecycleUpdate,
            NavigationUpdate, EntityUpdate
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
            
            from src.systems.social import SocialAppraisalSystem
            from src.core.strategic import ContractState, ContractKind
            from src.core.updates import InventoryUpdate, StrategicUpdate
            
            # Evaluate offer
            success = SocialAppraisalSystem.evaluate_recruitment_offer(
                target, entity.id, payout=payout, risk=0.1
            )
            
            if success:
                contract_id = f"contract_recruit_{entity.id}_{target_id}_{current_tick}"
                contract = ContractState(
                    id=contract_id,
                    kind=ContractKind.RECRUITMENT,
                    source_id=entity.id,
                    target_id=target_id,
                    active=True,
                    terms={"payout": payout}
                )
                
                attacker_up = EntityUpdate(
                    entity_id=entity.id,
                    readiness_delta=-100.0,
                    inventory=InventoryUpdate(gold_delta=-payout),
                    strategic=StrategicUpdate(contracts_add_or_update=[contract])
                )
                target_up = EntityUpdate(
                    entity_id=target_id,
                    inventory=InventoryUpdate(gold_delta=payout),
                    strategic=StrategicUpdate(contracts_add_or_update=[contract])
                )
                return {entity.id: attacker_up, target_id: target_up}
            else:
                return {entity.id: EntityUpdate(
                    entity_id=entity.id, 
                    readiness_delta=-50.0, 
                    task=replace(entity.task, payload={**payload, "outcome": "FAILURE", "reason": "REJECTED"})
                )}
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
                    return {entity.id: EntityUpdate(
                        entity_id=entity.id,
                        readiness_delta=-50.0, # Partial cost for failed intent
                        navigation=NavigationUpdate(failure_reason=reason)
                    )}

                from src.engine.combat import CombatResolutionSystem
                combat_up = CombatResolutionSystem.resolve_attack(entity, target, context)
                
                # Attacker Update: Cost + Rewards
                from src.core.updates import ResourceTransferIntent
                attacker_up = EntityUpdate(
                    entity_id=entity.id,
                    readiness_delta=-100.0,
                    reward=RewardUpdate(xp_gain=combat_up.xp_gain, gold_gain=0),
                    resource_transfers=[ResourceTransferIntent(
                        source_id=target.id,
                        source_kind="COMBAT",
                        gold_delta=combat_up.gold_gain,
                        transfer_kind="REWARD"
                    )]
                )
                
                # Check HUNT quests if target was killed
                if combat_up.alive_set is False:
                    from src.engine.quests import QuestResolutionSystem
                    q_updates = QuestResolutionSystem.evaluate_combat_victory(entity, target.kind)
                    if q_updates:
                        attacker_up = replace(attacker_up, quest=q_updates[0])

                
                # Defender Update: Damage + Mortality
                # Note: We strip the rewards from the defender's update
                defender_combat_up = replace(combat_up, xp_gain=0, gold_gain=0)
                
                # Phase 7: Betrayal Check
                from src.core.updates import StrategicUpdate, SocialUpdate
                social_up = SocialUpdate(grudge_delta={entity.id: combat_up.damage_taken / target.combat.max_hp})
                strat_up = StrategicUpdate()
                group_dissolve_upd = None
                
                if entity.group_id is not None and entity.group_id == target.group_id:
                    from src.systems.social import SocialAppraisalSystem
                    s_up, st_up = SocialAppraisalSystem.process_betrayal(
                        target, entity.id, salience=0.8, current_tick=current_tick
                    )
                    # Merge s_up with social_up
                    social_up = replace(s_up, grudge_delta=social_up.grudge_delta)
                    strat_up = st_up
                    group_dissolve_upd = -1 # None/Reset
                
                defender_up = EntityUpdate(
                    entity_id=target.id,
                    combat=defender_combat_up,
                    social=social_up,
                    strategic=strat_up if strat_up.directives_add_or_update else None,
                    group_id_set=group_dissolve_upd,
                    lifecycle=LifecycleUpdate(
                        age_delta=0,
                        generation_delta=combat_up.generation_delta,
                        is_permadeath_set=combat_up.is_permadeath_set
                    ) if (combat_up.generation_delta != 0 or combat_up.is_permadeath_set is not None) else None
                )
                
                # Attacker also leaves group on betrayal
                if group_dissolve_upd is not None:
                    attacker_up = replace(attacker_up, group_id_set=group_dissolve_upd)
                
                return {entity.id: attacker_up, target.id: defender_up}

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
        Milestone D Law: Views must be bit-identical across parallel executions.
        """
        if hasattr(state, "neighbor_view"):
             return getattr(state, "neighbor_view")
             
        neighbors = []
        sx, sy = subject.position
        for e_id, ent in state.entities.items():
            if e_id == subject.id:
                continue
            
            ex, ey = ent.position
            dist = ((ex - sx)**2 + (ey - sy)**2)**0.5
            if dist <= radius:
                neighbors.append((e_id, ent))
        
        # Sort by Entity ID for absolute determinism
        neighbors.sort(key=lambda x: x[0])
        return neighbors

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
