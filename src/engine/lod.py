from typing import List, Tuple, Dict
from src.core.state import EntityState, AuthoritativeState

class LODService:
    """
    Service for determining Level of Detail (LOD) for entities.
    LOD 0: Full frequency (1/1)
    LOD 1: High frequency (1/2)
    LOD 2: Medium frequency (1/5)
    LOD 3: Low frequency (1/10)
    """
    
    # CADENCE[lod] -> ticks between updates
    CADENCE = {
        0: 1,
        1: 2,
        2: 5,
        3: 10
    }

    @staticmethod
    def determine_lod(entity: EntityState, focus_points: List[Tuple[float, float]]) -> int:
        """
        Calculates the LOD level for an entity based on its distance to focus points.
        Entities in combat or with active tasks are always LOD 0.
        """
        # Active tasks force LOD 0 (full frequency)
        if entity.task.payload:
            return 0
            
        # Optional: Add wounded check if we want entities in combat to be LOD 0
        # if entity.combat.hp < entity.combat.max_hp: return 0

        if not focus_points:
            return 0

        pos = entity.navigation.position
        # Use square distance for performance optimization
        min_sq_dist = float('inf')
        for fx, fy in focus_points:
            sq_dist = (pos[0] - fx)**2 + (pos[1] - fy)**2
            if sq_dist < min_sq_dist:
                min_sq_dist = sq_dist

        # LOD Thresholds (Squared distances)
        # 0: < 25 units (625)
        # 1: < 60 units (3600)
        # 2: < 120 units (14400)
        # 3: >= 120 units
        
        if min_sq_dist < 625:
            return 0
        if min_sq_dist < 3600:
            return 1
        if min_sq_dist < 14400:
            return 2
        return 3

    @staticmethod
    def should_execute(tick: int, entity: EntityState, focus_points: List[Tuple[float, float]]) -> bool:
        """
        Determines if the entity should execute its behavior this tick based on its LOD.
        """
        lod = LODService.determine_lod(entity, focus_points)
        cadence = LODService.CADENCE[lod]
        
        if cadence <= 1:
            return True
            
        # Staggered execution based on entity_id to prevent spikes
        return (tick + entity.id) % cadence == 0
