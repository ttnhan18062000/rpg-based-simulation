# Compliance IDs: PERF-001, PERF-002, PERF-004, PERF-016, PERF-017, PERF-020
import pytest
from src.config.profiles import RuntimeProfile, HardwareClass
from src.config.optimization_profiles import (
    OptimizationProfile, IndexingMode, CompactionLevel, PhaseSkipPolicy,
    COMBAT_HEAVY, MOVEMENT_HEAVY, RESOURCE_HEAVY, METROPOLIS, LOW_MEMORY, DEBUG_REFERENCE, DEFAULT_PROFILE,
    OptimizationProfileResolver
)
from src.engine.phase_governor import PhaseBudgetGovernor
from src.core.governance import RuntimeMode


def test_standard_profiles_deterministic():
    """Verify that all standard profiles are deterministic and adhere to expected boundaries."""
    assert COMBAT_HEAVY.movement_budget == 500
    assert COMBAT_HEAVY.strategic_budget == 100
    assert COMBAT_HEAVY.indexing_mode == IndexingMode.EXACT_NARROW
    assert COMBAT_HEAVY.compaction_level == CompactionLevel.AGGRESSIVE
    assert COMBAT_HEAVY.cache_budget_policy.max_movement_plans == 5000

    assert MOVEMENT_HEAVY.movement_budget == 5000
    assert MOVEMENT_HEAVY.strategic_budget == 20
    assert MOVEMENT_HEAVY.compaction_level == CompactionLevel.NORMAL
    assert MOVEMENT_HEAVY.cache_budget_policy.max_movement_plans == 20000

    assert RESOURCE_HEAVY.cache_budget_policy.max_spatial_grid_versions == 25
    assert RESOURCE_HEAVY.movement_budget == 800

    assert METROPOLIS.movement_budget == 3000
    assert METROPOLIS.phase_skip_policy == PhaseSkipPolicy.CONSERVATIVE


def test_debug_reference_disables_unsafe_optimizations():
    """Verify that DEBUG_REFERENCE correctly disables narrowing, compaction, and phase skipping."""
    assert DEBUG_REFERENCE.indexing_mode == IndexingMode.UNSAFE_DISABLED
    assert DEBUG_REFERENCE.compaction_level == CompactionLevel.NONE
    assert DEBUG_REFERENCE.phase_skip_policy == PhaseSkipPolicy.NEVER_SKIP
    assert DEBUG_REFERENCE.movement_budget == 1000000
    assert DEBUG_REFERENCE.strategic_budget == 1000000


def test_low_memory_reduces_cache_envelopes():
    """Verify that LOW_MEMORY correctly constrains cache boundaries and increases sweep frequency."""
    assert LOW_MEMORY.movement_budget == 200
    assert LOW_MEMORY.strategic_budget == 10
    assert LOW_MEMORY.cache_budget_policy.max_movement_plans == 1000
    assert LOW_MEMORY.cache_budget_policy.max_read_dtos == 500
    assert LOW_MEMORY.cache_budget_policy.max_spatial_grid_versions == 2
    assert LOW_MEMORY.cache_budget_policy.sweep_interval_ticks == 3


def test_optimization_profile_resolver():
    """Verify that OptimizationProfileResolver resolves correctly from runtime flags or profiles."""
    profile_high = RuntimeProfile(
        name="TEST_NORMAL",
        hardware_class=HardwareClass.CLASS_A,
        max_ram_mb=8192,
        max_cpu_percent=100.0,
        max_worker_count=4,
        max_queue_depth=1000,
        max_replay_buffer_kb=10240,
        max_observability_budget_percent=10.0,
        max_tick_budget_ms=33.3
    )

    profile_low = RuntimeProfile(
        name="TEST_LOW",
        hardware_class=HardwareClass.CLASS_C,
        max_ram_mb=512,
        max_cpu_percent=50.0,
        max_worker_count=1,
        max_queue_depth=100,
        max_replay_buffer_kb=1024,
        max_observability_budget_percent=5.0,
        max_tick_budget_ms=100.0
    )

    # 1. Resolve flag override
    resolved = OptimizationProfileResolver.resolve(profile_high, {"optimization_profile": "COMBAT_HEAVY"})
    assert resolved == COMBAT_HEAVY

    resolved_debug = OptimizationProfileResolver.resolve(profile_low, {"optimization_profile": "debug_reference"})
    assert resolved_debug == DEBUG_REFERENCE

    # 2. Resolve hardware class fallback
    resolved_class_c = OptimizationProfileResolver.resolve(profile_low)
    assert resolved_class_c == LOW_MEMORY

    # 3. Resolve scenario name prefix fallback
    profile_stress = RuntimeProfile(
        name="PROD_STRESS_SCENARIO",
        hardware_class=HardwareClass.CLASS_A,
        max_ram_mb=8192,
        max_cpu_percent=100.0,
        max_worker_count=4,
        max_queue_depth=1000,
        max_replay_buffer_kb=10240,
        max_observability_budget_percent=10.0,
        max_tick_budget_ms=33.3
    )
    assert OptimizationProfileResolver.resolve(profile_stress) == MOVEMENT_HEAVY


def test_phase_budget_governor_respects_opt_profile():
    """Verify that PhaseBudgetGovernor propagates OptimizationProfile baseline budgets and overrides."""
    # Normal profile override
    budgets = PhaseBudgetGovernor.evaluate(None, None, RuntimeMode.NORMAL, 1, opt_profile=MOVEMENT_HEAVY)
    assert budgets.candidate_budget == 5000
    assert budgets.movement_budget == 5000
    assert budgets.strategic_budget == 20
    assert budgets.compaction_level == "NORMAL"

    # Debug reference override
    budgets_debug = PhaseBudgetGovernor.evaluate(None, None, RuntimeMode.NORMAL, 1, opt_profile=DEBUG_REFERENCE)
    assert budgets_debug.candidate_budget == 1000000
    assert budgets_debug.compaction_level == "NONE"
