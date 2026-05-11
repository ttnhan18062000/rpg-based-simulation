# Compliance IDs: COMB-106, PROG-053, PROG-056, PROG-058, PROG-059, PROG-093, SOC-005, SOC-166, SOC-167, SOC-169, SOC-170, STRAT-042, STRAT-140, STRAT-165, STRAT-167, STRAT-168, STRAT-175, STRAT-176, STRAT-215, SUB-002, SUB-123, TOWN-024, TOWN-138, TOWN-139, TOWN-140, WORLD-039, WORLD-040
# Compliance IDs: COMB-106, PROG-053, PROG-056, PROG-058, PROG-059, STRAT-042, STRAT-140, STRAT-165, STRAT-167, STRAT-168, STRAT-175, STRAT-176, SUB-123, TOWN-024
from __future__ import annotations

from enum import Enum, IntEnum, auto
from dataclasses import dataclass, field, replace, InitVar
from types import MappingProxyType
from typing import Dict, Any, Set, Optional, List, Tuple
from src.core.strategic import StrategicComponent
from src.core.enums import Faction, EntityRole
from src.core.movement_modes import MovementMode
from src.core.governance import RuntimeMode
from src.core.models.inventory import ItemKind, EquipSlot, ItemStack, InventoryComponent
from src.core.models.social import SocialBond, BetrayalRecord, SocialComponent


def _readonly_mapping(value):
    if value is None:
        return ReadOnlyDict({})
    if isinstance(value, ReadOnlyDict):
        return value
    return ReadOnlyDict(dict(value))



class ReadOnlyError(TypeError):
    """Raised when mutation is attempted on a read-only state view."""
    pass

class ReadOnlyDict(dict):
    """A dictionary that raises ReadOnlyError on mutation attempts."""
    def __setitem__(self, key, value):
        raise ReadOnlyError("Authoritative mutation attempted during read-only phase.")
    def __delitem__(self, key):
        raise ReadOnlyError("Authoritative mutation attempted during read-only phase.")
    def update(self, *args, **kwargs):
        raise ReadOnlyError("Authoritative mutation attempted during read-only phase.")
    def pop(self, *args, **kwargs):
        raise ReadOnlyError("Authoritative mutation attempted during read-only phase.")
    def clear(self):
        raise ReadOnlyError("Authoritative mutation attempted during read-only phase.")
    
    def __reduce__(self):
        return (self.__class__, (dict(self),))





@dataclass(frozen=True, slots=True)
class StaminaComponent:
    """Stamina resource for actions — drains on attack/move/harvest/skill use."""
    current: float = 100.0
    max_stamina: float = 100.0  # Derived from endurance
    regen_rate: float = 2.0     # Per-tick passive regen
    rest_regen_rate: float = 8.0  # Regen rate when resting
    exhaustion_threshold: float = 10.0  # Below this, exhaustion penalty applies
    exhaustion_penalty: float = 0.7     # Combat multiplier when exhausted

    # Drain constants
    ATTACK_COST: float = 8.0
    MOVE_COST: float = 3.0
    HARVEST_COST: float = 5.0
    SKILL_COST_MULT: float = 1.0  # Multiplied by skill.cost


@dataclass(frozen=True, slots=True)
class WoundState:
    """A persistent wound from a massive hit."""
    id: str
    kind: str  # SLASH, CRUSH, PIERCE, BURN
    severity: float  # 0.0 to 1.0
    tick_inflicted: int
    atk_penalty: float = 0.0
    def_penalty: float = 0.0
    speed_penalty: float = 0.0
    max_hp_penalty: float = 0.0
    healed: bool = False
    scar_created: bool = False


