from __future__ import annotations
import os
import math
import logging
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

class MetricWindowRecord(BaseModel):
    """
    Standard schema for a simulation rolling metric tick window.
    """
    schema_version: str = Field(default="observability_metric_v1")
    run_id: str
    window_start_tick: int
    window_end_tick: int
    ticks_observed: int
    
    # Required core metrics
    alive_entities_avg: float
    active_entities_avg: float
    gold_total_avg: float
    tick_compute_ms_avg: float
    tick_compute_ms_p95: float
    memory_rss_bytes_avg: float
    memory_rss_bytes_max: float
    hard_law_violation_count: int
    event_count: int
    anomaly_candidate_count: int
    
    # Optional / extension metrics
    rejection_count: int = 0
    quest_active_count: float = 0.0
    quest_completed_count: float = 0.0
    governor_mode_dominant: str = "NORMAL"
    worker_utilization_avg: float = 0.0
    queue_utilization_avg: float = 0.0

class MetricWindowAccumulator:
    """
    Accumulates per-tick snapshots to calculate rolling window statistics.
    """
    def __init__(self, run_id: str, window_start_tick: int) -> None:
        self.run_id = run_id
        self.window_start_tick = window_start_tick
        self.ticks_observed = 0
        
        # Aggregation registers
        self._alive_entities: List[int] = []
        self._active_entities: List[int] = []
        self._gold_total: List[float] = []
        self._tick_compute_ms: List[float] = []
        self._memory_rss_bytes: List[float] = []
        self._hard_law_violation_count = 0
        self._event_count = 0
        self._rejection_count = 0
        self._quest_active: List[int] = []
        self._quest_completed: List[int] = []
        self._governor_modes: List[str] = []
        self._worker_utilization: List[float] = []
        self._queue_utilization: List[float] = []

    def record_tick(
        self,
        tick: int,
        world_metrics: Optional[Any],
        pressure_signals: Optional[Any],
        runtime_status: Optional[Any],
        event_count_delta: int,
        violation_count_delta: int
    ) -> None:
        """
        Record the observability snapshots of the current tick.
        """
        if self.ticks_observed == 0:
            self.window_start_tick = tick
        self.ticks_observed += 1
        
        # 1. World Metrics extraction
        if world_metrics:
            alive = getattr(world_metrics, "alive_entities", 0)
            total = getattr(world_metrics, "total_entities", 0)
            gold = getattr(world_metrics, "total_gold", 0.0)
            
            self._alive_entities.append(alive)
            self._active_entities.append(total)
            self._gold_total.append(gold)
            
            # Rejections
            rejections = getattr(world_metrics, "rejection_counts", {})
            if isinstance(rejections, dict):
                self._rejection_count += sum(rejections.values())
                
            # Quests
            quest_status = getattr(world_metrics, "quest_status_counts", {})
            if isinstance(quest_status, dict):
                self._quest_active.append(quest_status.get("ACTIVE", 0))
                self._quest_completed.append(quest_status.get("COMPLETED", 0))
        else:
            self._alive_entities.append(0)
            self._active_entities.append(0)
            self._gold_total.append(0.0)
            self._quest_active.append(0)
            self._quest_completed.append(0)

        # 2. Pressure Signals extraction
        if pressure_signals:
            compute_ms = getattr(pressure_signals, "tick_compute_ms", 0.0)
            mem_mb = getattr(pressure_signals, "memory_estimate_mb", 0.0)
            worker_util = getattr(pressure_signals, "worker_utilization", 0.0)
            queue_util = getattr(pressure_signals, "queue_utilization", 0.0)
            
            self._tick_compute_ms.append(compute_ms)
            self._memory_rss_bytes.append(mem_mb * 1024 * 1024)
            self._worker_utilization.append(worker_util)
            self._queue_utilization.append(queue_util)
        else:
            self._tick_compute_ms.append(0.0)
            self._memory_rss_bytes.append(0.0)
            self._worker_utilization.append(0.0)
            self._queue_utilization.append(0.0)

        # 3. Runtime Status extraction
        if runtime_status:
            mode = getattr(runtime_status, "current_mode", None)
            if mode is not None:
                self._governor_modes.append(str(getattr(mode, "name", mode)))
            else:
                self._governor_modes.append("NORMAL")
        else:
            self._governor_modes.append("NORMAL")

        # 4. Deltas
        self._event_count += event_count_delta
        self._hard_law_violation_count += violation_count_delta

    def _calculate_p95(self, values: List[float]) -> float:
        """
        Deterministic windowed 95th percentile using linear interpolation.
        """
        if not values:
            return 0.0
        sorted_vals = sorted(values)
        idx = (len(sorted_vals) - 1) * 0.95
        low = math.floor(idx)
        high = math.ceil(idx)
        if low == high:
            return sorted_vals[low]
        return sorted_vals[low] + (sorted_vals[high] - sorted_vals[low]) * (idx - low)

    def _calculate_dominant_mode(self, modes: List[str]) -> str:
        """
        Calculate the most frequent governor mode in this window.
        """
        if not modes:
            return "NORMAL"
        counts: Dict[str, int] = {}
        for m in modes:
            counts[m] = counts.get(m, 0) + 1
        return max(counts, key=counts.get)

    def flush(self, end_tick: int) -> MetricWindowRecord:
        """
        Flush rolling aggregates into a standard MetricWindowRecord.
        """
        ticks = self.ticks_observed if self.ticks_observed > 0 else 1
        
        alive_avg = sum(self._alive_entities) / ticks
        active_avg = sum(self._active_entities) / ticks
        gold_avg = sum(self._gold_total) / ticks
        compute_avg = sum(self._tick_compute_ms) / ticks
        compute_p95 = self._calculate_p95(self._tick_compute_ms)
        
        mem_avg = sum(self._memory_rss_bytes) / ticks
        mem_max = max(self._memory_rss_bytes) if self._memory_rss_bytes else 0.0
        
        quest_active_avg = sum(self._quest_active) / ticks
        quest_completed_avg = sum(self._quest_completed) / ticks
        dominant_mode = self._calculate_dominant_mode(self._governor_modes)
        
        worker_util_avg = sum(self._worker_utilization) / ticks
        queue_util_avg = sum(self._queue_utilization) / ticks

        return MetricWindowRecord(
            run_id=self.run_id,
            window_start_tick=self.window_start_tick,
            window_end_tick=end_tick,
            ticks_observed=self.ticks_observed,
            alive_entities_avg=alive_avg,
            active_entities_avg=active_avg,
            gold_total_avg=gold_avg,
            tick_compute_ms_avg=compute_avg,
            tick_compute_ms_p95=compute_p95,
            memory_rss_bytes_avg=mem_avg,
            memory_rss_bytes_max=mem_max,
            hard_law_violation_count=self._hard_law_violation_count,
            event_count=self._event_count,
            anomaly_candidate_count=0, # Bounded: analysis is post-run (Milestone 11)
            rejection_count=self._rejection_count,
            quest_active_count=quest_active_avg,
            quest_completed_count=quest_completed_avg,
            governor_mode_dominant=dominant_mode,
            worker_utilization_avg=worker_util_avg,
            queue_utilization_avg=queue_util_avg
        )

