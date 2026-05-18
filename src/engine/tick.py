from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, List

if TYPE_CHECKING:
    from src.config.profiles import RuntimeProfile
    from src.core.state import AuthoritativeState


@dataclass(frozen=True, slots=True)
class TickContext:
    """
    Mutable-but-bounded context for a single tick execution.
    This serves as the transport between phases.
    """
    tick: int
    profile: RuntimeProfile
    state: AuthoritativeState
    
    # Transient state for the duration of the tick
    active_entity_ids: List[int] = field(default_factory=list)
    applied_changes: List[str] = field(default_factory=list)
    
    # Resource metrics captured during the tick
    phase_timings_ms: dict[str, float] = field(default_factory=dict)
