from __future__ import annotations
import logging
import uuid
from typing import TYPE_CHECKING
from src.systems.infrastructure.base import System
from src.core.models.lived_structure import GroupRecord
from src.core.models.enums import GroupKind, GoalType

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
            for mid in group.member_ids:
                member = context.world.entities.get(mid)
                if member and member.identity.group_id == gid:
                    member.identity.group_id = None
            if context.emit:
                context.emit("group", f"Group {gid} dissolved.", entity_ids=tuple(group.member_ids))

    def _process_dissolution(self, context: SystemContext) -> None:
        """Cleanup groups with 0 or 1 members (handled in maintenance)."""
        pass
