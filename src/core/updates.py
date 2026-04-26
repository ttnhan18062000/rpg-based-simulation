from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, Any, Optional, TYPE_CHECKING, List
if TYPE_CHECKING:
    from src.core.state import GroupRecord, ItemStack, EquipSlot, AttributeComponent, LocalScarState, ChestState, EntityState
    from src.core.quests import QuestStatus
    from src.core.strategic import (
        ConcernState, CandidateZone, HypothesisState, SourceTrustEntry,
        CognitionProfile, GroundItemState, CorpseState, BlockerState, LeadState, DirectiveState, ProjectState, ContractState, SocialContract
    )
from src.core.state import ItemStack, EquipSlot, AttributeComponent
from src.core.movement_modes import MovementMode


@dataclass(frozen=True, slots=True)
class InventoryUpdate:
    """Updates to item container and currency."""
    items_add: List[ItemStack] = field(default_factory=list)
    items_remove: List[ItemStack] = field(default_factory=list)
    gold_delta: int = 0

@dataclass(frozen=True, slots=True)
class EquipmentUpdate:
    """Updates to equipped items."""
    slot_updates: Dict[EquipSlot, str | None] = field(default_factory=dict)

@dataclass(frozen=True, slots=True)
class InteractionUpdate:
    """Multi-tick progress update."""
    target_node_id: Optional[int] = None
    progress_delta: float = 0.0
    reset: bool = False

@dataclass(frozen=True, slots=True)
class ResourceTransferIntent:
    """
    Proposed atomic transfer between a world source and an entity.
    Used by ResourceTransactionResolver to enforce conservation laws.
    """
    source_id: str | int
    source_kind: str # "NODE", "GROUND_ITEM", "CORPSE", "CRAFTING", "SHOP_BUY", "SHOP_SELL"
    items_add: List[ItemStack] = field(default_factory=list)
    items_remove: List[ItemStack] = field(default_factory=list)
    gold_delta: int = 0
    gold_cost: int = 0
    xp_reward: int = 0
    transfer_kind: str = "AUTO" # "HARVEST", "LOOT", "PICKUP", "CRAFT", "BUY", "SELL"

@dataclass(frozen=True, slots=True)
class CombatIntent:
    """A single combat interaction intent within a tick."""
    attacker_id: int
    damage: int
    is_opportunity_attack: bool = False
    is_lethal: bool = True
    splash_radius: int = 0
    splash_damage: int = 0

@dataclass(frozen=True, slots=True)
class CombatUpdate:
    """Authoritative combat interaction results."""
    damage_taken: int = 0
    hp_delta: int = 0
    attacker_id: Optional[int] = None
    is_opportunity_attack: bool = False
    alive_set: Optional[bool] = None
    outcome_kind: str = "SURVIVE" # SURVIVE, DEFEAT, KILL
    is_lethal: bool = False
    max_hp_delta: int = 0
    atk_delta: int = 0
    def_delta: int = 0
    xp_gain: int = 0 # Rewards for the attacker
    gold_gain: int = 0
    speed_delta: int = 0
    generation_delta: int = 0 # Lifecycle changes for the defender
    is_permadeath_set: Optional[bool] = None
    simultaneous_intents: List[CombatIntent] = field(default_factory=list)
    trace: Dict[str, float] = field(default_factory=dict) # Breakdown of modifiers

@dataclass(frozen=True, slots=True)
class NavigationUpdate:
    """Updates to movement intent and pathfinding."""
    target_set: Optional[tuple[float, float]] = None
    path_set: Optional[List[tuple[float, float]]] = None
    moved_recently_set: Optional[bool] = None
    movement_mode_set: Optional[MovementMode] = None
    failure_reason: Optional[str] = None

@dataclass(frozen=True, slots=True)
class TaskUpdate:
    """Updates to next-tick work intent."""
    work_kind_set: Optional[str] = None
    payload_set: Optional[Dict[str, Any]] = None
    
