"""Story Detector models."""
from __future__ import annotations
import uuid
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple


@dataclass
class StoryCandidate:
    story_id: str = field(default_factory=lambda: uuid.uuid4().hex[:12])
    story_type: str = ""
    title: str = ""
    summary: str = ""
    entities: List[int] = field(default_factory=list)
    factions: List[str] = field(default_factory=list)
    regions: List[str] = field(default_factory=list)
    tick_range: Optional[Tuple[int, int]] = None
    supporting_events: List[str] = field(default_factory=list)
    interestingness_score: float = 0.0   # 0.0–1.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "story_id": self.story_id,
            "story_type": self.story_type,
            "title": self.title,
            "summary": self.summary,
            "entities": self.entities,
            "factions": self.factions,
            "regions": self.regions,
            "tick_range": list(self.tick_range) if self.tick_range else None,
            "supporting_events": self.supporting_events,
            "interestingness_score": round(self.interestingness_score, 3),
        }


class StoryPattern(ABC):
    """Abstract base for story detection patterns."""
    pattern_id: str = ""

    @abstractmethod
    def detect(self, ctx: "AnalysisContext") -> List[StoryCandidate]:  # type: ignore[name-defined]
        ...
