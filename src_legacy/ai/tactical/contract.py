from __future__ import annotations
from enum import IntEnum
from pydantic import BaseModel, Field
from typing import Optional, Union
from src_legacy.core.models.enums import TacticalRole
from src_legacy.core.models.reason_codes import ActionReason

class TacticalMode(IntEnum):
    """Spatial engagement strategies."""
    CLOSE = 0     # Move to minimum range (Melee default)
    MAINTAIN = 1  # Stay within weapon range, maximize distance (Ranged default)
    WIDEN = 2     # Move away to increase distance (Kiting)
    HOLD = 3      # Stay in current position (Defensive/Waiting)
    RETREAT = 4   # Deliberate withdrawal to safety
    COVER = 5     # Seek adjacent walls against ranged threats [Milestone 4]
    CHOKEPOINT = 6 # Hold a 1-tile gap bottleneck [Milestone 4]

class TacticalEvaluation(BaseModel):
    """Structured output of a tactical evaluation cycle."""
    target_id: Optional[int] = None
    mode: TacticalMode = TacticalMode.CLOSE
    role: TacticalRole = TacticalRole.MELEE_STRIKER
    is_safe_shot: bool = False
    preferred_dist: int = 1
    reason: ActionReason = Field(default_factory=lambda: ActionReason(code=ReasonCode.ADVANCING)) # [Milestone 7] Strictly typed
    
    # Coordinates for specific tactical positioning (e.g., chokepoint)
    target_pos: Optional[tuple[int, int]] = None