@dataclass(frozen=True, slots=True)
class IdentityUpdate:
    """Updates to characteristics or knowledge."""
    role_set: Optional[int] = None
    faction_set: Optional[int] = None
    recipes_learned: list[str] = field(default_factory=list)
    craft_target: Optional[str] = None
    evolution_level_set: Optional[int] = None
    evolution_points_delta: int = 0
    veterancy_points_delta: int = 0
    breakthroughs_add: list[str] = field(default_factory=list)
    unspent_ap_delta: int = 0
    unspent_ap_set: Optional[int] = None

@dataclass(frozen=True, slots=True)
class SocialBondUpdate:
    """Updates to a first-class directed relationship record."""
    target_id: int
    familiarity_delta: float = 0.0
    sentiment_delta: float = 0.0
    last_interaction_tick_set: Optional[int] = None

@dataclass(frozen=True, slots=True)
class SocialUpdate:
    # PH15 Recovery: Bond updates
    bond_updates: List[SocialBondUpdate] = field(default_factory=list)
    trust_delta: Dict[int, float] = field(default_factory=dict)
    familiarity_delta: Dict[int, float] = field(default_factory=dict)
    debt_delta: Dict[int, float] = field(default_factory=dict)
    fear_delta: Dict[int, float] = field(default_factory=dict)
    grudge_delta: Dict[int, float] = field(default_factory=dict)
    salience_delta: Dict[int, float] = field(default_factory=dict)
    
    betrayal_increment: int = 0
    reputation_set: Optional[float] = None
    heroism_delta: float = 0.0
    notoriety_delta: float = 0.0
    
    contracts_add: List[SocialContract] = field(default_factory=list)
    contracts_remove: List[str] = field(default_factory=list) # IDs
    
@dataclass(frozen=True, slots=True)
class BiologicalUpdate:
    """Updates to sleep, hunger, and biological pressures."""
    sleep_debt_delta: float = 0.0
    sleep_debt_set: Optional[float] = None
    hunger_delta: float = 0.0
    hunger_set: Optional[float] = None
    rest_pressure_delta: float = 0.0
    last_meal_tick_set: Optional[int] = None
    last_sleep_tick_set: Optional[int] = None
    well_rested_until_set: Optional[int] = None
    

@dataclass(frozen=True, slots=True)
class AttributeUpdate:
    """Updates to base attributes."""
    strength_delta: int = 0
    agility_delta: int = 0
    vitality_delta: int = 0
    endurance_delta: int = 0
    intelligence_delta: int = 0
    spirit_delta: int = 0
    wisdom_delta: int = 0
    perception_delta: int = 0
    charisma_delta: int = 0

@dataclass(frozen=True, slots=True)
class LifecycleUpdate:
    """Updates to aging and death mechanics."""
    age_delta: int = 0
    generation_delta: int = 0
    is_permadeath_set: Optional[bool] = None
    death_tick_set: Optional[int] = None
    death_reason_set: Optional[str] = None
    heir_entity_id_set: Optional[int] = None
    heirlooms_add: list[str] = field(default_factory=list)


@dataclass(frozen=True, slots=True)
class QuestUpdate:
    """Updates to quest progress and status."""
    quest_id: str
    progress_delta: float = 0.0
    status_set: Optional[QuestStatus] = None

@dataclass(frozen=True, slots=True)
class RewardUpdate:
    """Granting quest rewards."""
    xp_gain: int = 0
    gold_gain: int = 0
    items_gain: List[str] = field(default_factory=list)

@dataclass(frozen=True, slots=True)
class StrategicUpdate:
    """Updates to strategic markers (blockers, leads, directives, projects, concerns, etc.)."""
    # Blockers
    blockers_add_or_update: list[BlockerState] = field(default_factory=list)
    blockers_remove: list[str] = field(default_factory=list)
    # Leads
    leads_add_or_update: list[LeadState] = field(default_factory=list)
    leads_remove: list[str] = field(default_factory=list)
    # Directives
    directives_add_or_update: list[DirectiveState] = field(default_factory=list)
    directives_remove: list[str] = field(default_factory=list)
    # Projects
    projects_add_or_update: list[ProjectState] = field(default_factory=list)
    projects_remove: list[str] = field(default_factory=list)
    current_project_id_set: Optional[str] = None
    current_objective_id_set: Optional[str] = None
    # Boredom (PH5 M2)
    boredom_delta: Dict[str, float] = field(default_factory=dict) # GoalKind -> delta
    # Concerns
    concerns_add_or_update: list[ConcernState] = field(default_factory=list)
    concerns_remove: list[str] = field(default_factory=list)
    # Candidate Zones
    candidate_zones_add_or_update: list[CandidateZone] = field(default_factory=list)
    candidate_zones_remove: list[str] = field(default_factory=list)
    # Hypotheses
    hypotheses_add_or_update: list[HypothesisState] = field(default_factory=list)
    hypotheses_remove: list[str] = field(default_factory=list)
    # Source Trust
    source_trust_updates: list[SourceTrustEntry] = field(default_factory=list)
    # Contracts
    contracts_add_or_update: list[ContractState] = field(default_factory=list)
    contracts_remove: list[str] = field(default_factory=list)
    # Overload
    overload_source_set: Optional[str] = None
    overload_tick_set: Optional[int] = None

