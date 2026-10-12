"""
src/observability/run_state.py
───────────────────────────────────────────────────────────────────────────────
The per-run observability seams the kernel calls: clear every run-scoped cache at run start, and extract one tick's events (the extractor's, then
the M0-gate starvation-death record, TCK-20261009-...-H6). One module, so the kernel names each once.
"""
from __future__ import annotations

from typing import Any, List

from src.core.state import AuthoritativeState
from src.observability.config import ObservabilityMode
from src.observability.event_extractor import EventExtractor
from src.observability.event_recorder import EventRecorder
from src.observability.event_shapers import (
    FactionShaper,
    ProgressionShaper,
    SocialShaper,
    StrategyShaper,
)
from src.observability.events import SimulationEvent
from src.observability.starvation_record import StarvationRecorder

if StarvationRecorder.closing_event not in EventRecorder.closing_event_sources:
    EventRecorder.closing_event_sources.append(StarvationRecorder.closing_event)

__all__ = ["EventExtractor", "extract_events", "reset_run_state"]


def reset_run_state(strategic_cadence: int) -> None:
    """Clear every run-scoped observability cache; ``strategic_cadence`` is the profile's strategic re-decision period (ticks)."""
    EventExtractor.reset_run_state()
    StarvationRecorder.reset_run_state()
    StarvationRecorder.configure(strategic_cadence)
    StrategyShaper.reset_run_state()
    ProgressionShaper.reset_run_state()
    SocialShaper.reset_run_state()
    FactionShaper.reset_run_state()


def extract_events(prior: AuthoritativeState, current: AuthoritativeState, update: Any, mode: ObservabilityMode = ObservabilityMode.LIGHT) -> List[SimulationEvent]:
    """One tick's curated events plus the starvation-death record channel (silent when observability is OFF: no header, so the channel reads as not live)."""
    events = EventExtractor.extract(prior, current, update, mode)
    if mode != ObservabilityMode.OFF:
        events = events + StarvationRecorder.observe(prior, current, update)
    return events
