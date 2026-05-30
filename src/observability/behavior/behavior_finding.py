"""
BehaviorFinding — Phase 25 semantic behavior finding model.
Represents a specific detected behavioral pattern occurrence (good, bad, or suspicious).
"""
from __future__ import annotations
from dataclasses import dataclass
from typing import Any, Optional


@dataclass(frozen=True)
class BehaviorFinding:
    """
    An immutable record representing a single behavioral finding event or pattern.
    """
    finding_id: str
    finding_type: str  # 'repeated_failure_loop', 'hidden_knowledge_suspicion', 'route_convergence', 'stagnation', 'unsafe_engagement', 'successful_adaptation'
    severity: str      # 'INFO', 'WARNING', 'ERROR', 'CRITICAL'
    summary: str
    affected_entities: tuple[int, ...]
    tick_range: Optional[tuple[int, int]]
    evidence_event_ids: tuple[str, ...]
    evidence_episode_ids: tuple[str, ...]
    suggested_systems: tuple[str, ...]
    recommendation: str

    def to_dict(self) -> dict[str, Any]:
        """Serialize to a JSON-compatible dict."""
        return {
            "finding_id": self.finding_id,
            "finding_type": self.finding_type,
            "severity": self.severity,
            "summary": self.summary,
            "affected_entities": list(self.affected_entities),
            "tick_range": list(self.tick_range) if self.tick_range else None,
            "evidence_event_ids": list(self.evidence_event_ids),
            "evidence_episode_ids": list(self.evidence_episode_ids),
            "suggested_systems": list(self.suggested_systems),
            "recommendation": self.recommendation,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> BehaviorFinding:
        """Deserialize from a JSON-compatible dict."""
        tick_r = data.get("tick_range")
        return cls(
            finding_id=data["finding_id"],
            finding_type=data["finding_type"],
            severity=data["severity"],
            summary=data["summary"],
            affected_entities=tuple(data.get("affected_entities") or []),
            tick_range=tuple(tick_r) if tick_r else None,
            evidence_event_ids=tuple(data.get("evidence_event_ids") or []),
            evidence_episode_ids=tuple(data.get("evidence_episode_ids") or []),
            suggested_systems=tuple(data.get("suggested_systems") or []),
            recommendation=data["recommendation"],
        )