@dataclass(frozen=True, slots=True)
class EntityUpdate:
    """
    Authoritative update for a single entity.
    """
    entity_id: int
    kind_set: Optional[str] = None
    new_position: Optional[tuple[float, float]] = None
    moved_this_tick: bool = False
    readiness_delta: float = 0.0
    active: Optional[bool] = None
    interaction: Optional[InteractionUpdate] = None
    resource_transfers: List[ResourceTransferIntent] = field(default_factory=list)
    identity: Optional[IdentityUpdate] = None
    attributes: Optional[AttributeUpdate] = None
    inventory: Optional[InventoryUpdate] = None
    strategic: Optional[StrategicUpdate] = None
    biological: Optional[BiologicalUpdate] = None
    social: Optional[SocialUpdate] = None
    quest: Optional[QuestUpdate] = None
    reward: Optional[RewardUpdate] = None
    lifecycle: Optional[LifecycleUpdate] = None
    combat: Optional[CombatUpdate] = None
    equipment: Optional[EquipmentUpdate] = None
    navigation: Optional[NavigationUpdate] = None
    task: Optional[TaskUpdate] = None
    group_id_set: Optional[int] = None
    property_updates: Dict[str, Any] = field(default_factory=dict)

    def merge(self, other: EntityUpdate) -> EntityUpdate:
        """Merges another EntityUpdate into this one, summing deltas and preferring non-None sets."""
        from dataclasses import replace
        if self.entity_id != other.entity_id:
            raise ValueError("Cannot merge EntityUpdates for different entities")
            
        return replace(self,
            kind_set=other.kind_set if other.kind_set is not None else self.kind_set,
            new_position=other.new_position if other.new_position is not None else self.new_position,
            moved_this_tick=self.moved_this_tick or other.moved_this_tick,
            readiness_delta=self.readiness_delta + other.readiness_delta,
            active=other.active if other.active is not None else self.active,
            interaction=other.interaction if other.interaction is not None else self.interaction, # Simplified
            resource_transfers=self.resource_transfers + other.resource_transfers,
            identity=other.identity if other.identity is not None else self.identity, # Simplified
            attributes=other.attributes if other.attributes is not None else self.attributes, # Simplified
            inventory=other.inventory if other.inventory is not None else self.inventory, # Simplified
            strategic=other.strategic if other.strategic is not None else self.strategic, # Simplified
            biological=other.biological if other.biological is not None else self.biological, # Simplified
            social=other.social if other.social is not None else self.social, # Simplified
            quest=other.quest if other.quest is not None else self.quest, # Simplified
            reward=other.reward if other.reward is not None else self.reward, # Simplified
            lifecycle=other.lifecycle if other.lifecycle is not None else self.lifecycle, # Simplified
            combat=other.combat if other.combat is not None else self.combat, # Simplified
            equipment=other.equipment if other.equipment is not None else self.equipment, # Simplified
            navigation=other.navigation if other.navigation is not None else self.navigation, # Simplified
            task=other.task if other.task is not None else self.task, # Simplified
            group_id_set=other.group_id_set if other.group_id_set is not None else self.group_id_set,
            property_updates={**self.property_updates, **other.property_updates}
        )
        return res


@dataclass(frozen=True, slots=True)
class ResourceNodeUpdate:
    """Updates to a harvestable node."""
    node_id: int
    charges_delta: int = 0
    cooldown_set: Optional[int] = None


