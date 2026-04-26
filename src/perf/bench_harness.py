from __future__ import annotations

import time
import json
import logging
from pathlib import Path
from typing import Dict, List, Any

from src.engine.kernel import Kernel
from src.core.state import AuthoritativeState
from src.platform.rng import DeterministicRNG
from src.config.profiles import RuntimeProfile

logger = logging.getLogger(__name__)

class BenchHarness:
    """
    Dedicated harness for high-frequency performance measurement.
    Adheres to the V2 Engine Performance Contract.
    """

    def __init__(self, profile: RuntimeProfile):
        self._profile = profile

    def run_benchmark(
        self,
        scenario_id: str,
        initial_state: AuthoritativeState,
        warmup_ticks: int = 100,
        sample_ticks: int = 1000
    ) -> Dict[str, Any]:
        """
        Execute a stable measurement run: Warmup -> Sample -> Collate.
        """
        logger.info(f"Starting Benchmark: {scenario_id} ({self._profile.name})")
        
        # Initialize Kernel
        rng = DeterministicRNG(initial_state.seed)
        kernel = Kernel(self._profile, initial_state, rng)
        
        # 1. WARMUP
        for _ in range(warmup_ticks):
            kernel.tick_once()
            
        # 2. SAMPLING
        start_ts = time.perf_counter()
        for _ in range(sample_ticks):
            kernel.tick_once()
        end_ts = time.perf_counter()
        
        total_time_s = end_ts - start_ts
        avg_tps = sample_ticks / total_time_s
        
        # 3. COLLATION
        # Extract the last sample_ticks worth of history
        history = kernel.status.get_recent_history(sample_ticks)
        
        phase_aggregates: Dict[str, List[float]] = {}
        for signals in history:
            for phase, cost in signals.phase_costs_ms.items():
                if phase not in phase_aggregates:
                    phase_aggregates[phase] = []
                phase_aggregates[phase].append(cost)
        
        phase_stats = {}
        for phase, costs in phase_aggregates.items():
            phase_stats[phase] = {
                "avg_ms": sum(costs) / len(costs),
                "max_ms": max(costs),
                "min_ms": min(costs)
            }
            
        avg_tick_ms = sum(s.tick_compute_ms for s in history) / len(history)
        
        result = {
            "scenario_id": scenario_id,
            "profile": self._profile.name,
            "sample_ticks": sample_ticks,
            "total_time_s": total_time_s,
            "avg_tps": avg_tps,
            "avg_tick_compute_ms": avg_tick_ms,
            "phase_breakdown": phase_stats,
            "timestamp": time.time()
        }
        
        return result