@dataclass(frozen=True, slots=True)
class ScarState:
    """Permanent mark from a healed wound — lesser but persistent penalty."""
    id: str
    wound_kind: str
    tick_created: int
    atk_penalty: float = 0.0
    def_penalty: float = 0.0
    speed_penalty: float = 0.0


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
    active: bool = True


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
    retaliation_pressure: float = 0.0 # Short-term monster response to kills
    stability: float = 1.0         # 0.0 to 1.0, recovery rate of regions
    owner_faction_id: Optional[int] = None # Faction that currently controls the region
    influence: float = 0.0         # -100.0 (Monster) to 100.0 (Hero)
    weather: str = "CLEAR"
    active_modifiers: List[str] = field(default_factory=list)
    price_modifiers: Dict[str, float] = field(default_factory=dict) # ItemKind -> Multiplier

    @property
    def center(self) -> tuple[float, float]:
        xmin, ymin, xmax, ymax = self.bounds
        return ((xmin + xmax) / 2.0, (ymin + ymax) / 2.0)




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
    move_cost: float = 10.0
    tactical_role: str = "VANGUARD"
    action_style: int = 0 # ActionStyle.BALANCED
    alive: bool = True
    readiness: float = 0.0
    wounds: List[WoundState] = field(default_factory=list)
    scars: List[ScarState] = field(default_factory=list)
    latest_result: Optional["IntentResult"] = None


# Terrain cost weights for pathfinding
TERRAIN_COST: Dict[str, float] = {
    "ROAD": 0.5,
    "PLAIN": 1.0,
    "FLOOR": 1.0,
    "GRASS": 1.0,
    "FOREST": 1.5,
    "SWAMP": 3.0,
    "HILL": 2.0,
    "MOUNTAIN": 4.0,
    "SAND": 1.5,
}


@dataclass(frozen=True, slots=True)
class NavigationComponent:
    """State for movement intent and pathfinding."""
    position: tuple[float, float] = (0.0, 0.0)
    target: Optional[tuple[float, float]] = None
    path: List[tuple[float, float]] = field(default_factory=list)
    moved_recently: bool = False
    movement_mode: MovementMode = MovementMode.WANDER
    last_failure_reason: Optional[str] = None
    
    # Phase 4 additions: Movement Congestion Recovery
    wait_count: int = 0
    oscillation_count: int = 0
    last_position: Optional[tuple[float, float]] = None

    # Mob Leash fields
    home_position: Optional[tuple[float, float]] = None
    leash_radius: float = 0.0  # 0 = no leash
    chase_ticks: int = 0
    max_chase_ticks: int = 15
    returning_home: bool = False


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
    traits: Set[str] = field(default_factory=set)
    active_breakthroughs: Set[str] = field(default_factory=set)
    cooldowns: Dict[str, int] = field(default_factory=dict) # skill_id -> tick when ready
    personality: PersonalityComponent = field(default_factory=PersonalityComponent)
    life_stage: LifeStage = LifeStage.ADULT
    group_id: Optional[int] = None
    properties: Dict[str, Any] = field(default_factory=dict)
    latest_intent_results: List["IntentResult"] = field(default_factory=list)

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
class EquipmentComponent:
    """Currently equipped items per slot."""
    slots: Dict[EquipSlot, str | None] = field(default_factory=dict)
    durability: Dict[EquipSlot, float] = field(default_factory=dict)



@dataclass(frozen=True, slots=True)
class IntentResult:
    """The outcome of a specific resource transfer intent."""
    transaction_id: str | None
    accepted: bool
    reason: Any
    source_kind: str
    source_id: str | int

