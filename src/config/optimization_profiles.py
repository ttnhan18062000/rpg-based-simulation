# Compliance IDs: PERF-001, PERF-002, PERF-004, PERF-016, PERF-017, PERF-020
from __future__ import annotations

from enum import Enum
from dataclasses import dataclass, field
from typing import Dict, Optional, Any

from src.config.profiles import RuntimeProfile, HardwareClass
from src.engine.cache_registry import CacheBudgetPolicy


class IndexingMode(str, Enum):
    """Defines spatial indexing narrowing and caching aggressiveness."""
    DEFAULT = "DEFAULT"
    EXACT_NARROW = "EXACT_NARROW"
    UNSAFE_DISABLED = "UNSAFE_DISABLED"  # Used for DEBUG_REFERENCE parity baseline


class CompactionLevel(str, Enum):
    """Defines StateUpdate compaction aggressiveness."""
    NORMAL = "NORMAL"
    AGGRESSIVE = "AGGRESSIVE"
    NONE = "NONE"  # Used for DEBUG_REFERENCE parity baseline


class PhaseSkipPolicy(str, Enum):
    """Defines PhaseDependencyGraph dynamic phase skipping rules."""
    ALLOW_SKIP = "ALLOW_SKIP"
    CONSERVATIVE = "CONSERVATIVE"
    NEVER_SKIP = "NEVER_SKIP"  # Used for DEBUG_REFERENCE parity baseline


@dataclass(frozen=True, slots=True)
class OptimizationProfile:
    """
    Scenario-aware optimization configuration contract (Milestone 20).
    Tailors candidate budgets, cache boundaries, indexing modes, compaction levels,
    and phase skipping rules to specific simulation workloads.
    """
    name: str
    movement_budget: int = 1000
    strategic_budget: int = 50
    background_sweep_interval: int = 1
    indexing_mode: IndexingMode = IndexingMode.DEFAULT
    compaction_level: CompactionLevel = CompactionLevel.NORMAL
    phase_skip_policy: PhaseSkipPolicy = PhaseSkipPolicy.ALLOW_SKIP
    cache_budget_policy: CacheBudgetPolicy = field(default_factory=CacheBudgetPolicy)


# Milestone 20 Standard Pre-Configured Optimization Profiles

COMBAT_HEAVY = OptimizationProfile(
    name="COMBAT_HEAVY",
    movement_budget=500,
    strategic_budget=100,
    background_sweep_interval=2,
    indexing_mode=IndexingMode.EXACT_NARROW,
    compaction_level=CompactionLevel.AGGRESSIVE,
    phase_skip_policy=PhaseSkipPolicy.ALLOW_SKIP,
    cache_budget_policy=CacheBudgetPolicy(max_movement_plans=5000, max_read_dtos=5000, max_spatial_grid_versions=10)
)

MOVEMENT_HEAVY = OptimizationProfile(
    name="MOVEMENT_HEAVY",
    movement_budget=5000,
    strategic_budget=20,
    background_sweep_interval=1,
    indexing_mode=IndexingMode.EXACT_NARROW,
    compaction_level=CompactionLevel.NORMAL,
    phase_skip_policy=PhaseSkipPolicy.ALLOW_SKIP,
    cache_budget_policy=CacheBudgetPolicy(max_movement_plans=20000, max_read_dtos=2000, max_spatial_grid_versions=10)
)

RESOURCE_HEAVY = OptimizationProfile(
    name="RESOURCE_HEAVY",
    movement_budget=800,
    strategic_budget=30,
    background_sweep_interval=2,
    indexing_mode=IndexingMode.EXACT_NARROW,
    compaction_level=CompactionLevel.AGGRESSIVE,
    phase_skip_policy=PhaseSkipPolicy.ALLOW_SKIP,
    cache_budget_policy=CacheBudgetPolicy(max_movement_plans=8000, max_read_dtos=8000, max_spatial_grid_versions=25)
)

METROPOLIS = OptimizationProfile(
    name="METROPOLIS",
    movement_budget=3000,
    strategic_budget=100,
    background_sweep_interval=5,
    indexing_mode=IndexingMode.DEFAULT,
    compaction_level=CompactionLevel.AGGRESSIVE,
    phase_skip_policy=PhaseSkipPolicy.CONSERVATIVE,
    cache_budget_policy=CacheBudgetPolicy(max_movement_plans=15000, max_read_dtos=10000, max_spatial_grid_versions=15)
)

LOW_MEMORY = OptimizationProfile(
    name="LOW_MEMORY",
    movement_budget=200,
    strategic_budget=10,
    background_sweep_interval=5,
    indexing_mode=IndexingMode.DEFAULT,
    compaction_level=CompactionLevel.AGGRESSIVE,
    phase_skip_policy=PhaseSkipPolicy.ALLOW_SKIP,
    cache_budget_policy=CacheBudgetPolicy(
        max_movement_plans=1000, 
        max_read_dtos=500, 
        max_spatial_grid_versions=2, 
        max_strategic_queues=500, 
        sweep_interval_ticks=3
    )
)

DEBUG_REFERENCE = OptimizationProfile(
    name="DEBUG_REFERENCE",
    movement_budget=1000000,
    strategic_budget=1000000,
    background_sweep_interval=1,
    indexing_mode=IndexingMode.UNSAFE_DISABLED,
    compaction_level=CompactionLevel.NONE,
    phase_skip_policy=PhaseSkipPolicy.NEVER_SKIP,
    cache_budget_policy=CacheBudgetPolicy(
        max_movement_plans=100000, 
        max_read_dtos=100000, 
        max_spatial_grid_versions=50, 
        max_strategic_queues=100000, 
        sweep_interval_ticks=1
    )
)

DEFAULT_PROFILE = OptimizationProfile(
    name="DEFAULT",
    movement_budget=1000,
    strategic_budget=50,
    background_sweep_interval=1,
    indexing_mode=IndexingMode.DEFAULT,
    compaction_level=CompactionLevel.NORMAL,
    phase_skip_policy=PhaseSkipPolicy.ALLOW_SKIP,
    cache_budget_policy=CacheBudgetPolicy()
)

PROFILES_MAP: Dict[str, OptimizationProfile] = {
    "COMBAT_HEAVY": COMBAT_HEAVY,
    "MOVEMENT_HEAVY": MOVEMENT_HEAVY,
    "RESOURCE_HEAVY": RESOURCE_HEAVY,
    "METROPOLIS": METROPOLIS,
    "LOW_MEMORY": LOW_MEMORY,
    "DEBUG_REFERENCE": DEBUG_REFERENCE,
    "DEFAULT": DEFAULT_PROFILE
}


class OptimizationProfileResolver:
    """Resolves standard optimization profiles from runtime profile parameters or explicit override flags."""
    
    @staticmethod
    def resolve(profile: Optional[RuntimeProfile], flags: Optional[Dict[str, Any]] = None) -> OptimizationProfile:
        if flags and "optimization_profile" in flags:
            opt_name = str(flags["optimization_profile"]).upper()
            if opt_name in PROFILES_MAP:
                return PROFILES_MAP[opt_name]
                
        if not profile:
            return DEFAULT_PROFILE
            
        if profile.hardware_class == HardwareClass.CLASS_C or profile.max_ram_mb <= 1024:
            return LOW_MEMORY
            
        if profile.name.startswith("PROD_LARGE"):
            return METROPOLIS
            
        if profile.name.startswith("PROD_STRESS"):
            return MOVEMENT_HEAVY
            
        return DEFAULT_PROFILE
