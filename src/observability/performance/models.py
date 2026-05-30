from dataclasses import dataclass

@dataclass(frozen=True)
class PhaseTimingRecord:
    run_id: str
    tick: int
    phase_name: str
    duration_ns: int
    entity_count: int = 0
    update_count: int = 0
    event_count: int = 0
    provider_call_count: int = 0
    cache_hit_count: int = 0
    cache_miss_count: int = 0
    budget_status: str = "OK"
    failed: bool = False
