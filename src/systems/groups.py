from __future__ import annotations
from dataclasses import replace
from typing import Dict, List, Set, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from src.core.state import AuthoritativeState, EntityState, GroupRecord
    from src.core.updates import StateUpdate, EntityUpdate
    from src.core.strategic import ContractStatus

class GroupSystem:
    """
    Authoritative logic for group formation, cohesion, and dissolution.
    Groups allow entities to cooperate on shared targets and stay spatially together.
    """

    @staticmethod
    def update_groups(state: AuthoritativeState) -> StateUpdate:
        from src.core.updates import StateUpdate, EntityUpdate
        from src.core.state import GroupRecord
        
        groups_add_or_update: List[GroupRecord] = []
        groups_remove: List[int] = []
        entity_updates: Dict[int, EntityUpdate] = {}

        # 1. Process Existing Groups (Dissolution & Cohesion)
        for g_id, group in state.groups.items():
            # Check leader
            leader = state.entities.get(group.leader_id)
            if not leader or not leader.combat.alive:
                # Leader is gone, dissolve group
                groups_remove.append(g_id)
                for m_id in group.member_ids:
                    if m_id in state.entities:
                        entity_updates[m_id] = EntityUpdate(entity_id=m_id, group_id_set=-1) # -1 means None/Reset
                continue

            # Filter members (alive and within reasonable range)
            new_member_ids: Set[int] = {group.leader_id}
            member_positions: List[tuple[float, float]] = [leader.position]
            
            for m_id in group.member_ids:
                if m_id == group.leader_id:
                    continue
                
                member = state.entities.get(m_id)
                if not member or not member.combat.alive:
                    entity_updates[m_id] = EntityUpdate(entity_id=m_id, group_id_set=-1)
                    continue
                
                # Cohesion check
                dx = member.position[0] - group.anchor[0]
                dy = member.position[1] - group.anchor[1]
                dist_sq = dx*dx + dy*dy
                
                # Phase 7: Contract validity check
                contract_invalid = False
                if group.contract_id:
                    from src.core.strategic import ContractStatus
                    contract = leader.strategic.contracts.get(group.contract_id)
                    if not contract or contract.status != ContractStatus.ACTIVE:
                        contract_invalid = True
                    elif contract.expiry_tick != -1 and state.tick > contract.expiry_tick:
                        contract_invalid = True
                
                if dist_sq > (group.cohesion_radius * 2)**2 or contract_invalid: 
                    entity_updates[m_id] = EntityUpdate(entity_id=m_id, group_id_set=-1)
                    continue
                
                new_member_ids.add(m_id)
                member_positions.append(member.position)

            if len(new_member_ids) < 2:
                groups_remove.append(g_id)
                for m_id in new_member_ids:
                    entity_updates[m_id] = EntityUpdate(entity_id=m_id, group_id_set=-1)
                continue

            # Update Anchor
            avg_x = sum(p[0] for p in member_positions) / len(member_positions)
            avg_y = sum(p[1] for p in member_positions) / len(member_positions)
            
            # Propagate Shared Target from Leader
            new_shared_target_id = leader.task.payload.get("target_id")
            if not new_shared_target_id:
                # Fallback to navigation target if any
                new_shared_target_id = leader.navigation.target # Wait, this is a tuple.
            
            # Actually, let's use the task payload target_id specifically for combat focus.
            
            updated_group = replace(
                group,
                member_ids=new_member_ids,
                anchor=(avg_x, avg_y),
                shared_target_id=new_shared_target_id if isinstance(new_shared_target_id, int) else None,
                last_updated_tick=state.tick
            )
            groups_add_or_update.append(updated_group)

        # 2. Group Formation (Purpose-Driven)
        # Find entities without groups
        ungrouped_ids = [e_id for e_id, e in state.entities.items() 
                         if e.combat.alive and e.group_id is None]
        
        # Purpose-Driven Formation: Check for active social contracts (Recruitment/Protection)
        already_forming: Set[int] = set()
        for i, id_a in enumerate(ungrouped_ids):
            if id_a in already_forming:
                continue
            
            entity_a = state.entities[id_a]
            new_group_members = {id_a}
            active_contract_id = None
            
            # Check for contracts where id_a is source or target
            for c_id, contract in entity_a.strategic.contracts.items():
                from src.core.strategic import ContractStatus
                if contract.status != ContractStatus.ACTIVE: continue
                
                other_id = contract.target_id if contract.source_id == id_a else contract.source_id
                if other_id in state.entities:
                    other_entity = state.entities[other_id]
                    if other_entity.combat.alive and other_entity.group_id is None:
                        # Cohesion check: only form group if they are within range
                        dx = entity_a.position[0] - other_entity.position[0]
                        dy = entity_a.position[1] - other_entity.position[1]
                        if (dx*dx + dy*dy) < (10.0**2):
                            new_group_members.add(other_id)
                            active_contract_id = c_id
                            break # Simplified: stop at first contract
            
            if len(new_group_members) >= 2:
                # Form new group
                new_g_id = 10000 + len(state.groups) + len(groups_add_or_update)
                leader_id = id_a # Simplified: initiator is leader
                anchor_x = sum(state.entities[m_id].position[0] for m_id in new_group_members) / len(new_group_members)
                anchor_y = sum(state.entities[m_id].position[1] for m_id in new_group_members) / len(new_group_members)
                
                new_group = GroupRecord(
                    id=new_g_id,
                    leader_id=leader_id,
                    member_ids=new_group_members,
                    anchor=(anchor_x, anchor_y),
                    contract_id=active_contract_id,
                    last_updated_tick=state.tick
                )
                groups_add_or_update.append(new_group)
                
                for m_id in new_group_members:
                    already_forming.add(m_id)
                    entity_updates[m_id] = EntityUpdate(entity_id=m_id, group_id_set=new_g_id)

        return StateUpdate(
            entity_updates=entity_updates,
            groups_add_or_update=groups_add_or_update,
            groups_remove=groups_remove
        )
