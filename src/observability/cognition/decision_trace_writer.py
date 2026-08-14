"""
src/observability/cognition/decision_trace_writer.py
───────────────────────────────────────────────────────────────────────────────
Decision Trace Writer — Epic 2.2A.

Writes per-entity scored adventure route traces to decision_trace.jsonl in
LIGHT and above observability modes. Wired into AdventureGoalScorer.score()
(src/ai/goals/adventure_scorer.py) after AdventureDecisionService.decide()
completes -- relocated here from the now-deleted AdventureDecisionPhase.apply()
by TCK-20260811-DELETE-ADVENTURE-DECISION-PHASE. Does NOT modify execute_brain()
in any way.

Module-level singleton pattern (parallel to ObservabilityConfig) allows
injection from the Kernel without threading the writer through pipeline.refine().

Epic 2.2B extension: maintains a DecisionTraceIndex sidecar, updated on the
drain worker's cadence (crash recovery) and rebuilt on close (completeness).

TCK-20260702-OBSISO-TRACE-ASYNC: write_trace() is a bounded in-memory enqueue
only (hot-path safety contract §3). The actual decision_trace.jsonl write and
DecisionTraceIndex.append_entry() call happen off-path on a private
QueueDrainWorker, following the same per-instance queue+worker pattern as
EventRecorder. See docs/guidelines/intentional_divergences.md for the
resulting bounded crash-loss and queue-overflow-drop windows.
"""
from __future__ import annotations

import json
import os
import logging
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from src.observability.config import ObservabilityConfig
from src.observability.cognition.tick_index import DecisionTraceIndex
from src.observability.queue import BoundedObservabilityQueue, QueueDrainWorker

logger = logging.getLogger(__name__)


@dataclass
class _DecisionTraceQueueItem:
    # Decision-trace entries carry no real priority semantics; this constant value exists
    # only to satisfy BoundedObservabilityQueue's shared severity-eviction interface.
    severity: str = "INFO"
    entry: Dict[str, Any] = field(default_factory=dict)


# Module-level active writer registry — set by Kernel at run start/end.
_active_writer: Optional["DecisionTraceWriter"] = None


def set_active_writer(writer: Optional["DecisionTraceWriter"]) -> None:
    """Register (or clear) the run-scoped DecisionTraceWriter singleton."""
    global _active_writer
    _active_writer = writer


def get_active_writer() -> Optional["DecisionTraceWriter"]:
    """Return the currently active DecisionTraceWriter, or None."""
    return _active_writer


class DecisionTraceWriter:
    """
    Writes per-entity scored route traces to decision_trace.jsonl in LIGHT+ modes.

    Lifecycle: one instance per run, created by the Kernel alongside the
    cognition recorder. File is opened lazily on first write (append mode)
    so an empty file is never created for runs with no eligible heroes.
    """

    def __init__(self, run_dir: str) -> None:
        self._path = os.path.join(run_dir, "decision_trace.jsonl")
        self._file = None
        self._index = DecisionTraceIndex(run_dir)
        # Cache of top-3 goal scores per entity from the most recent write_trace() call.
        # Schema: {entity_id: [{"goal_id": str, "score": float, "rank": int}, ...]}
        self._latest_goal_scores: Dict[int, List[Dict[str, Any]]] = {}

        self._queue = BoundedObservabilityQueue(max_size=ObservabilityConfig.get_max_queue_size())
        self._worker = QueueDrainWorker(queue=self._queue, file_write_fn=self._write_entry_to_file)
        self._worker.start()

    def _ensure_open(self) -> None:
        if self._file is None:
            os.makedirs(os.path.dirname(self._path), exist_ok=True)
            self._file = open(self._path, "a", encoding="utf-8")

    def write_trace(
        self,
        entity_id: int,
        tick: int,
        scored_routes: List[Any],
    ) -> None:
        """
        Write top-5 scored routes for one entity at one tick.

        scored_routes is a list of AdventureRouteOption instances (already scored).
        The first entry is the selected route; remaining are rejected alternatives.
        Silently no-ops if OBS_DECISION_TRACE flag is disabled.
        """
        if not ObservabilityConfig.is_decision_trace_enabled():
            return

        if not scored_routes:
            return

        try:
            # Sort descending by score so winner is always at index 0.
            sorted_routes = sorted(scored_routes, key=lambda r: r.score, reverse=True)

            # Build top-3 goal-score list (winner + up to 2 runner-ups).
            top3 = sorted_routes[:3]
            goal_scores_list: List[Dict[str, Any]] = [
                {
                    "goal_id": r.family.value if hasattr(r.family, "value") else str(r.family),
                    "score": r.score,
                    "rank": i + 1,
                }
                for i, r in enumerate(top3)
            ]
            # Cache for EntityInspector queries between ticks.
            self._latest_goal_scores[entity_id] = goal_scores_list

            source_goal_score: Optional[float] = sorted_routes[0].score if sorted_routes else None
            # Runner-up scores are ranks 2 and 3 only (winner is captured in source_goal_score).
            runner_up_scores = goal_scores_list[1:]

            routes_payload = []
            for idx, r in enumerate(sorted_routes[:5]):
                routes_payload.append({
                    "route_kind": r.family.value if hasattr(r.family, "value") else str(r.family),
                    "score": r.score,
                    "urgency": getattr(r, "urgency", 0.0),
                    "benefit": getattr(r, "benefit_score", 0.0),
                    "personality_bias": getattr(r, "personality_bias", 0.0),
                    "confidence_bonus": getattr(r, "confidence_bonus", 0.0),
                    "risk_penalty": getattr(r, "risk_penalty", 0.0),
                    "blocker_penalty": getattr(r, "blocker_penalty", 0.0),
                    "selected": idx == 0,
                })
            entry = {
                "entity_id": entity_id,
                "tick": tick,
                "source_goal_score": source_goal_score,
                "runner_up_scores": runner_up_scores,
                "routes": routes_payload,
            }
            self._queue.try_push(_DecisionTraceQueueItem(entry=entry))
        except Exception:
            logger.exception("DecisionTraceWriter.write_trace failed (non-fatal)")

    def _write_entry_to_file(self, item: "_DecisionTraceQueueItem") -> None:
        self._ensure_open()
        offset = self._file.tell()
        self._file.write(json.dumps(item.entry) + "\n")
        self._file.flush()
        self._index.append_entry(item.entry["tick"], offset)

    def get_latest_goal_scores(self, entity_id: int) -> List[Dict[str, Any]]:
        """
        Return the top-3 goal scores from the most recent write_trace() call for
        the given entity.  Each entry: {"goal_id": str, "score": float, "rank": int}.
        Returns [] if no tick has been written yet for this entity.
        """
        return self._latest_goal_scores.get(entity_id, [])

    def close(self) -> None:
        """Stop the drain worker, flush remaining queued entries, close the file, rebuild the index sidecar."""
        if getattr(self, "_worker", None):
            self._worker.stop()

        try:
            remaining = self._queue.drain()
            for item in remaining:
                self._write_entry_to_file(item)
        except Exception:
            logger.exception("DecisionTraceWriter.close final queue drain failed (non-fatal)")

        if self._file is not None:
            try:
                self._file.close()
            except Exception:
                logger.exception("DecisionTraceWriter.close failed (non-fatal)")
            finally:
                self._file = None

        # Rebuild the index from the completed file to ensure a clean, complete sidecar
        # even if any incremental append_entry calls were missed during the run.
        try:
            self._index.rebuild()
        except Exception:
            logger.exception("DecisionTraceWriter.close index rebuild failed (non-fatal)")
