from __future__ import annotations
from typing import Optional
import math
from src_legacy.core.state import AuthoritativeState, EntityState
from src_legacy.core.updates import StateUpdate, BuildingUpdate

class SabotageAction:
    """Action to damage or sabotage town buildings."""

    @staticmethod
    def apply(entity: EntityState, building_id: int, state: AuthoritativeState) -> Optional[StateUpdate]:
        """
        Reduce building HP based on entity ATK.
        Requires proximity (distance < 5.0).
        """
        # 1. Validation: Building exists and is functional
        if building_id not in state.buildings:
            return None
        
        building = state.buildings[building_id]
        if not building.functional:
            return None
            
        # 2. Proximity check
        ex, ey = entity.position
        bx, by = building.position
        dist = math.sqrt((ex - bx)**2 + (ey - by)**2)
        if dist > 5.0:
            return None
            
        # 3. Calculate Damage (based on entity ATK)
        damage = entity.combat.atk
        
        # 4. Emit BuildingUpdate
        return StateUpdate(
            building_updates={
                building_id: BuildingUpdate(
                    building_id=building_id,
                    hp_delta=-damage
                )
            }
        )
