"""
ObservabilityBudgetProfile — Phase 28 budget, sampling policy, and degradation model.

Defines the upper bounds for observability overhead to protect the main
simulation engine from observability-induced slowdowns or instability.

Three preset profiles are provided:
  PRESET_PRODUCTION — conservative, safe for production sweeps
  PRESET_RESEARCH   — relaxed, for research/comparison runs
  PRESET_DEBUG      — maximum visibility, dev/debug only

Usage:
    from src.observability.budget.budget_profile import PRESET_PRODUCTION
    if profiler.overhead_percent > PRESET_PRODUCTION.max_hot_path_overhead_percent:
        degrade_observability()
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum, auto


# ---------------------------------------------------------------------------
# Degradation levels (Phase 28 spec)
# ---------------------------------------------------------------------------

class DegradationLevel(Enum):
    """
    Observability degradation levels.

    NORMAL           — Configured observability runs as designed.
    CONSTRAINED      — Sample low-priority events; disable live episode processing.
    DEGRADED         — Raw critical events only; behavior timeline disabled.
    CRITICAL_OBS_ONLY — Hard-law events, fatal errors, minimal phase timing only.
    """

    NORMAL = auto()
    CONSTRAINED = auto()
    DEGRADED = auto()
    CRITICAL_OBS_ONLY = auto()


# ---------------------------------------------------------------------------
# Sampling policies (Phase 28 spec)
# ---------------------------------------------------------------------------

class SamplingPolicy(Enum):
    """
    Sampling policy constants for the observability budget guard.

    These define what is NEVER dropped vs what can be sampled/dropped
    under queue pressure or budget constraints.
    """

    ALWAYS_KEEP_HARD_LAW = auto()
    """Hard-law violation events are never dropped regardless of pressure."""

    ALWAYS_KEEP_FATAL = auto()
    """Fatal errors are never dropped."""

    ALWAYS_KEEP_DEBUG_ENTITIES = auto()
    """Explicitly selected debug entities are always fully sampled."""

    ALWAYS_KEEP_RESEARCH_MARKERS = auto()
    """Events explicitly marked for research are never dropped."""

    SAMPLE_LOW_SEVERITY = auto()
    """Low-severity repeated events may be sampled (not all recorded)."""

    SUMMARIZE_REPEATED = auto()
    """Repeated behavior of the same type may be summarized, not fully recorded."""

    DROP_LOW_PRIORITY = auto()
    """Low-priority events (INFO/DEBUG) may be dropped under queue pressure."""


# ---------------------------------------------------------------------------
# ObservabilityBudgetProfile (Phase 28 spec)
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class ObservabilityBudgetProfile:
    """
    Defines upper bounds for observability system overhead.

    All fields from the Phase 28 roadmap spec are included.
    No field may be None — explicit bounds are required for production safety.
    """

    max_hot_path_overhead_percent: float
    """Maximum allowed observability overhead as % of tick compute time."""

    max_event_emit_ns_per_event: int
    """Maximum nanoseconds spent emitting a single event in the hot path."""

    max_raw_events_per_tick: int
    """Maximum raw simulation events recorded per tick."""

    max_behavior_events_per_tick: int
    """Maximum behavior events produced by the async normalizer per tick."""

    max_event_queue_size: int
    """Maximum BoundedObservabilityQueue capacity."""

    max_timeline_events_per_entity: int
    """Maximum events stored per entity in the behavior timeline store."""

    max_open_episodes_per_entity: int
    """Maximum simultaneously open behavior episodes per entity."""

    max_live_publish_ms_per_tick: float
    """Maximum milliseconds spent on live stream publish per tick."""

    max_postrun_analysis_seconds: float
    """Maximum wall time for full post-run behavior analysis."""


# ---------------------------------------------------------------------------
# Preset profiles
# ---------------------------------------------------------------------------

PRESET_PRODUCTION = ObservabilityBudgetProfile(
    max_hot_path_overhead_percent=3.0,      # ≤ 3% overhead in production
    max_event_emit_ns_per_event=5_000,       # ≤ 5µs per event
    max_raw_events_per_tick=50,              # conservative event volume
    max_behavior_events_per_tick=20,         # behavior worker bounded
    max_event_queue_size=500,               # bounded queue
    max_timeline_events_per_entity=100,      # bounded timelines
    max_open_episodes_per_entity=5,          # open episode cap
    max_live_publish_ms_per_tick=0.5,        # fast publish or drop
    max_postrun_analysis_seconds=120.0,      # 2-minute analysis budget
)

PRESET_RESEARCH = ObservabilityBudgetProfile(
    max_hot_path_overhead_percent=10.0,      # up to 10% acceptable in research
    max_event_emit_ns_per_event=20_000,
    max_raw_events_per_tick=500,
    max_behavior_events_per_tick=200,
    max_event_queue_size=5_000,
    max_timeline_events_per_entity=1_000,
    max_open_episodes_per_entity=20,
    max_live_publish_ms_per_tick=2.0,
    max_postrun_analysis_seconds=600.0,      # 10-minute analysis budget
)

PRESET_DEBUG = ObservabilityBudgetProfile(
    max_hot_path_overhead_percent=30.0,      # debug mode allows high overhead
    max_event_emit_ns_per_event=100_000,
    max_raw_events_per_tick=10_000,
    max_behavior_events_per_tick=5_000,
    max_event_queue_size=50_000,
    max_timeline_events_per_entity=10_000,
    max_open_episodes_per_entity=100,
    max_live_publish_ms_per_tick=10.0,
    max_postrun_analysis_seconds=3_600.0,   # unlimited analysis time in debug
)
