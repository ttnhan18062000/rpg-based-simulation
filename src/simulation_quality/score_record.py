from __future__ import annotations
from dataclasses import dataclass
from collections.abc import Mapping
from typing import Optional

from src.simulation_quality.pillars import PillarId


@dataclass(frozen=True)
class ScoreRecord:
    """Atomic, immutable unit of simulation quality scoring."""
    tick: int
    event_id: str
    pillar: PillarId
    delta: float
    reason: str
    event_type: str
    entity_id: Optional[int]
    region_id: Optional[str]
    tags: tuple[str, ...]


@dataclass(frozen=True)
class ScoringContext:
    """Read-only context passed to every scorer.score() call. Must not be mutated."""
    run_id: str
    current_tick: int
    entity_count: int
    pillar_scores: Mapping[PillarId, float]
    pillar_event_counts: Mapping[PillarId, int]
    window_tag_counts: Mapping[PillarId, Mapping[str, int]]
