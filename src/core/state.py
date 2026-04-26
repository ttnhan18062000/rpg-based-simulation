from __future__ import annotations

from enum import Enum, IntEnum, auto
from dataclasses import dataclass, field, replace
from typing import Dict, Any, Set, Optional, List, Tuple
from src.core.strategic import StrategicComponent
from src.core.enums import Faction, EntityRole
from src.core.movement_modes import MovementMode


class ItemKind(str, Enum):
    """Broad categories of items."""
    MATERIAL = "MATERIAL"
    CONSUMABLE = "CONSUMABLE"
    WEAPON = "WEAPON"
    ARMOR = "ARMOR"
    CURRENCY = "CURRENCY"

class EquipSlot(str, Enum):
    """Valid equipment locations on an entity."""
    HEAD = "HEAD"
    TORSO = "TORSO"
    LEGS = "LEGS"
    MAIN_HAND = "MAIN_HAND"
    OFF_HAND = "OFF_HAND"


@dataclass(frozen=True, slots=True)
class ItemStack:
    """A quantity of a specific item template."""
    item_id: str
    quantity: int = 1

@dataclass(frozen=True, slots=True)
class BiologicalComponent:
    """State for sleep, hunger, and other biological pressures."""
    sleep_debt: float = 0.0      # 0.0 to 100.0, affects performance
    hunger: float = 0.0          # 0.0 to 100.0, affects stamina/readiness
    rest_pressure: float = 0.0   # 0.0 to 100.0, forced rest at high values
    last_meal_tick: int = 0
    last_sleep_tick: int = 0
    well_rested_until: int = -1   # Tick until which well-rested buff applies


@dataclass(frozen=True, slots=True)
class LifecycleComponent:
    """State for hero aging and death mechanics."""
    age_ticks: int = 0
    max_age_ticks: int = 10000
    is_permadeath: bool = False
    death_tick: Optional[int] = None
    death_reason: Optional[str] = None
    generation: int = 1
    heir_entity_id: Optional[int] = None
    heirlooms: list[str] = field(default_factory=list)


@dataclass(frozen=True, slots=True)
class LocalScarState:
    """Localized world trauma at a specific coordinate."""
    id: int
    position: tuple[float, float]
    kind: str # e.g. BATTLE_FIELD, RAID_DAMAGE
    severity: float = 0.5
    created_tick: int = 0
    recovery_rate: float = 0.0005
    source_event_id: Optional[str] = None
    behavioral_modifiers: Dict[str, float] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class RegionState:
    """Regional attributes and world dynamic markers."""
    id: str
    name: str
    bounds: tuple[int, int, int, int] # x_min, y_min, x_max, y_max
    kind: str = "FOREST"
    hazard_level: float = 0.0      # 0.0 to 1.0, affects HP/Readiness drain
    suppression_active: bool = False # Prevents certain worker actions
    calamity_intensity: float = 0.0  # Scales regional hazards
    trauma_score: float = 0.0      # Persistent regional 'scar' value
    stability: float = 1.0         # 0.0 to 1.0, recovery rate of regions
    owner_faction_id: Optional[int] = None # Faction that currently controls the region
    influence: float = 0.0         # -100.0 (Monster) to 100.0 (Hero)
    weather: str = "CLEAR"
    active_modifiers: List[str] = field(default_factory=list)

    @property
    def center(self) -> tuple[float, float]:
        xmin, ymin, xmax, ymax = self.bounds
        return ((xmin + xmax) / 2.0, (ymin + ymax) / 2.0)


@dataclass(frozen=True, slots=True)
class SocialBond:
    """A first-class directed relationship record."""
    target_id: int
    familiarity: float = 0.0 # Interaction depth (0.0 to 1.0)
    sentiment: float = 0.0   # Bias/Liking (-1.0 to 1.0)
    last_interaction_tick: int = 0

