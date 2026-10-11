"""The range rule (designer; owner decision D57): a subject bound to a home range pursues only ways to meet a need that lie inside that range.

A creature with a leash is returned home every tick once it strays past the leash radius (``LEASH_RETURN``), so a way outside its range can
never be reached. A subject with no leash (``leash_radius`` 0) has no range, and every way is in range. The one rule lives in
``LeashService.way_in_range`` (src/engine/rpg_depth.py); this module is the import point the sleep goal uses, so the hunger ways, the sleep
ways and the opening steps all share a single definition.
"""
from __future__ import annotations

from typing import Any, Optional, Tuple

from src.engine.rpg_depth import LeashService


def way_in_range(entity: Any, position: Optional[Tuple[float, float]]) -> bool:
    """True when ``position`` is inside the entity's home range (Manhattan from its home within the leash radius), or the entity has no range."""
    return LeashService.way_in_range(entity, position)
