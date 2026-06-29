from __future__ import annotations
import logging
import os
import threading
from collections import Counter
from typing import Any, Optional

from src.observability.events import ObservabilityEventEnvelope
from src.simulation_quality.pillar_accumulator import PillarAccumulator
from src.simulation_quality.pillars import PillarId
from src.simulation_quality.quality_report import QualityReport, QualityReportBuilder, _assign_grade
from src.simulation_quality.score_record import ScoringContext
from src.simulation_quality.scorers.base import PillarScorer
from src.simulation_quality.weights import ScoringWeights

logger = logging.getLogger(__name__)


class QualityHub:
    """Feed-mode-agnostic hub that routes observability events to pillar scorers."""

    def __init__(
        self,
        scorers: list[PillarScorer],
        weights: ScoringWeights,
        persistence: Any,
        run_id: str = "unknown",
    ) -> None:
        self._disabled = os.environ.get("QUALITY_SCORING_DISABLED") == "1"
        self._weights = weights
        self._persistence = persistence
        self._run_id = run_id
        self._tick: int = 0
        self._entity_count: int = 0
        self._lock = threading.Lock()

        # Build SCORER_REGISTRY from each scorer's declared EVENT_TYPES
        self.SCORER_REGISTRY: dict[str, list[PillarScorer]] = {}
        for scorer in scorers:
            for event_type in scorer.EVENT_TYPES:
                self.SCORER_REGISTRY.setdefault(event_type, []).append(scorer)

        self._accumulators: dict[PillarId, PillarAccumulator] = {
            pid: PillarAccumulator(pid, weights) for pid in PillarId
        }

    def on_envelope(self, envelope: ObservabilityEventEnvelope) -> None:
        if self._disabled:
            return

        with self._lock:
            if envelope.tick > self._tick:
                self._tick = envelope.tick

        context = self._build_context()
        scorers = self.SCORER_REGISTRY.get(envelope.event_type, [])
        for scorer in scorers:
            try:
                record = scorer.score(envelope, context)
                if record is not None:
                    self._accumulators[record.pillar].add(record)
                    self._persistence.write(record)
            except Exception as exc:
                logger.warning(
                    "scorer_error scorer=%s event=%s error=%s",
                    scorer.__class__.__name__,
                    envelope.event_id,
                    exc,
                )

    def _build_context(self) -> ScoringContext:
        with self._lock:
            tick = self._tick
            entity_count = self._entity_count

        snaps = {pid: self._accumulators[pid].snapshot() for pid in PillarId}
        pillar_scores = {pid: snaps[pid]["raw_score"] for pid in PillarId}
        pillar_event_counts = {pid: snaps[pid]["event_count"] for pid in PillarId}

        window_tag_counts: dict[PillarId, dict[str, int]] = {}
        for pid in PillarId:
            tag_counts: Counter[str] = Counter()
            for rec in snaps[pid]["window_buffer"]:
                for tag in rec.tags:
                    tag_counts[tag] += 1
            window_tag_counts[pid] = dict(tag_counts)

        return ScoringContext(
            run_id=self._run_id,
            current_tick=tick,
            entity_count=entity_count,
            pillar_scores=pillar_scores,
            pillar_event_counts=pillar_event_counts,
            window_tag_counts=window_tag_counts,
        )

    def update_entity_count(self, count: int) -> None:
        with self._lock:
            self._entity_count = count

    def get_pillar_score(self, pillar: PillarId) -> float:
        return self._accumulators[pillar].snapshot()["raw_score"]

    def get_pillar_grade(self, pillar: PillarId) -> str:
        with self._lock:
            tick = self._tick
        snap = self._accumulators[pillar].snapshot()
        normalized = snap["raw_score"] / max(1, tick)
        return _assign_grade(normalized, self._weights.grade_thresholds)

    def get_quality_report(self) -> QualityReport:
        with self._lock:
            tick = self._tick
            run_id = self._run_id
        return QualityReportBuilder.build(self._accumulators, tick, run_id, self._weights)

    def start(self, feed: Any) -> None:
        feed.start(self)

    def stop(self, feed: Any) -> None:
        feed.stop()
