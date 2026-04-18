from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, Any


@dataclass(frozen=True, slots=True)
class EntityState:
    """
    Authoritative state for a single simulation entity.
    """
    id: int
    kind: str
    position: tuple[float, float]
    readiness: float = 0.0
    active: bool = True
    properties: Dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class AuthoritativeState:
    """
    The minimum state required to determine future simulation outcomes.
    Optimized for execution leanness and deterministic progression.
    """
    tick: int
    seed: int
    world_time: int = 0
    entities: Dict[int, EntityState] = field(default_factory=dict)
    global_resources: Dict[str, float] = field(default_factory=dict)
    periodic_due_ticks: Dict[str, int] = field(default_factory=dict)
    work_debt: Dict[str, int] = field(default_factory=dict)
    rng_checkpoint: Any = None
