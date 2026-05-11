# Compliance IDs: TOWN-001, TOWN-002, TOWN-131, TOWN-156, TOWN-157, TOWN-159, TOWN-160, TOWN-161, TOWN-162, TOWN-163
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, Any, Optional, TYPE_CHECKING, List
if TYPE_CHECKING:
    from src.core.state import GroupRecord, ItemStack, EquipSlot, AttributeComponent, LocalScarState, ChestState, EntityState, GroundItemState, CorpseState, WoundState, ScarState
    from src.core.quests import QuestStatus
    from src.core.strategic import (
        ConcernState, CandidateZone, HypothesisState, SourceTrustEntry,
        CognitionProfile, BlockerState, LeadState, DirectiveState, ProjectState, 
        ContractState, TurningPointState
    )
from src.core.state import ItemStack, EquipSlot, AttributeComponent
from src.core.movement_modes import MovementMode
from src.core.enums import ReasonCode
from src.core.update_models.inventory import InventoryUpdate
from src.core.update_models.quests import QuestUpdate
from src.core.update_models.resources import ResourceTransferIntent


@dataclass(frozen=True, slots=True)
class RejectionEvent:
    """
    Structured record of an authoritative rejection.
    Logic ID: RPG-AUTH-009
    """
    tick: int
    actor_id: int
    action_kind: str
    reason: ReasonCode
    target_id: Optional[int | str] = None


@dataclass(frozen=True, slots=True)
class EquipmentUpdate:
    """Updates to equipped items."""
    slot_updates: Dict[EquipSlot, str | None] = field(default_factory=dict)
    durability_delta: Dict[EquipSlot, float] = field(default_factory=dict)
    durability_set: Dict[EquipSlot, float] = field(default_factory=dict)

    def merge(self, other: EquipmentUpdate) -> EquipmentUpdate:
        """Merge another EquipmentUpdate into this one."""
        from dataclasses import replace
        new_slots = {**self.slot_updates, **other.slot_updates}
        new_deltas = dict(self.durability_delta)
        for s, d in other.durability_delta.items():
            new_deltas[s] = new_deltas.get(s, 0.0) + d
        new_sets = {**self.durability_set, **other.durability_set}
        return replace(self, slot_updates=new_slots, durability_delta=new_deltas, durability_set=new_sets)

@dataclass(frozen=True, slots=True)
class InteractionUpdate:
    """Multi-tick progress update."""
    target_node_id: Optional[int] = None
    progress_delta: float = 0.0
    reset: bool = False

    def merge(self, other: InteractionUpdate) -> InteractionUpdate:
        from dataclasses import replace
        return replace(self,
            target_node_id=other.target_node_id if other.target_node_id is not None else self.target_node_id,
            progress_delta=self.progress_delta + other.progress_delta,
            reset=self.reset or other.reset
        )

@dataclass(frozen=True, slots=True)
class CombatIntent:
    """A single combat interaction intent within a tick."""
    attacker_id: int
    damage: int
    is_opportunity_attack: bool = False
    is_lethal: bool = True
    splash_radius: int = 0
    splash_damage: int = 0
    impact_pos: Optional[tuple[float, float]] = None