@dataclass(frozen=True, slots=True)
class SocialComponent:
    """State for reputation, trust, and betrayal history."""
    trust_history: Dict[int, float] = field(default_factory=dict)       # EntityID -> Trust Score
    familiarity_history: Dict[int, float] = field(default_factory=dict) # EntityID -> Familiarity
    debt_history: Dict[int, float] = field(default_factory=dict)        # EntityID -> Debt (Social/Gold)
    fear_history: Dict[int, float] = field(default_factory=dict)        # EntityID -> Fear Score
    grudge_history: Dict[int, float] = field(default_factory=dict)      # EntityID -> Grudge Score (Nemesis)
    salience_history: Dict[int, float] = field(default_factory=dict)    # EntityID -> Interaction Salience
    
    # PH15 Recovery: First-class bonds
    bonds: Dict[int, SocialBond] = field(default_factory=dict)         # EntityID -> Bond
    
    betrayal_count: int = 0
    public_reputation: float = 1.0   # Unified reputation score (0.0 to 2.0)
    heroism_score: float = 0.0       # Cumulative good deeds
    notoriety_score: float = 0.0     # Cumulative bad deeds


@dataclass(frozen=True, slots=True)
class CombatComponent:
    """State for authoritative combat resolution."""
    hp: int = 100
    max_hp: int = 100
    atk: int = 10
    def_stat: int = 5
    speed: int = 10
    range: int = 1
    evasion: float = 0.05
    tactical_role: str = "VANGUARD"
    action_style: int = 0 # ActionStyle.BALANCED
    alive: bool = True


@dataclass(frozen=True, slots=True)
class NavigationComponent:
    """State for movement intent and pathfinding."""
    target: Optional[tuple[float, float]] = None
    path: List[tuple[float, float]] = field(default_factory=list)
    moved_recently: bool = False
    movement_mode: MovementMode = MovementMode.WANDER
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

class LifeStage(str, Enum):
    """Developmental stage of an entity."""
    CHILD = "CHILD"
    ADULT = "ADULT"
    ELDER = "ELDER"

@dataclass(frozen=True, slots=True)
class PersonalityComponent:
    """Persistent psychological traits."""
    greed: float = 0.0      # Biases loot/harvest
    bravery: float = 0.0    # Biases combat vs flee
    sociability: float = 0.0 # Biases social goals
    industry: float = 0.0    # Biases work/harvest goals

@dataclass(frozen=True, slots=True)
class AttributeComponent:
    """Base attributes that drive derived combat and strategic stats."""
    strength: int = 5
    agility: int = 5
    vitality: int = 5
    endurance: int = 5
    intelligence: int = 5
    spirit: int = 5
    wisdom: int = 5
    perception: int = 5
    charisma: int = 5

@dataclass(frozen=True, slots=True)
class IdentityComponent:
    """Core entity characteristics and knowledge."""
    role: int = 0 # EntityRole.HERO
    faction: int = 0 # Faction.HERO_GUILD
    known_recipes: Set[str] = field(default_factory=set)
    craft_target: str | None = None
    evolution_level: int = 1
    evolution_points: int = 0
    veterancy_points: int = 0
    veterancy_rank: int = 0
    unspent_ap: int = 0
    class_id: str = "NOVICE"
    learned_skills: Set[str] = field(default_factory=set)
    active_breakthroughs: Set[str] = field(default_factory=set)
    personality: PersonalityComponent = field(default_factory=PersonalityComponent)
    life_stage: LifeStage = LifeStage.ADULT

@dataclass(frozen=True, slots=True)
class AptitudeComponent:
    """Genetic multipliers for stat growth (Pillar 2)."""
    learning_rate: float = 1.0
    stamina_efficiency: float = 1.0
    str_apt: float = 1.0
    agi_apt: float = 1.0
    vit_apt: float = 1.0
    end_apt: float = 1.0
    int_apt: float = 1.0
    spi_apt: float = 1.0
    wis_apt: float = 1.0
    per_apt: float = 1.0
    cha_apt: float = 1.0

@dataclass(frozen=True, slots=True)
class GroupRecord:
    """Authoritative state for a multi-entity coordination unit."""
    id: int
    leader_id: int
    member_ids: Set[int]
    anchor: tuple[float, float]
    shared_target_id: Optional[int] = None
    contract_id: Optional[str] = None
    cohesion_radius: float = 5.0
    last_updated_tick: int = 0
    roles: Dict[int, str] = field(default_factory=dict) # entity_id -> role_name
    str_apt: float = 1.0
    int_apt: float = 1.0
    agi_apt: float = 1.0
    vit_apt: float = 1.0
    end_apt: float = 1.0

@dataclass(frozen=True, slots=True)
class InventoryComponent:
    """Bounded container for items and gold."""
    items: List[ItemStack] = field(default_factory=list)
    gold: int = 0
    max_slots: int = 16
    max_weight: float = 50.0

