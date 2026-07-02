# Compliance IDs: SOC-025, SOC-145, SOC-146, SOC-147, SOC-148, SOC-149, SOC-150, SOC-151, SOC-152, SOC-153, SOC-154, SOC-155, SOC-156, SOC-157, SOC-160, SOC-162, SOC-163, SOC-164, SOC-172, SOC-173, SOC-174, SOC-176, SOC-177, SOC-178, SOC-179, SOC-183, SOC-184
# Compliance IDs: SOC-025
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
    def update_groups(state: AuthoritativeState, current_update: Optional[StateUpdate] = None) -> StateUpdate:
        """
        Main authoritative group coordination logic.
        Logic ID: SOC-182 (Party target propagation occurs inside authoritative tick pipeline)
        Logic ID: SOC-192 (Group coordination test runs through normal kernel tick)
        """
        from src.core.updates import StateUpdate, EntityUpdate
        from src.core.state import GroupRecord
        
        groups_add_or_update: List[GroupRecord] = []
        groups_remove: List[int] = []
        entity_updates: Dict[int, EntityUpdate] = {}

        def is_alive(e_id: int) -> bool:
            # Check for death in current update
            if current_update and e_id in current_update.entity_updates:
                upd = current_update.entity_updates[e_id]
                if upd.combat and upd.combat.alive_set is False:
                    return False
            
            ent = state.entities.get(e_id)
            return ent.combat.alive if ent else False
        
        def is_active(e_id: int) -> bool:
            """
            Return whether an entity is active after applying same-tick updates.

            Group lifecycle must use the effective same-tick state, not only the
            start-of-tick state. Otherwise a leader/member that becomes inactive during
            the tick can incorrectly remain in a group until the next tick.
            """
            if current_update and e_id in current_update.entity_updates:
                upd = current_update.entity_updates[e_id]

                if upd.active is False:
                    return False

            ent = state.entities.get(e_id)
            return ent.lifecycle.active if ent else False

        def get_pos(e_id: int) -> tuple[float, float]:
            # Check for move in current update
            if current_update and e_id in current_update.entity_updates:
                upd = current_update.entity_updates[e_id]
                if upd.new_position:
                    return upd.new_position
            
            ent = state.entities.get(e_id)
            return ent.navigation.position if ent else (0.0, 0.0)

        # 1. Process Existing Groups (Dissolution & Cohesion)
        # Optimization: Only process groups that were explicitly modified or had member changes
        # Logic ID: PERF-006 (Dirty Entity Tracking)
        from src.core.dirty import get_relevant_group_ids
        relevant_groups = get_relevant_group_ids(state, current_update)
        
        for g_id in sorted(relevant_groups):
            group = state.groups.get(g_id)
            if not group: continue
            
            leader = state.entities.get(group.leader_id)

            # Logic ID: SOC-176 (Party dissolves when leader is dead/missing)
            # Logic ID: SOC-189 (Group dissolution test covers dead leader)
            #
            # Important:
            #   Use is_alive(...) / is_active(...) instead of reading only the
            #   start-of-tick entity.
            #
            # Why:
            #   GroupSystem runs near the end of the authoritative pipeline and receives
            #   the current same-tick StateUpdate. If the leader died earlier in this same
            #   tick, the start-of-tick state may still show leader.combat.alive=True.
            #   Therefore same-tick CombatUpdate(alive_set=False) must be respected here.
            if (
                leader is None
                or not is_alive(group.leader_id)
                or not is_active(group.leader_id)
            ):
                groups_remove.append(g_id)

                for m_id in group.member_ids:
                    # Logic ID: SOC-179 (Party dissolution updates member group IDs)
                    if m_id in state.entities:
                        entity_updates[m_id] = EntityUpdate(
                            entity_id=m_id,
                            group_id_set=-1,
                        )

                continue

            # Filter members (alive and within reasonable range)
            new_member_ids: Set[int] = {group.leader_id}
            member_positions: List[tuple[float, float]] = [get_pos(group.leader_id)]
            
            for m_id in group.member_ids:
                if m_id == group.leader_id:
                    continue
                
                if not is_alive(m_id) or not is_active(m_id):
                    entity_updates[m_id] = EntityUpdate(
                        entity_id=m_id,
                        group_id_set=-1,
                    )
                    continue
                
                # Cohesion check
                # VERIFIED v2: group_cohesion_check
                m_pos = get_pos(m_id)
                dx = m_pos[0] - group.anchor[0]
                dy = m_pos[1] - group.anchor[1]
                dist_sq = dx*dx + dy*dy
                
                # Phase 7: Contract validity check
                # VERIFIED v2: group_contract_binding
                contract_invalid = False
                leader = state.entities.get(group.leader_id) # Needed for contract access
                if group.contract_id and leader:
                    from src.core.strategic import ContractStatus
                    contract = None
                    if current_update and group.leader_id in current_update.entity_updates:
                        leader_up = current_update.entity_updates[group.leader_id]
                        if leader_up.strategic:
                            contract = next((c for c in leader_up.strategic.contracts_add_or_update if c.id == group.contract_id), None)
                    if not contract:
                        contract = leader.strategic.contracts.get(group.contract_id)
                    if not contract or contract.status != ContractStatus.ACTIVE:
                        contract_invalid = True
                    elif contract.expiry_tick != -1 and state.tick > contract.expiry_tick:
                        contract_invalid = True
                
                if dist_sq > (group.cohesion_radius * 2)**2 or contract_invalid: 
                    entity_updates[m_id] = EntityUpdate(entity_id=m_id, group_id_set=-1)
                    continue
                
                new_member_ids.add(m_id)
                member_positions.append(m_pos)

            if len(new_member_ids) < 2:
                groups_remove.append(g_id)
                for m_id in new_member_ids:
                    entity_updates[m_id] = EntityUpdate(entity_id=m_id, group_id_set=-1)
                continue

            # Update Anchor
            # Logic ID: SOC-172 (Party anchor follows leader or agreed anchor rule)
            avg_x = sum(p[0] for p in member_positions) / len(member_positions)
            avg_y = sum(p[1] for p in member_positions) / len(member_positions)
            
            # Domain 7 Hardening: Shared Target Logic
            # Logic ID: SOC-183 (Shared target is valid and alive when assigned)
            # Logic ID: SOC-184 (Shared target clears when invalid/dead)
            new_shared_target_id = leader.task.payload.get("target_id")
            if not new_shared_target_id:
                new_shared_target_id = leader.navigation.target
            
            # Hysteresis: Keep old target if new one is None but leader is still acting
            if new_shared_target_id is None and group.shared_target_id is not None:
                if leader.task.work_kind in ("ENTITY_ACT", "COMBAT_ACT"):
                    new_shared_target_id = group.shared_target_id
            
            # Domain 4: Target Validity Check (Hardened)
            if new_shared_target_id:
                 target_ent = state.entities.get(new_shared_target_id)
                 if not target_ent or not target_ent.combat.alive or not target_ent.lifecycle.active:
                     new_shared_target_id = None
                 else:
                     # Range check
                     dx = target_ent.navigation.position[0] - avg_x
                     dy = target_ent.navigation.position[1] - avg_y
                     if (dx*dx + dy*dy) > (group.cohesion_radius * 2.0)**2:
                         new_shared_target_id = None
            else:
                 from src.systems.party import PartyCoordinationSystem
                 new_shared_target_id = PartyCoordinationSystem.validate_shared_target(g_id, state)
            
            # Update Roles
            new_roles = {group.leader_id: "LEADER"}
            for m_id in new_member_ids:
                if m_id == group.leader_id: continue
                existing_role = group.roles.get(m_id)
                if existing_role:
                    new_roles[m_id] = existing_role
                else:
                    member = state.entities.get(m_id)
                    role = member.combat.tactical_role if member and member.combat.tactical_role else "VANGUARD"
                    new_roles[m_id] = role

            updated_group = replace(
                group,
                member_ids=new_member_ids,
                anchor=(avg_x, avg_y),
                shared_target_id=new_shared_target_id if isinstance(new_shared_target_id, int) else None,
                roles=new_roles,
                last_updated_tick=state.tick
            )
            groups_add_or_update.append(updated_group)
            
            # Domain 7: Directive Propagation
            # Members inherit leader's project as a GROUP_OBJECTIVE directive
            if leader.strategic.current_project_id:
                project = leader.strategic.projects.get(leader.strategic.current_project_id)
                if project:
                    from src.core.strategic import DirectiveState, DirectivePriority
                    from src.core.updates import StrategicUpdate
                    for m_id in new_member_ids:
                        if m_id == leader.id: continue
                        
                        # Only propagate if member trusts leader
                        member = state.entities.get(m_id)
                        bond = member.social.bonds.get(leader.id)
                        trust = (bond.sentiment + 1.0) / 2.0 if bond else member.social.trust_history.get(leader.id, 0.5)
                        
                        if trust >= 0.3:
                            directive = DirectiveState(
                                id=f"group_obj_{group.id}_{m_id}",
                                kind="GROUP_OBJECTIVE",
                                target=project.kind,
                                priority=DirectivePriority.NORMAL,
                                salience=0.5,
                                created_tick=state.tick
                            )
                            m_upd = entity_updates.get(m_id, EntityUpdate(entity_id=m_id))
                            # Merge strategic updates
                            existing_strat = m_upd.strategic if m_upd.strategic else StrategicUpdate()
                            new_strat = replace(existing_strat,
                                directives_add_or_update=existing_strat.directives_add_or_update + [directive]
                            )
                            entity_updates[m_id] = replace(m_upd, strategic=new_strat)

        # 2. Group Formation (Purpose-Driven)
        # VERIFIED v2: group_formation_purpose_driven
        # Find entities without groups
        # Logic ID: PERF-006 (Dirty Entity Tracking - Relaxed for ungrouped entities)
        if getattr(state, "_has_contracts_cache", True):
            ungrouped_ids = sorted([e_id for e_id, e in state.entities.items() 
                                    if e.combat.alive and e.identity.group_id is None])
            
            # Purpose-Driven Formation: Check for active social contracts (Recruitment/Protection)
            already_forming: Set[int] = set()
            for i, id_a in enumerate(ungrouped_ids):
                if id_a in already_forming:
                    continue
                
                entity_a = state.entities[id_a]
                new_group_members = {id_a}
                active_contract_id = None
                
                # Check for contracts where id_a is source or target
                # Logic ID: SOC-160 (Party formation can be driven by accepted social contract)
                # Logic ID: SOC-187 (Group formation test covers accepted contract)
                # Logic ID: SOC-188 (Group formation test covers no contract / proximity-only rejection)
                # Logic ID: SOC-164 (Proximity alone does not create a party)
                for c_id in sorted(entity_a.strategic.contracts.keys()):
                    contract = entity_a.strategic.contracts[c_id]
                    from src.core.strategic import ContractStatus
                    if contract.status != ContractStatus.ACTIVE: continue
                    
                    other_id = contract.target_id if contract.source_id == id_a else contract.source_id
                    if other_id in state.entities:
                        other_entity = state.entities[other_id]
                        # Law: Entity must be alive, ungrouped, and NOT already being assigned a group this tick
                        if (other_entity.combat.alive and 
                            other_entity.identity.group_id is None and 
                            other_id not in already_forming):
                            
                            # Cohesion check: only form group if they are within range
                            dx = entity_a.navigation.position[0] - other_entity.navigation.position[0]
                            dy = entity_a.navigation.position[1] - other_entity.navigation.position[1]
                            if (dx*dx + dy*dy) < (10.0**2):
                                new_group_members.add(other_id)
                                # Use the first contract ID as the primary group contract
                                if active_contract_id is None:
                                    active_contract_id = c_id
                
                if len(new_group_members) >= 2:
                    # Form new group
                    new_g_id = 10000 + len(state.groups) + len(groups_add_or_update)
                    leader_id = id_a # Simplified: initiator is leader
                    anchor_x = sum(state.entities[m_id].navigation.position[0] for m_id in new_group_members) / len(new_group_members)
                    anchor_y = sum(state.entities[m_id].navigation.position[1] for m_id in new_group_members) / len(new_group_members)
                    
                    # Assign Roles
                    roles = {leader_id: "LEADER"}
                    for m_id in new_group_members:
                        if m_id == leader_id: continue
                        member = state.entities[m_id]
                        # Derive role from combat component or default
                        role = member.combat.tactical_role if member.combat.tactical_role else "VANGUARD"
                        roles[m_id] = role

                    from src.systems.social_systems.party_composition import PartyCompositionScorer
                    member_entities = [state.entities[mid] for mid in new_group_members if mid in state.entities]
                    comp_score = PartyCompositionScorer.score(member_entities)

                    new_group = GroupRecord(
                        id=new_g_id,
                        leader_id=leader_id,
                        member_ids=new_group_members,
                        anchor=(anchor_x, anchor_y),
                        contract_id=active_contract_id,
                        roles=roles,
                        last_updated_tick=state.tick,
                        composition_score=comp_score,
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