@dataclass(frozen=True, slots=True)
class CombatUpdate:
    """Authoritative combat interaction results."""
    damage_taken: int = 0
    hp_delta: int = 0
    attacker_id: Optional[int] = None
    is_opportunity_attack: bool = False
    alive_set: Optional[bool] = None
    outcome_kind: str = "SURVIVE" # SURVIVE, DEFEAT, KILL, REJECTED
    is_lethal: bool = False
    failure_reason: Optional[str] = None
    max_hp_delta: int = 0
    atk_delta: int = 0
    def_delta: int = 0
    speed_delta: int = 0
    generation_delta: int = 0 # Lifecycle changes for the defender
    is_permadeath_set: Optional[bool] = None
    simultaneous_intents: List[CombatIntent] = field(default_factory=list)
    resource_transfers: List[ResourceTransferIntent] = field(default_factory=list)
    equipment_upd: Optional[EquipmentUpdate] = None # For defender
    attacker_equipment_upd: Optional[EquipmentUpdate] = None
    wound_update: Optional[WoundUpdate] = None
    social_upd: Optional[SocialUpdate] = None
    strategic_upd: Optional[StrategicUpdate] = None
    trace: Dict[str, float] = field(default_factory=dict) # Breakdown of modifiers

    def merge(self, other: CombatUpdate) -> CombatUpdate:
        """Merges another CombatUpdate into this one, aggregating results."""
        from dataclasses import replace
        return replace(self,
            damage_taken=self.damage_taken + other.damage_taken,
            hp_delta=self.hp_delta + other.hp_delta,
            attacker_id=other.attacker_id if other.attacker_id is not None else self.attacker_id,
            is_opportunity_attack=self.is_opportunity_attack or other.is_opportunity_attack,
            alive_set=other.alive_set if other.alive_set is not None else self.alive_set,
            outcome_kind=other.outcome_kind if (self.outcome_kind == "SURVIVE" or other.outcome_kind == "KILL") else self.outcome_kind,
            is_lethal=self.is_lethal or other.is_lethal,
            max_hp_delta=self.max_hp_delta + other.max_hp_delta,
            atk_delta=self.atk_delta + other.atk_delta,
            def_delta=self.def_delta + other.def_delta,
            speed_delta=self.speed_delta + other.speed_delta,
            generation_delta=self.generation_delta + other.generation_delta,
            is_permadeath_set=other.is_permadeath_set if other.is_permadeath_set is not None else self.is_permadeath_set,
            simultaneous_intents=self.simultaneous_intents + other.simultaneous_intents,
            resource_transfers=self.resource_transfers + other.resource_transfers,
            equipment_upd=other.equipment_upd if other.equipment_upd is not None else self.equipment_upd,
            attacker_equipment_upd=other.attacker_equipment_upd if other.attacker_equipment_upd is not None else self.attacker_equipment_upd,
            wound_update=other.wound_update if other.wound_update is not None else self.wound_update,
            social_upd=self.social_upd.merge(other.social_upd) if self.social_upd and other.social_upd else (other.social_upd or self.social_upd),
            strategic_upd=self.strategic_upd.merge(other.strategic_upd) if self.strategic_upd and other.strategic_upd else (other.strategic_upd or self.strategic_upd),
            trace={**self.trace, **other.trace}
        )

@dataclass(frozen=True, slots=True)
class NavigationUpdate:
    """Updates to movement intent and pathfinding."""
    target_set: Optional[tuple[float, float]] = None
    target_clear: bool = False
    path_set: Optional[List[tuple[float, float]]] = None
    moved_recently_set: Optional[bool] = None
    movement_mode_set: Optional[MovementMode] = None
    failure_reason: Optional[str] = None
    clear_target: bool = False
    clear_path: bool = False
    
    # Phase 4 additions
    wait_count_delta: int = 0
    oscillation_count_delta: int = 0
    last_position_set: Optional[tuple[float, float]] = None

    def merge(self, other: NavigationUpdate) -> NavigationUpdate:
        from dataclasses import replace
        return replace(self,
            target_set=other.target_set if other.target_set is not None else self.target_set,
            target_clear=self.target_clear or other.target_clear,
            path_set=other.path_set if other.path_set is not None else self.path_set,
            moved_recently_set=other.moved_recently_set if other.moved_recently_set is not None else self.moved_recently_set,
            movement_mode_set=other.movement_mode_set if other.movement_mode_set is not None else self.movement_mode_set,
            failure_reason=other.failure_reason if other.failure_reason is not None else self.failure_reason,
            clear_target=self.clear_target or other.clear_target,
            clear_path=self.clear_path or other.clear_path,
            wait_count_delta=self.wait_count_delta + other.wait_count_delta,
            oscillation_count_delta=self.oscillation_count_delta + other.oscillation_count_delta,
            last_position_set=other.last_position_set if other.last_position_set is not None else self.last_position_set
        )