@dataclass(frozen=True, slots=True)
class EquipmentComponent:
    """Currently equipped items per slot."""
    slots: Dict[EquipSlot, str | None] = field(default_factory=dict)



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
    attributes: AttributeComponent = field(default_factory=AttributeComponent)
    inventory: InventoryComponent = field(default_factory=InventoryComponent)
    strategic: StrategicComponent = field(default_factory=StrategicComponent)
    social: SocialComponent = field(default_factory=SocialComponent)
    biological: BiologicalComponent = field(default_factory=BiologicalComponent)
    lifecycle: LifecycleComponent = field(default_factory=LifecycleComponent)
    aptitude: AptitudeComponent = field(default_factory=AptitudeComponent)
    combat: CombatComponent = field(default_factory=CombatComponent)
    equipment: EquipmentComponent = field(default_factory=EquipmentComponent)
    navigation: NavigationComponent = field(default_factory=NavigationComponent)
    task: TaskComponent = field(default_factory=TaskComponent)
    group_id: Optional[int] = None
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
class GroundItemState:
    """An item dropped on the ground."""
    id: int
    item_id: str
    quantity: int
    position: tuple[float, float]

@dataclass(frozen=True, slots=True)
class CorpseState:
    """A dead entity that can be looted."""
    id: int
    original_entity_id: int
    position: tuple[float, float]
    items: List[ItemStack]
    decay_tick: int
    generation: int = 1


@dataclass(frozen=True, slots=True)
class ChestState:
    """A world object containing loot."""
    id: int
    position: tuple[float, float]
    items: List[ItemStack]
    respawn_tick: int = 0
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
    ground_items: Dict[int, GroundItemState] = field(default_factory=dict)
    corpses: Dict[int, CorpseState] = field(default_factory=dict)
    chests: Dict[int, ChestState] = field(default_factory=dict)
    buildings: Dict[int, BuildingState] = field(default_factory=dict) # Sabotage truth
    regions: Dict[str, RegionState] = field(default_factory=dict)    # World dynamics truth
    local_scars: Dict[int, LocalScarState] = field(default_factory=dict) # Spatial trauma
    groups: Dict[int, GroupRecord] = field(default_factory=dict)     # Social coordination truth
    terrain: Dict[tuple[int, int], str] = field(default_factory=dict) # Local tile truth (WALL, FOREST, etc)
    global_resources: Dict[str, float] = field(default_factory=dict)
    home_storage: Dict[int, InventoryComponent] = field(default_factory=dict) # Milestone 5
    town_center: tuple[float, float] = (0.0, 0.0) # Milestone 7
    periodic_due_ticks: Dict[str, int] = field(default_factory=dict)
    work_debt: Dict[str, int] = field(default_factory=dict)
    movement_count: int = 0  # Milestone 2: Throughput truth
    maturity: int = 0
    last_calamity_tick: int = 0
    blocked_tiles: set[tuple[int, int]] = field(default_factory=set) # Spatial truth
    town_tiles: set[tuple[int, int]] = field(default_factory=set)    # Social truth
    building_tiles: Dict[tuple[int, int], str] = field(default_factory=dict) # Service mapping
    rng_checkpoint: Any = None

    def readonly_view(self) -> AuthoritativeState:
        """
        Produce a read-only view of the state for decision logic.
        M8 Law: Decision logic must not mutate authoritative state.
        """
        from src.core.immutability import shallow_freeze
        return replace(
            self,
            entities=shallow_freeze(self.entities),
            resource_nodes=shallow_freeze(self.resource_nodes),
            buildings=shallow_freeze(self.buildings),
            regions=shallow_freeze(self.regions),
            local_scars=shallow_freeze(self.local_scars),
            groups=shallow_freeze(self.groups),
            terrain=shallow_freeze(self.terrain),
            global_resources=shallow_freeze(self.global_resources),
            periodic_due_ticks=shallow_freeze(self.periodic_due_ticks),
            work_debt=shallow_freeze(self.work_debt),
            blocked_tiles=shallow_freeze(self.blocked_tiles),
            town_tiles=shallow_freeze(self.town_tiles),
            building_tiles=shallow_freeze(self.building_tiles)
        )

    def fingerprint(self) -> Dict[str, Any]:
        """
        Produce a deterministic, multi-domain fingerprint of the current state.
        Used for authoritative export and parity verification.
        """
        from src.replay.fingerprint import StateFingerprinter
        return StateFingerprinter.get_fingerprint(self)
