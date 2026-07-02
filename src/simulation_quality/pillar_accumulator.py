from __future__ import annotations
import threading
from collections import Counter, deque
from typing import Any, Optional

from src.simulation_quality.pillars import PillarId
from src.simulation_quality.score_record import ScoreRecord
from src.simulation_quality.weights import ScoringWeights


class PillarAccumulator:
    """Thread-safe per-pillar accumulator for simulation quality scoring."""

    def __init__(
        self,
        pillar_id: PillarId,
        weights: Optional[ScoringWeights] = None,
        max_worst_events: int = 100,
        window_size: int = 200,
        loop_threshold: float = 0.70,
    ) -> None:
        self.pillar_id = pillar_id
        self._max_worst_events = (
            weights.detection.max_worst_events if weights is not None else max_worst_events
        )
        self._window_size = (
            weights.detection.window_size if weights is not None else window_size
        )
        self._loop_threshold = (
            weights.detection.loop_threshold if weights is not None else loop_threshold
        )

        self.raw_score: float = 0.0
        self.event_count: int = 0
        self.negative_count: int = 0
        self.worst_events: list[ScoreRecord] = []
        self.window_buffer: deque[ScoreRecord] = deque(maxlen=self._window_size)
        self.loop_flags: set[str] = set()
        self._seen_event_ids: set[str] = set()
        self._lock = threading.Lock()
        self.last_event_tick: int = 0

    def add(self, record: ScoreRecord) -> None:
        with self._lock:
            if record.event_id in self._seen_event_ids:
                return
            self._seen_event_ids.add(record.event_id)
            self.last_event_tick = max(self.last_event_tick, record.tick)
            self.raw_score += record.delta
            self.event_count += 1
            if record.delta < 0:
                self.negative_count += 1
                self.worst_events.append(record)
                self.worst_events.sort(key=lambda r: abs(r.delta), reverse=True)
                if len(self.worst_events) > self._max_worst_events:
                    self.worst_events.pop()
            self.window_buffer.append(record)
            self._check_loop_detection()

    def _check_loop_detection(self) -> None:
        if len(self.window_buffer) == 0:
            return
        tag_counts: Counter[str] = Counter()
        for record in self.window_buffer:
            for tag in record.tags:
                tag_counts[tag] += 1
        window_len = len(self.window_buffer)
        for tag, count in tag_counts.items():
            if count / window_len > self._loop_threshold:
                self.loop_flags.add(tag)

    def snapshot(self) -> dict[str, Any]:
        with self._lock:
            return {
                "pillar_id": self.pillar_id.value,
                "raw_score": self.raw_score,
                "event_count": self.event_count,
                "negative_count": self.negative_count,
                "last_event_tick": self.last_event_tick,
                "worst_events": tuple(self.worst_events),
                "window_buffer": tuple(self.window_buffer),
                "loop_flags": frozenset(self.loop_flags),
            }
