from __future__ import annotations
import logging
import uuid
from typing import TYPE_CHECKING
from src.systems.infrastructure.base import System
from src.core.models.lived_structure import GroupRecord
from src.core.models.enums import GroupKind, GoalType, ContractKind
from src.core.models.strategy import StrategicStatus
from src.ai.strategy.contract_outcome import ContractOutcomeService

if TYPE_CHECKING:
    from src.systems.infrastructure.base import SystemContext

logger = logging.getLogger(__name__)

class GroupSystem(System):
    """Phase 3: Tactical coordination system for small-group scenarios."""

    def on_tick(self, context: SystemContext, tick: int) -> None:
        """Process group formation and maintenance every 10 ticks."""
        if tick % 10 != 0:
            return

        self._process_dissolution(context)
        self._process_formation(context)
        self._process_contract_formation(context)
        self._process_maintenance(context)

    def _process_formation(self, context: SystemContext) -> None:
        """Scan for entities with the same cluster_id and faction to form groups."""
        # Find all entities with a cluster_id who aren't already in a group
        eligible = []
        # Get existing member IDs for optimization
        all_member_ids = set()
        for group in context.world.group_registry.values():
            all_member_ids.update(group.member_ids)

        print(f"DEBUG: Found {len(context.world.entities)} total entities in world")
        for ent in context.world.entities.values():
            print(f"DEBUG: Checking entity {ent.id}: alive={ent.combat.alive}, cluster={ent.identity.cluster_id}, faction={ent.identity.faction}")
            if not ent.combat.alive: continue
            if not ent.identity.cluster_id: continue
            if ent.id in all_member_ids: continue
            eligible.append(ent)

        print(f"DEBUG: Eligible entities: {[e.id for e in eligible]}")
        # Cluster them by (faction, cluster_id)
        clusters = {}
        for ent in eligible:
            key = (ent.identity.faction, ent.identity.cluster_id)
            if key not in clusters: clusters[key] = []
            clusters[key].append(ent)

        # Create groups for clusters with 2+ members
        for (faction, cluster_id), members in clusters.items():
            if len(members) < 2: continue
            
            # Simple formation: just group them if they are "nearby" (within 15 tiles)
            # Leader selection: Highest level
            members.sort(key=lambda e: e.progression.level, reverse=True)
            leader = members[0]
            
            group_id = f"group_{cluster_id}_{uuid.uuid4().hex[:4]}"
            group = GroupRecord(
                group_id=group_id,
                leader_id=leader.id,
                kind=GroupKind.SOCIAL_CLIQUE,
                shared_goal=GoalType.EXPLORE, # Default
                member_ids={m.id for m in members},
                anchor_pos=leader.spatial.pos,
                cohesion_level=1.0
            )
            context.world.group_registry[group_id] = group
            
            # Update member components for inspection parity
            for m in members:
                m.identity.group_id = group_id
            
            if context.emit:
                context.emit("group", f"Group {group_id} formed with {len(members)} members led by {leader.id}", 
                             entity_ids=tuple(group.member_ids))
            logger.info(f"Formed group {group_id} for cluster {cluster_id} with leader {leader.id}")

    def _process_contract_formation(self, context: SystemContext) -> None:
        """Scan for active social contracts and instantiate GroupRecords for them."""
        # 1. Group active contract_ids across all entities
        active_contract_parties: dict[str, set[int]] = {}
        contract_info: dict[str, Any] = {}
        
        from src.core.models.strategy import StrategicStatus
        
        for ent in context.world.entities.values():
            if not ent.combat.alive: continue
            
            for ct in ent.mind.strategic.contracts:
                if ct.status == StrategicStatus.ACTIVE:
                    if ct.contract_id not in active_contract_parties:
                        active_contract_parties[ct.contract_id] = set()
                        contract_info[ct.contract_id] = ct
                    active_contract_parties[ct.contract_id].add(ent.id)
                    
        # 2. Reconcile with GroupRegistry
        for cid, member_ids in active_contract_parties.items():
            if len(member_ids) < 2: continue
            
            ct = contract_info[cid]
            group_id = ct.party_id
            
            # If contract has a group_id, check if it still exists
            existing_group = context.world.group_registry.get(group_id) if group_id else None
            
            if not existing_group:
                # Create NEW GroupRecord for this contract
                new_group_id = f"party_{cid}_{uuid.uuid4().hex[:4]}"
                
                # Map contract 'purpose' to group shared_goal
                shared_goal = GoalType.EXPLORE
                if ct.kind == ContractKind.EXPEDITION: shared_goal = GoalType.EXPLORE
                elif ct.kind == ContractKind.ESCORT: shared_goal = GoalType.WANDER 
                elif ct.kind == ContractKind.MERCENARY: shared_goal = GoalType.HUNT
                elif ct.kind == ContractKind.REVENGE_PACT: shared_goal = GoalType.HUNT
                
                group = GroupRecord(
                    group_id=new_group_id,
                    leader_id=ct.founder_id,
                    kind=GroupKind.PARTY,
                    shared_goal=shared_goal,
                    member_ids=member_ids,
                    anchor_pos=None, # Will be set in maintenance
                    cohesion_level=1.2
                )
                context.world.group_registry[new_group_id] = group
                
                # Authoritative update of member components
                for mid in member_ids:
                    m_ent = context.world.get_entity(mid)
                    if m_ent:
                        m_ent.identity.group_id = new_group_id
                        # Update the contract record inside strategic state
                        for m_ct in m_ent.mind.strategic.contracts:
                            if m_ct.contract_id == cid:
                                m_ct.party_id = new_group_id
                
                if context.emit:
                    context.emit("group", f"Contract party formed for {cid} with {len(member_ids)} members", 
                                 entity_ids=tuple(member_ids))
                logger.info(f"Formed contract party {new_group_id} for contract {cid}")
            else:
                # Refresh member IDs and ensure linkage
                existing_group.member_ids = member_ids
                for mid in member_ids:
                    m_ent = context.world.get_entity(mid)
                    if m_ent and m_ent.identity.group_id != existing_group.group_id:
                        m_ent.identity.group_id = existing_group.group_id

    def _process_maintenance(self, context: SystemContext) -> None:
        """Update group state: leader position, cohesion, and adding stray members."""
        to_remove = []
        for gid, group in list(context.world.group_registry.items()):
            leader = context.world.get_entity(group.leader_id) if group.leader_id else None
            
            if not leader or not leader.combat.alive:
                # Disband if leader is dead (simple approach for now)
                to_remove.append(gid)
                continue
            
            # Update anchor to leader pos
            group.anchor_pos = leader.spatial.pos
            
            # Filter dead members
            group.member_ids = {mid for mid in group.member_ids if (e := context.world.get_entity(mid)) and e.combat.alive}
            
            # Dissolve if members scattered too far or lonely
            if len(group.member_ids) < 2:
                to_remove.append(gid)
                continue

            total_dist = 0.0
            for mid in group.member_ids:
                if mid == group.leader_id: continue
                member = context.world.get_entity(mid)
                if member and member.combat.alive:
                    total_dist += member.spatial.pos.manhattan(leader.spatial.pos)
            
            avg_dist = total_dist / max(1, len(group.member_ids) - 1)
            group.cohesion_level = max(0.0, 2.0 - (avg_dist / 15.0)) 

        for gid in to_remove:
            group = context.world.group_registry.pop(gid)
            
            # Phase 4: Handle Contract Failure on group dissolution
            if group.kind == GroupKind.PARTY:
                # Find the associated contract (search all member strategic states)
                # Optimization: check the leader first
                leader = context.world.get_entity(group.leader_id)
                if leader:
                    for ct in leader.mind.strategic.contracts:
                        if ct.party_id == gid and ct.status == StrategicStatus.ACTIVE:
                            # Apply consequences
                            ContractOutcomeService.resolve_contract(context.world, ct, StrategicStatus.ABANDONED, emit=context.emit)
                            break

            for mid in group.member_ids:
                member = context.world.entities.get(mid)
                if member and member.identity.group_id == gid:
                    member.identity.group_id = None
            if context.emit:
                context.emit("group", f"Group {gid} dissolved.", entity_ids=tuple(group.member_ids))

    def _process_dissolution(self, context: SystemContext) -> None:
        """Cleanup groups with 0 or 1 members (handled in maintenance)."""
        pass
