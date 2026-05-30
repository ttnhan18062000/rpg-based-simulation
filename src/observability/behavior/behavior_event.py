"""
BehaviorEvent — Phase 22 semantic behavior event model.

Represents what an entity *did* in semantic terms, produced by
BehaviorEventNormalizer outside the simulation hot path.

Behavior categories follow the roadmap taxonomy:
  movement, combat, recovery, preparation, progression,
  information_seeking, resource_gathering, trade, crafting, quest,
  cooperation, avoidance, failure_response, world_response,
  idle_or_defer, unknown_behavior
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Mapping, Optional


# ---------------------------------------------------------------------------
# Canonical category and family constants (frozen strings)
# ---------------------------------------------------------------------------

BEHAVIOR_CATEGORIES = frozenset({
    "movement",
    "combat",
    "recovery",
    "preparation",
    "progression",
    "information_seeking",
    "resource_gathering",
    "trade",
    "crafting",
    "quest",
    "cooperation",
    "avoidance",
    "failure_response",
    "world_response",
    "idle_or_defer",
    "unknown_behavior",
})


@dataclass(frozen=True)
class BehaviorEvent:
    """
    A semantic behavior event produced from one or more raw SimulationEvents.

    This is the unit of analysis for behavior timelines, episodes, metrics,
    pattern detectors, and scorecards (Phases 23–26).

    Key design rules:
    - Immutable (frozen dataclass).
    - Does not carry full EntityState or AuthoritativeState.
    - Links back to source raw event IDs for traceability.
    - Does not require world state to produce.
    - Can be serialized to/from JSON for post-run artifact files.
    """

    run_id: str
    tick: int
    entity_id: Optional[int]

    # Semantic classification ------------------------------------------------
    behavior_category: str
    """One of BEHAVIOR_CATEGORIES, e.g. 'combat', 'movement'."""

    behavior_family: str
    """Fine-grained sub-type within the category, e.g. 'engage', 'travel'."""

    # Optional enrichment ----------------------------------------------------
    subject: Optional[str] = None
    """Human-readable subject label (e.g. entity class, role)."""

    target_id: Optional[int | str] = None
    """Target entity or object ID if applicable."""

    source_event_ids: tuple[str, ...] = field(default_factory=tuple)
    """IDs of the originating raw SimulationEvent(s)."""

    route_family: Optional[str] = None
    """The strategic route/plan family driving this behavior (if known)."""

    action_type: Optional[str] = None
    """Specific raw action type (e.g. 'combat_damage', 'movement')."""

    outcome: Optional[str] = None
    """Result of the behavior: 'success', 'failure', 'blocked', 'lethal', etc."""

    reason: Optional[str] = None
    """Optional human-readable reason string (not authoritative — for diagnostics)."""

    payload: Mapping[str, Any] = field(default_factory=dict)
    """Small supplemental payload; must not carry full world state."""

    def to_dict(self) -> dict[str, Any]:
        """Serialize to a JSON-compatible dict for artifact writing."""
        return {
            "run_id": self.run_id,
            "tick": self.tick,
            "entity_id": self.entity_id,
            "behavior_category": self.behavior_category,
            "behavior_family": self.behavior_family,
            "subject": self.subject,
            "target_id": self.target_id,
            "source_event_ids": list(self.source_event_ids),
            "route_family": self.route_family,
            "action_type": self.action_type,
            "outcome": self.outcome,
            "reason": self.reason,
            "payload": dict(self.payload),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "BehaviorEvent":
        """Deserialize from a JSON-compatible dict (e.g. from a JSONL artifact)."""
        return cls(
            run_id=data["run_id"],
            tick=data["tick"],
            entity_id=data.get("entity_id"),
            behavior_category=data["behavior_category"],
            behavior_family=data["behavior_family"],
            subject=data.get("subject"),
            target_id=data.get("target_id"),
            source_event_ids=tuple(data.get("source_event_ids") or []),
            route_family=data.get("route_family"),
            action_type=data.get("action_type"),
            outcome=data.get("outcome"),
            reason=data.get("reason"),
            payload=data.get("payload") or {},
        )
