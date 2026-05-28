# TDD tests for Phase 10 Cache Invalidation
import pytest
from src.domains.optimization.cache_strategy import CacheStrategy, CacheKey

def test_resource_cache_invalidates_on_node_depletion():
    cs = CacheStrategy(max_size=3)
    key = CacheKey(region_id="forest", query_type="resource_nodes")
    cs.put(key, ["ore_node_1", "ore_node_2"])
    assert cs.get(key) == ["ore_node_1", "ore_node_2"]
    
    # Send resource_depleted event
    cs.invalidate("resource_depleted", region_id="forest")
    assert cs.get(key) is None

def test_shop_cache_invalidates_on_stock_change():
    cs = CacheStrategy(max_size=3)
    key = CacheKey(region_id="town", query_type="shop_stock")
    cs.put(key, {"potions": 5})
    assert cs.get(key) == {"potions": 5}
    
    # stock change event
    cs.invalidate("shop_stock_changed", region_id="town")
    assert cs.get(key) is None

def test_service_cache_invalidates_on_service_unavailable():
    cs = CacheStrategy(max_size=3)
    key = CacheKey(region_id="town", query_type="services")
    cs.put(key, ["healer"])
    
    cs.invalidate("service_unavailable", region_id="town")
    assert cs.get(key) is None

def test_region_cache_invalidates_on_pressure_change():
    cs = CacheStrategy(max_size=3)
    key = CacheKey(region_id="swamp", query_type="pressure")
    cs.put(key, 0.8)
    
    cs.invalidate("region_pressure_changed", region_id="swamp")
    assert cs.get(key) is None

def test_provider_cache_key_includes_query_context():
    key1 = CacheKey(region_id="swamp", query_type="pressure", extra_param="level_1")
    key2 = CacheKey(region_id="swamp", query_type="pressure", extra_param="level_2")
    assert key1 != key2

def test_cache_size_is_bounded():
    cs = CacheStrategy(max_size=2)
    key1 = CacheKey(region_id="r1", query_type="q1")
    key2 = CacheKey(region_id="r2", query_type="q2")
    key3 = CacheKey(region_id="r3", query_type="q3")
    
    cs.put(key1, "v1")
    cs.put(key2, "v2")
    cs.put(key3, "v3") # Should evict the first inserted (LRU or FIFO)
    
    assert cs.get(key1) is None
    assert cs.get(key2) == "v2"
    assert cs.get(key3) == "v3"

def test_stale_cache_does_not_recommend_depleted_resource():
    cs = CacheStrategy(max_size=5)
    key = CacheKey(region_id="mine", query_type="active_resources")
    cs.put(key, ["iron_vein"])
    
    # Deplete the iron_vein
    cs.invalidate("resource_depleted", region_id="mine")
    assert cs.get(key) is None
