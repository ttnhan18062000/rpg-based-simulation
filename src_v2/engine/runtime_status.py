from __future__ import annotations

from dataclasses import dataclass, field
from collections import deque
from typing import List, Optional
from src_v2.core.governance import RuntimeMode, PressureSignals


@dataclass
class RuntimeStatus:
    """
    Operational control state for the simulation engine.
    M5 Law: This state is isolated from AuthoritativeState and does not 
    contaminate simulation hashes.
    """
    current_mode: RuntimeMode = RuntimeMode.NORMAL
    
    # Stability tracking
    mode_dwell_ticks: int = 0
    
    # Bounded signal history (Step 5 tightening)
    # Stores the last 100 sets of pressure signals.
    signal_history: deque[PressureSignals] = field(
        default_factory=lambda: deque(maxlen=100)
    )
    
    # Outcome accounting
    total_dropped_work: int = 0
    dropped_work_delta: int = 0  # Replaced every tick
    last_transition_tick: int = 0

    def record_signals(self, signals: PressureSignals) -> None:
        """Append fresh signals and calculate trends."""
        # 1. Calculate computed trending fields
        avg_compute = signals.tick_compute_ms
        memory_trend = 0.0
        
        if self.signal_history:
            prev = self.signal_history[-1]
            memory_trend = signals.memory_estimate_mb - prev.memory_estimate_mb
            
            # Simple window-based average for CPU
            all_compute = [s.tick_compute_ms for s in self.signal_history] + [signals.tick_compute_ms]
            avg_compute = sum(all_compute) / len(all_compute)
            
        # 2. Enrich signals with calculated trends
        enriched = PressureSignals(
            tick_compute_ms = signals.tick_compute_ms,
            tick_compute_ms_avg = avg_compute,
            work_debt_total = signals.work_debt_total,
            worker_utilization = signals.worker_utilization,
            queue_utilization = signals.queue_utilization,
            memory_estimate_mb = signals.memory_estimate_mb,
            memory_trend_mb_per_tick = memory_trend,
            replay_backlog_kb = signals.replay_backlog_kb,
            active_workers = signals.active_workers,
            dropped_work_delta = signals.dropped_work_delta
        )
        
        self.signal_history.append(enriched)

    def record_dropped_work(self, count: int) -> None:
        """Accumulate work shed due to degradation policy."""
        self.total_dropped_work += count
        self.dropped_work_delta = count

    def increment_dwell(self) -> None:
        """Track how long we've stayed in the current mode."""
        self.mode_dwell_ticks += 1

    def reset_dwell(self, new_mode: RuntimeMode, current_tick: int) -> None:
        """Reset counters when a transition occurs."""
        self.current_mode = new_mode
        self.mode_dwell_ticks = 0
        self.last_transition_tick = current_tick
