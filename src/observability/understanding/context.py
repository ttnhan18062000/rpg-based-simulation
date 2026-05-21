"""
AnalysisContext — shared input passed to all Phase 8 analyzers.

Contains a fully loaded snapshot of one run's events, anomalies, and
optional contextual data (expectation pack, baseline) so each analyzer
can work from a single consistent source without re-loading files.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, TYPE_CHECKING

from src.observability.events import SimulationEvent
from src.observability.anomaly.rules import Anomaly

if TYPE_CHECKING:
    from src.observability.understanding.expectations.models import ScenarioExpectationPack
    from src.observability.reporting.baseline_generator import BaselineConfig


@dataclass
class AnalysisContext:
    """
    Shared input object for all Phase 8 analyzers.

    Created once per post-run analysis pipeline run and passed to every
    domain analyzer, root-cause engine, balance engine, story detector,
    and quality reporter.
    """
    run_id: str
    scenario_type: str  # e.g. "resource_economy", "combat_heavy", "mixed_sandbox"
    events: List[SimulationEvent] = field(default_factory=list)
    anomalies: List[Anomaly] = field(default_factory=list)
    expectation_pack: Optional[Any] = None   # ScenarioExpectationPack when M43 available
    baseline: Optional[Any] = None           # BaselineConfig when baseline available
    run_dir: Optional[str] = None
    extra_metadata: Dict[str, Any] = field(default_factory=dict)

    # Derived helpers
    def events_by_category(self, category: str) -> List[SimulationEvent]:
        """Return all events matching the given event_category."""
        return [e for e in self.events if e.event_category == category]

    def events_by_type(self, event_type: str) -> List[SimulationEvent]:
        """Return all events matching the given event_type."""
        return [e for e in self.events if e.event_type == event_type]

    def anomalies_by_rule(self, rule_name: str) -> List[Anomaly]:
        """Return all anomalies produced by the given rule."""
        return [a for a in self.anomalies if a.rule_name == rule_name]

    def anomalies_by_severity(self, severity: str) -> List[Anomaly]:
        """Return all anomalies with the given severity."""
        return [a for a in self.anomalies if a.severity == severity]

    def has_events(self, *categories: str) -> bool:
        """True if any events exist for any of the given categories."""
        cats = set(categories)
        return any(e.event_category in cats for e in self.events)

    def final_tick(self) -> int:
        """Return the max tick seen in the event stream, or 0 if no events."""
        return max((e.tick for e in self.events), default=0)
