# Compliance IDs: COMB-011, PERF-009, PERF-019
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, Tuple, Optional, TYPE_CHECKING

from src.engine.cache_registry import ICacheable, CacheMetrics, CacheBudgetPolicy

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
    last_accessed_tick: int = 0


class MovementPlanCache(ICacheable):
    """
    Authoritative cache for next-step movement decisions in V2.
    Eliminates redundant routing and pathfinding calculations when spatial and occupancy conditions remain unchanged.
    Implements ICacheable protocol for centralized budget enforcement and deterministic eviction.
    """
    def __init__(self) -> None:
        self._cache: Dict[MovementPlanKey, MovementPlan] = {}
        self._occupancy_version: int = 0
        self.hits: int = 0
        self.misses: int = 0
        self._eviction_count: int = 0
        self._last_invalidation_tick: int = 0

    @property
    def occupancy_version(self) -> int:
        return self._occupancy_version

    def get_metrics(self) -> CacheMetrics:
        """Report standardized cache telemetry."""
        return CacheMetrics(
            name="movement_plan_cache",
            current_size=len(self._cache),
            hit_count=self.hits,
            miss_count=self.misses,
            eviction_count=self._eviction_count,
            last_invalidation_tick=self._last_invalidation_tick
        )

    def evict_expired(self, current_tick: int, policy: CacheBudgetPolicy) -> int:
        """
        Enforce deterministic budget bounds.
        1. Prune expired entries.
        2. If still over budget, FIFO/LRU evict oldest entries.
        """
        initial_size = len(self._cache)
        
        # 1. Prune expired entries
        expired_keys = [
            k for k, plan in self._cache.items() 
            if plan.valid_until_tick < current_tick or k.occupancy_version != self._occupancy_version
        ]
        for k in expired_keys:
            self._cache.pop(k, None)
            
        # 2. Prune excess entries exceeding max budget
        excess = len(self._cache) - policy.max_movement_plans
        if excess > 0:
            # Sort by valid_until_tick ascending (earliest expiration first)
            sorted_keys = sorted(self._cache.keys(), key=lambda x: self._cache[x].valid_until_tick)
            for k in sorted_keys[:excess]:
                self._cache.pop(k, None)
                
        pruned = initial_size - len(self._cache)
        if pruned > 0:
            self._eviction_count += pruned
            
        return pruned

    def clear(self) -> None:
        """Purge all cached entries."""
        pruned = len(self._cache)
        self._cache.clear()
        if pruned > 0:
            self._eviction_count += pruned

    def get(self, key: MovementPlanKey, current_tick: int = 0) -> Optional[MovementPlan]:
        plan = self._cache.get(key)
        if plan is not None:
            if plan.valid_until_tick >= current_tick and key.occupancy_version == self._occupancy_version:
                self.hits += 1
                # Update last accessed tick if needed
                return plan
            # Expired or version mismatch: evict
            self._cache.pop(key, None)
            self._eviction_count += 1
        self.misses += 1
        return None

    def put(self, key: MovementPlanKey, plan: MovementPlan) -> None:
        if key.occupancy_version == self._occupancy_version:
            self._cache[key] = plan

    def invalidate_for_dirty(self, dirty: Optional[DirtySet], current_tick: int = 0) -> None:
        """Invalidate cached plans based on dirty entity modifications."""
        self._last_invalidation_tick = current_tick
        
        if dirty is None:
            pruned = len(self._cache)
            self._cache.clear()
            if pruned > 0:
                self._eviction_count += pruned
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
                self._eviction_count += 1
