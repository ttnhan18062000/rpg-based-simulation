from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, Any, Set, Optional, List
from src_v2.core.strategic import StrategicComponent


@dataclass(frozen=True, slots=True)
class RegionState:
    """Regional attributes and world dynamic markers."""
    id: str
    name: str
    bounds: tuple[int, int, int, int] # x_min, y_min, x_max, y_max
    hazard_level: float = 0.0      # 0.0 to 1.0, affects HP/Readiness drain
    suppression_active: bool = False # Prevents certain worker actions
    calamity_intensity: float = 0.0  # Scales regional hazards
    trauma_score: float = 0.0      # Persistent regional 'scar' value


@dataclass(frozen=True, slots=True)
class SocialComponent:
    """State for reputation, trust, and betrayal history."""
    trust_history: Dict[int, float] = field(default_factory=dict) # EntityID -> Trust Score
    betrayal_count: int = 0
    public_reputation: float = 1.0 # Standard recruitment modifier


@dataclass(frozen=True, slots=True)
class CombatComponent:
    """State for authoritative combat resolution."""
    hp: int = 100
    max_hp: int = 100
    atk: int = 10
    def_stat: int = 5
    evasion: float = 0.05
    alive: bool = True


@dataclass(frozen=True, slots=True)
class NavigationComponent:
    """State for movement intent and pathfinding."""
    target: Optional[tuple[float, float]] = None
    path: List[tuple[float, float]] = field(default_factory=list)
    moved_recently: bool = False
    last_failure_reason: Optional[str] = None


@dataclass(frozen=True, slots=True)
class TaskComponent:
    """Authoritative intent for the next simulation cycle."""
    work_kind: str = "ENTITY_ACT"
    payload: Dict[str, Any] = field(default_factory=dict)


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
    evolution_level: int = 1
    evolution_points: int = 0

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
    social: SocialComponent = field(default_factory=SocialComponent)
    combat: CombatComponent = field(default_factory=CombatComponent)
    navigation: NavigationComponent = field(default_factory=NavigationComponent)
    task: TaskComponent = field(default_factory=TaskComponent)
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
class BuildingState:
    """Authoritative state for a town building (Shop, Blacksmith, etc)."""
    id: int
    kind: str
    position: tuple[float, float]
    hp: int = 500
    max_hp: int = 500
    functional: bool = True


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
    buildings: Dict[int, BuildingState] = field(default_factory=dict) # Sabotage truth
    regions: Dict[str, RegionState] = field(default_factory=dict)    # World dynamics truth
    global_resources: Dict[str, float] = field(default_factory=dict)
    periodic_due_ticks: Dict[str, int] = field(default_factory=dict)
    work_debt: Dict[str, int] = field(default_factory=dict)
    movement_count: int = 0  # Milestone 2: Throughput truth
    blocked_tiles: set[tuple[int, int]] = field(default_factory=set) # Spatial truth
    town_tiles: set[tuple[int, int]] = field(default_factory=set)    # Social truth
    building_tiles: Dict[tuple[int, int], str] = field(default_factory=dict) # Service mapping
    rng_checkpoint: Any = None

    def fingerprint(self) -> Dict[str, Any]:
        """
        Produce a deterministic, multi-domain fingerprint of the current state.
        Used for authoritative export and parity verification.
        """
        import hashlib
        
        # 1. Identity & Spatial (Sorted by ID)
        entity_ident = "".join(f"{id}:{e.position}" for id, e in sorted(self.entities.items()))
        
        # 2. Resources & Dynamics
        resource_ident = "".join(f"{k}:{v}" for k, v in sorted(self.global_resources.items()))
        region_ident = "".join(f"{k}:{r.hazard_level}:{r.calamity_intensity}" 
                               for k, r in sorted(self.regions.items()))
        
        # 3. Combine into hashes
        state_hash = hashlib.md5(f"{self.seed}|{entity_ident}|{resource_ident}|{region_ident}".encode()).hexdigest()
        
        return {
            "state_hash": state_hash,
            "entity_count": len(self.entities),
            "resource_count": len(self.global_resources),
            "tick": self.tick,
            "seed": self.seed
        }
