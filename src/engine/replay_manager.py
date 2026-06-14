from __future__ import annotations

import dataclasses
import json
import time
from pathlib import Path
from typing import List, Dict, Any, Optional, TYPE_CHECKING

from src.certification.artifact_budget import get_default_registry
from src.config.optimization_profiles import SubsystemBudget, SubsystemPressureReport, DEFAULT_REPLAY_BUDGET
from src.core.diagnostic import TraceEvent
from src.engine.replay_buffer import ReplayBuffer
from src.engine.replay_sink import ReplaySink
from src.core.replay_modes import ReplayMode

from concurrent.futures import ThreadPoolExecutor
import logging
import threading
if TYPE_CHECKING:
    from src.engine.policy import GovernorPolicy

logger = logging.getLogger(__name__)


class ReplayManager:
    """
    Orchestrator for streaming replay and bounded persistence.
    M6 Law: Replay management is non-blocking and respects resource bounds.
    """

    def __init__(
        self,
        run_dir: Path,
        profile_name: str,
        buffer_capacity_kb: int = 1024,
        chunk_tick_limit: int = 100,
        replay_mode: ReplayMode = ReplayMode.DEBUG_WINDOWED,
        rotation_threshold: float = 0.9
    ):
        self._run_dir = run_dir
        self._profile_name = profile_name

        # M6 Law: Mode-specific retention policy
        from src.core.retention import OverflowPolicy
        policy = OverflowPolicy.EVICT_OLDEST
        if replay_mode == ReplayMode.FORENSIC_SHORT_RUN:
            policy = OverflowPolicy.TRUNCATE_NEWEST

        self._buffer = ReplayBuffer(buffer_capacity_kb, policy)
        self._sink = ReplaySink(run_dir)

        self._chunk_tick_limit = chunk_tick_limit
        self._rotation_threshold = rotation_threshold
        self._current_chunk_id = 0
        self._chunk_start_tick = 0

        self._manifest: Dict[str, Any] = {
            "profile": profile_name,
            "mode": str(replay_mode),
            "start_time": time.time(),
            "chunks": [],
            "status": "IN_PROGRESS"
        }

        # M7 Law: Replay IO MUST NOT block the kernel heart-beat.
        # Background executor for non-blocking persistence.
        self._executor = ThreadPoolExecutor(max_workers=1)
        self._manifest_lock = threading.Lock()
        # Advisory only — plain int, no lock needed; slight race is acceptable
        # for pressure signal.  Incremented inside _execute_persistence() on
        # success only; read lock-free by pressure_report().
        self._chunks_persisted: int = 0

    def emit(self, event: TraceEvent, policy: GovernorPolicy) -> None:
        """
        Emit an event for capture.
        M6 Law: Respect richness policy and non-blocking staging.
        """
        if not policy.replay_allowed:
            return

        # Filtering based on richness
        if policy.replay_richness == "MINIMAL":
            # Only allow Entity Actions or Auth Periodic (simplified check)
            if event.system not in ("KERNEL", "ENTITY"):
                return

        if not policy.allow_subsystem_traces:
            if event.system not in ("KERNEL", "ENTITY"):
                return

        # Explicit non-blocking record
        self._buffer.record(event)

    def on_tick_end(self, current_tick: int) -> None:
        """
        Check for deterministic or pressure-based chunk rotation.
        """
        # 1. Time/Tick based rotation
        ticks_in_chunk = current_tick - self._chunk_start_tick
        if ticks_in_chunk >= self._chunk_tick_limit:
            self._rotate_chunk(current_tick)
            return

        # 2. Saturation based early rotation (M6 Law)
        stats = self.get_stats()
        if stats["buffer_utilization"] >= self._rotation_threshold:
            self._rotate_chunk(current_tick)

    def finalize(self, timeout_s: float = 5.0) -> LifecycleOutcome:
        """
        Finalize the run and write the manifest.
        M7 Law: Bounded non-authoritative flush budget.
        Pre-emptive timeout enforcement: Skip flush if near budget.
        """
        from src.core.lifecycle import LifecycleOutcome
        start_finalize = time.perf_counter()

        # Shutdown background executor and WAIT for pending flushes
        # M7 Law: Bounded non-authoritative flush budget.
        # Note: ThreadPoolExecutor.shutdown does not support timeout in standard Python.
        self._executor.shutdown(wait=True)

        outcome = LifecycleOutcome.SUCCESS
        try:
            # M7 Law: Establish a safety margin for the manifest write itself.
            manifest_safety_margin = 0.5  # 500ms

            # Step 1: Pre-emptive budget check for the final rotation
            elapsed = time.perf_counter() - start_finalize
            remaining = timeout_s - elapsed

            if remaining > manifest_safety_margin + 0.1:
                # We have enough budget to attempt a final rotation
                # Note: This one can be synchronous as the kernel is shutting down
                self._rotate_chunk(self._chunk_start_tick, async_write=False)
                self._manifest["status"] = "COMPLETED"
            else:
                logger.warning("Replay finalize: Skipping final rotation due to insufficient budget (Remaining: %.3fs)", remaining)
                self._manifest["status"] = "SKIPPED_TIMEOUT"
                outcome = LifecycleOutcome.SKIPPED

            # Step 2: Final post-fact check
            if time.perf_counter() - start_finalize > timeout_s:
                self._manifest["status"] = "TIMEOUT"
                outcome = LifecycleOutcome.TIMEOUT

        except Exception as e:
            logger.error("Replay finalize failed: %s", e)
            self._manifest["status"] = "FAILED"
            outcome = LifecycleOutcome.FAILED

        self._manifest["end_time"] = time.time()
        self._manifest["metrics"] = {
            "bytes_written": self._sink.metrics.bytes_written,
            "chunks_persisted": self._sink.metrics.chunks_persisted,
            "dropped_events": self.get_stats()["dropped_events_count"]
        }

        # M7 Law: Atomic Manifest Update (Write then Rename)
        with self._manifest_lock:
            self._sink.write_manifest(self._manifest)
        return outcome

    def _rotate_chunk(self, end_tick: int, async_write: bool = True) -> None:
        """Move staged events from buffer to a durable chunk."""
        events = self._buffer.extract_chunk()
        if not events:
            return

        # INFRA-193: Budget check before dispatch (synchronous, caller thread).
        # Never raise here — async thread path cannot safely propagate exceptions (INFRA-060 / M6 Law).
        try:
            def _to_dict(e):
                if isinstance(e, dict):
                    return e
                if dataclasses.is_dataclass(e) and not isinstance(e, type):
                    return dataclasses.asdict(e)
                if hasattr(e, '__dict__'):
                    return e.__dict__
                return str(e)

            estimated_bytes = len(
                json.dumps([_to_dict(e) for e in events], default=str).encode()
            )
            _bcheck = get_default_registry().check("replay_chunk", estimated_bytes)
            if _bcheck.action in ("warn", "reject"):
                logger.warning(
                    "ReplayManager: budget %s for replay_chunk — size=%.2f MB reason=%s",
                    _bcheck.action,
                    estimated_bytes / 1048576,
                    _bcheck.reason,
                )
        except Exception as _budget_err:
            # Budget check must never stall the replay pipeline (INFRA-060).
            logger.debug("ReplayManager: budget check skipped: %s", _budget_err)

        if async_write:
            # Submit to background thread to satisfy M7 "Non-blocking" Law
            # M6 Law: Capture metadata snapshot to prevent race with next tick
            self._executor.submit(
                self._execute_persistence,
                self._current_chunk_id,
                self._chunk_start_tick,
                end_tick,
                events
            )
        else:
            # Synchronous path for shutdown or small-scale tests
            self._execute_persistence(
                self._current_chunk_id,
                self._chunk_start_tick,
                end_tick,
                events
            )

        self._current_chunk_id += 1
        self._chunk_start_tick = end_tick + 1

    def _execute_persistence(
        self,
        chunk_id: int,
        start_tick: int,
        end_tick: int,
        events: List[TraceEvent]
    ) -> None:
        """Authoritative persistence handler (runs in background thread)."""
        try:
            success = self._sink.persist_chunk(chunk_id, events)

            if success:
                with self._manifest_lock:
                    self._manifest["chunks"].append({
                        "id": chunk_id,
                        "start_tick": start_tick,
                        "end_tick": end_tick,
                        "event_count": len(events)
                    })
                    # Atomic manifest write
                    self._sink.write_manifest(self._manifest)
                # Advisory only — plain int, no lock needed (see __init__ comment).
                self._chunks_persisted += 1
        except Exception as e:
            # M6 Law: Non-authoritative fallback. Failure must not stall.
            logger.error("Background persistence failed: %s", e)

    @property
    def metrics(self):
        return self._sink.metrics

    def pressure_report(self, budget: SubsystemBudget | None = None) -> SubsystemPressureReport:
        """
        Return an advisory pressure snapshot for the replay subsystem.

        Non-blocking and read-only — must never be called on the kernel tick
        hot path.  The inflight count is derived from _current_chunk_id minus
        _chunks_persisted; both are plain ints read without a lock (advisory
        accuracy is acceptable for a pressure signal).

        degradation_action is a string description consumed by the Governor;
        ReplayManager does not execute it.
        """
        budget = budget or DEFAULT_REPLAY_BUDGET
        # Lock-free advisory snapshot.
        inflight = max(0, self._current_chunk_id - self._chunks_persisted)
        max_f = budget.max_inflight_chunks
        if max_f is None:
            return SubsystemPressureReport(
                subsystem="replay",
                current_usage=float(inflight),
                budget=None,
                pressure_state="OK",
                degradation_action=None,
            )
        pct = inflight / max_f
        if pct < 0.8:
            state, action = "OK", None
        elif pct < 1.0:
            state, action = "WARN", "reduce_replay_richness"
        else:
            state, action = "DEGRADED", "disable_replay_capture"
        return SubsystemPressureReport(
            subsystem="replay",
            current_usage=float(inflight),
            budget=float(max_f),
            pressure_state=state,
            degradation_action=action,
        )

    def get_stats(self) -> Dict[str, Any]:
        """
        Produce a read-only snapshot of replay statistics.
        M7 Law: This is the authoritative way for observability to read pressure.
        """
        buffer_stats = self._buffer.get_stats()

        return {
            "backlog_kb": buffer_stats["backlog_kb"],
            "buffer_utilization": (
                buffer_stats["backlog_kb"] / buffer_stats["capacity_kb"]
                if buffer_stats["capacity_kb"] > 0 else 0.0
            ),
            "dropped_events_count": buffer_stats["dropped_events_count"],
            "total_bytes_written": self._sink.metrics.bytes_written
        }
