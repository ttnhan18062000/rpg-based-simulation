from enum import Enum, IntEnum, unique

@unique
class EntityRole(IntEnum):
    HERO = 0
    SHOPKEEPER = 1
    MONSTER = 2
    CITIZEN = 3

@unique
class Faction(IntEnum):
    HERO_GUILD = 0
    MONSTER_HORDE = 1
    TOWN_COUNCIL = 2
    NEUTRAL = 3

@unique
class Direction(IntEnum):
    """Cardinal directions for grid movement."""
    NORTH = 0
    EAST = 1
    SOUTH = 2
    WEST = 3

@unique
class MovementIntention(IntEnum):
    """Explicit purpose of the current movement."""
    NONE = 0
    PURSUIT = 1
    RETREAT = 2
    HOLD = 3
    REPOSITION = 4
    INTERCEPT = 5
    GUARD = 6
@unique
class ActionType(IntEnum):
    """Authoritative action categories."""
    REST = 0
    MOVE = 1
    INTERACT = 2
    ATTACK = 3

@unique
class ActionStyle(IntEnum):
    """Tactical bias for action selection."""
    BALANCED = 0
    AGGRESSIVE = 1
    EVASIVE = 2

class ReasonCode(Enum):
    """Stable identifiers for simulation decision drivers."""
    # Movement
    ADVANCING = "advancing"
    OCCUPANCY_VIOLATION = "occupancy_violation"
    PATH_NOT_FOUND = "path_not_found"
    YIELDING = "yielding"
    SIDESTEPPING = "sidestepping"
    WAITING = "waiting"
    CONGESTION = "congestion"
    PATH_EXHAUSTED = "path_exhausted"
    TARGET_REACHED = "target_reached"
    
    # Combat/Interaction
    OUT_OF_RANGE = "out_of_range"
    TARGET_INVALID = "target_invalid"
    ACTION_EXHAUSTION = "exhaustion"
    INTERACTION_REJECTED = "interaction_rejected"
    ENGAGED = "engaged"
    
    # Tactical AI
    NO_TARGET = "no_target"
    LOW_HP_RETREAT = "low_hp_retreat"
    KITING = "kiting"
    MAINTAIN_DISTANCE = "maintain_distance"
    ALLY_SPACING = "ally_spacing"
    CLOSING_RANGE = "closing_range"
    
    # Routine / Biological
    HUNGER = "hunger"
    SLEEPY = "sleepy"
    FORCED_REST = "forced_rest"
    
    # Legacy/Fallback
    UNKNOWN = "unknown"

@unique
class Domain(IntEnum):
    """Scoping for deterministic RNG."""
    DEFAULT = 0
    SPAWN = 1
    WORLD = 2
    CALAMITY = 3
    SOCIAL = 4
    STRATEGIC = 5
    TACTICAL = 6
    ECONOMY = 7
    QUEST = 8
