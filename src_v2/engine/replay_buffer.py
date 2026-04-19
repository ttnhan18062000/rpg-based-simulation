from __future__ import annotations

from typing import List, Optional, Collection
from src_v2.core.retention import BoundedBuffer, OverflowPolicy
from src_v2.core.diagnostic import TraceEvent


class ReplayBuffer:
    """
    A policy-bound staging area for simulation forensics.
    M6 Law: Replay staging remains within declared memory bounds. 
    Implements non-blocking emission with explicit overflow handling.
    """

    def __init__(self, capacity_kb: int, policy: OverflowPolicy = OverflowPolicy.EVICT_OLDEST):
        # Rough estimate: each TraceEvent is ~256 bytes (0.25 KB)
        # So capacity in items is roughly capacity_kb * 4.
        self._item_capacity = max(1, capacity_kb * 4)
        self._buffer: BoundedBuffer[TraceEvent] = BoundedBuffer(
            capacity=self._item_capacity,
            policy=policy
        )
        self._dropped_events = 0

    def record(self, event: TraceEvent) -> bool:
        """
        Add an event to the staging buffer.
        M6 Law: This MUST NOT block kernel execution.
        """
        kept = self._buffer.append(event)
        if not kept:
            self._dropped_events += 1
        return kept

    def extract_chunk(self) -> List[TraceEvent]:
        """
        Extract ALL currently staged events and clear the buffer.
        Used by the ReplayManager during chunk rotation.
        """
        events = self._buffer.to_list()
        self._buffer.clear()
        # Reset dropped count per chunk? 
        # Actually better to keep it cumulative for the snapshot, 
        # but extract_chunk might want to know how many were lost in THIS chunk.
        return events

    @property
    def item_count(self) -> int:
        return len(self._buffer)

    @property
    def capacity_kb(self) -> int:
        return self._item_capacity // 4

    def get_stats(self) -> Dict[str, Any]:
        """Produce a read-only snapshot of buffer state."""
        # Estimate: each item is ~256 bytes (0.25 KB)
        backlog_kb = len(self._buffer) * 0.25
        return {
            "backlog_kb": backlog_kb,
            "item_count": len(self._buffer),
            "capacity_kb": self.capacity_kb,
            "dropped_events_count": self._dropped_events
        }
