"""The range rule (designer): a subject bound to a home range pursues only ways to meet a need that lie inside that range.

A creature with a leash is returned home every tick once it strays past the leash radius (``LEASH_RETURN``), so a way outside its range can
never be reached. A subject with no leash (``leash_radius`` 0) has no range, and every way is in range. Placeholder name and behaviour shared
with the lane that adds the same helper for the hunger ways; whichever lands second converges on one copy.
"""
from __future__ import annotations

from typing import Any, Tuple


def way_in_range(entity: Any, position: Tuple[float, float]) -> bool:
    """True when ``position`` is inside the entity's home range (Manhattan from its home within the leash radius), or the entity has no range."""
    nav = entity.navigation
    if not nav.leash_radius or nav.leash_radius <= 0 or nav.home_position is None:
        return True
    home = nav.home_position
    return abs(int(home[0]) - int(position[0])) + abs(int(home[1]) - int(position[1])) <= nav.leash_radius
