from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, Any, Optional


@dataclass(frozen=True, slots=True)
class EntityUpdate:
    """
    Authoritative update for a single entity.
    """
    entity_id: int
    new_position: Optional[tuple[float, float]] = None
    readiness_delta: float = 0.0
    active: Optional[bool] = None
    property_updates: Dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class StateUpdate:
    """
    A collection of authoritative changes to be applied to the world state.
    """
    entity_updates: Dict[int, EntityUpdate] = field(default_factory=dict)
    resource_updates: Dict[str, float] = field(default_factory=dict)
    periodic_updates: Dict[str, int] = field(default_factory=dict)
    work_debt_updates: Dict[str, int] = field(default_factory=dict)
    rng_checkpoint: Any = None