@dataclass(frozen=True, slots=True)
class TaskUpdate:
    """Updates to next-tick work intent."""
    work_kind_set: Optional[str] = None
    payload_set: Optional[Dict[str, Any]] = None

    def merge(self, other: TaskUpdate) -> TaskUpdate:
        from dataclasses import replace
        new_payload = dict(self.payload_set or {})
        if other.payload_set:
            new_payload.update(other.payload_set)
        return replace(self,
            work_kind_set=other.work_kind_set if other.work_kind_set is not None else self.work_kind_set,
            payload_set=new_payload if new_payload else None
        )
    
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
    learned_skills: list[str] = field(default_factory=list)
    traits_add: list[str] = field(default_factory=list)
    traits_remove: list[str] = field(default_factory=list)
    cooldown_updates: Dict[str, int] = field(default_factory=dict) # skill_id -> tick_ready
    
    def merge(self, other: IdentityUpdate) -> IdentityUpdate:
        from dataclasses import replace
        return replace(self,
            role_set=other.role_set if other.role_set is not None else self.role_set,
            faction_set=other.faction_set if other.faction_set is not None else self.faction_set,
            recipes_learned=list(set(self.recipes_learned + other.recipes_learned)),
            craft_target=other.craft_target if other.craft_target is not None else self.craft_target,
            evolution_level_set=other.evolution_level_set if other.evolution_level_set is not None else self.evolution_level_set,
            evolution_points_delta=self.evolution_points_delta + other.evolution_points_delta,
            veterancy_points_delta=self.veterancy_points_delta + other.veterancy_points_delta,
            breakthroughs_add=list(set(self.breakthroughs_add + other.breakthroughs_add)),
            unspent_ap_delta=self.unspent_ap_delta + other.unspent_ap_delta,
            unspent_ap_set=other.unspent_ap_set if other.unspent_ap_set is not None else self.unspent_ap_set,
            learned_skills=list(set(self.learned_skills + other.learned_skills)),
            traits_add=list(set(self.traits_add + other.traits_add)),
            traits_remove=list(set(self.traits_remove + other.traits_remove)),
            cooldown_updates={**self.cooldown_updates, **other.cooldown_updates}
        )

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
    betrayal_records_add: List[Any] = field(default_factory=list) # List[BetrayalRecord]
    reputation_set: Optional[float] = None
    heroism_delta: float = 0.0
    notoriety_delta: float = 0.0
    
    # Domain 7 Hardening: Social Fatigue
    last_offer_tick_set: Optional[int] = None
    rejection_increment: Dict[int, int] = field(default_factory=dict) # SourceID -> Increment
    
    # Domain 4 Hardening
    nemesis_promotion: List[int] = field(default_factory=list) # EntityIDs to add to nemesis_ids
    place_attachment_delta: Dict[str, float] = field(default_factory=dict) # RegionID -> Delta
    
    contracts_add: List[ContractState] = field(default_factory=list)
    contracts_remove: List[str] = field(default_factory=list) # IDs
    
    def merge(self, other: SocialUpdate) -> SocialUpdate:
        """Merges another SocialUpdate into this one."""
        from dataclasses import replace
        
        # Merge dictionaries by summing values
        new_trust = dict(self.trust_delta)
        for k, v in other.trust_delta.items():
            new_trust[k] = new_trust.get(k, 0.0) + v
            
        new_grudge = dict(self.grudge_delta)
        for k, v in other.grudge_delta.items():
            new_grudge[k] = new_grudge.get(k, 0.0) + v
            
        new_places = dict(self.place_attachment_delta)
        for k, v in other.place_attachment_delta.items():
            new_places[k] = new_places.get(k, 0.0) + v

        return replace(self,
            bond_updates=self.bond_updates + other.bond_updates,
            trust_delta=new_trust,
            grudge_delta=new_grudge,
            nemesis_promotion=self.nemesis_promotion + other.nemesis_promotion,
            place_attachment_delta=new_places,
            betrayal_increment=self.betrayal_increment + other.betrayal_increment,
            heroism_delta=self.heroism_delta + other.heroism_delta,
            notoriety_delta=self.notoriety_delta + other.notoriety_delta,
            contracts_add=self.contracts_add + other.contracts_add,
            contracts_remove=self.contracts_remove + other.contracts_remove
        )
    
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
    
    def merge(self, other: BiologicalUpdate) -> BiologicalUpdate:
        from dataclasses import replace
        return replace(self,
            sleep_debt_delta=self.sleep_debt_delta + other.sleep_debt_delta,
            sleep_debt_set=other.sleep_debt_set if other.sleep_debt_set is not None else self.sleep_debt_set,
            hunger_delta=self.hunger_delta + other.hunger_delta,
            hunger_set=other.hunger_set if other.hunger_set is not None else self.hunger_set,
            rest_pressure_delta=self.rest_pressure_delta + other.rest_pressure_delta,
            last_meal_tick_set=other.last_meal_tick_set if other.last_meal_tick_set is not None else self.last_meal_tick_set,
            last_sleep_tick_set=other.last_sleep_tick_set if other.last_sleep_tick_set is not None else self.last_sleep_tick_set,
            well_rested_until_set=other.well_rested_until_set if other.well_rested_until_set is not None else self.well_rested_until_set
        )
    

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
    
    def merge(self, other: AttributeUpdate) -> AttributeUpdate:
        from dataclasses import replace
        return replace(self,
            strength_delta=self.strength_delta + other.strength_delta,
            agility_delta=self.agility_delta + other.agility_delta,
            vitality_delta=self.vitality_delta + other.vitality_delta,
            endurance_delta=self.endurance_delta + other.endurance_delta,
            intelligence_delta=self.intelligence_delta + other.intelligence_delta,
            spirit_delta=self.spirit_delta + other.spirit_delta,
            wisdom_delta=self.wisdom_delta + other.wisdom_delta,
            perception_delta=self.perception_delta + other.perception_delta,
            charisma_delta=self.charisma_delta + other.charisma_delta
        )

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

    def merge(self, other: LifecycleUpdate) -> LifecycleUpdate:
        from dataclasses import replace
        return replace(self,
            age_delta=self.age_delta + other.age_delta,
            generation_delta=self.generation_delta + other.generation_delta,
            is_permadeath_set=other.is_permadeath_set if other.is_permadeath_set is not None else self.is_permadeath_set,
            death_tick_set=other.death_tick_set if other.death_tick_set is not None else self.death_tick_set,
            death_reason_set=other.death_reason_set if other.death_reason_set is not None else self.death_reason_set,
            heir_entity_id_set=other.heir_entity_id_set if other.heir_entity_id_set is not None else self.heir_entity_id_set,
            heirlooms_add=self.heirlooms_add + other.heirlooms_add
        )



