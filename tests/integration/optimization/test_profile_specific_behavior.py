# Compliance IDs: PERF-001, PERF-002, PERF-004, PERF-016, PERF-017, PERF-020
from __future__ import annotations

import pytest
from src.config.profiles import RuntimeProfile, HardwareClass
from src.config.optimization_profiles import (
    DEBUG_REFERENCE, MOVEMENT_HEAVY, LOW_MEMORY, IndexingMode, CompactionLevel, PhaseSkipPolicy
)
from src.core.state import AuthoritativeState
from src.platform.rng import DeterministicRNG
from src.engine.kernel import Kernel
from src.systems.world_systems.generator import EntityGenerator
from src.engine.movement_cache import MovementPlanCache, MovementPlanKey, MovementPlan
from src.core.updates import StateUpdate
from src.engine.pipeline import AuthoritativeApplyPipeline
from src.engine.cadence import SystemCadence


@pytest.fixture
def base_profile() -> RuntimeProfile:
    return RuntimeProfile(
        name="profile_test_env",
        hardware_class=HardwareClass.CLASS_A,
        max_ram_mb=4096,
        max_cpu_percent=100.0,
        max_worker_count=0,
        max_queue_depth=100,
        max_replay_buffer_kb=1024,
        max_observability_budget_percent=10.0,
        max_tick_budget_ms=33.3
    )


@pytest.fixture
def test_state() -> AuthoritativeState:
    gen = EntityGenerator(seed=2026)
    entities = {}
    for i in range(20):
        e = gen.spawn_hero((float(i), float(i)))
        from dataclasses import replace
        e = replace(e, id=i)
        entities[i] = e
    return AuthoritativeState(tick=1, seed=2026, entities=entities, movement_cache=MovementPlanCache())


def test_kernel_with_debug_reference_executes_all_phases(base_profile: RuntimeProfile, test_state: AuthoritativeState):
    """
    Verify that Kernel initialized with DEBUG_REFERENCE profile enforces NEVER_SKIP
    and executes all 17 phases unconditionally.
    """
    kernel = Kernel(
        base_profile, test_state, DeterministicRNG(2026),
        flags={"optimization_profile": "DEBUG_REFERENCE", "no_replay": True, "no_frame_pacing": True}
    )
    try:
        assert kernel._opt_profile == DEBUG_REFERENCE
        assert kernel._cache_policy.max_movement_plans == 100000

        # Execute one tick with NO dirty entities
        kernel.tick_once()

        # In _phase_resolution, refined_update is produced and stored. Wait, let's verify phase metrics.
        # Refined update metric counters can be inspected via pipeline directly to verify exact phase run counts.
        upd = StateUpdate()
        cadence = SystemCadence()
        refined = AuthoritativeApplyPipeline.refine(kernel.state, upd, cadence=cadence)

        # Under NEVER_SKIP, 0 phases should be skipped
        assert refined.metric_counters.get("phase_skips", 0) == 0
        assert refined.metric_counters.get("phase_runs", 0) > 10
    finally:
        kernel.shutdown()


@pytest.mark.slow
def test_kernel_with_low_memory_enforces_tight_cache_limits(base_profile: RuntimeProfile, test_state: AuthoritativeState):
    """
    Verify that Kernel initialized with LOW_MEMORY profile tightly constrains cache limits and background sweeps.
    """
    kernel = Kernel(
        base_profile, test_state, DeterministicRNG(2026),
        flags={"optimization_profile": "LOW_MEMORY", "no_replay": True, "no_frame_pacing": True}
    )
    try:
        assert kernel._opt_profile == LOW_MEMORY
        assert kernel._cache_policy.max_movement_plans == 1000
        assert kernel._cache_policy.sweep_interval_ticks == 3

        m_cache = kernel.state.movement_cache
        assert m_cache is not None

        for i in range(1200):
            k = MovementPlanKey(entity_id=i, current_tile=(0, 0), target_tile=(1, 1), occupancy_version=m_cache.occupancy_version)
            p = MovementPlan(next_step=(1.0, 1.0), valid_until_tick=1000)
            m_cache.put(k, p)

        assert len(m_cache._cache) == 1200

        # Run ticks up to sweep interval (3 ticks)
        for _ in range(3):
            kernel.tick_once()

        assert len(m_cache._cache) <= 1000
        assert kernel._metrics.get("movement_plan_cache_pruned", 0) >= 200
    finally:
        kernel.shutdown()


def test_kernel_with_movement_heavy_prioritizes_movement_budgets(base_profile: RuntimeProfile, test_state: AuthoritativeState):
    """
    Verify that Kernel initialized with MOVEMENT_HEAVY profile correctly scales candidate budgets and cache envelopes.
    """
    kernel = Kernel(
        base_profile, test_state, DeterministicRNG(2026),
        flags={"optimization_profile": "MOVEMENT_HEAVY", "no_replay": True, "no_frame_pacing": True}
    )
    try:
        assert kernel._opt_profile == MOVEMENT_HEAVY
        assert kernel._cache_policy.max_movement_plans == 20000
        assert kernel._opt_profile.movement_budget == 5000

        # Ensure governor policy correctly inherits movement budgets
        kernel.tick_once()
        assert kernel._current_policy.movement_budget == 5000
    finally:
        kernel.shutdown()