@dataclass(frozen=True, slots=True)
class EntityState:
    """The authoritative atom of the simulation."""
    id: int
    kind: str
    init_position: InitVar[Optional[tuple[float, float]]] = None
    init_group_id: InitVar[Optional[int]] = None
    init_properties: InitVar[Optional[Dict[str, Any]]] = None
    interaction: InteractionComponent = field(default_factory=InteractionComponent)
    identity: IdentityComponent = field(default_factory=IdentityComponent)
    attributes: AttributeComponent = field(default_factory=AttributeComponent)
    inventory: InventoryComponent = field(default_factory=InventoryComponent)
    strategic: StrategicComponent = field(default_factory=StrategicComponent)
    social: SocialComponent = field(default_factory=SocialComponent)
    biological: BiologicalComponent = field(default_factory=BiologicalComponent)
    lifecycle: LifecycleComponent = field(default_factory=LifecycleComponent)
    _readonly_cache: Any = field(default=None, repr=False, compare=False)
    aptitude: AptitudeComponent = field(default_factory=AptitudeComponent)
    combat: CombatComponent = field(default_factory=CombatComponent)
    equipment: EquipmentComponent = field(default_factory=EquipmentComponent)
    navigation: NavigationComponent = field(default_factory=NavigationComponent)
    task: TaskComponent = field(default_factory=TaskComponent)
    stamina: StaminaComponent = field(default_factory=StaminaComponent)
    
    # Legacy properties for backward compatibility
    @property
    def position(self) -> tuple[float, float]:
        return self.navigation.position
        
    @property
    def group_id(self) -> Optional[int]:
        return self.identity.group_id
        
    @property
    def properties(self) -> Dict[str, Any]:
        return self.identity.properties
        
    @property
    def active(self) -> bool:
        return self.lifecycle.active
        
    @property
    def readiness(self) -> float:
        return self.combat.readiness

    # No legacy InitVars or __post_init__ - strictly component-based initialization.
    def __post_init__(self, init_position: Optional[tuple[float, float]], init_group_id: Optional[int], init_properties: Optional[Dict[str, Any]]):
        # M10 Law: Ensure cache is cleared on every new object creation (including replace)
        object.__setattr__(self, "_readonly_cache", None)
        
        if init_position is not None:
            if self.navigation.position == (0.0, 0.0):
                object.__setattr__(self, "navigation", replace(self.navigation, position=init_position))
        if init_group_id is not None:
            if self.identity.group_id is None:
                object.__setattr__(self, "identity", replace(self.identity, group_id=init_group_id))
        if init_properties is not None:
            if not self.identity.properties:
                object.__setattr__(self, "identity", replace(self.identity, properties=init_properties))

    def to_readonly(self) -> "EntityState":
        """Returns a read-only view of the entity state."""
        from src.core.immutability import shallow_freeze
        res = replace(self, 
            interaction=shallow_freeze(self.interaction),
            identity=replace(self.identity, 
                properties=ReadOnlyDict(self.identity.properties),
                latest_intent_results=tuple(self.identity.latest_intent_results)
            ),
            navigation=shallow_freeze(self.navigation),
            task=shallow_freeze(self.task),
            inventory=replace(self.inventory, items=tuple(self.inventory.items)),
            combat=replace(self.combat,
                wounds=tuple(self.combat.wounds),
                scars=tuple(self.combat.scars)
            ),
            equipment=replace(self.equipment, 
                slots=shallow_freeze(self.equipment.slots),
                durability=shallow_freeze(self.equipment.durability)
            )
        )
        # object.__setattr__(res, "_readonly_cache", res)
        return res

    def to_dict(self) -> Dict[str, Any]:
        """
        VERIFIED v2: EntityState.to_dict
        """
        from dataclasses import asdict
        return asdict(self)

# EntityState properties moved into class body to support slots.


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
    inventory: InventoryComponent = field(default_factory=InventoryComponent)
    price_modifiers: Dict[str, float] = field(default_factory=dict) # ItemKind -> Multiplier


@dataclass(frozen=True, slots=True)
class CampState:
    """Authoritative state for a persistent world encampment."""
    id: str
    kind: str
    position: tuple[float, float]
    maturity: float = 0.0
    active: bool = True
    faction: str = "hostile"
    last_raid_tick: int = 0


