from __future__ import annotations

import time
from pathlib import Path
from typing import List, Dict, Any, Optional, TYPE_CHECKING
from src_v2.core.diagnostic import TraceEvent
from src_v2.engine.replay_buffer import ReplayBuffer
from src_v2.engine.replay_sink import ReplaySink
from src_v2.core.replay_modes import ReplayMode

if TYPE_CHECKING:
    from src_v2.engine.policy import GovernorPolicy


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
        chunk_tick_limit: int = 100
    ):
        self._run_dir = run_dir
        self._profile_name = profile_name
        self._buffer = ReplayBuffer(buffer_capacity_kb)
        self._sink = ReplaySink(run_dir)
        
        self._chunk_tick_limit = chunk_tick_limit
        self._current_chunk_id = 0
        self._chunk_start_tick = 0
        
        self._manifest: Dict[str, Any] = {
            "profile": profile_name,
            "start_time": time.time(),
            "chunks": [],
            "status": "IN_PROGRESS"
        }

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
        Check for deterministic chunk rotation at tick boundary.
        """
        ticks_in_chunk = current_tick - self._chunk_start_tick
        
        if ticks_in_chunk >= self._chunk_tick_limit:
            self._rotate_chunk(current_tick)

    def finalize(self) -> None:
        """Finalize the run and write the manifest."""
        # M7 Law: Hard Timeout for Non-Authoritative Flush
        # Since this is single-threaded, we can't easily kill an IO thread, 
        # but we can check if it's taking too long between chunks if we had many.
        try:
            self._rotate_chunk(self._chunk_start_tick)
        except Exception:
            pass

        self._manifest["status"] = "COMPLETED"
        self._manifest["end_time"] = time.time()
        self._manifest["metrics"] = {
            "bytes_written": self._sink.metrics.bytes_written,
            "chunks_persisted": self._sink.metrics.chunks_persisted
        }
        self._sink.write_manifest(self._manifest)

    def _rotate_chunk(self, end_tick: int) -> None:
        """Move staged events from buffer to a durable chunk."""
        events = self._buffer.extract_chunk()
        if not events:
            return

        try:
            success = self._sink.persist_chunk(self._current_chunk_id, events)
            
            if success:
                self._manifest["chunks"].append({
                    "id": self._current_chunk_id,
                    "start_tick": self._chunk_start_tick,
                    "end_tick": end_tick,
                    "event_count": len(events)
                })
                # Immediate write of manifest for resilience
                self._sink.write_manifest(self._manifest)
        except Exception:
            # M6 Law: Non-authoritative fallback. Failure must not stall.
            pass
            
        self._current_chunk_id += 1
        self._chunk_start_tick = end_tick + 1

    @property
    def metrics(self):
        return self._sink.metrics