@dataclass(frozen=True, slots=True)
class BuildingUpdate:
    """Updates to building health/status."""
    building_id: int
    hp_delta: int = 0
    functional_set: Optional[bool] = None


@dataclass(frozen=True, slots=True)
class WorldUpdate:
    """Updates to regional world state."""
    region_id: str
    hazard_level_set: Optional[float] = None
    suppression_set: Optional[bool] = None
    calamity_intensity_set: Optional[float] = None
    trauma_delta: float = 0.0
    influence_delta: float = 0.0
    owner_faction_id_set: Optional[int] = None
    kind_set: Optional[str] = None
    weather_set: Optional[str] = None
    modifiers_add: List[str] = field(default_factory=list)
    modifiers_remove: List[str] = field(default_factory=list)
    
    def merge(self, other: WorldUpdate) -> WorldUpdate:
        """Merges another WorldUpdate into this one, summing deltas and preferring non-None sets."""
        from dataclasses import replace
        if self.region_id != other.region_id:
            raise ValueError("Cannot merge WorldUpdates for different regions")
            
        return replace(self,
            hazard_level_set=other.hazard_level_set if other.hazard_level_set is not None else self.hazard_level_set,
            suppression_set=other.suppression_set if other.suppression_set is not None else self.suppression_set,
            calamity_intensity_set=other.calamity_intensity_set if other.calamity_intensity_set is not None else self.calamity_intensity_set,
            trauma_delta=self.trauma_delta + other.trauma_delta,
            influence_delta=self.influence_delta + other.influence_delta,
            owner_faction_id_set=other.owner_faction_id_set if other.owner_faction_id_set is not None else self.owner_faction_id_set,
            kind_set=other.kind_set if other.kind_set is not None else self.kind_set,
            weather_set=other.weather_set if other.weather_set is not None else self.weather_set,
            modifiers_add=list(set(self.modifiers_add + other.modifiers_add)),
            modifiers_remove=list(set(self.modifiers_remove + other.modifiers_remove))
        )


@dataclass(frozen=True, slots=True)
class ChestUpdate:
    """Updates to a world chest."""
    chest_id: int
    cooldown_set: Optional[int] = None
    items_set: Optional[List[ItemStack]] = None

@dataclass(frozen=True, slots=True)
class StateUpdate:
    """
    A collection of authoritative changes to be applied to the world state.
    """
    entity_updates: Dict[int, EntityUpdate] = field(default_factory=dict)
    entities_add: List[EntityState] = field(default_factory=list)
    entities_remove: List[int] = field(default_factory=list)
    node_updates: Dict[int, ResourceNodeUpdate] = field(default_factory=dict)
    ground_items_add_or_update: List[GroundItemState] = field(default_factory=list)
    ground_items_remove: List[int] = field(default_factory=list)
    corpses_add_or_update: List[CorpseState] = field(default_factory=list)
    corpses_remove: List[int] = field(default_factory=list)
    scars_add_or_update: List[LocalScarState] = field(default_factory=list)
    scars_remove: List[int] = field(default_factory=list)
    chest_updates: Dict[int, ChestUpdate] = field(default_factory=dict)
    chest_add_or_update: List[ChestState] = field(default_factory=list)
    building_updates: Dict[int, BuildingUpdate] = field(default_factory=dict)
    world_updates: Dict[str, WorldUpdate] = field(default_factory=dict)
    resource_updates: Dict[str, float] = field(default_factory=dict)
    home_storage_updates: Dict[int, InventoryUpdate] = field(default_factory=dict) # Milestone 5
    periodic_updates: Dict[str, int] = field(default_factory=dict)
    work_debt_updates: Dict[str, int] = field(default_factory=dict)
    groups_add_or_update: List[GroupRecord] = field(default_factory=list)
    groups_remove: List[int] = field(default_factory=list)
    maturity_set: Optional[int] = None
    last_calamity_tick_set: Optional[int] = None
    rng_checkpoint: Any = None
    
    def replace(self, **kwargs) -> StateUpdate:
        from dataclasses import replace
        return replace(self, **kwargs)
