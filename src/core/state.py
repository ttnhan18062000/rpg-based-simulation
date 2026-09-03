# Compliance IDs: AUTH-009
# Compliance IDs: COMB-106, PROG-053, PROG-056, PROG-058, PROG-059, PROG-093, SOC-005, SOC-166, SOC-167, SOC-169, SOC-170, STRAT-042, STRAT-140, STRAT-165, STRAT-167, STRAT-168, STRAT-175, STRAT-176, STRAT-215, SUB-002, SUB-123, TOWN-024, TOWN-138, TOWN-139, TOWN-140, WORLD-039, WORLD-040
# Compliance IDs: COMB-106, PROG-053, PROG-056, PROG-058, PROG-059, STRAT-042, STRAT-140, STRAT-165, STRAT-167, STRAT-168, STRAT-175, STRAT-176, SUB-123, TOWN-024
from __future__ import annotations

from enum import Enum, IntEnum, auto
from dataclasses import dataclass, field, replace, InitVar, asdict
from types import MappingProxyType
from typing import Dict, Any, Set, Optional, List, Tuple, ClassVar, TYPE_CHECKING
if TYPE_CHECKING:
    from src.core.models.quests import QuestOpportunity, QuestOpportunityStatus
from src.core.strategic import StrategicComponent
from src.core.enums import Faction, EntityRole, DiplomaticState
from src.core.movement_modes import MovementMode
from src.core.governance import RuntimeMode
from src.core.models.inventory import ItemKind, EquipSlot, ItemStack, InventoryComponent, ItemInstance, AcquiredMethod
from src.core.models.social import SocialBond, BetrayalRecord, SocialComponent
from src.core.immutability import shallow_freeze
from src.core.self_model import SelfModelBundle
from src.core.cognition import CognitionModel
from src.systems.lifecycle_systems.genetics import GeneticProfile


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
    _canonical_cache: Any = field(default=None, init=False, repr=False, compare=False)

    def to_canonical_dict(self) -> Dict[str, Any]:
        if self._canonical_cache is not None:
            return self._canonical_cache
        res = {
            "current": self.current,
            "max_stamina": self.max_stamina,
            "regen_rate": self.regen_rate,
            "rest_regen_rate": self.rest_regen_rate,
            "exhaustion_threshold": self.exhaustion_threshold,
            "exhaustion_penalty": self.exhaustion_penalty
        }
        object.__setattr__(self, "_canonical_cache", res)
        return res


    # Drain constants
    ATTACK_COST: ClassVar[float] = 8.0
    MOVE_COST: ClassVar[float] = 3.0
    HARVEST_COST: ClassVar[float] = 5.0
    SKILL_COST_MULT: ClassVar[float] = 1.0  # Multiplied by skill.cost


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
class StatusEffectState:
    """A persistent status effect (e.g. frozen, stunned) applied to an entity."""
    kind: str  # "frozen", "stunned"
    source: str = ""
    magnitude: float = 0.0
    expires_tick: int = -1


@dataclass(frozen=True, slots=True)
class BiologicalComponent:
    """State for sleep, hunger, and other biological pressures."""
    sleep_debt: float = 0.0      # 0.0 to 100.0, affects performance
    hunger: float = 0.0          # 0.0 to 100.0, affects stamina/readiness
    rest_pressure: float = 0.0   # 0.0 to 100.0, forced rest at high values
    last_meal_tick: int = 0
    last_sleep_tick: int = 0
    well_rested_until: int = -1   # Tick until which well-rested buff applies
    _canonical_cache: Any = field(default=None, init=False, repr=False, compare=False)

    def to_canonical_dict(self) -> Dict[str, Any]:
        if self._canonical_cache is not None:
            return self._canonical_cache
        res = {
            "sleep_debt": self.sleep_debt,
            "hunger": self.hunger,
            "rest_pressure": self.rest_pressure,
            "last_meal_tick": self.last_meal_tick,
            "last_sleep_tick": self.last_sleep_tick,
            "well_rested_until": self.well_rested_until
        }
        object.__setattr__(self, "_canonical_cache", res)
        return res



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
    parent_a_entity_id: Optional[int] = None
    parent_b_entity_id: Optional[int] = None
    dependent_entity_ids: list[int] = field(default_factory=list)
    birth_tick: int = 0
    birth_city_id: Optional[int] = None
    reproduction_cooldowns: Dict[int, int] = field(default_factory=dict)  # partner_entity_id -> cooldown_expiry_tick
    active: bool = True
    genetic_profile: Optional[GeneticProfile] = None
    _canonical_cache: Any = field(default=None, init=False, repr=False, compare=False)

    def to_canonical_dict(self) -> Dict[str, Any]:
        if self._canonical_cache is not None:
            return self._canonical_cache
        res = {
            "age_ticks": self.age_ticks,
            "max_age_ticks": self.max_age_ticks,
            "is_permadeath": self.is_permadeath,
            "death_tick": self.death_tick,
            "death_reason": self.death_reason,
            "generation": self.generation,
            "heir_entity_id": self.heir_entity_id,
            "heirlooms": sorted(list(self.heirlooms)),
            "parent_a_entity_id": self.parent_a_entity_id,
            "parent_b_entity_id": self.parent_b_entity_id,
            "dependent_entity_ids": sorted(list(self.dependent_entity_ids)),
            "birth_tick": self.birth_tick,
            "birth_city_id": self.birth_city_id,
            "reproduction_cooldowns": dict(sorted(self.reproduction_cooldowns.items())),
            "active": self.active,
            "genetic_profile": asdict(self.genetic_profile) if self.genetic_profile else None
        }
        object.__setattr__(self, "_canonical_cache", res)
        return res



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
    _canonical_cache: Any = field(default=None, init=False, repr=False, compare=False)

    def to_canonical_dict(self) -> Dict[str, Any]:
        if self._canonical_cache is not None:
            return self._canonical_cache
        res = {
            "id": self.id,
            "position": self.position,
            "kind": self.kind,
            "severity": self.severity,
            "created_tick": self.created_tick,
            "recovery_rate": self.recovery_rate,
            "source_event_id": self.source_event_id,
            "behavioral_modifiers": dict(sorted(self.behavioral_modifiers.items()))
        }
        object.__setattr__(self, "_canonical_cache", res)
        return res


