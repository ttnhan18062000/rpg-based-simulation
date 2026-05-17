# Compliance IDs: COMB-011, PERF-009
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, Tuple, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from src.core.dirty import DirtySet


@dataclass(frozen=True, slots=True)
class MovementPlanKey:
    entity_id: int
    current_tile: Tuple[int, int]
    target_tile: Tuple[int, int]
    occupancy_version: int


@dataclass(frozen=True, slots=True)
class MovementPlan:
    next_step: Tuple[float, float]
    valid_until_tick: int


class MovementPlanCache:
    """
    Authoritative cache for next-step movement decisions in V2.
    Eliminates redundant routing and pathfinding calculations when spatial and occupancy conditions remain unchanged.
    """
    def __init__(self) -> None:
        self._cache: Dict[MovementPlanKey, MovementPlan] = {}
        self._occupancy_version: int = 0

    @property
    def occupancy_version(self) -> int:
        return self._occupancy_version

    def get(self, key: MovementPlanKey, current_tick: int = 0) -> Optional[MovementPlan]:
        plan = self._cache.get(key)
        if plan is not None:
            if plan.valid_until_tick >= current_tick and key.occupancy_version == self._occupancy_version:
                return plan
            # Expired or version mismatch: evict
            self._cache.pop(key, None)
        return None

    def put(self, key: MovementPlanKey, plan: MovementPlan) -> None:
        if key.occupancy_version == self._occupancy_version:
            self._cache[key] = plan

    def invalidate_for_dirty(self, dirty: Optional[DirtySet]) -> None:
        """Invalidate cached plans based on dirty entity modifications."""
        if dirty is None:
            self._cache.clear()
            self._occupancy_version += 1
            return

        # If any entity moved or changed lifecycle state, global occupancy is affected
        if dirty.movement_entities or dirty.lifecycle_entities:
            self._occupancy_version += 1

        # Evict any specific plans for entities that moved or changed lifecycle
        invalidated_eids = dirty.movement_entities | dirty.lifecycle_entities
        if invalidated_eids:
            keys_to_remove = [k for k in self._cache.keys() if k.entity_id in invalidated_eids]
            for k in keys_to_remove:
                self._cache.pop(k, None)