@dataclass(frozen=True, slots=True)
# VERIFIED v2: authoritative_state_model
class AuthoritativeState:
    """
    The minimum state required to determine future simulation outcomes.
    Optimized for execution leanness and deterministic progression.
    VERIFIED v2: authoritative_world_objects
    """
    # VERIFIED v2: state_tick_increment
    tick: int
    seed: int
    world_time: int = 0
    entities: Dict[int, EntityState] = field(default_factory=dict)
    resource_nodes: Dict[int, ResourceNodeState] = field(default_factory=dict)
    ground_items: Dict[int, GroundItemState] = field(default_factory=dict)
    corpses: Dict[int, CorpseState] = field(default_factory=dict)
    chests: Dict[int, ChestState] = field(default_factory=dict)
    buildings: Dict[int, BuildingState] = field(default_factory=dict)
    camps: Dict[str, CampState] = field(default_factory=dict)
    regions: Dict[str, RegionState] = field(default_factory=dict)
    local_scars: Dict[int, LocalScarState] = field(default_factory=dict)
    _readonly_cache: Any = field(default=None, repr=False, compare=False)
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
    transaction_trace: List[str] = field(default_factory=list)
    # VERIFIED v2: rejection_registry_tracking
    rejection_registry: Dict[str, int] = field(default_factory=dict) # Global counters for discarded truth
    # Phase E5.6: Pressure-Aware Economy
    pressure_signals: Dict[str, float] = field(default_factory=dict)

    def __post_init__(self):
        # M10 Law: Ensure cache is cleared on every new object creation (including replace)
        object.__setattr__(self, "_readonly_cache", None)
        object.__setattr__(self, "entities", _readonly_mapping(self.entities))
    current_mode: RuntimeMode = RuntimeMode.NORMAL
    # Phase E5.3: Exactly-Once Idempotency
    processed_transaction_ids: set[str] = field(default_factory=set)
    next_node_id: int = 1000
    next_entity_id: int = 1

    def to_readonly(self) -> AuthoritativeState:
        """Returns a read-only view of the entire world state."""
        if self._readonly_cache is not None:
            return self._readonly_cache
            
        from src.core.immutability import shallow_freeze
        res = replace(self,
            entities=ReadOnlyDict({eid: e.to_readonly() for eid, e in self.entities.items()}),
            resource_nodes=ReadOnlyDict(self.resource_nodes),
            corpses=ReadOnlyDict(self.corpses),
            chests=ReadOnlyDict(self.chests),
            buildings=ReadOnlyDict(self.buildings),
            camps=ReadOnlyDict(self.camps),
            regions=ReadOnlyDict(self.regions),
            local_scars=ReadOnlyDict(self.local_scars),
            home_storage=ReadOnlyDict(self.home_storage),
            groups=shallow_freeze(self.groups),
            terrain=shallow_freeze(self.terrain),
            global_resources=shallow_freeze(self.global_resources),
            periodic_due_ticks=shallow_freeze(self.periodic_due_ticks),
            work_debt=shallow_freeze(self.work_debt),
            blocked_tiles=shallow_freeze(self.blocked_tiles),
            town_tiles=shallow_freeze(self.town_tiles),
            building_tiles=shallow_freeze(self.building_tiles),
            processed_transaction_ids=shallow_freeze(self.processed_transaction_ids)
        )
        # M10 Law: Cache the view on the mutable source
        object.__setattr__(self, "_readonly_cache", res)
        # Optimization: Cache the view on the result itself (idempotency)
        object.__setattr__(res, "_readonly_cache", res)
        return res

    def readonly_view(self) -> AuthoritativeState:
        return self.to_readonly()

    def fingerprint(self) -> Dict[str, Any]:
        """
        Produce a deterministic, multi-domain fingerprint of the current state.
        Used for authoritative export and parity verification.
        """
        from src.replay.fingerprint import StateFingerprinter
        return StateFingerprinter.get_fingerprint(self)
