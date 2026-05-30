import time
from typing import Optional, Any, Callable
from src.observability.config import ObservabilityConfig
from src.observability.performance.models import PhaseTimingRecord

class PhaseProfileScope:
    """
    Exception-safe context manager scope for timing a specific simulation phase.
    """
    def __init__(
        self,
        run_id: str,
        tick: int,
        phase_name: str,
        on_complete: Callable[[PhaseTimingRecord], None],
        enabled: bool = True
    ) -> None:
        self.run_id = run_id
        self.tick = tick
        self.phase_name = phase_name
        self.on_complete = on_complete
        self.enabled = enabled
        
        self.start_ns: int = 0
        self.failed: bool = False
        
        # Counters matching PhaseTimingRecord
        self.entity_count = 0
        self.update_count = 0
        self.event_count = 0
        self.provider_call_count = 0
        self.cache_hit_count = 0
        self.cache_miss_count = 0
        self.budget_status = "OK"

    def __enter__(self) -> "PhaseProfileScope":
        if self.enabled:
            self.start_ns = time.perf_counter_ns()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        if not self.enabled:
            return
            
        duration_ns = time.perf_counter_ns() - self.start_ns
        if exc_type is not None:
            self.failed = True
            
        record = PhaseTimingRecord(
            run_id=self.run_id,
            tick=self.tick,
            phase_name=self.phase_name,
            duration_ns=duration_ns,
            entity_count=self.entity_count,
            update_count=self.update_count,
            event_count=self.event_count,
            provider_call_count=self.provider_call_count,
            cache_hit_count=self.cache_hit_count,
            cache_miss_count=self.cache_miss_count,
            budget_status=self.budget_status,
            failed=self.failed
        )
        try:
            self.on_complete(record)
        except Exception:
            # Silence profiler handler exceptions to never crash simulation loop
            pass

    def set_counter(self, name: str, value: int) -> None:
        if not self.enabled:
            return
        if hasattr(self, name):
            setattr(self, name, value)

    def inc_counter(self, name: str, delta: int = 1) -> None:
        if not self.enabled:
            return
        if hasattr(self, name):
            current = getattr(self, name, 0)
            setattr(self, name, current + delta)


class PhaseProfiler:
    """
    Manages low-overhead timing and recording of simulation engine phases.
    """
    def __init__(self, run_id: str) -> None:
        self.run_id = run_id
        self.records: list[PhaseTimingRecord] = []

    def profile_phase(self, tick: int, phase_name: str) -> PhaseProfileScope:
        """
        Return a profiling scope context manager.
        Automatically bypasses timing checks if OBS_RUNTIME_PROFILING is disabled.
        """
        enabled = ObservabilityConfig.is_runtime_profiling_enabled()
        return PhaseProfileScope(
            run_id=self.run_id,
            tick=tick,
            phase_name=phase_name,
            on_complete=self.records.append,
            enabled=enabled
        )

    def clear(self) -> None:
        self.records.clear()
