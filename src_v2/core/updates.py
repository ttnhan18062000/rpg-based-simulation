from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, Any, Optional, TYPE_CHECKING
if TYPE_CHECKING:
    from src_v2.core.strategic import BlockerState, LeadState


@dataclass(frozen=True, slots=True)
class InteractionUpdate:
    """Multi-tick progress update."""
    target_node_id: Optional[int] = None
    progress_delta: float = 0.0
    reset: bool = False

@dataclass(frozen=True, slots=True)
class CombatUpdate:
    """Authoritative combat interaction results."""
    damage_taken: float = 0.0
    attacker_id: Optional[int] = None
    is_opportunity_attack: bool = False
    
@dataclass(frozen=True, slots=True)
class IdentityUpdate:
    """Updates to characteristics or knowledge."""
    recipes_learned: list[str] = field(default_factory=list)
    craft_target: Optional[str] = None
    navigation_target: Optional[tuple[float, float]] = None

@dataclass(frozen=True, slots=True)
class SocialUpdate:
    """Updates to trust, reputation, and betrayal history."""
    trust_delta: Dict[int, float] = field(default_factory=dict) # EntityID -> Delta
    betrayal_increment: int = 0
    reputation_set: Optional[float] = None


@dataclass(frozen=True, slots=True)
class StrategicUpdate:
    """Updates to markers for strategic markers (blockers, leads)."""
    blockers_add_or_update: list[BlockerState] = field(default_factory=list)
    blockers_remove: list[str] = field(default_factory=list)
    leads_add_or_update: list[LeadState] = field(default_factory=list)
    leads_remove: list[str] = field(default_factory=list)

@dataclass(frozen=True, slots=True)
class InventoryUpdate:
    """Authoritative inventory changes."""
    items_added: list[str] = field(default_factory=list)
    items_removed: list[str] = field(default_factory=list)
    gold_delta: int = 0


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
    identity: Optional[IdentityUpdate] = None
    inventory: Optional[InventoryUpdate] = None
    strategic: Optional[StrategicUpdate] = None
    social: Optional[SocialUpdate] = None
    combat: Optional[CombatUpdate] = None
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
