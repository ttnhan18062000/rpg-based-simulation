"""
EntityBehaviorTimeline & BehaviorTimelineStore — Phase 23 timeline components.
"""
from __future__ import annotations
import threading
from dataclasses import dataclass
from typing import Optional, Dict, List
from src.observability.behavior.behavior_event import BehaviorEvent


@dataclass(frozen=True)
class EntityBehaviorTimeline:
    """
    Immutable representation of an entity's chronological behavior history.
    """
    run_id: str
    entity_id: int
    events: tuple[BehaviorEvent, ...]
    dropped_count: int = 0
    start_tick: Optional[int] = None
    end_tick: Optional[int] = None


class BehaviorTimelineStore:
    """
    Thread-safe, bounded, memory-safe store for in-process BehaviorEvent logging.
    """
    def __init__(self, capacity_per_entity: int = 500) -> None:
        self.capacity = capacity_per_entity
        self._store: Dict[int, List[BehaviorEvent]] = {}
        self._dropped: Dict[int, int] = {}
        self._lock = threading.Lock()

    def record(self, event: BehaviorEvent) -> None:
        if event.entity_id is None:
            return
        with self._lock:
            eid = event.entity_id
            if eid not in self._store:
                self._store[eid] = []
                self._dropped[eid] = 0
            
            buf = self._store[eid]
            if len(buf) >= self.capacity:
                buf.pop(0)
                self._dropped[eid] += 1
            buf.append(event)

    def get_entity_timeline(self, run_id: str, entity_id: int) -> EntityBehaviorTimeline:
        with self._lock:
            events = tuple(self._store.get(entity_id, []))
            dropped = self._dropped.get(entity_id, 0)
            
            start_tick = events[0].tick if events else None
            end_tick = events[-1].tick if events else None
            
            return EntityBehaviorTimeline(
                run_id=run_id,
                entity_id=entity_id,
                events=events,
                dropped_count=dropped,
                start_tick=start_tick,
                end_tick=end_tick
            )
