from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, Any, Optional


@dataclass(frozen=True, slots=True)
class InteractionUpdate:
    """Multi-tick progress update."""
    target_node_id: Optional[int] = None
    progress_delta: float = 0.0
    reset: bool = False

@dataclass(frozen=True, slots=True)
class InventoryUpdate:
    """Authoritative inventory changes."""
    items_added: list[str] = field(default_factory=list)
    items_removed: list[str] = field(default_factory=list)


@dataclass(frozen=True, slots=True)
class EntityUpdate:
    """
    Authoritative update for a single entity.
    """
    entity_id: int
    new_position: Optional[tuple[float, float]] = None
    moved_this_tick: bool = False
    readiness_delta: float = 0.0
    active: Optional[bool] = None
    interaction: Optional[InteractionUpdate] = None
    inventory: Optional[InventoryUpdate] = None
    property_updates: Dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class ResourceNodeUpdate:
    """Updates to a harvestable node."""
    node_id: int
    charges_delta: int = 0
    cooldown_set: Optional[int] = None


@dataclass(frozen=True, slots=True)
class StateUpdate:
    """
    A collection of authoritative changes to be applied to the world state.
    """
    entity_updates: Dict[int, EntityUpdate] = field(default_factory=dict)
    node_updates: Dict[int, ResourceNodeUpdate] = field(default_factory=dict)
    resource_updates: Dict[str, float] = field(default_factory=dict)
    periodic_updates: Dict[str, int] = field(default_factory=dict)
    work_debt_updates: Dict[str, int] = field(default_factory=dict)
    rng_checkpoint: Any = None