@dataclass(frozen=True, slots=True)
class RewardUpdate:
    """
    Non-inventory progression rewards (XP, evolution points).
    Authority: Allowed from workers for pure progression, but verified by ApplyGate.
    Law: Gold and Items must use ResourceTransferIntent for authoritative conservation.
    """
    xp_gain: int = 0
    evolution_points_delta: int = 0
    
    def merge(self, other: RewardUpdate) -> RewardUpdate:
        from dataclasses import replace
        return replace(self,
            xp_gain=self.xp_gain + other.xp_gain,
            evolution_points_delta=self.evolution_points_delta + other.evolution_points_delta
        )

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
    # Turning Points
    turning_points_add: list[TurningPointState] = field(default_factory=list)
    # Overload
    overload_source_set: Optional[str] = None
    overload_tick_set: Optional[int] = None

    def merge(self, other: StrategicUpdate) -> StrategicUpdate:
        """Merges another StrategicUpdate into this one."""
        from dataclasses import replace
        # Dictionaries sum deltas
        new_boredom = dict(self.boredom_delta)
        for k, v in other.boredom_delta.items():
            new_boredom[k] = new_boredom.get(k, 0.0) + v
            
        return replace(self,
            blockers_add_or_update=self.blockers_add_or_update + other.blockers_add_or_update,
            blockers_remove=self.blockers_remove + other.blockers_remove,
            leads_add_or_update=self.leads_add_or_update + other.leads_add_or_update,
            leads_remove=self.leads_remove + other.leads_remove,
            directives_add_or_update=self.directives_add_or_update + other.directives_add_or_update,
            directives_remove=self.directives_remove + other.directives_remove,
            projects_add_or_update=self.projects_add_or_update + other.projects_add_or_update,
            projects_remove=self.projects_remove + other.projects_remove,
            current_project_id_set=other.current_project_id_set if other.current_project_id_set is not None else self.current_project_id_set,
            current_objective_id_set=other.current_objective_id_set if other.current_objective_id_set is not None else self.current_objective_id_set,
            boredom_delta=new_boredom,
            concerns_add_or_update=self.concerns_add_or_update + other.concerns_add_or_update,
            concerns_remove=self.concerns_remove + other.concerns_remove,
            candidate_zones_add_or_update=self.candidate_zones_add_or_update + other.candidate_zones_add_or_update,
            candidate_zones_remove=self.candidate_zones_remove + other.candidate_zones_remove,
            hypotheses_add_or_update=self.hypotheses_add_or_update + other.hypotheses_add_or_update,
            hypotheses_remove=self.hypotheses_remove + other.hypotheses_remove,
            source_trust_updates=self.source_trust_updates + other.source_trust_updates,
            contracts_add_or_update=self.contracts_add_or_update + other.contracts_add_or_update,
            contracts_remove=self.contracts_remove + other.contracts_remove,
            turning_points_add=self.turning_points_add + other.turning_points_add,
            overload_source_set=other.overload_source_set if other.overload_source_set is not None else self.overload_source_set,
            overload_tick_set=other.overload_tick_set if other.overload_tick_set is not None else self.overload_tick_set
        )

