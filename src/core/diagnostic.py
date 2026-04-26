from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional


@dataclass(frozen=True, slots=True)
class TraceEvent:
    """
    Experimental diagnostic trace of a single kernel event.
    """
    tick: int
    system: str
    event_type: str
    payload: Dict[str, Any] = field(default_factory=dict)
    causal_id: Optional[str] = None


@dataclass(frozen=True, slots=True)
class DiagnosticReport:
    """
    A collection of traces and metrics for a simulation window.
    Strictly non-authoritative.
    """
    start_tick: int
    end_tick: int
    traces: List[TraceEvent] = field(default_factory=list)
    performance_metrics: Dict[str, float] = field(default_factory=dict)
