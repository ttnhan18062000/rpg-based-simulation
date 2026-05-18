from __future__ import annotations

from typing import Protocol, runtime_checkable


@runtime_checkable
class ReadinessEvaluator(Protocol):
    """
    Protocol for determining entity action eligibility.
    Eligibility must be separate from world-time advancement.
    """
    def is_ready(self, entity_id: int, current_tick: int) -> bool:
        ...


class DefaultReadinessEvaluator:
    """Skeletal implementation for Milestone 1."""
    def is_ready(self, entity_id: int, current_tick: int) -> bool:
        # Placeholder: No entities are ready in the skeletal shell.
        return False
