"""CombatInteractionService — Centralized authority for combat time model and interaction logic.

Milestone 2 implementation:
- Engagement mechanics (AOE and stickiness).
- Disengagement consequences (Opportunity Attacks).
- Anti-stalemate loop breaking.
"""

from __future__ import annotations
import logging
from typing import TYPE_CHECKING

from src.core.models.enums import ActionType
from src.core.models.vectors import Vector2

if TYPE_CHECKING:
    from src.core.models.world_state import WorldState
    from src.core.entities.entity import Entity
    from src.core.models.snapshot import Snapshot

logger = logging.getLogger(__name__)

class CombatInteractionService:
    """Authoritative service for evaluating combat situational context."""

    STALEMATE_THRESHOLD = 3  # Ticks of rhythmic oscillation before breaking
    STICKINESS_UTILITY_BONUS = 0.3 # Bias to stay on current engagement target

    @staticmethod
    def is_engaged(entity: Entity, world: WorldState | Snapshot) -> bool:
        """Returns True if the entity is orthogonally adjacent to any hostile."""
        from src.core.logic.legality_service import LegalityService
        
        pos = entity.spatial.pos
        faction = entity.identity.faction
        
        # Use spatial index to find neighbors (Manhattan dist 1)
        for oid in world.spatial_index.query_radius(pos, 1):
            if oid == entity.id:
                continue
            other = world.entities.get(oid)
            if not other or not other.combat.alive or other.kind == "generator":
                continue
            
            # Check orthogonal adjacency and hostility
            if LegalityService.is_adjacent(pos, other.spatial.pos):
                # Hostility check (Snapshots use faction_reg or just string comparison)
                is_hostile = False
                if hasattr(world, "faction_reg") and world.faction_reg:
                    is_hostile = world.faction_reg.is_hostile(faction, other.identity.faction)
                else:
                    is_hostile = faction != other.identity.faction
                
                if is_hostile:
                    return True
        return False

    @staticmethod
    def evaluate_disengagement(entity: Entity, target_pos: Vector2, world: WorldState | Snapshot) -> list[int]:
        """Returns a list of hostile entity IDs that can trigger an Opportunity Attack.
        
        Triggered when an entity moves from an engaged tile to a non-adjacent tile 
        OR moves away from a specific hostile.
        """
        from src.core.logic.legality_service import LegalityService
        
        old_pos = entity.spatial.pos
        # If not actually moving or moving to an adjacent tile (standard move), check if disengaging
        # In this simulation, ANY movement from an engaged tile triggers OA from all adjacent hostiles.
        
        attackers: list[int] = []
        faction = entity.identity.faction
        
        for oid in world.spatial_index.query_radius(old_pos, 1):
            if oid == entity.id:
                continue
            other = world.entities.get(oid)
            if not other or not other.combat.alive:
                continue
            
            adj = LegalityService.is_adjacent(old_pos, other.spatial.pos)
            if adj:
                is_hostile = False
                if hasattr(world, "faction_reg") and world.faction_reg:
                    is_hostile = world.faction_reg.is_hostile(faction, other.identity.faction)
                else:
                    is_hostile = faction != other.identity.faction
                
                if is_hostile:
                    # If moving to a position NOT adjacent to this specific hostile, trigger OA
                    still_adj = LegalityService.is_adjacent(target_pos, other.spatial.pos)
                    if not still_adj:
                        attackers.append(oid)
                        
        return attackers

    @classmethod
    def get_stickiness_bonus(cls, attacker: Entity, current_target_id: int | None) -> float:
        """Returns a utility bonus if the current target is the same as the previous turn's target."""
        if current_target_id is not None and attacker.mind.navigation.engagement_target_id == current_target_id:
            return cls.STICKINESS_UTILITY_BONUS
        return 0.0

    @classmethod
    def detect_stalemate(cls, entity: Entity, world: WorldState | Snapshot) -> bool:
        """Heuristic for detecting step-forward/step-back loops.
        
        Implementation: Checks pos_history for rhythmic oscillation.
        Example: [A, B, A, B] -> Stalemate.
        """
        history = entity.mind.navigation.pos_history
        if len(history) < 4:
            return False
            
        # Check for A-B-A-B pattern
        # history[-1] is current (about to be moved), history[-2] is last, etc.
        # But ActionSystem appends TO history. Let's assume history[-1] is where we just came from.
        if history[-1] == history[-3] and history[-2] == history[-4] and history[-1] != history[-2]:
            return True
        return False