class MetricWindowRecorder:
    """
    Manages filesystem recording and rolling accumulation boundaries.
    """
    def __init__(
        self,
        run_id: str,
        run_dir: Optional[str],
        window_size: int = 100,
        enabled: bool = True
    ) -> None:
        self.run_id = run_id
        self.run_dir = run_dir
        self.window_size = window_size
        self.enabled = enabled
        
        self.filepath: Optional[str] = None
        self._file_handle = None
        
        if self.enabled and self.run_dir:
            try:
                os.makedirs(self.run_dir, exist_ok=True)
                self.filepath = os.path.join(self.run_dir, "metric_windows.jsonl")
                self._file_handle = open(self.filepath, "a", encoding="utf-8")
            except Exception as e:
                logger.error(f"Failed to open metric windows file at {self.run_dir}: {e}")
                self.enabled = False

        self._accumulator = MetricWindowAccumulator(run_id, 1)

    def record_tick(
        self,
        tick: int,
        world_metrics: Optional[Any],
        pressure_signals: Optional[Any],
        runtime_status: Optional[Any],
        event_count_delta: int,
        violation_count_delta: int
    ) -> None:
        """
        Record tick data and trigger standard window boundaries.
        """
        if not self.enabled:
            return
            
        self._accumulator.record_tick(
            tick,
            world_metrics,
            pressure_signals,
            runtime_status,
            event_count_delta,
            violation_count_delta
        )
        
        # Flush on window boundaries
        if self._accumulator.ticks_observed >= self.window_size:
            self._flush_window(tick)

    def _flush_window(self, end_tick: int) -> None:
        """
        Flush current accumulator into the JSONL log file and start a new accumulator.
        """
        record = self._accumulator.flush(end_tick)
        
        if self._file_handle:
            try:
                self._file_handle.write(record.model_dump_json() + "\n")
                self._file_handle.flush()
            except Exception as e:
                logger.error(f"Error writing metric window record: {e}")
                
        # Start fresh window starting at tick + 1
        self._accumulator = MetricWindowAccumulator(self.run_id, end_tick + 1)

    def shutdown(self, current_tick: int) -> None:
        """
        Flush any partial final window and close active file streams.
        """
        if not self.enabled:
            return
            
        if self._accumulator.ticks_observed > 0:
            self._flush_window(current_tick)
            
        if self._file_handle:
            try:
                self._file_handle.close()
            except Exception:
                pass
            self._file_handle = None
