from __future__ import annotations
from typing import Dict, Any, List, Set, Optional
from src.core.state import GroupRecord, AuthoritativeState

class GroupService:
    """
    Authoritative service for multi-entity coordination (Parties/Groups).
    """

    @staticmethod
    def calculate_cohesion(group: GroupRecord, state: AuthoritativeState) -> float:
        """
        Returns a cohesion score (0.0 to 1.0) based on how many members are 
        within the cohesion_radius of the anchor.
        """
        if not group.member_ids:
            return 1.0
            
        inside_count = 0
        anchor_x, anchor_y = group.anchor
        
        for eid in group.member_ids:
            entity = state.entities.get(eid)
            if not entity:
                continue
                
            ex, ey = entity.navigation.position
            dist_sq = (ex - anchor_x)**2 + (ey - anchor_y)**2
            if dist_sq <= group.cohesion_radius**2:
                inside_count += 1
                
        return inside_count / len(group.member_ids)

    @staticmethod
    def assign_role(group: GroupRecord, entity_id: int, role: str) -> GroupRecord:
        """Helper to return a new GroupRecord with a role assigned."""
        from dataclasses import replace
        new_roles = dict(group.roles)
        new_roles[entity_id] = role
        return replace(group, roles=new_roles)
