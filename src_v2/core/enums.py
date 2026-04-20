from enum import IntEnum, unique

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
    REGROUP = 7
