from __future__ import annotations

import time
import logging
from concurrent.futures import ThreadPoolExecutor, Future
from typing import List, Dict, Any, Optional, Callable
from src_v2.core.worker_protocol import WorkerPacket, WorkerResult
from src_v2.core.updates import EntityUpdate

logger = logging.getLogger(__name__)


class WorkerManager:
    """
    Law: Concurrency must be bounded and profile-controlled. (M8 Rule 6)
    Orchestrates execution across a thread pool with deterministic local fallback.
    """

    def __init__(self, max_workers: int = 1, max_queue_depth: int = 100):
        self._max_workers = max_workers
        self._max_queue_depth = max_queue_depth
        
        # Initialize pool only if workers > 0
        self._pool = (ThreadPoolExecutor(max_workers=max_workers) 
                      if max_workers > 0 else None)
        
        # Track inflight counts for backpressure
        self._inflight_count = 0

    def execute_batch(
        self, 
        packets: List[WorkerPacket], 
        worker_fn: Callable[[WorkerPacket], WorkerResult],
        force_local: bool = False
    ) -> List[WorkerResult]:
        """
        Execute a batch of worker packets.
        M8 Law: If queue is full, fall back to synchronous execution.
        """
        if self._pool is None or force_local:
            return self._execute_locally(packets, worker_fn)

        results: List[WorkerResult] = []
        futures: List[Future] = []
        
        # Submission with backpressure
        for packet in packets:
            # Check if we are over the queue limit
            # This is a simple heuristic: if we have more packets than depth, 
            # execute the remainder locally.
            if self._inflight_count >= self._max_queue_depth:
                results.append(worker_fn(packet))
            else:
                try:
                    self._inflight_count += 1
                    future = self._pool.submit(self._wrap_work, packet, worker_fn)
                    futures.append(future)
                except Exception as e:
                    logger.error("Worker submission failed: %s. Falling back.", e)
                    results.append(worker_fn(packet))
                    self._inflight_count -= 1

        # Collect results from futures
        for future in futures:
            try:
                result = future.result()
                results.append(result)
            except Exception as e:
                logger.error("Worker execution failed: %s", e)
            finally:
                self._inflight_count -= 1

        # M8 Law: Deterministic Equivalence. 
        # Results must be sorted by Entity ID before returning to ensure 
        # identical application order regardless of thread race.
        results.sort(key=lambda r: r.entity_id)
        return results

    def _execute_locally(
        self, 
        packets: List[WorkerPacket], 
        worker_fn: Callable[[WorkerPacket], WorkerResult]
    ) -> List[WorkerResult]:
        """Strictly synchronous execution fallback."""
        results = [worker_fn(p) for p in packets]
        results.sort(key=lambda r: r.entity_id)
        return results

    def _wrap_work(self, packet: WorkerPacket, fn: Callable) -> WorkerResult:
        """Helper to capture compute time and handle errors inside the pool."""
        start = time.perf_counter_ns()
        try:
            result = fn(packet)
            elapsed = time.perf_counter_ns() - start
            # Add compute time to metadata
            if isinstance(result, WorkerResult):
                result = WorkerResult(
                    entity_id=result.entity_id,
                    update=result.update,
                    compute_time_ns=elapsed
                )
            return result
        except Exception as e:
            logger.error("Internal worker crash: %s", e)
            return WorkerResult(
                entity_id=packet.subject.id,
                update=EntityUpdate(entity_id=packet.subject.id, readiness_delta=0.0) # No-op
            )

    def shutdown(self) -> None:
        """Gracefully terminate the pool."""
        if self._pool:
            self._pool.shutdown(wait=True)
            self._pool = None
