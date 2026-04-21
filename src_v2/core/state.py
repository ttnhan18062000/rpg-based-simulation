from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, Any, Set
from src_v2.core.strategic import StrategicComponent


@dataclass(frozen=True, slots=True)
class InteractionComponent:
    """State for multi-tick channeling logic."""
    target_node_id: int | None = None
    progress: int = 0
    start_tick: int = 0

@dataclass(frozen=True, slots=True)
class IdentityComponent:
    """Core entity characteristics and knowledge."""
    role: int = 0 # EntityRole.HERO
    faction: int = 0 # Faction.HERO_GUILD
    known_recipes: Set[str] = field(default_factory=set)
    craft_target: str | None = None
    navigation_target: tuple[float, float] | None = None

@dataclass(frozen=True, slots=True)
class InventoryComponent:
    """Bounded container for items."""
    max_slots: int = 16
    max_weight: int = 50
    current_slots_used: int = 0
    current_weight: int = 0
    gold: int = 0
    items: list[str] = field(default_factory=list)


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
    interaction: InteractionComponent = field(default_factory=InteractionComponent)
    identity: IdentityComponent = field(default_factory=IdentityComponent)
    inventory: InventoryComponent = field(default_factory=InventoryComponent)
    strategic: StrategicComponent = field(default_factory=StrategicComponent)
    properties: Dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class ResourceNodeState:
    """Authoritative state for a harvestable resource."""
    id: int
    kind: str
    position: tuple[float, float]
    yields_item: str
    remaining_charges: int
    max_charges: int
    required_ticks: int
    respawn_cooldown: int = 100
    cooldown_remaining: int = 0


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
    resource_nodes: Dict[int, ResourceNodeState] = field(default_factory=dict)
    global_resources: Dict[str, float] = field(default_factory=dict)
    periodic_due_ticks: Dict[str, int] = field(default_factory=dict)
    work_debt: Dict[str, int] = field(default_factory=dict)
    movement_count: int = 0  # Milestone 2: Throughput truth
    blocked_tiles: set[tuple[int, int]] = field(default_factory=set) # Spatial truth
    town_tiles: set[tuple[int, int]] = field(default_factory=set)    # Social truth
    building_tiles: Dict[tuple[int, int], str] = field(default_factory=dict) # Service truth
    rng_checkpoint: Any = None
