# Compliance IDs: PERF-001, PERF-002, PERF-004, PERF-019
from __future__ import annotations

import logging
import weakref
from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional, Protocol, runtime_checkable

logger = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True)
class CacheMetrics:
    """Standardized telemetry reported by every runtime optimization cache."""
    name: str
    current_size: int
    hit_count: int
    miss_count: int
    eviction_count: int
    last_invalidation_tick: int

    def __getitem__(self, key: str) -> Any:
        """Support legacy dictionary indexing for backward compatibility with existing tests."""
        if key == "hits" or key == "hit_count":
            return self.hit_count
        elif key == "misses" or key == "miss_count":
            return self.miss_count
        elif key == "invalidations" or key == "eviction_count":
            return self.eviction_count
        elif key == "cached_entities" or key == "current_size":
            return self.current_size
        elif hasattr(self, key):
            return getattr(self, key)
        raise KeyError(f"Key {key} not found in CacheMetrics.")

    def get(self, key: str, default: Any = None) -> Any:
        try:
            return self[key]
        except KeyError:
            return default


@dataclass(frozen=True, slots=True)
class CacheBudgetPolicy:
    """
    Defines capacity caps and retention windows across all runtime optimization caches.
    Enforces deterministic eviction when boundaries are breached.
    """
    max_movement_plans: int = 10000
    max_read_dtos: int = 5000
    max_spatial_grid_versions: int = 10
    max_strategic_queues: int = 5000
    sweep_interval_ticks: int = 10


@runtime_checkable
class ICacheable(Protocol):
    """Protocol defining standardized cache observability and budget eviction lifecycle."""
    
    def get_metrics(self) -> CacheMetrics:
        """Report current cache telemetry and hit/miss/eviction ratios."""
        ...
        
    def evict_expired(self, current_tick: int, policy: CacheBudgetPolicy) -> int:
        """
        Enforce deterministic eviction if cache size exceeds policy budgets.
        Returns number of items evicted.
        """
        ...
        
    def clear(self) -> None:
        """Purge all cached entries."""
        ...


class CacheRegistry:
    """
    Central registry for all runtime optimization caches (indexes, movement plans, read models).
    Orchestrates tick-based monitoring and budget-enforced deterministic eviction.
    """
    
    def __init__(self):
        self._caches: Dict[str, weakref.ref[ICacheable]] = {}
        self._strong_caches: Dict[str, ICacheable] = {}

    def register_cache(self, name: str, cache: ICacheable, use_weakref: bool = True) -> None:
        """Register a cache instance for centralized tick sweeps and metric collation."""
        if not isinstance(cache, ICacheable):
            logger.warning(f"Cache {name} does not strictly implement ICacheable protocol.")
            
        if use_weakref:
            try:
                self._caches[name] = weakref.ref(cache)
                self._strong_caches.pop(name, None)
                logger.debug(f"Successfully registered weakref for cache: {name}")
                return
            except TypeError:
                pass
                
        self._strong_caches[name] = cache
        self._caches.pop(name, None)
        logger.debug(f"Successfully registered strong reference for cache: {name}")

    def deregister_cache(self, name: str) -> bool:
        """Remove a registered cache from tracking."""
        w_removed = self._caches.pop(name, None) is not None
        s_removed = self._strong_caches.pop(name, None) is not None
        return w_removed or s_removed

    def get_all_metrics(self) -> Dict[str, CacheMetrics]:
        """Collate standardized telemetry across all currently registered caches."""
        results: Dict[str, CacheMetrics] = {}
        
        dead_keys = []
        for name, w_ref in self._caches.items():
            cache = w_ref()
            if cache is not None:
                results[name] = cache.get_metrics()
            else:
                dead_keys.append(name)
                
        for k in dead_keys:
            del self._caches[k]
            
        for name, cache in self._strong_caches.items():
            results[name] = cache.get_metrics()
            
        return results

    def sweep_caches(self, current_tick: int, policy: CacheBudgetPolicy) -> Dict[str, int]:
        """
        Execute deterministic budget-enforced sweep across all registered caches.
        Returns dictionary mapping cache name to count of items evicted during this sweep.
        """
        evictions: Dict[str, int] = {}
        
        dead_keys = []
        for name, w_ref in self._caches.items():
            cache = w_ref()
            if cache is not None:
                pruned = cache.evict_expired(current_tick, policy)
                if pruned > 0:
                    evictions[name] = pruned
            else:
                dead_keys.append(name)
                
        for k in dead_keys:
            del self._caches[k]
            
        for name, cache in self._strong_caches.items():
            pruned = cache.evict_expired(current_tick, policy)
            if pruned > 0:
                evictions[name] = pruned
                
        if evictions:
            logger.debug(f"Cache sweep at tick {current_tick} pruned entries: {evictions}")
            
        return evictions

    def clear_all(self) -> None:
        """Forcefully purge all entries across all active registered caches."""
        for w_ref in self._caches.values():
            cache = w_ref()
            if cache is not None:
                cache.clear()
                
        for cache in self._strong_caches.values():
            cache.clear()
            
        logger.info("Purged all optimization caches in registry.")
