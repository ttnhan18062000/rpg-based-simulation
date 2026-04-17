from __future__ import annotations
from enum import IntEnum
from pydantic import BaseModel, Field
from typing import Optional, Union
from src.core.models.reason_codes import ActionReason

class TacticalMode(IntEnum):
    """Spatial engagement strategies."""
    CLOSE = 0     # Move to minimum range (Melee default)
    MAINTAIN = 1  # Stay within weapon range, maximize distance (Ranged default)
    WIDEN = 2     # Move away to increase distance (Kiting)
    HOLD = 3      # Stay in current position (Defensive/Waiting)
    RETREAT = 4   # Deliberate withdrawal to safety

class TacticalRole(IntEnum):
    """Inherent or assigned combat roles."""
    MELEE_STRIKER = 0
    RANGED_SKIRMISHER = 1
    SUPPORT_HEALER = 2
    AOE_PRESSURE = 3
    RETREAT_BIASED = 4

class TacticalEvaluation(BaseModel):
    """Structured output of a tactical evaluation cycle."""
    target_id: Optional[int] = None
    mode: TacticalMode = TacticalMode.CLOSE
    role: TacticalRole = TacticalRole.MELEE_STRIKER
    is_safe_shot: bool = False
    preferred_dist: int = 1
    reason: Union[ActionReason, str] = "default"
    
    # Coordinates for specific tactical positioning (e.g., chokepoint)
    target_pos: Optional[tuple[int, int]] = None
