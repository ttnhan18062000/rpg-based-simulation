from __future__ import annotations

import time
import logging
import math
import threading
from concurrent.futures import ThreadPoolExecutor, Future
from typing import List, Dict, Any, Optional, Callable
from src.core.worker_protocol import WorkerPacket, WorkerResult
from src.core.updates import EntityUpdate

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
        
        # Track peak usage for the current tick (Operational Truth)
        self._inflight_count = 0  # Total (Active + Queued)
        self._active_count = 0    # Currently executing
        self._peak_active = 0
        self._peak_queued = 0

    def execute_batch(
        self, 
        packets: List[WorkerPacket], 
        worker_fn: Callable[[WorkerPacket], WorkerResult],
        force_local: bool = False,
        concurrency_limit: float = 1.0
    ) -> List[WorkerResult]:
        """
        Execute a batch of worker packets.
        M8 Law: If queue is full, fall back to synchronous execution.
        Adaptive Cap: Parallelism is capped by concurrency_limit * max_workers.
        """
        if self._pool is None or force_local:
            return self._execute_locally(packets, worker_fn)

        results: List[WorkerResult] = []
        futures: List[Future] = []
        
        # Effective concurrency cap for this batch
        effective_cap = max(1, math.ceil(self._max_workers * concurrency_limit))
        # We use a local semaphore to throttle submission to the executor.
        throttle = threading.Semaphore(effective_cap)
        for packet in packets:
            # Check if we are over the queue limit
            # This is a simple heuristic: if we have more packets than depth, 
            # execute the remainder locally.
            if self._inflight_count >= self._max_queue_depth:
                results.append(self._wrap_work(packet, worker_fn))
            else:
                try:
                    self._inflight_count += 1
                    # Total pressure peak
                    queued_now = max(0, self._inflight_count - self._max_workers)
                    self._peak_queued = max(self._peak_queued, queued_now)
                    
                    # Throttle parallelism before submission
                    throttle.acquire()
                    
                    def throttled_work(p=packet, f=worker_fn, t=throttle):
                        try:
                            return self._wrap_work(p, f)
                        finally:
                            t.release()

                    future = self._pool.submit(throttled_work)
                    futures.append(future)
                except Exception as e:
                    logger.error("Worker submission failed: %s. Falling back.", e)
                    results.append(self._wrap_work(packet, worker_fn))
                    self._inflight_count -= 1

        # Collect results from futures
        for future in futures:
            try:
                result = future.result()
                results.append(result)
            except Exception as e:
                from src.core.worker_protocol import ResultStatus
                logger.error("Unexpected worker future failure: %s", e)
                # This should be rare if _wrap_work is doing its job, but we must protect the batch.
                # However, we don't have the packet here easily. 
                # Actually, future results are collected in order of submission if we want,
                # but futures list might not be 1:1 if some failed submission.
                # This is a safety net.
                pass
            finally:
                self._inflight_count -= 1

        # M8 Law: Deterministic Equivalence. 
        # Removal of opportunistic sorting; Kernel owns authoritative commit order.
        return results

    def _execute_locally(
        self, 
        packets: List[WorkerPacket], 
        worker_fn: Callable[[WorkerPacket], WorkerResult]
    ) -> List[WorkerResult]:
        """Strictly synchronous execution fallback."""
        return [self._wrap_work(p, worker_fn) for p in packets]

    def _wrap_work(self, packet: WorkerPacket, fn: Callable) -> WorkerResult:
        """Helper to capture compute time and handle errors inside the pool."""
        from src.core.worker_protocol import ResultStatus
        self._active_count += 1
        self._peak_active = max(self._peak_active, self._active_count)
        
        start = time.perf_counter_ns()
        try:
            result = fn(packet)
            elapsed = time.perf_counter_ns() - start
            # Add compute time to metadata
            if isinstance(result, WorkerResult):
                result = WorkerResult(
                    source_packet_id=result.source_packet_id,
                    work_id=result.work_id,
                    entity_id=result.entity_id,
                    work_class=result.work_class,
                    update=result.update,
                    status=result.status,
                    compute_time_ns=elapsed
                )
            return result
        except Exception as e:
            logger.error("Internal worker crash: %s", e)
            return WorkerResult(
                source_packet_id=packet.packet_id,
                work_id=packet.work_id,
                entity_id=packet.subject.id,
                work_class=packet.work_class,
                update=EntityUpdate(entity_id=packet.subject.id), # No-op
                status=ResultStatus.FAILURE
            )
        finally:
            self._active_count -= 1

    def get_stats(self) -> Dict[str, Any]:
        """
        Produce a read-only snapshot of worker statistics.
        M7 Law: This is the authoritative way for observability to read pressure.
        """
        # Capacity utilization is PEAK active workers in this tick.
        worker_utilization = (
            self._peak_active / self._max_workers 
            if self._max_workers > 0 else 1.0
        )
        
        # Queue utilization is PEAK depth observed relative to limit.
        queue_utilization = (
            self._peak_queued / self._max_queue_depth
            if self._max_queue_depth > 0 else 1.0
        )
        
        return {
            "capacity_utilization": worker_utilization,
            "worker_utilization": worker_utilization,
            "queue_utilization": queue_utilization,
            "active_workers": self._active_count,
            "peak_workers": self._peak_active,
            "peak_queued": self._peak_queued,
            "max_capacity": self._max_workers
        }

    def reset_tick_stats(self) -> None:
        """Reset peak counters for the next tick window."""
        self._peak_active = 0
        self._peak_queued = 0

    def shutdown(self) -> None:
        """Gracefully terminate the pool."""
        if self._pool:
            self._pool.shutdown(wait=True)
            self._pool = None
