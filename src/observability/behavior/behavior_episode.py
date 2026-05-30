"""
BehaviorEpisode — Phase 23 semantic behavior episode model.
Represents a continuous interval of entity actions grouped semantically.
"""
from __future__ import annotations
from dataclasses import dataclass
from typing import Any, Optional


@dataclass(frozen=True)
class BehaviorEpisode:
    """
    An immutable record representing a detected continuous episode of behavior.
    """
    episode_id: str
    run_id: str
    entity_id: int
    episode_type: str  # e.g. 'combat_episode', 'quest_episode', 'recovery_episode', 'information_episode'
    start_tick: int
    end_tick: Optional[int]
    trigger: Optional[str]
    steps: tuple[str, ...]
    outcome: str       # 'success', 'failure', 'escaped', 'resolved', 'stuck', 'ongoing'
    source_behavior_event_ids: tuple[str, ...]
    summary: str

    def to_dict(self) -> dict[str, Any]:
        """Serialize to a JSON-compatible dict."""
        return {
            "episode_id": self.episode_id,
            "run_id": self.run_id,
            "entity_id": self.entity_id,
            "episode_type": self.episode_type,
            "start_tick": self.start_tick,
            "end_tick": self.end_tick,
            "trigger": self.trigger,
            "steps": list(self.steps),
            "outcome": self.outcome,
            "source_behavior_event_ids": list(self.source_behavior_event_ids),
            "summary": self.summary,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> BehaviorEpisode:
        """Deserialize from a JSON-compatible dict."""
        return cls(
            episode_id=data["episode_id"],
            run_id=data["run_id"],
            entity_id=data["entity_id"],
            episode_type=data["episode_type"],
            start_tick=data["start_tick"],
            end_tick=data.get("end_tick"),
            trigger=data.get("trigger"),
            steps=tuple(data.get("steps") or []),
            outcome=data["outcome"],
            source_behavior_event_ids=tuple(data.get("source_behavior_event_ids") or []),
            summary=data["summary"],
        )
