# Compliance IDs: PERF-001, PERF-002, PERF-004, PERF-019
from __future__ import annotations

import pytest

from src.config.profiles import RuntimeProfile, HardwareClass
from src.core.state import AuthoritativeState
from src.platform.rng import DeterministicRNG
from src.engine.kernel import Kernel
from src.systems.world_systems.generator import EntityGenerator
from src.engine.movement_cache import MovementPlanCache, MovementPlanKey, MovementPlan
from src.engine.cache_registry import CacheBudgetPolicy


@pytest.fixture
def test_profile() -> RuntimeProfile:
    return RuntimeProfile(
        name="cache_bounds_test",
        hardware_class=HardwareClass.CLASS_A,
        max_ram_mb=256,
        max_cpu_percent=80.0,
        max_worker_count=0,
        max_queue_depth=100,
        max_replay_buffer_kb=1024,
        max_observability_budget_percent=10.0,
        max_tick_budget_ms=50.0
    )


@pytest.fixture
def metropolis_state() -> AuthoritativeState:
    gen = EntityGenerator(seed=101)
    entities = {}
    for i in range(50):
        e = gen.spawn_hero((float(i % 10), float(i // 10)))
        from dataclasses import replace
        e = replace(e, id=i)
        entities[i] = e
    return AuthoritativeState(tick=1, seed=101, entities=entities, movement_cache=MovementPlanCache())


@pytest.mark.slow
def test_kernel_integrated_cache_sweep(test_profile: RuntimeProfile, metropolis_state: AuthoritativeState):
    """
    Verify that Kernel automatically sweeps registered caches when tick intervals hit policy budgets,
    enforcing capacity caps and recording eviction metrics.
    """
    kernel = Kernel(test_profile, metropolis_state, DeterministicRNG(101), flags={"no_replay": True, "no_frame_pacing": True})
    try:
        # Configure strict budget policy
        strict_policy = CacheBudgetPolicy(max_movement_plans=10, max_read_dtos=10, sweep_interval_ticks=5)
        kernel._cache_policy = strict_policy

        m_cache = kernel.state.movement_cache
        assert m_cache is not None

        # 1. Populate movement cache with 30 plans
        for i in range(30):
            k = MovementPlanKey(entity_id=i, current_tile=(0, 0), target_tile=(1, 1), occupancy_version=m_cache.occupancy_version)
            p = MovementPlan(next_step=(1.0, 1.0), valid_until_tick=1000)
            m_cache.put(k, p)

        assert len(m_cache._cache) == 30

        # 2. Run simulation ticks up to sweep interval (tick 5)
        for _ in range(5):
            kernel.tick_once()

        # 3. Assert sweep occurred and pruned excess entries down to max_movement_plans (10)
        assert len(m_cache._cache) <= 10
        assert kernel._metrics.get("movement_plan_cache_pruned", 0) >= 20
        assert m_cache.get_metrics().eviction_count >= 20
    finally:
        kernel.shutdown()
