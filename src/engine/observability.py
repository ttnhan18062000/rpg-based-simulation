from __future__ import annotations

import os
import time
import psutil
from dataclasses import dataclass, asdict
from collections import deque
from typing import Dict, Any, Optional, List
from src.core.governance import RuntimeMode


@dataclass(frozen=True)
class RuntimeSnapshot:
    """
    Law: Surfaced runtime signals must be stable in meaning and naming.
    This is the closed, typed operational surface for Milestone B.
    """
    profile_name: str
    runtime_mode: str
    
    # Primary Pressure Inputs
    memory_rss_mb: float
    memory_trend_mb_per_tick: float
    tick_compute_ms_avg: float
    work_debt_total: int
    worker_utilization: float
    queue_utilization: float
    replay_backlog_kb: int
    
    # Outcome Accounting
    active_workers: int
    dropped_work_count: int      # Autoritative work shed by governor
    replay_dropped_events: int   # Non-authoritative events lost due to buffer pressure
    uptime_seconds: float
    last_tick: int


class SignalCollector:
    """
    Responsible for platform-level sampling and trend calculation.
    M7 Law: Platform sampling must stay within budget.
    """

    def __init__(self, profile_name: str, sampling_interval: int = 10):
        self._profile_name = profile_name
        self._sampling_interval = sampling_interval
        self._process = psutil.Process(os.getpid())
        self._start_time = time.perf_counter()
        
        # Last sampled RSS and Slope Window
        self._last_rss_mb = 0.0
        self._cached_rss_mb = 0.0
        
        # Trends (Moving Windows - Law: 5-sample window)
        self._rss_history: deque[float] = deque(maxlen=5)
        self._compute_ms_sum = 0.0
        self._sample_count = 0

    def collect_platform_signals(self, tick: int, interval_override: Optional[int] = None) -> Dict[str, float]:
        """
        Sample system resources if at interval boundary.
        M7 Law: RSS sampling is every N ticks by default.
        """
        interval = interval_override or self._sampling_interval
        
        if tick % interval == 0:
            try:
                # Real RSS sampling (Expensive)
                mem_info = self._process.memory_info()
                rss_mb = mem_info.rss / (1024 * 1024)
                
                # Update window
                self._rss_history.append(rss_mb)
                self._cached_rss_mb = rss_mb
                
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass

        # Calculate memory trend (slope of the last window)
        trend = 0.0
        if len(self._rss_history) >= 2:
            # Simple average delta over the samples we have
            deltas = [
                self._rss_history[i] - self._rss_history[i-1] 
                for i in range(1, len(self._rss_history))
            ]
            # Normalize by sampling interval (per-tick slope)
            trend = (sum(deltas) / len(deltas)) / interval

        return {
            "rss_mb": self._cached_rss_mb,
            "memory_trend": trend
        }

    def get_snapshot(self, kernel: Any) -> RuntimeSnapshot:
        """
        Produce a truthful snapshot of the engine's operational state.
        M7 Law: No placeholders. All data must be sourced from real behavior.
        """
        status = kernel.status
        profile = kernel._profile # Kernel law for Milestone B
        
        # 1. Primary Pressure: Platform (Respecting Profile Cadence)
        platform = self.collect_platform_signals(
            kernel.state.tick, 
            interval_override=profile.sampling_interval_ticks
        )
        
        # 2. Primary Pressure: Compute (from history)
        compute_avg = 0.0
        if status.signal_history:
            total_compute = sum(s.tick_compute_ms for s in status.signal_history)
            compute_avg = total_compute / len(status.signal_history)

        # 3. Primary Pressure: Subsystems (via explicit interfaces)
        worker_stats = kernel._worker_manager.get_stats()
        replay_stats = kernel._replay.get_stats()
        
        # 4. Primary Pressure: Authoritative State
        work_debt_total = sum(kernel.state.work_debt.values())

        return RuntimeSnapshot(
            profile_name=self._profile_name,
            runtime_mode=status.current_mode.name,
            memory_rss_mb=platform["rss_mb"],
            memory_trend_mb_per_tick=platform["memory_trend"],
            tick_compute_ms_avg=compute_avg,
            work_debt_total=work_debt_total,
            worker_utilization=worker_stats["worker_utilization"],
            queue_utilization=worker_stats["queue_utilization"],
            replay_backlog_kb=replay_stats["backlog_kb"],
            # Outcome Accounting
            active_workers=worker_stats["active_workers"],
            dropped_work_count=status.total_dropped_work,
            replay_dropped_events=replay_stats["dropped_events_count"],
            uptime_seconds=time.perf_counter() - self._start_time,
            last_tick=kernel.state.tick
        )
