from __future__ import annotations
from abc import ABC, abstractmethod
from typing import Optional

from src.observability.events import ObservabilityEventEnvelope
from src.simulation_quality.pillars import PillarId
from src.simulation_quality.score_record import ScoreRecord, ScoringContext
from src.simulation_quality.weights import ScoringWeights


class PillarScorer(ABC):
    """Abstract base for all simulation quality pillar scorers."""

    EVENT_TYPES: tuple[str, ...] = ()
    PILLAR_ID: PillarId

    def __init__(self, weights: ScoringWeights) -> None:
        self.weights = weights.for_pillar(self.PILLAR_ID)

    @abstractmethod
    def score(
        self,
        envelope: ObservabilityEventEnvelope,
        context: ScoringContext,
    ) -> Optional[ScoreRecord]:
        """Return a ScoreRecord if this event scores for this pillar, else None."""
