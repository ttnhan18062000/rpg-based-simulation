from __future__ import annotations
import dataclasses
import logging
import os
import threading
from collections import Counter
from typing import Any, Callable, Optional

from src.observability.events import ObservabilityEventEnvelope
from src.simulation_quality.pillar_accumulator import PillarAccumulator
from src.simulation_quality.pillars import PillarId
from src.simulation_quality.quality_report import QualityReport, QualityReportBuilder, _assign_grade
from src.simulation_quality.score_record import ScoringContext
from src.simulation_quality.scorers.base import PillarScorer
from src.simulation_quality.weights import ScoringWeights

logger = logging.getLogger(__name__)

# Direct one-to-one engine event_type → contract event_type remaps.
_TRANSLATE_SIMPLE: dict[str, str] = {
    "combat_kill":              "entity_killed",
    "gold_transaction":         "gold_transferred",
    "StrategicObjectiveChanged": "strategic_goal_changed",
    "StrategicConcernRaised":   "strategic_goal_changed",
    "StrategicDetourCreated":   "project_started",
    "StrategicLeadExhausted":   "knowledge_default_fallback",
}


def _translate_quest_event(env: ObservabilityEventEnvelope) -> str:
    status = (env.payload or {}).get("status", "started")
    if status == "completed":
        return "quest_completed"
    if status == "failed":
        return "quest_failed"
    return "quest_started"


def _translate_lifecycle(env: ObservabilityEventEnvelope) -> str:
    action = (env.payload or {}).get("action", "")
    if action == "level_up":
        return "level_up"
    if action in ("despawn", "death"):
        return "entity_killed"
    return env.event_type  # no translation


def _translate_strategic_project(env: ObservabilityEventEnvelope) -> str:
    reason = str((env.payload or {}).get("reason", "")).lower()
    if "complet" in reason:
        return "project_completed"
    if "abandon" in reason:
        return "project_abandoned"
    return "project_started"


def _translate_invariant(env: ObservabilityEventEnvelope) -> str:
    law_id = str((env.payload or {}).get("law_id", "")).upper()
    if law_id.startswith("COMBAT"):
        return "combat_hard_law_violation"
    if law_id.startswith("CONSERVATION"):
        return "conservation_law_violated"
    return env.event_type  # unknown violation — no translation


# Payload-conditional translators keyed by engine event_type.
_TRANSLATE_CONDITIONAL: dict[str, Callable[[ObservabilityEventEnvelope], str]] = {
    "quest_event":             _translate_quest_event,
    "lifecycle":               _translate_lifecycle,
    "StrategicProjectChanged": _translate_strategic_project,
    "InvariantViolation":      _translate_invariant,
}


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

    @staticmethod
    def _translate(env: ObservabilityEventEnvelope) -> ObservabilityEventEnvelope:
        """Remap engine event_type to contract vocabulary before scorer dispatch.

        Original event_type is preserved in payload["_original_event_type"] for traceability.
        Returns the original envelope unchanged when no mapping applies.
        """
        original = env.event_type
        if original in _TRANSLATE_SIMPLE:
            contract_type = _TRANSLATE_SIMPLE[original]
        elif original in _TRANSLATE_CONDITIONAL:
            contract_type = _TRANSLATE_CONDITIONAL[original](env)
        else:
            return env

        if contract_type == original:
            return env

        new_payload = dict(env.payload) if env.payload else {}
        new_payload["_original_event_type"] = original
        return dataclasses.replace(env, event_type=contract_type, payload=new_payload)

    def on_envelope(self, envelope: ObservabilityEventEnvelope) -> None:
        if self._disabled:
            return

        envelope = self._translate(envelope)

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
