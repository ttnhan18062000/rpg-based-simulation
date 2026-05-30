from dataclasses import dataclass
from typing import Optional

@dataclass(frozen=True, slots=True)
class PhaseBudget:
    phase_name: str
    max_ms_per_tick: float
    max_entities_per_tick: int
    max_provider_calls_per_tick: int
    max_results_per_entity: int
    max_trace_events_per_tick: int
    max_memory_entries_per_entity: int

@dataclass(frozen=True, slots=True)
class PhaseBudgetResult:
    allowed: bool
    skipped_reason: Optional[str] = None
    consumed_ms: float = 0.0
    consumed_entities: int = 0
    consumed_provider_calls: int = 0
    consumed_trace_events: int = 0

class PhaseBudgetManager:
    """Limits computation usage for enhanced simulation phases."""
    def __init__(self, budget: PhaseBudget) -> None:
        self.budget = budget
        self.current_ms = 0.0
        self.current_entities = 0
        self.current_provider_calls = 0
        self.current_trace_events = 0

    def reset(self) -> None:
        self.current_ms = 0.0
        self.current_entities = 0
        self.current_provider_calls = 0
        self.current_trace_events = 0

    def check_and_consume(self, entities: int = 0, provider_calls: int = 0, trace_events: int = 0, ms_spent: float = 0.0) -> PhaseBudgetResult:
        if self.current_ms + ms_spent > self.budget.max_ms_per_tick:
            return PhaseBudgetResult(allowed=False, skipped_reason="Time budget exhausted")
        if self.current_entities + entities > self.budget.max_entities_per_tick:
            return PhaseBudgetResult(allowed=False, skipped_reason="Entity limit exhausted")
        if self.current_provider_calls + provider_calls > self.budget.max_provider_calls_per_tick:
            return PhaseBudgetResult(allowed=False, skipped_reason="Provider calls limit exhausted")
        if self.current_trace_events + trace_events > self.budget.max_trace_events_per_tick:
            return PhaseBudgetResult(allowed=False, skipped_reason="Trace events limit exhausted")

        self.current_ms += ms_spent
        self.current_entities += entities
        self.current_provider_calls += provider_calls
        self.current_trace_events += trace_events

        return PhaseBudgetResult(
            allowed=True,
            consumed_ms=self.current_ms,
            consumed_entities=self.current_entities,
            consumed_provider_calls=self.current_provider_calls,
            consumed_trace_events=self.current_trace_events
        )
