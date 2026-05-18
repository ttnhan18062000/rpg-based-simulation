# Compliance IDs: API-001, API-009, API-018, API-019, PERF-005, PERF-006, PERF-015, PERF-019
from __future__ import annotations
import logging
import threading
from typing import Dict, Any, Optional, Set, List, Tuple, TYPE_CHECKING

from src.engine.cache_registry import ICacheable, CacheMetrics, CacheBudgetPolicy

if TYPE_CHECKING:
    from src.core.state import AuthoritativeState, EntityState
    from src.core.dirty import DirtySet

logger = logging.getLogger(__name__)

class ReadModelInvalidationPolicy:
    """
    Determines which cached API projection DTOs must be invalidated based on the tick's DirtySet.
    M12 Law: Invalidation must be conservative and driven by DirtySet domain tracking.
    """
    @staticmethod
    def get_dirty_entity_ids(dirty_set: Optional[DirtySet], all_entity_ids: Set[int], force_full_scan: bool = False) -> Set[int]:
        """
        Returns the set of entity IDs that were modified across any simulation domain.
        If no DirtySet is provided or force_full_scan is True, invalidates all entities.
        """
        if force_full_scan or dirty_set is None:
            return set(all_entity_ids)
        return set(dirty_set.all_dirty_entities)


class ReadModelCache(ICacheable):
    """
    Authoritative read model cache for API/UI projections.
    Eliminates expensive O(N) full-state DTO recalculations by reusing clean entity dictionaries.
    Implements ICacheable protocol for centralized budget enforcement and deterministic eviction.
    """
    def __init__(self):
        self._minimal_summary: Dict[str, Any] = {}
        self._entity_dtos: Dict[int, Dict[str, Any]] = {}
        self._lock = threading.RLock()
        
        # Observability metrics
        self._hits: int = 0
        self._misses: int = 0
        self._invalidations: int = 0
        self._last_invalidation_tick: int = 0

    def get_metrics(self) -> CacheMetrics:
        """Returns standardized cache observability telemetry."""
        with self._lock:
            return CacheMetrics(
                name="read_model_cache",
                current_size=len(self._entity_dtos),
                hit_count=self._hits,
                miss_count=self._misses,
                eviction_count=self._invalidations,
                last_invalidation_tick=self._last_invalidation_tick
            )

    def evict_expired(self, current_tick: int, policy: CacheBudgetPolicy) -> int:
        """
        Enforce deterministic capacity boundaries.
        Prunes excess DTOs if size exceeds policy.max_read_dtos.
        """
        with self._lock:
            initial_size = len(self._entity_dtos)
            excess = initial_size - policy.max_read_dtos
            if excess > 0:
                # FIFO eviction by popping oldest keys
                sorted_keys = sorted(self._entity_dtos.keys())
                for k in sorted_keys[:excess]:
                    self._entity_dtos.pop(k, None)
                    self._invalidations += 1
                return excess
            return 0

    def clear(self) -> None:
        """Purge all cached entries."""
        with self._lock:
            pruned = len(self._entity_dtos)
            self._minimal_summary.clear()
            self._entity_dtos.clear()
            if pruned > 0:
                self._invalidations += pruned
            self.reset_metrics()

    def update(self, state: AuthoritativeState, dirty_set: Optional[DirtySet] = None, force_full_scan: bool = False) -> Set[int]:
        """
        Updates minimal snapshot and invalidates dirty entity DTOs.
        Returns the set of invalidated entity IDs.
        """
        from src.api.presenters.state_presenter import StatePresenter
        
        with self._lock:
            self._last_invalidation_tick = state.tick
            # Law: Minimal summary is updated every tick (O(1)).
            self._minimal_summary = StatePresenter.present_minimal(state)
            
            all_ids = set(state.entities.keys())
            dirty_ids = ReadModelInvalidationPolicy.get_dirty_entity_ids(dirty_set, all_ids, force_full_scan)
            
            # Prune deleted entities
            cached_ids = set(self._entity_dtos.keys())
            deleted_ids = cached_ids - all_ids
            for eid in deleted_ids:
                self._entity_dtos.pop(eid, None)
                
            # Invalidate dirty entities
            invalidated = set()
            for eid in dirty_ids:
                if eid in self._entity_dtos:
                    self._entity_dtos.pop(eid, None)
                    invalidated.add(eid)
                    
            self._invalidations += len(invalidated) + len(deleted_ids)
            return invalidated

    def get_minimal_summary(self, state: Optional[AuthoritativeState] = None) -> Dict[str, Any]:
        """Returns the cached minimal world summary."""
        from src.api.presenters.state_presenter import StatePresenter
        with self._lock:
            if not self._minimal_summary and state is not None:
                self._minimal_summary = StatePresenter.present_minimal(state)
            return dict(self._minimal_summary)

    def get_entity_dto(self, entity: EntityState) -> Dict[str, Any]:
        """
        Retrieves a cached entity DTO or generates and caches it on demand.
        """
        from src.api.presenters.state_presenter import StatePresenter
        with self._lock:
            if entity.id in self._entity_dtos:
                self._hits += 1
                return self._entity_dtos[entity.id]
                
            self._misses += 1
            dto = StatePresenter.present_entity(entity)
            self._entity_dtos[entity.id] = dto
            return dto

    def get_entities_paged(self, state: AuthoritativeState, offset: int = 0, limit: int = 100) -> Dict[str, Any]:
        """
        Retrieves a paged list of entity DTOs utilizing the cache.
        """
        with self._lock:
            all_ids = sorted(state.entities.keys())
            paged_ids = all_ids[offset : offset + limit]
            
            entities = [
                self.get_entity_dto(state.entities[eid])
                for eid in paged_ids
            ]
            
            return {
                "entities": entities,
                "total": len(all_ids),
                "offset": offset,
                "limit": limit
            }

    def reset_metrics(self):
        with self._lock:
            self._hits = 0
            self._misses = 0
            self._invalidations = 0