@dataclass(frozen=True, slots=True)
class SiegeState:
    """Durable state of an active siege on a region (E53Cb).

    Survives across ticks. Stored on RegionState.siege_state.
    Transfer to attacker triggers when siege_progress >= 1.0 (handled in E53Cc).
    """
    attacker_faction_id: str
    defender_faction_id: str
    siege_progress: float  # 0.0 to 1.0; transfer triggers at >= 1.0
    started_tick: int

    def to_canonical_dict(self) -> dict:
        return {
            "attacker_faction_id": self.attacker_faction_id,
            "defender_faction_id": self.defender_faction_id,
            "siege_progress": self.siege_progress,
            "started_tick": self.started_tick,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "SiegeState":
        return cls(
            attacker_faction_id=d["attacker_faction_id"],
            defender_faction_id=d["defender_faction_id"],
            siege_progress=float(d["siege_progress"]),
            started_tick=int(d["started_tick"]),
        )


@dataclass(frozen=True, slots=True)
class RegionState:
    """Regional attributes and world dynamic markers."""
    id: str
    name: str
    bounds: tuple[int, int, int, int] # x_min, y_min, x_max, y_max
    kind: str = "FOREST"
    hazard_level: float = 0.0      # 0.0 to 1.0, affects HP/Readiness drain
    hazard_kind: str = "PHYSICAL"  # Semantic hazard type; matched against FactionDefinition.hazard_immunities
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
    # E52A: Per-region demographic cohorts keyed by age bracket ("young"|"adult"|"elder")
    population_cohorts: Dict[str, Any] = field(default_factory=dict)
    # E53Cb: Siege mechanics
    siege_state: Optional["SiegeState"] = None
    service_availability: float = 1.0  # 0.0 to 1.0; degraded by active siege
    _canonical_cache: Any = field(default=None, init=False, repr=False, compare=False)

    def to_canonical_dict(self) -> Dict[str, Any]:
        if self._canonical_cache is not None:
            return self._canonical_cache
        res = {
            "id": self.id,
            "name": self.name,
            "bounds": self.bounds,
            "kind": self.kind,
            "hazard_level": self.hazard_level,
            "hazard_kind": self.hazard_kind,
            "suppression_active": self.suppression_active,
            "calamity_intensity": self.calamity_intensity,
            "trauma_score": self.trauma_score,
            "retaliation_pressure": self.retaliation_pressure,
            "stability": self.stability,
            "owner_faction_id": self.owner_faction_id,
            "influence": self.influence,
            "weather": self.weather,
            "active_modifiers": sorted(list(self.active_modifiers)),
            "price_modifiers": dict(sorted(self.price_modifiers.items())),
            "population_cohorts": {k: v.to_canonical_dict() for k, v in sorted(self.population_cohorts.items())},
            "siege_state": self.siege_state.to_canonical_dict() if self.siege_state is not None else None,
            "service_availability": self.service_availability,
        }
        object.__setattr__(self, "_canonical_cache", res)
        return res

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
    readiness_speed: float = 10.0
    wounds: List[WoundState] = field(default_factory=list)
    scars: List[ScarState] = field(default_factory=list)
    status_effects: List[StatusEffectState] = field(default_factory=list)
    latest_result: Optional["IntentResult"] = None
    _canonical_cache: Any = field(default=None, init=False, repr=False, compare=False)

    def to_canonical_dict(self) -> Dict[str, Any]:
        if self._canonical_cache is not None:
            return self._canonical_cache
        res = {
            "hp": self.hp,
            "max_hp": self.max_hp,
            "atk": self.atk,
            "def_stat": self.def_stat,
            "speed": self.speed,
            "range": self.range,
            "evasion": self.evasion,
            "move_cost": self.move_cost,
            "tactical_role": self.tactical_role,
            "action_style": self.action_style,
            "alive": self.alive,
            "readiness": self.readiness,
            "readiness_speed": self.readiness_speed,
            "wounds": [asdict(w) for w in self.wounds],
            "scars": [asdict(s) for s in self.scars],
            "status_effects": [asdict(s) for s in self.status_effects],
            "latest_result": asdict(self.latest_result) if self.latest_result else None
        }
        object.__setattr__(self, "_canonical_cache", res)
        return res



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
    
    # Phase 3 Hardening: Cache region_id to avoid O(N) scans
    region_id: Optional[str] = None
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
    kind: Optional[str] = None  # "harvest", "ground_item", "corpse", "chest", "guild", "inn", "tavern"
    _canonical_cache: Any = field(default=None, init=False, repr=False, compare=False)

    def to_canonical_dict(self) -> Dict[str, Any]:
        if self._canonical_cache is not None:
            return self._canonical_cache
        res = {
            "target_node_id": self.target_node_id,
            "progress": self.progress,
            "start_tick": self.start_tick,
            "kind": self.kind
        }
        object.__setattr__(self, "_canonical_cache", res)
        return res


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
    _canonical_cache: Any = field(default=None, init=False, repr=False, compare=False)

    def to_canonical_dict(self) -> Dict[str, Any]:
        if self._canonical_cache is not None:
            return self._canonical_cache
        res = {
            "greed": self.greed,
            "bravery": self.bravery,
            "sociability": self.sociability,
            "industry": self.industry
        }
        object.__setattr__(self, "_canonical_cache", res)
        return res


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
    _canonical_cache: Any = field(default=None, init=False, repr=False, compare=False)

    def to_canonical_dict(self) -> Dict[str, Any]:
        if self._canonical_cache is not None:
            return self._canonical_cache
        res = {
            "strength": self.strength,
            "agility": self.agility,
            "vitality": self.vitality,
            "endurance": self.endurance,
            "intelligence": self.intelligence,
            "spirit": self.spirit,
            "wisdom": self.wisdom,
            "perception": self.perception,
            "charisma": self.charisma
        }
        object.__setattr__(self, "_canonical_cache", res)
        return res


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
    territory_maturity: float = 0.0
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
    _canonical_cache: Any = field(default=None, init=False, repr=False, compare=False)

    def to_canonical_dict(self) -> Dict[str, Any]:
        if self._canonical_cache is not None:
            return self._canonical_cache
        res = {
            "role": self.role,
            "faction": self.faction,
            "class_id": self.class_id,
            "evolution_level": self.evolution_level,
            "evolution_points": self.evolution_points,
            "veterancy_rank": self.veterancy_rank,
            "unspent_ap": self.unspent_ap,
            "territory_maturity": self.territory_maturity,
            "known_recipes": sorted(list(self.known_recipes)),
            "learned_skills": sorted(list(self.learned_skills)),
            "active_breakthroughs": sorted(list(self.active_breakthroughs)),
            "personality": self.personality.to_canonical_dict(),
            "life_stage": str(self.life_stage)
        }
        object.__setattr__(self, "_canonical_cache", res)
        return res

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
    _canonical_cache: Any = field(default=None, init=False, repr=False, compare=False)

    def to_canonical_dict(self) -> Dict[str, Any]:
        if self._canonical_cache is not None:
            return self._canonical_cache
        res = {
            "learning_rate": self.learning_rate,
            "stamina_efficiency": self.stamina_efficiency,
            "str_apt": self.str_apt,
            "agi_apt": self.agi_apt,
            "vit_apt": self.vit_apt,
            "end_apt": self.end_apt,
            "int_apt": self.int_apt,
            "spi_apt": self.spi_apt,
            "wis_apt": self.wis_apt,
            "per_apt": self.per_apt,
            "cha_apt": self.cha_apt
        }
        object.__setattr__(self, "_canonical_cache", res)
        return res


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
    formation_tick: int = 0
    escort_target_id: Optional[int] = None
    grievance_log: Tuple[str, ...] = ()
    reward_pool: int = 0
    last_leadership_check_tick: int = 0
    dissolution_tick: Optional[int] = None
    composition_score: float = 0.0  # PartyCompositionScorer result at formation (SOC-232)
    _canonical_cache: Any = field(default=None, init=False, repr=False, compare=False)

    def to_canonical_dict(self) -> Dict[str, Any]:
        if self._canonical_cache is not None:
            return self._canonical_cache
        res = {
            "id": self.id,
            "leader_id": self.leader_id,
            "member_ids": sorted(list(self.member_ids)),
            "anchor": self.anchor,
            "shared_target_id": self.shared_target_id,
            "contract_id": self.contract_id,
            "cohesion_radius": self.cohesion_radius,
            "last_updated_tick": self.last_updated_tick,
            "roles": {str(k): v for k, v in sorted(self.roles.items())},
            "aptitudes": {
                "str": self.str_apt,
                "int": self.int_apt,
                "agi": self.agi_apt,
                "vit": self.vit_apt,
                "end": self.end_apt
            },
            "formation_tick": self.formation_tick,
            "escort_target_id": self.escort_target_id,
            "grievance_log": list(self.grievance_log),
            "reward_pool": self.reward_pool,
            "last_leadership_check_tick": self.last_leadership_check_tick,
            "dissolution_tick": self.dissolution_tick,
            "composition_score": self.composition_score,
        }
        object.__setattr__(self, "_canonical_cache", res)
        return res


@dataclass(frozen=True, slots=True)
class FactionState:
    """Authoritative durable state for a named faction (E53 family)."""
    faction_id: str
    territory: Tuple[str, ...] = ()           # region_ids controlled
    resources: Dict[str, int] = field(default_factory=dict)
    diplomatic_relations: Dict[str, DiplomaticState] = field(default_factory=dict)
    active_doctrines: Tuple[str, ...] = ()
    military_strength: float = 1.0
    tension_level: float = 0.0
    _canonical_cache: Any = field(default=None, init=False, repr=False, compare=False)

    def to_canonical_dict(self) -> Dict[str, Any]:
        if self._canonical_cache is not None:
            return self._canonical_cache
        res: Dict[str, Any] = {
            "faction_id": self.faction_id,
            "territory": list(self.territory),
            "resources": dict(sorted(self.resources.items())),
            "diplomatic_relations": {k: v.value for k, v in sorted(self.diplomatic_relations.items())},
            "active_doctrines": list(self.active_doctrines),
            "military_strength": self.military_strength,
            "tension_level": self.tension_level,
        }
        object.__setattr__(self, "_canonical_cache", res)
        return res

    @classmethod
    def from_dict(cls, d: dict) -> "FactionState":
        return cls(
            faction_id=d["faction_id"],
            territory=tuple(d.get("territory", [])),
            resources=dict(d.get("resources", {})),
            diplomatic_relations={k: DiplomaticState(v) for k, v in d.get("diplomatic_relations", {}).items()},
            active_doctrines=tuple(d.get("active_doctrines", [])),
            military_strength=float(d.get("military_strength", 1.0)),
            tension_level=float(d.get("tension_level", 0.0)),
        )


@dataclass(frozen=True, slots=True)
class ClanState:
    """Authoritative durable state for a named clan (schema-only; idea 40/M4 owns lifecycle)."""
    clan_id: str
    name: str = ""
    member_entity_ids: Tuple[int, ...] = ()
    home_region_ids: Tuple[str, ...] = ()
    tension_level: float = 0.0
    leader_entity_id: Optional[int] = None
    founded_tick: int = 0
    dissolved_tick: Optional[int] = None
    _canonical_cache: Any = field(default=None, init=False, repr=False, compare=False)

    def to_canonical_dict(self) -> Dict[str, Any]:
        if self._canonical_cache is not None:
            return self._canonical_cache
        res: Dict[str, Any] = {
            "clan_id": self.clan_id,
            "name": self.name,
            "member_entity_ids": sorted(self.member_entity_ids),
            "home_region_ids": sorted(self.home_region_ids),
            "tension_level": self.tension_level,
            "leader_entity_id": self.leader_entity_id,
            "founded_tick": self.founded_tick,
            "dissolved_tick": self.dissolved_tick,
        }
        object.__setattr__(self, "_canonical_cache", res)
        return res

    @classmethod
    def from_dict(cls, d: dict) -> "ClanState":
        return cls(
            clan_id=d["clan_id"],
            name=d.get("name", ""),
            member_entity_ids=tuple(d.get("member_entity_ids", [])),
            home_region_ids=tuple(d.get("home_region_ids", [])),
            tension_level=float(d.get("tension_level", 0.0)),
            leader_entity_id=d.get("leader_entity_id"),
            founded_tick=int(d.get("founded_tick", 0)),
            dissolved_tick=d.get("dissolved_tick"),
        )


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
    _spatial_grid_cache: Any = field(default=None, repr=False, compare=False)
    aptitude: AptitudeComponent = field(default_factory=AptitudeComponent)
    combat: CombatComponent = field(default_factory=CombatComponent)
    equipment: EquipmentComponent = field(default_factory=EquipmentComponent)
    navigation: NavigationComponent = field(default_factory=NavigationComponent)
    task: TaskComponent = field(default_factory=TaskComponent)
    stamina: StaminaComponent = field(default_factory=StaminaComponent)
    self_model: SelfModelBundle = field(default_factory=SelfModelBundle)
    cognition: CognitionModel = field(default_factory=CognitionModel)
    _canonical_cache: Any = field(default=None, init=False, repr=False, compare=False)
    timeline: Any = field(default=None, init=False, repr=False, compare=False)

    def to_canonical_dict(self) -> Dict[str, Any]:
        if self._canonical_cache is not None:
            return self._canonical_cache
        
        res = {
            "id": self.id,
            "kind": self.kind,
            "position": self.navigation.position,
            "readiness": self.combat.readiness,
            "active": self.lifecycle.active,
            "interaction": self.interaction.to_canonical_dict(),
            "identity": self.identity.to_canonical_dict(),
            "attributes": self.attributes.to_canonical_dict(),
            "aptitude": self.aptitude.to_canonical_dict(),
            "inventory": self.inventory.to_canonical_dict(),
            "equipment": {str(k): v for k, v in sorted(self.equipment.slots.items())},
            "strategic": {
                "current_project_id": self.strategic.current_project_id,
                "current_objective_id": self.strategic.current_objective_id,
                "projects": {k: {
                    "kind": v.kind, 
                     "status": str(v.status),
                    "active_objective_id": v.active_objective_id,
                    "objectives": [asdict(o) for o in v.objectives]
                } for k, v in sorted(self.strategic.projects.items())},
                "directives": {k: asdict(v) for k, v in sorted(self.strategic.directives.items())},
                "blockers": {k: asdict(v) for k, v in sorted(self.strategic.blockers.items())},
                "leads": {k: asdict(v) for k, v in sorted(self.strategic.leads.items())},
                "concerns": {k: asdict(v) for k, v in sorted(self.strategic.concerns.items())},
                "boredom": dict(sorted(self.strategic.boredom.items())),
                "beliefs": {k: asdict(v) for k, v in sorted(self.strategic.beliefs.items())},
                "marriages": {k: asdict(v) for k, v in sorted(self.strategic.marriages.items())}
            },
            "social": {
                "trust_history": {str(k): v for k, v in sorted(self.social.trust_history.items())},
                "familiarity_history": {str(k): v for k, v in sorted(self.social.familiarity_history.items())},
                "debt_history": {str(k): v for k, v in sorted(self.social.debt_history.items())},
                "fear_history": {str(k): v for k, v in sorted(self.social.fear_history.items())},
                "grudge_history": {str(k): v for k, v in sorted(self.social.grudge_history.items())},
                "combat_loss_counts": {str(k): v for k, v in sorted(self.social.combat_loss_counts.items())},
                "salience_history": {str(k): v for k, v in sorted(self.social.salience_history.items())},
                "bonds": {str(k): asdict(v) for k, v in sorted(self.social.bonds.items())},
                "nemesis_ids": sorted(self.social.nemesis_ids),
                "place_attachment": dict(sorted(self.social.place_attachment.items())),
                "betrayal_count": self.social.betrayal_count,
                "betrayal_records": [asdict(b) for b in self.social.betrayal_records],
                "public_reputation": self.social.public_reputation,
                "heroism_score": self.social.heroism_score,
                "notoriety_score": self.social.notoriety_score,
                "last_offer_tick": self.social.last_offer_tick,
                "rejection_count": {str(k): v for k, v in sorted(self.social.rejection_count.items())},
            },
            "combat": self.combat.to_canonical_dict(),
            "biological": self.biological.to_canonical_dict(),
            "lifecycle": self.lifecycle.to_canonical_dict(),
            "navigation": {
                "target": self.navigation.target,
                "path": self.navigation.path,
                "moved_recently": self.navigation.moved_recently
            },
            "task": {
                "work_kind": self.task.work_kind,
                "payload": dict(sorted(self.task.payload.items()))
            },
            "group_id": self.identity.group_id,
            "properties": dict(sorted(self.identity.properties.items())),
            "self_model": self.self_model.to_canonical_dict(),
            "cognition": self.cognition.to_canonical_dict(),
        }
        object.__setattr__(self, "_canonical_cache", res)
        return res
    
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
        object.__setattr__(self, "_readonly_cache", None)
        object.__setattr__(self, "_canonical_cache", None)
        from collections import deque
        object.__setattr__(self, "timeline", deque(maxlen=200))
        
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
        if self._readonly_cache is not None:
            return self._readonly_cache
            
        if (type(self.identity.properties) is ReadOnlyDict and 
            type(self.identity.latest_intent_results) is tuple and 
            type(self.inventory.items) is tuple and 
            type(self.combat.wounds) is tuple and 
            type(self.combat.scars) is tuple and 
            type(self.equipment.slots) is ReadOnlyDict and 
            type(self.equipment.durability) is ReadOnlyDict):
            object.__setattr__(self, "_readonly_cache", self)
            return self
        
        # Identity Component Optimization
        # Logic ID: CORE-PERF-010 (Manual constructor is faster than replace)
        id_comp = self.identity
        if type(id_comp.properties) is not ReadOnlyDict or type(id_comp.latest_intent_results) is not tuple:
             id_comp = IdentityComponent(
                role=id_comp.role,
                faction=id_comp.faction,
                known_recipes=frozenset(id_comp.known_recipes),
                craft_target=id_comp.craft_target,
                evolution_level=id_comp.evolution_level,
                evolution_points=id_comp.evolution_points,
                veterancy_points=id_comp.veterancy_points,
                veterancy_rank=id_comp.veterancy_rank,
                unspent_ap=id_comp.unspent_ap,
                class_id=id_comp.class_id,
                learned_skills=frozenset(id_comp.learned_skills),
                traits=frozenset(id_comp.traits),
                active_breakthroughs=frozenset(id_comp.active_breakthroughs),
                cooldowns=ReadOnlyDict(id_comp.cooldowns),
                personality=id_comp.personality,
                life_stage=id_comp.life_stage,
                group_id=id_comp.group_id,
                properties=ReadOnlyDict(id_comp.properties),
                latest_intent_results=tuple(id_comp.latest_intent_results)
            )

        inv_comp = self.inventory
        if type(inv_comp.items) is not tuple:
            inv_comp = InventoryComponent(
                max_slots=inv_comp.max_slots,
                items=tuple(inv_comp.items),
                gold=inv_comp.gold
            )
            
        combat_comp = self.combat
        if type(combat_comp.wounds) is not tuple or type(combat_comp.scars) is not tuple:
            combat_comp = CombatComponent(
                hp=combat_comp.hp,
                max_hp=combat_comp.max_hp,
                atk=combat_comp.atk,
                def_stat=combat_comp.def_stat,
                speed=combat_comp.speed,
                range=combat_comp.range,
                evasion=combat_comp.evasion,
                move_cost=combat_comp.move_cost,
                tactical_role=combat_comp.tactical_role,
                action_style=combat_comp.action_style,
                alive=combat_comp.alive,
                readiness=combat_comp.readiness,
                readiness_speed=combat_comp.readiness_speed,
                wounds=tuple(combat_comp.wounds),
                scars=tuple(combat_comp.scars),
                latest_result=combat_comp.latest_result
            )

        equip_comp = self.equipment
        if type(equip_comp.slots) is not ReadOnlyDict or type(equip_comp.durability) is not ReadOnlyDict:
            equip_comp = replace(equip_comp, 
                slots=shallow_freeze(equip_comp.slots),
                durability=shallow_freeze(equip_comp.durability)
            )

        res = EntityState(
            id=self.id,
            kind=self.kind,
            interaction=shallow_freeze(self.interaction),
            identity=id_comp,
            attributes=self.attributes,
            inventory=inv_comp,
            strategic=self.strategic,
            social=self.social,
            biological=self.biological,
            lifecycle=self.lifecycle,
            aptitude=self.aptitude,
            combat=combat_comp,
            equipment=equip_comp,
            navigation=shallow_freeze(self.navigation),
            task=shallow_freeze(self.task),
            stamina=self.stamina,
            self_model=self.self_model,
            cognition=self.cognition
        )
        object.__setattr__(self, "_readonly_cache", res)
        object.__setattr__(res, "_readonly_cache", res)
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
    regen_rate_per_tick: int = 0  # charges regenerated per ecology tick (0 = no regen)
    _canonical_cache: Any = field(default=None, init=False, repr=False, compare=False)
    _readonly_cache: Any = field(default=None, init=False, repr=False, compare=False)

    def __post_init__(self):
        object.__setattr__(self, "_readonly_cache", self)

    def to_canonical_dict(self) -> Dict[str, Any]:
        if self._canonical_cache is not None:
            return self._canonical_cache
        res = {
            "id": self.id,
            "kind": self.kind,
            "position": self.position,
            "yields_item": self.yields_item,
            "remaining_charges": self.remaining_charges,
            "max_charges": self.max_charges,
            "required_ticks": self.required_ticks,
            "respawn_cooldown": self.respawn_cooldown,
            "cooldown_remaining": self.cooldown_remaining,
            "regen_rate_per_tick": self.regen_rate_per_tick,
        }
        object.__setattr__(self, "_canonical_cache", res)
        return res

@dataclass(frozen=True, slots=True)
class GroundItemState:
    """An item dropped on the ground."""
    id: int
    item_id: str
    quantity: int
    position: tuple[float, float]
    _canonical_cache: Any = field(default=None, init=False, repr=False, compare=False)
    _readonly_cache: Any = field(default=None, init=False, repr=False, compare=False)

    def __post_init__(self):
        object.__setattr__(self, "_readonly_cache", self)

    def to_canonical_dict(self) -> Dict[str, Any]:
        if self._canonical_cache is not None:
            return self._canonical_cache
        res = {
            "id": self.id,
            "item_id": self.item_id,
            "quantity": self.quantity,
            "position": self.position
        }
        object.__setattr__(self, "_canonical_cache", res)
        return res

@dataclass(frozen=True, slots=True)
class CorpseState:
    """A dead entity that can be looted."""
    id: int
    original_entity_id: int
    position: tuple[float, float]
    items: List[ItemStack]
    decay_tick: int
    generation: int = 1
    _canonical_cache: Any = field(default=None, init=False, repr=False, compare=False)

    def to_canonical_dict(self) -> Dict[str, Any]:
        if self._canonical_cache is not None:
            return self._canonical_cache
        res = {
            "id": self.id,
            "original_entity_id": self.original_entity_id,
            "position": self.position,
            "items": [i.to_canonical_dict() for i in sorted(self.items, key=lambda x: x.item_id)],
            "decay_tick": self.decay_tick,
            "generation": self.generation
        }
        object.__setattr__(self, "_canonical_cache", res)
        return res


@dataclass(frozen=True, slots=True)
class ChestState:
    """A world object containing loot."""
    id: int
    position: tuple[float, float]
    items: List[ItemStack]
    respawn_tick: int = 0
    cooldown_remaining: int = 0
    _canonical_cache: Any = field(default=None, init=False, repr=False, compare=False)

    def to_canonical_dict(self) -> Dict[str, Any]:
        if self._canonical_cache is not None:
            return self._canonical_cache
        res = {
            "id": self.id,
            "position": self.position,
            "items": [i.to_canonical_dict() for i in sorted(self.items, key=lambda x: x.item_id)],
            "respawn_tick": self.respawn_tick,
            "cooldown_remaining": self.cooldown_remaining
        }
        object.__setattr__(self, "_canonical_cache", res)
        return res


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
    _canonical_cache: Any = field(default=None, init=False, repr=False, compare=False)

    def to_canonical_dict(self) -> Dict[str, Any]:
        if self._canonical_cache is not None:
            return self._canonical_cache
        res = {
            "id": self.id,
            "kind": self.kind,
            "position": self.position,
            "hp": self.hp,
            "max_hp": self.max_hp,
            "functional": self.functional,
            "inventory": self.inventory.to_canonical_dict(),
            "price_modifiers": dict(sorted(self.price_modifiers.items()))
        }
        object.__setattr__(self, "_canonical_cache", res)
        return res


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
    _canonical_cache: Any = field(default=None, init=False, repr=False, compare=False)
    _readonly_cache: Any = field(default=None, init=False, repr=False, compare=False)

    def __post_init__(self):
        object.__setattr__(self, "_readonly_cache", self)

    def to_canonical_dict(self) -> Dict[str, Any]:
        if self._canonical_cache is not None:
            return self._canonical_cache
        res = {
            "id": self.id,
            "kind": self.kind,
            "position": self.position,
            "maturity": self.maturity,
            "active": self.active,
            "faction": self.faction,
            "last_raid_tick": self.last_raid_tick
        }
        object.__setattr__(self, "_canonical_cache", res)
        return res


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
    MAX_PROCESSED_IDS: int = 1000
    MAX_TRACE_SIZE: int = 100
    entities: Dict[int, EntityState] = field(default_factory=dict)
    resource_nodes: Dict[int, ResourceNodeState] = field(default_factory=dict)
    ground_items: Dict[int, GroundItemState] = field(default_factory=dict)
    corpses: Dict[int, CorpseState] = field(default_factory=dict)
    chests: Dict[int, ChestState] = field(default_factory=dict)
    buildings: Dict[int, BuildingState] = field(default_factory=dict)
    camps: Dict[str, CampState] = field(default_factory=dict)
    regions: Dict[str, RegionState] = field(default_factory=dict)
    local_scars: Dict[int, LocalScarState] = field(default_factory=dict)
    item_instances: Dict[int, ItemInstance] = field(default_factory=dict)
    _readonly_cache: Any = field(default=None, repr=False, compare=False)
    _readonly_entities_cache: Any = field(default=None, repr=False, compare=False)
    _spatial_grid_cache: Any = field(default=None, repr=False, compare=False)
    _region_list_cache: Any = field(default=None, repr=False, compare=False)
    _occupancy_map_cache: Any = field(default=None, repr=False, compare=False)
    occupancy_snapshot: Any = field(default=None, repr=False, compare=False)
    movement_cache: Any = field(default=None, repr=False, compare=False)
    world_indexes: Any = field(default=None, repr=False, compare=False)
    semantic_entity_indexes: Any = field(default=None, repr=False, compare=False)
    _index_hits: int = field(default=0, repr=False, compare=False)
    _index_misses: int = field(default=0, repr=False, compare=False)
    transient_claims: Any = field(default=None, repr=False, compare=False)
    _node_map_cache: Any = field(default=None, repr=False, compare=False)
    _active_nodes_grid: Any = field(default=None, repr=False, compare=False)
    _corpse_map_cache: Any = field(default=None, repr=False, compare=False)
    _ground_item_map_cache: Any = field(default=None, repr=False, compare=False)
    _building_map_cache: Any = field(default=None, repr=False, compare=False)
    _region_index_cache: Any = field(default=None, repr=False, compare=False)
    _building_region_map_cache: Any = field(default=None, repr=False, compare=False)
    _regions_global_bounds: Any = field(default=None, repr=False, compare=False)
    _has_hostiles_or_dead_cache: Any = field(default=None, repr=False, compare=False)
    _has_contracts_cache: Any = field(default=None, repr=False, compare=False)
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
    town_entity_ids: set[int] = field(default_factory=set) # Optimization: Cached IDs of entities currently in town
    rng_checkpoint: Any = None
    transaction_trace: List[str] = field(default_factory=list)
    # VERIFIED v2: rejection_registry_tracking
    rejection_registry: Dict[str, int] = field(default_factory=dict) # Global counters for discarded truth
    # Phase E5.6: Pressure-Aware Economy
    pressure_signals: Dict[str, float] = field(default_factory=dict)
    _opt_profile: Any = field(default=None, repr=False, compare=False)
    _force_full_scan: bool = field(default=False, repr=False, compare=False)
    pending_information_responses: List[Dict[str, Any]] = field(default_factory=list, repr=False, compare=False)
    pending_self_model_information_events: List[Dict[str, Any]] = field(default_factory=list, repr=False, compare=False)
    information_source_profiles: List[Any] = field(default_factory=list, repr=False, compare=False)
    feature_flags: Dict[str, Any] = field(default_factory=dict, repr=False, compare=False)
    recent_world_events: List["WorldEvent"] = field(default_factory=list)
    quest_registry: Dict[str, "QuestOpportunity"] = field(default_factory=dict)
    # Epic 4.2B: Durable registry of entities classified as information providers.
    information_providers: Dict[int, "InformationProviderState"] = field(default_factory=dict)
    # Epic 5.3: Durable faction-level state (E53Aa)
    factions: Dict[str, "FactionState"] = field(default_factory=dict)

    def __post_init__(self):
        # M10 Law: Ensure cache is cleared on every new object creation (including replace)
        object.__setattr__(self, "_readonly_cache", None)
        object.__setattr__(self, "_readonly_entities_cache", None)
        object.__setattr__(self, "_spatial_grid_cache", None)
        object.__setattr__(self, "_region_list_cache", None)
        object.__setattr__(self, "_occupancy_map_cache", None)
        object.__setattr__(self, "transient_claims", None)
        object.__setattr__(self, "_node_map_cache", None)
        if getattr(self, "_active_nodes_grid", None) is None:
            object.__setattr__(self, "_active_nodes_grid", None)
        object.__setattr__(self, "_corpse_map_cache", None)
        object.__setattr__(self, "_ground_item_map_cache", None)
        if getattr(self, "_building_map_cache", None) is None:
            object.__setattr__(self, "_building_map_cache", None)
        object.__setattr__(self, "_region_index_cache", None)
        object.__setattr__(self, "_building_region_map_cache", None)
        object.__setattr__(self, "_regions_global_bounds", None)
        object.__setattr__(self, "entities", _readonly_mapping(self.entities))
        has_hostile = False
        has_contracts = False
        if self.entities:
            int_e_keys = [k for k in self.entities.keys() if isinstance(k, int)]
            if int_e_keys and self.next_entity_id <= max(int_e_keys):
                object.__setattr__(self, "next_entity_id", max(int_e_keys) + 1)
            first_fac = next(iter(self.entities.values())).identity.faction
            for ent in self.entities.values():
                if ent.identity.faction != first_fac or not ent.combat.alive:
                    has_hostile = True
                if ent.strategic and ent.strategic.contracts:
                    has_contracts = True
                if has_hostile and has_contracts:
                    break
        if self.resource_nodes:
            int_n_keys = [k for k in self.resource_nodes.keys() if isinstance(k, int)]
            if int_n_keys and self.next_node_id <= max(int_n_keys):
                object.__setattr__(self, "next_node_id", max(int_n_keys) + 1)
        if self.item_instances:
            int_i_keys = [k for k in self.item_instances.keys() if isinstance(k, int)]
            if int_i_keys and self.next_item_instance_id <= max(int_i_keys):
                object.__setattr__(self, "next_item_instance_id", max(int_i_keys) + 1)
        object.__setattr__(self, "_has_hostiles_or_dead_cache", has_hostile)
        object.__setattr__(self, "_has_contracts_cache", has_contracts)
        # Ensure town_entity_ids is frozen if in readonly mode
        if isinstance(self.entities, ReadOnlyDict):
             object.__setattr__(self, "town_entity_ids", shallow_freeze(self.town_entity_ids))
    current_mode: RuntimeMode = RuntimeMode.NORMAL
    # Phase E5.3: Exactly-Once Idempotency
    processed_transaction_ids: List[str] = field(default_factory=list)
    next_node_id: int = 1000
    next_entity_id: int = 1
    next_item_instance_id: int = 1

    def to_readonly(self) -> AuthoritativeState:
        """Returns a read-only view of the entire world state."""
        if self._readonly_cache is not None:
            return self._readonly_cache
            
        from src.core.immutability import shallow_freeze
        
        # CORE-PERF-015: Cache entities dictionary separately to avoid reconstruction
        if self._readonly_entities_cache is None:
            ro_entities = ReadOnlyDict({eid: e.to_readonly() for eid, e in self.entities.items()})
            object.__setattr__(self, "_readonly_entities_cache", ro_entities)
            object.__setattr__(self, "entities", ro_entities)
        else:
            ro_entities = self._readonly_entities_cache

        res = replace(self,
            entities=ro_entities,
            resource_nodes=ReadOnlyDict(self.resource_nodes),
            corpses=ReadOnlyDict(self.corpses),
            chests=ReadOnlyDict(self.chests),
            buildings=ReadOnlyDict(self.buildings),
            camps=ReadOnlyDict(self.camps),
            regions=ReadOnlyDict(self.regions),
            local_scars=ReadOnlyDict(self.local_scars),
            home_storage=ReadOnlyDict(self.home_storage),
            quest_registry=ReadOnlyDict(self.quest_registry),
            information_providers=ReadOnlyDict(self.information_providers),
            factions=ReadOnlyDict(self.factions),
            item_instances=ReadOnlyDict(self.item_instances),
            groups=shallow_freeze(self.groups),
            terrain=shallow_freeze(self.terrain),
            global_resources=shallow_freeze(self.global_resources),
            periodic_due_ticks=shallow_freeze(self.periodic_due_ticks),
            work_debt=shallow_freeze(self.work_debt),
            blocked_tiles=shallow_freeze(self.blocked_tiles),
            town_tiles=shallow_freeze(self.town_tiles),
            building_tiles=shallow_freeze(self.building_tiles),
            processed_transaction_ids=shallow_freeze(self.processed_transaction_ids),
            _has_hostiles_or_dead_cache=self._has_hostiles_or_dead_cache,
            _has_contracts_cache=self._has_contracts_cache,
            _active_nodes_grid=self._active_nodes_grid,
            _building_map_cache=self._building_map_cache,
            occupancy_snapshot=self.occupancy_snapshot,
            movement_cache=self.movement_cache,
            world_indexes=self.world_indexes,
            semantic_entity_indexes=self.semantic_entity_indexes
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

    def validate_dirty_set(self, prior_state: AuthoritativeState, dirty_set: DirtySet) -> None:
        """
        Verify that all changes between prior_state and self are captured in dirty_set.
        Logic ID: PERF-006-AUDIT
        """
        from src.core.dirty import DirtySetLeakError
        
        # 1. Entities
        all_dirty = dirty_set.all_dirty_entities
        for e_id, entity in self.entities.items():
            prior = prior_state.entities.get(e_id)
            if prior is None:
                if e_id not in all_dirty:
                    raise DirtySetLeakError(f"Entity {e_id} added but not in DirtySet")
                continue
            if entity is not prior:
                if e_id not in all_dirty:
                    diff = self._find_entity_diff(prior, entity)
                    raise DirtySetLeakError(f"Entity {e_id} changed but not in DirtySet. Diff: {diff}")

        # 2. Resource Nodes
        for n_id, node in self.resource_nodes.items():
            prior = prior_state.resource_nodes.get(n_id)
            if prior is None or node is not prior:
                if n_id not in dirty_set.resource_node_ids:
                    raise DirtySetLeakError(f"ResourceNode {n_id} changed/added but not in DirtySet")

        # 3. Buildings
        for b_id, building in self.buildings.items():
            prior = prior_state.buildings.get(b_id)
            if prior is None or building is not prior:
                if b_id not in dirty_set.building_ids:
                    raise DirtySetLeakError(f"Building {b_id} changed/added but not in DirtySet")

        # 4. Regions
        for r_id, region in self.regions.items():
            prior = prior_state.regions.get(r_id)
            if prior is None or region is not prior:
                if r_id not in dirty_set.region_ids:
                    raise DirtySetLeakError(f"Region {r_id} changed/added but not in DirtySet")

        # 5. Groups
        for g_id, group in self.groups.items():
            prior = prior_state.groups.get(g_id)
            if prior is None or group is not prior:
                if g_id not in dirty_set.group_ids:
                    raise DirtySetLeakError(f"Group {g_id} changed/added but not in DirtySet")

    def _find_entity_diff(self, prior: EntityState, current: EntityState) -> List[str]:
        """Diagnostic helper to find which components diverged."""
        diffs = []
        if prior.navigation is not current.navigation: diffs.append("navigation")
        if prior.identity is not current.identity: diffs.append("identity")
        if prior.combat is not current.combat: diffs.append("combat")
        if prior.inventory is not current.inventory: diffs.append("inventory")
        if prior.strategic is not current.strategic: diffs.append("strategic")
        if prior.social is not current.social: diffs.append("social")
        if prior.biological is not current.biological: diffs.append("biological")
        if prior.lifecycle is not current.lifecycle: diffs.append("lifecycle")
        if prior.task is not current.task: diffs.append("task")
        if prior.stamina is not current.stamina: diffs.append("stamina")
        if prior.attributes is not current.attributes: diffs.append("attributes")
        return diffs