@dataclass(frozen=True, slots=True)
class StaminaUpdate:
    """Updates to stamina resource."""
    current_delta: float = 0.0
    current_set: Optional[float] = None
    max_stamina_set: Optional[float] = None

    def merge(self, other: StaminaUpdate) -> StaminaUpdate:
        from dataclasses import replace
        return replace(self,
            current_delta=self.current_delta + other.current_delta,
            current_set=other.current_set if other.current_set is not None else self.current_set,
            max_stamina_set=other.max_stamina_set if other.max_stamina_set is not None else self.max_stamina_set
        )

@dataclass(frozen=True, slots=True)
class WoundUpdate:
    """New wounds and scar transitions."""
    wounds_add: List[WoundState] = field(default_factory=list)
    wounds_heal: List[str] = field(default_factory=list)  # wound IDs to heal
    scars_add: List[ScarState] = field(default_factory=list)

    def merge(self, other: WoundUpdate) -> WoundUpdate:
        from dataclasses import replace
        return replace(self,
            wounds_add=self.wounds_add + other.wounds_add,
            wounds_heal=self.wounds_heal + other.wounds_heal,
            scars_add=self.scars_add + other.scars_add
        )

@dataclass(frozen=True, slots=True)
class EntityUpdate:
    """
    Authoritative update for a single entity.
    Logic ID: TOWN-001 (Action proposals are typed intents)
    Logic ID: TOWN-002 (Every side effect is represented as a typed update bucket)
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
    stamina_update: Optional[StaminaUpdate] = None
    wound_update: Optional[WoundUpdate] = None
    group_id_set: Optional[int] = None
    intent_results: List[IntentResult] = field(default_factory=list)
    property_updates: Dict[str, Any] = field(default_factory=dict)

    def merge(self, other: EntityUpdate) -> EntityUpdate:
        """Merges another EntityUpdate into this one, summing deltas and preferring non-None sets."""
        from dataclasses import replace
        if self.entity_id != other.entity_id:
            raise ValueError("Cannot merge EntityUpdates for different entities")
            
        res = replace(self,
            kind_set=other.kind_set if other.kind_set is not None else self.kind_set,
            new_position=other.new_position if other.new_position is not None else self.new_position,
            moved_this_tick=self.moved_this_tick or other.moved_this_tick,
            readiness_delta=self.readiness_delta + other.readiness_delta,
            active=other.active if other.active is not None else self.active,
            interaction=other.interaction if other.interaction is not None else self.interaction,
            resource_transfers=self.resource_transfers + other.resource_transfers,
            identity=self.identity.merge(other.identity) if self.identity and other.identity else (other.identity or self.identity),
            attributes=self.attributes.merge(other.attributes) if self.attributes and other.attributes else (other.attributes or self.attributes),
            inventory=self.inventory.merge(other.inventory) if self.inventory and other.inventory else (other.inventory or self.inventory),
            strategic=self.strategic.merge(other.strategic) if self.strategic and other.strategic else (other.strategic or self.strategic),
            biological=self.biological.merge(other.biological) if self.biological and other.biological else (other.biological or self.biological),
            social=self.social.merge(other.social) if self.social and other.social else (other.social or self.social),
            quest=self.quest.merge(other.quest) if self.quest and other.quest else (other.quest or self.quest),
            reward=self.reward.merge(other.reward) if self.reward and other.reward else (other.reward or self.reward),
            lifecycle=self.lifecycle.merge(other.lifecycle) if self.lifecycle and other.lifecycle else (other.lifecycle or self.lifecycle),
            combat=self.combat.merge(other.combat) if self.combat and other.combat else (other.combat or self.combat),
            equipment=self.equipment.merge(other.equipment) if self.equipment and other.equipment else (other.equipment or self.equipment),
            navigation=self.navigation.merge(other.navigation) if self.navigation and other.navigation else (other.navigation or self.navigation),
            task=self.task.merge(other.task) if self.task and other.task else (other.task or self.task),
            stamina_update=self.stamina_update.merge(other.stamina_update) if self.stamina_update and other.stamina_update else (other.stamina_update or self.stamina_update),
            wound_update=self.wound_update.merge(other.wound_update) if self.wound_update and other.wound_update else (other.wound_update or self.wound_update),
            group_id_set=other.group_id_set if other.group_id_set is not None else self.group_id_set,
            intent_results=self.intent_results + other.intent_results,
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
    inventory: Optional[InventoryUpdate] = None
    price_modifiers_set: Optional[Dict[str, float]] = None


@dataclass(frozen=True, slots=True)
class WorldUpdate:
    """Updates to regional world state."""
    region_id: str
    hazard_level_set: Optional[float] = None
    suppression_set: Optional[bool] = None
    calamity_intensity_set: Optional[float] = None
    trauma_delta: float = 0.0
    trauma_score_set: Optional[float] = None
    retaliation_pressure_delta: float = 0.0
    retaliation_pressure_set: Optional[float] = None
    influence_delta: float = 0.0
    owner_faction_id_set: Optional[int] = None
    kind_set: Optional[str] = None
    weather_set: Optional[str] = None
    modifiers_add: List[str] = field(default_factory=list)
    modifiers_remove: List[str] = field(default_factory=list)
    price_modifiers_set: Optional[Dict[str, float]] = None
    
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
            trauma_score_set=other.trauma_score_set if other.trauma_score_set is not None else self.trauma_score_set,
            retaliation_pressure_delta=self.retaliation_pressure_delta + other.retaliation_pressure_delta,
            retaliation_pressure_set=other.retaliation_pressure_set if other.retaliation_pressure_set is not None else self.retaliation_pressure_set,
            influence_delta=self.influence_delta + other.influence_delta,
            owner_faction_id_set=other.owner_faction_id_set if other.owner_faction_id_set is not None else self.owner_faction_id_set,
            kind_set=other.kind_set if other.kind_set is not None else self.kind_set,
            weather_set=other.weather_set if other.weather_set is not None else self.weather_set,
            modifiers_add=list(set(self.modifiers_add + other.modifiers_add)),
            modifiers_remove=list(set(self.modifiers_remove + other.modifiers_remove)),
            price_modifiers_set=other.price_modifiers_set if other.price_modifiers_set is not None else self.price_modifiers_set
        )


@dataclass(frozen=True, slots=True)
class ChestUpdate:
    """Updates to a world chest."""
    chest_id: int
    cooldown_set: Optional[int] = None
    items_set: Optional[List[ItemStack]] = None

@dataclass(frozen=True, slots=True)
class CampUpdate:
    """Updates to a persistent encampment."""
    id: str
    maturity_delta: float = 0.0
    active_set: Optional[bool] = None
    last_raid_tick_set: Optional[int] = None


@dataclass(frozen=True, slots=True)
class StateUpdate:
    """
    A collection of authoritative changes to be applied to the world state.
    VERIFIED v2: action_proposals_as_intents
    """
    entity_updates: Dict[int, EntityUpdate] = field(default_factory=dict)
    entities_add: List[EntityState] = field(default_factory=list)
    entities_remove: List[int] = field(default_factory=list)
    nodes_add: List[ResourceNodeState] = field(default_factory=list)
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
    camp_updates: Dict[str, CampUpdate] = field(default_factory=dict)
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
    transaction_trace: List[str] = field(default_factory=list)
    rejections_delta: Dict[str, int] = field(default_factory=dict) # Rejection counters for this tick
    pressure_signals_set: Optional[Dict[str, float]] = None
    current_mode_set: Optional[RuntimeMode] = None
    rejection_events: List[RejectionEvent] = field(default_factory=list) # Detailed rejection audit
    processed_transaction_ids: set[str] = field(default_factory=set)
    next_node_id_set: Optional[int] = None
    next_entity_id_set: Optional[int] = None
    
    def replace(self, **kwargs) -> StateUpdate:
        from dataclasses import replace
        return replace(self, **kwargs)
