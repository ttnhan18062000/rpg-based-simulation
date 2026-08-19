# Compliance IDs: PERF-001, PERF-002, PERF-004, PERF-019
from __future__ import annotations

import gc
from dataclasses import replace
from typing import Dict, Any
import pytest

from src.engine.cache_registry import (
    CacheRegistry, 
    CacheBudgetPolicy, 
    CacheMetrics, 
    ICacheable
)
from src.engine.movement_cache import MovementPlanCache, MovementPlanKey, MovementPlan
from src.api.read_model_cache import ReadModelCache
from src.systems.world_systems.generator import EntityGenerator


class MockCache(ICacheable):
    def __init__(self, name: str, size: int):
        self._name = name
        self.size = size
        self.evictions = 0

    def get_metrics(self) -> CacheMetrics:
        return CacheMetrics(
            name=self._name,
            current_size=self.size,
            hit_count=10,
            miss_count=2,
            eviction_count=self.evictions,
            last_invalidation_tick=5
        )

    def evict_expired(self, current_tick: int, policy: CacheBudgetPolicy) -> int:
        if self.size > 10:
            pruned = self.size - 10
            self.size = 10
            self.evictions += pruned
            return pruned
        return 0

    def clear(self) -> None:
        self.evictions += self.size
        self.size = 0


def test_cache_registry_registration_and_metrics():
    registry = CacheRegistry()
    mock1 = MockCache("mock_alpha", 15)
    mock2 = MockCache("mock_beta", 5)
    
    registry.register_cache("mock_alpha", mock1)
    registry.register_cache("mock_beta", mock2)
    
    metrics = registry.get_all_metrics()
    assert len(metrics) == 2
    assert metrics["mock_alpha"].current_size == 15
    assert metrics["mock_beta"].current_size == 5
    assert metrics["mock_alpha"]["hits"] == 10  # Test legacy indexing


def test_cache_registry_weakref_cleanup():
    registry = CacheRegistry()
    mock = MockCache("ephemeral_mock", 20)
    registry.register_cache("ephemeral_mock", mock)
    
    assert "ephemeral_mock" in registry.get_all_metrics()
    
    # Delete strong reference
    del mock
    gc.collect()
    
    # Registry should automatically prune dead weakref
    assert "ephemeral_mock" not in registry.get_all_metrics()


def test_movement_plan_cache_budget_eviction():
    cache = MovementPlanCache()
    policy = CacheBudgetPolicy(max_movement_plans=5)
    
    # Put 10 plans
    for i in range(10):
        key = MovementPlanKey(entity_id=i, current_tile=(0, 0), target_tile=(1, 1), occupancy_version=0)
        plan = MovementPlan(next_step=(1.0, 1.0), valid_until_tick=100)
        cache.put(key, plan)
        
    assert len(cache._cache) == 10
    
    # Evict
    pruned = cache.evict_expired(50, policy)
    assert pruned == 5
    assert len(cache._cache) == 5
    assert cache.get_metrics().eviction_count == 5


def test_read_model_cache_budget_eviction():
    cache = ReadModelCache()
    policy = CacheBudgetPolicy(max_read_dtos=3)
    gen = EntityGenerator(seed=101)
    
    # Populate cache with 5 entities
    for i in range(5):
        e = gen.spawn_hero((float(i), float(i)))
        e = replace(e, id=i)
        cache.get_entity_dto(e)
        
    assert cache.get_metrics().current_size == 5
    
    pruned = cache.evict_expired(10, policy)
    assert pruned == 2
    assert cache.get_metrics().current_size == 3
    assert cache.get_metrics()["invalidations"] == 2


def test_cache_registry_sweep_execution():
    registry = CacheRegistry()
    m_cache = MovementPlanCache()
    r_cache = ReadModelCache()
    
    registry.register_cache("movement_plans", m_cache)
    registry.register_cache("read_models", r_cache)
    
    policy = CacheBudgetPolicy(max_movement_plans=2, max_read_dtos=2)
    gen = EntityGenerator(seed=202)
    
    for i in range(5):
        k = MovementPlanKey(entity_id=i, current_tile=(0, 0), target_tile=(1, 1), occupancy_version=0)
        p = MovementPlan(next_step=(1.0, 1.0), valid_until_tick=100)
        m_cache.put(k, p)
        
        e = gen.spawn_hero((float(i), float(i)))
        e = replace(e, id=i)
        r_cache.get_entity_dto(e)
        
    assert m_cache.get_metrics().current_size == 5
    assert r_cache.get_metrics().current_size == 5
    
    evictions = registry.sweep_caches(current_tick=10, policy=policy)
    assert evictions["movement_plans"] == 3
    assert evictions["read_models"] == 3
    
    assert m_cache.get_metrics().current_size == 2
    assert r_cache.get_metrics().current_size == 2
