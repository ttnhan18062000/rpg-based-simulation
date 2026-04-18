from __future__ import annotations

import os
import time
import psutil
from dataclasses import dataclass, asdict
from typing import Dict, Any, Optional, List
from src_v2.core.governance import RuntimeMode


@dataclass(frozen=True)
class RuntimeSnapshot:
    """
    Law: Surfaced runtime signals must be stable in meaning and naming.
    This is the closed, typed operational surface for Milestone 7.
    """
    profile_name: str
    runtime_mode: str
    memory_rss_mb: float
    memory_trend_mb_per_tick: float
    tick_compute_ms_avg: float
    work_debt_total: int
    queue_utilization: float
    dropped_work_count: int
    replay_backlog_kb: int
    active_workers: int
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
        
        # Last sampled RSS
        self._last_rss_mb = 0.0
        self._cached_rss_mb = 0.0
        
        # Trends (Moving Averages)
        self._memory_delta_sum = 0.0
        self._compute_ms_sum = 0.0
        self._sample_count = 0

    def collect_platform_signals(self, tick: int) -> Dict[str, float]:
        """
        Sample system resources if at interval boundary.
        M7 Law: RSS sampling is every N ticks by default.
        """
        if tick % self._sampling_interval == 0:
            try:
                # Real RSS sampling (Expensive)
                mem_info = self._process.memory_info()
                rss_mb = mem_info.rss / (1024 * 1024)
                
                # Calculate trend if we have previous sample
                if self._last_rss_mb > 0:
                    delta = (rss_mb - self._last_rss_mb) / self._sampling_interval
                    self._memory_delta_sum += delta
                    self._sample_count += 1
                
                self._last_rss_mb = rss_mb
                self._cached_rss_mb = rss_mb
                
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass

        return {
            "rss_mb": self._cached_rss_mb,
            "memory_trend": (self._memory_delta_sum / self._sample_count 
                             if self._sample_count > 0 else 0.0)
        }

    def get_snapshot(self, kernel: Any) -> RuntimeSnapshot:
        """Derive a stable, typed snapshot from the current kernel state."""
        status = kernel.status
        replay = kernel.replay
        
        platform = self.collect_platform_signals(kernel.state.tick)
        
        # Calculate compute trend from status history
        compute_avg = 0.0
        if status.signal_history:
            total_compute = sum(s.tick_compute_ms for s in status.signal_history)
            compute_avg = total_compute / len(status.signal_history)

        return RuntimeSnapshot(
            profile_name=self._profile_name,
            runtime_mode=status.current_mode.name,
            memory_rss_mb=platform["rss_mb"],
            memory_trend_mb_per_tick=platform["memory_trend"],
            tick_compute_ms_avg=compute_avg,
            work_debt_total=kernel.state.work_debt_total if hasattr(kernel.state, "work_debt_total") else 0, # Placeholder
            queue_utilization=0.0, # Placeholder
            dropped_work_count=0,   # Placeholder
            replay_backlog_kb=replay.buffer_usage_kb if hasattr(replay, "buffer_usage_kb") else 0,
            active_workers=1,        # M6/M7 is single-threaded
            uptime_seconds=time.perf_counter() - self._start_time,
            last_tick=kernel.state.tick
        )
