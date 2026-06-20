"""
src/observability/cognition/decision_trace_writer.py
───────────────────────────────────────────────────────────────────────────────
Decision Trace Writer — Epic 2.2A.

Writes per-entity scored adventure route traces to decision_trace.jsonl in
LIGHT and above observability modes. Wired into AdventureDecisionPhase.apply()
after scoring completes. Does NOT modify execute_brain() in any way.

Module-level singleton pattern (parallel to ObservabilityConfig) allows
injection from the Kernel without threading the writer through pipeline.refine().

Epic 2.2B extension: maintains a DecisionTraceIndex sidecar updated
incrementally on each write (crash recovery) and rebuilt on close (completeness).
"""
from __future__ import annotations

import json
import os
import logging
from typing import Any, List, Optional

from src.observability.config import ObservabilityConfig
from src.observability.cognition.tick_index import DecisionTraceIndex

logger = logging.getLogger(__name__)

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
            self._ensure_open()
            offset = self._file.tell()
            routes_payload = []
            for idx, r in enumerate(scored_routes[:5]):
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
                "routes": routes_payload,
            }
            self._file.write(json.dumps(entry) + "\n")
            self._file.flush()
            # Incremental index update: record first offset for this tick (crash recovery).
            self._index.append_entry(tick, offset)
        except Exception:
            logger.exception("DecisionTraceWriter.write_trace failed (non-fatal)")

    def close(self) -> None:
        """Close the underlying file handle and rebuild the tick index sidecar."""
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
