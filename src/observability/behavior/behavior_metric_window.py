"""
BehaviorMetricWindow — Phase 24 semantic behavior metric model.
Stops behavioral metrics from mixing with existing performance MetricWindowRecords.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Mapping


@dataclass(frozen=True)
class BehaviorMetricWindow:
    """
    An immutable record of behavioral activities within a specific tick window.
    Supports complete decoupling of behavior analysis from performance analytics.
    """
    run_id: str
    window_start_tick: int
    window_end_tick: int
    
    behavior_counts: Mapping[str, int] = field(default_factory=dict)
    route_family_counts: Mapping[str, int] = field(default_factory=dict)
    episode_counts: Mapping[str, int] = field(default_factory=dict)
    episode_outcomes: Mapping[str, int] = field(default_factory=dict)
    failure_counts: Mapping[str, int] = field(default_factory=dict)
    adaptation_counts: Mapping[str, int] = field(default_factory=dict)
    entity_activity_counts: Mapping[str, int] = field(default_factory=dict)
    
    schema_version: int = 1

    def to_dict(self) -> dict[str, Any]:
        """Serialize to a JSON-compatible dict for JSONL logging."""
        return {
            "run_id": self.run_id,
            "window_start_tick": self.window_start_tick,
            "window_end_tick": self.window_end_tick,
            "behavior_counts": dict(self.behavior_counts),
            "route_family_counts": dict(self.route_family_counts),
            "episode_counts": dict(self.episode_counts),
            "episode_outcomes": dict(self.episode_outcomes),
            "failure_counts": dict(self.failure_counts),
            "adaptation_counts": dict(self.adaptation_counts),
            "entity_activity_counts": dict(self.entity_activity_counts),
            "schema_version": self.schema_version,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> BehaviorMetricWindow:
        """Deserialize from a JSON-compatible dict."""
        return cls(
            run_id=data["run_id"],
            window_start_tick=data["window_start_tick"],
            window_end_tick=data["window_end_tick"],
            behavior_counts=data.get("behavior_counts") or {},
            route_family_counts=data.get("route_family_counts") or {},
            episode_counts=data.get("episode_counts") or {},
            episode_outcomes=data.get("episode_outcomes") or {},
            failure_counts=data.get("failure_counts") or {},
            adaptation_counts=data.get("adaptation_counts") or {},
            entity_activity_counts=data.get("entity_activity_counts") or {},
            schema_version=data.get("schema_version", 1),
        )
