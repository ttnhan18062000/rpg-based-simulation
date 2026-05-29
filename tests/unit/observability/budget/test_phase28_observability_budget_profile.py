"""
Phase 28 initial guard — ObservabilityBudgetProfile model tests.

These tests verify that the budget profile dataclass is correctly defined
and that the sampling policy constants are well-formed.

These are unit-level guards — the full Phase 28 rollout gate is deferred.
"""
from __future__ import annotations

import pytest

from src.observability.budget.budget_profile import (
    ObservabilityBudgetProfile,
    SamplingPolicy,
    DegradationLevel,
    PRESET_PRODUCTION,
    PRESET_RESEARCH,
    PRESET_DEBUG,
)


class TestObservabilityBudgetProfile:

    def test_budget_profile_is_frozen(self):
        profile = PRESET_PRODUCTION
        with pytest.raises((AttributeError, TypeError)):
            profile.max_hot_path_overhead_percent = 99.0  # type: ignore[misc]

    def test_preset_production_has_conservative_limits(self):
        """Production preset must keep overhead low."""
        assert PRESET_PRODUCTION.max_hot_path_overhead_percent <= 5.0
        assert PRESET_PRODUCTION.max_raw_events_per_tick <= 100
        assert PRESET_PRODUCTION.max_event_queue_size >= 100

    def test_preset_research_allows_more_volume(self):
        """Research preset should allow more events than production."""
        assert PRESET_RESEARCH.max_raw_events_per_tick >= PRESET_PRODUCTION.max_raw_events_per_tick
        assert PRESET_RESEARCH.max_event_queue_size >= PRESET_PRODUCTION.max_event_queue_size

    def test_preset_debug_allows_most_volume(self):
        """Debug preset must allow maximum volume."""
        assert PRESET_DEBUG.max_raw_events_per_tick >= PRESET_RESEARCH.max_raw_events_per_tick

    def test_budget_profile_custom_construction(self):
        custom = ObservabilityBudgetProfile(
            max_hot_path_overhead_percent=2.0,
            max_event_emit_ns_per_event=5_000,
            max_raw_events_per_tick=50,
            max_behavior_events_per_tick=20,
            max_event_queue_size=200,
            max_timeline_events_per_entity=100,
            max_open_episodes_per_entity=5,
            max_live_publish_ms_per_tick=0.5,
            max_postrun_analysis_seconds=30.0,
        )
        assert custom.max_hot_path_overhead_percent == 2.0
        assert custom.max_raw_events_per_tick == 50

    def test_sampling_policy_constants_are_defined(self):
        """All sampling policies from Phase 28 spec must exist."""
        assert hasattr(SamplingPolicy, "ALWAYS_KEEP_HARD_LAW")
        assert hasattr(SamplingPolicy, "ALWAYS_KEEP_FATAL")
        assert hasattr(SamplingPolicy, "SAMPLE_LOW_SEVERITY")
        assert hasattr(SamplingPolicy, "DROP_LOW_PRIORITY")

    def test_degradation_levels_are_defined(self):
        """All degradation levels from Phase 28 spec must exist."""
        assert hasattr(DegradationLevel, "NORMAL")
        assert hasattr(DegradationLevel, "CONSTRAINED")
        assert hasattr(DegradationLevel, "DEGRADED")
        assert hasattr(DegradationLevel, "CRITICAL_OBS_ONLY")

    def test_budget_profile_all_fields_present(self):
        """Budget profile must have all 9 required fields from Phase 28 spec."""
        required_fields = {
            "max_hot_path_overhead_percent",
            "max_event_emit_ns_per_event",
            "max_raw_events_per_tick",
            "max_behavior_events_per_tick",
            "max_event_queue_size",
            "max_timeline_events_per_entity",
            "max_open_episodes_per_entity",
            "max_live_publish_ms_per_tick",
            "max_postrun_analysis_seconds",
        }
        for field in required_fields:
            assert hasattr(PRESET_PRODUCTION, field), f"Missing field: {field}"
