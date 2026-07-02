import time
import threading
from enum import Enum
from typing import Optional, List, Dict, Any, Callable
from src.observability.events import ObservabilityEventEnvelope
from src.observability.config import ObservabilityConfig

class PushStatus(str, Enum):
    SUCCESS = "SUCCESS"
    DROPPED = "DROPPED"
    REJECTED = "REJECTED"


class BoundedObservabilityQueue:
    """
    Thread-safe, bounded queue for raw simulation events.
    Never blocks the engine tick; drops low-priority events under high queue pressure.
    """
    def __init__(self, max_size: int = 1000) -> None:
        self.max_size = max_size
        self._queue: List[ObservabilityEventEnvelope] = []
        self._lock = threading.Lock()
        
        # Operational metric registers
        self.dropped_count = 0
        self.pushed_count = 0

    def try_push(self, event: ObservabilityEventEnvelope) -> PushStatus:
        """
        Attempt to push an event into the queue thread-safely.
        If the queue is full:
          - If the event is high priority (CRITICAL/ERROR), drops an existing low-priority event (DEBUG/INFO/WARNING).
          - If the event is low priority, drops it immediately.
        Never blocks execution.
        """
        with self._lock:
            # If we have space, insert directly
            if len(self._queue) < self.max_size:
                self._queue.append(event)
                self.pushed_count += 1
                return PushStatus.SUCCESS
                
            # Queue is full, check priority
            is_high_priority = event.severity in ("CRITICAL", "ERROR")
            if not is_high_priority:
                # Drop new low-priority event
                self.dropped_count += 1
                return PushStatus.DROPPED
                
            # High priority event needs room. Scan for a low-priority event to evict
            low_priority_idx = -1
            for idx, item in enumerate(self._queue):
                if item.severity in ("DEBUG", "INFO", "WARNING"):
                    low_priority_idx = idx
                    break
                    
            if low_priority_idx != -1:
                # Evict the low priority event
                self._queue.pop(low_priority_idx)
                self._queue.append(event)
                self.dropped_count += 1
                self.pushed_count += 1
                return PushStatus.SUCCESS
            else:
                # Even if the queue consists entirely of high-priority events, reject new high-priority
                self.dropped_count += 1
                return PushStatus.REJECTED

    def drain(self) -> List[ObservabilityEventEnvelope]:
        """
        Drain all events from the queue thread-safely for writing or consumption.
        """
        with self._lock:
            drained = list(self._queue)
            self._queue.clear()
            return drained

    def get_size(self) -> int:
        with self._lock:
            return len(self._queue)

    def is_full(self) -> bool:
        with self._lock:
            return len(self._queue) >= self.max_size


class QueueDrainWorker:
    """
    A daemon worker thread that drains BoundedObservabilityQueue and dispatches
    events asynchronously.
    """
    def __init__(
        self,
        queue: BoundedObservabilityQueue,
        file_write_fn: Optional[Callable[[ObservabilityEventEnvelope], None]] = None,
        stream_publish_fn: Optional[Callable[[ObservabilityEventEnvelope], None]] = None,
        quality_fn: Optional[Callable[[ObservabilityEventEnvelope], None]] = None,
        interval_sec: float = 0.01
    ) -> None:
        self.queue = queue
        self.file_write_fn = file_write_fn
        self.stream_publish_fn = stream_publish_fn
        self.quality_fn = quality_fn
        self.interval_sec = interval_sec
        self.running = False
        self._thread: Optional[threading.Thread] = None
        self.health_status = "HEALTHY"
        self.failure_count = 0

    def start(self) -> None:
        if self.running:
            return
        self.running = True
        self._thread = threading.Thread(target=self._run, daemon=True, name="observability-drain-worker")
        self._thread.start()

    def is_alive(self) -> bool:
        return self._thread is not None and self._thread.is_alive()

    def stop(self) -> None:
        self.running = False
        if self._thread:
            self._thread.join(timeout=1.0)
            self._thread = None

    def _run(self) -> None:
        while self.running:
            try:
                envelopes = self.queue.drain()
                for env in envelopes:
                    if self.file_write_fn:
                        try:
                            self.file_write_fn(env)
                        except Exception:
                            self.failure_count += 1
                            self.health_status = "DEGRADED"
                            
                    if self.stream_publish_fn:
                        try:
                            self.stream_publish_fn(env)
                        except Exception:
                            self.failure_count += 1
                            self.health_status = "DEGRADED"
                    if self.quality_fn:
                        try:
                            self.quality_fn(env)
                        except Exception:
                            self.failure_count += 1
                            self.health_status = "DEGRADED"
                time.sleep(self.interval_sec)
            except Exception:
                self.failure_count += 1
                self.health_status = "DEGRADED"
                time.sleep(self.interval_sec)


_global_queue: Optional[BoundedObservabilityQueue] = None
_queue_lock = threading.Lock()

_global_worker: Optional[QueueDrainWorker] = None
_global_worker_lock = threading.Lock()


def get_observability_queue() -> BoundedObservabilityQueue:
    global _global_queue
    with _queue_lock:
        if _global_queue is None:
            max_size = ObservabilityConfig.get_max_queue_size()
            _global_queue = BoundedObservabilityQueue(max_size=max_size)
        return _global_queue


def get_or_start_global_worker(queue: BoundedObservabilityQueue) -> QueueDrainWorker:
    """Return the active global drain worker, starting a new one if none is alive.

    Double-checked: the lock is held for the full check-and-start sequence so
    concurrent callers cannot each observe None and each start a worker.
    """
    global _global_worker
    with _global_worker_lock:
        if _global_worker is None or not _global_worker.is_alive():
            worker = QueueDrainWorker(queue=queue)
            worker.start()
            _global_worker = worker
        return _global_worker


def get_active_global_worker_count() -> int:
    """Return 1 if the global drain worker is alive, 0 otherwise."""
    return 1 if (_global_worker is not None and _global_worker.is_alive()) else 0
