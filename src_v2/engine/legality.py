# src_v2/engine/legality.py
from __future__ import annotations
from typing import TYPE_CHECKING, Tuple, Optional, Any

if TYPE_CHECKING:
    from src_v2.core.state import AuthoritativeState, EntityState

class LegalityServiceV2:
    """ Authoritative simulation laws for V2. """

    @staticmethod
    def get_manhattan_dist(a: Tuple[float, float], b: Tuple[float, float]) -> int:
        return int(abs(a[0] - b[0]) + abs(a[1] - b[1]))

    @staticmethod
    def is_adjacent(a: Tuple[float, float], b: Tuple[float, float]) -> bool:
        return LegalityServiceV2.get_manhattan_dist(a, b) == 1

    @staticmethod
    def verify_occupancy(
        pos: Tuple[float, float], 
        state_or_context: Any, 
        ignore_entity_id: Optional[int] = None
    ) -> Tuple[bool, str]:
        """
        V2 Authoritative Occupancy Rule:
        Works for both AuthoritativeState and WorkerPacket.
        """
        target_grid_pos = (int(pos[0]), int(pos[1]))
        
        # 1. Static Terrain
        blocked = getattr(state_or_context, 'blocked_tiles', [])
        if target_grid_pos in blocked:
            return False, "PATH_NOT_FOUND"

        # 2. Dynamic Claims (Position claimed this tick)
        claims = getattr(state_or_context, 'transient_claims', [])
        if target_grid_pos in claims:
            return False, "OCCUPANCY_VIOLATION"

        # 2. Dynamic Entities
        # Handles Dict[int, EntityState] (State) or List[Tuple[int, EntityState]] (Packet)
        entities = getattr(state_or_context, 'entities', None)
        if entities is None:
            # Try neighbor_view (WorkerPacket)
            entities_list = getattr(state_or_context, 'neighbor_view', [])
            for eid, entity in entities_list:
                if eid == ignore_entity_id: continue
                if not entity.active: continue
                if (int(entity.position[0]), int(entity.position[1])) == target_grid_pos:
                    return False, "OCCUPANCY_VIOLATION"
        else:
            # Handle Dictionary (AuthoritativeState)
            for eid, entity in entities.items():
                if eid == ignore_entity_id: continue
                if not entity.active: continue
                if (int(entity.position[0]), int(entity.position[1])) == target_grid_pos:
                    return False, "OCCUPANCY_VIOLATION"

        return True, "ADVANCING"

    @staticmethod
    def get_engaged_hostiles(
        actor: EntityState,
        state_or_context: Any
    ) -> list[int]:
        """
        Returns a list of hostile entity IDs adjacent to the actor.
        AOA Stabilization: Engagement is bit-identical to adjacency in V2.
        """
        engaged = []
        entities = getattr(state_or_context, 'entities', None)
        if entities is None:
            # Try neighbor_view (WorkerPacket)
            entities_list = getattr(state_or_context, 'neighbor_view', [])
            for eid, entity in entities_list:
                if eid == actor.id: continue
                if not entity.active: continue
                if entity.identity.faction != actor.identity.faction:
                    if LegalityServiceV2.is_adjacent(actor.position, entity.position):
                        engaged.append(eid)
        else:
            # Handle Dictionary (AuthoritativeState)
            for eid, entity in entities.items():
                if eid == actor.id: continue
                if not entity.active: continue
                if entity.identity.faction != actor.identity.faction:
                    if LegalityServiceV2.is_adjacent(actor.position, entity.position):
                        engaged.append(eid)
        return engaged
