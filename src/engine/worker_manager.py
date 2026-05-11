# Compliance IDs: INFRA-017
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
        # M10 Law: Protect stats with a lock to ensure thread-safety under high pressure.
        self._stats_lock = threading.Lock()
        self._inflight_count = 0  # Total (Waiting + Executing)
        self._active_count = 0    # Currently executing in a pool thread
        self._peak_active = 0
        self._peak_queued = 0

    def execute_batch(
        self, 
        packets: List[WorkerPacket], 
        worker_fn: Callable[[WorkerPacket], List[WorkerResult] | WorkerResult],
        force_local: bool = False,
        concurrency_limit: float = 1.0
    ) -> List[WorkerResult]:
        """
        Execute a batch of worker packets.
        M8 Law: If queue is full, fall back to synchronous execution.
        Adaptive Cap: Parallelism is capped by concurrency_limit * max_workers.
        """
        if self._pool is None or force_local:
            # Logic ID: INFRA-017 (Worker pool fallback to inline/local)
            return self._execute_locally(packets, worker_fn)

        results: List[WorkerResult] = []
        futures: List[Future] = []
        
        # Effective concurrency cap for this batch
        effective_cap = max(1, math.ceil(self._max_workers * concurrency_limit))
        # We use a local semaphore to throttle submission to the executor.
        throttle = threading.Semaphore(effective_cap)
        
        for packet in packets:
            with self._stats_lock:
                q_depth = self._inflight_count
            
            # Check if we are over the queue limit
            if q_depth >= self._max_queue_depth:
                # Force local execution for excess items (Pressure shedding)
                res = self._wrap_work(packet, worker_fn)
                if isinstance(res, list): results.extend(res)
                else: results.append(res)
            else:
                try:
                    with self._stats_lock:
                        self._inflight_count += 1
                        # Real queue depth is inflight minus what's capable of running
                        queued_now = max(0, self._inflight_count - effective_cap)
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
                    res = self._wrap_work(packet, worker_fn)
                    if isinstance(res, list): results.extend(res)
                    else: results.append(res)
                    with self._stats_lock:
                        self._inflight_count -= 1

        # Collect results from futures
        for future in futures:
            try:
                result = future.result()
                if isinstance(result, list):
                    results.extend(result)
                else:
                    results.append(result)
            except Exception as e:
                logger.error("Unexpected worker future failure: %s", e)
                pass
            finally:
                with self._stats_lock:
                    self._inflight_count -= 1

        return results

    def _execute_locally(
        self, 
        packets: List[WorkerPacket], 
        worker_fn: Callable[[WorkerPacket], List[WorkerResult] | WorkerResult]
    ) -> List[WorkerResult]:
        """Strictly synchronous execution fallback."""
        all_results = []
        for p in packets:
            res = self._wrap_work(p, worker_fn)
            if isinstance(res, list): all_results.extend(res)
            else: all_results.append(res)
        return all_results

    def _wrap_work(self, packet: WorkerPacket, fn: Callable) -> List[WorkerResult] | WorkerResult:
        """Helper to capture compute time and handle errors inside the pool."""
        from src.core.worker_protocol import ResultStatus
        
        with self._stats_lock:
            self._active_count += 1
            self._peak_active = max(self._peak_active, self._active_count)
        
        start = time.perf_counter_ns()
        try:
            result = fn(packet)
            elapsed = time.perf_counter_ns() - start
            from dataclasses import replace
            if isinstance(result, list):
                result = [replace(r, compute_time_ns=elapsed // len(result)) for r in result]
            elif isinstance(result, WorkerResult):
                result = replace(result, compute_time_ns=elapsed)
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
            with self._stats_lock:
                self._active_count -= 1

    def get_stats(self) -> Dict[str, Any]:
        """
        Produce a read-only snapshot of worker statistics.
        M7 Law: This is the authoritative way for observability to read pressure.
        """
        with self._stats_lock:
            peak_active = self._peak_active
            peak_queued = self._peak_queued
            active_now = self._active_count
            
        # Capacity utilization is PEAK active workers in this tick.
        # Hardened Mode (MB): Use max_workers as the denominator for relative pressure
        worker_utilization = (
            peak_active / self._max_workers 
            if self._max_workers > 0 else 1.0
        )
        
        # Queue utilization is PEAK depth observed relative to limit.
        queue_utilization = (
            peak_queued / self._max_queue_depth
            if self._max_queue_depth > 0 else 1.0
        )
        
        return {
            "worker_utilization": worker_utilization,
            "queue_utilization": queue_utilization,
            "active_workers": active_now,
            "peak_workers": peak_active,
            "peak_queued": peak_queued,
            "max_capacity": self._max_workers
        }

    def reset_tick_stats(self) -> None:
        """Reset peak counters for the next tick window."""
        with self._stats_lock:
            self._peak_active = 0
            self._peak_queued = 0

    def shutdown(self) -> None:
        """Gracefully terminate the pool."""
        if self._pool:
            self._pool.shutdown(wait=True)
            self._pool = None
