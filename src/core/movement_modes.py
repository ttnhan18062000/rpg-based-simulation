from enum import Enum

class MovementMode(str, Enum):
    """
    Semantic intention for movement behavior.
    VERIFIED v2: movement_intent_modes
    """
    PURSUE = "PURSUE"         # Aggressive closing of distance
    RETREAT = "RETREAT"       # Priority movement away from threats
    HOLD = "HOLD"             # Staying in place, refusing to yield
    REPOSITION = "REPOSITION" # Tactical shifting (e.g. to cover or flank)
    INTERCEPT = "INTERCEPT"   # Moving to cut off a target's path
    GUARD = "GUARD"           # Staying near a target/location
    REGROUP = "REGROUP"       # Moving toward allies
    WANDER = "WANDER"         # Low-priority exploration
