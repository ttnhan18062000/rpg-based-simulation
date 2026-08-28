# Compliance IDs: AUTH-005, AUTH-006, AUTH-007, INFRA-122
# Compliance IDs: TOWN-001, TOWN-002, TOWN-131, TOWN-156, TOWN-157, TOWN-159, TOWN-160, TOWN-161, TOWN-162, TOWN-163
from __future__ import annotations

from dataclasses import dataclass, field, replace
from typing import Dict, Any, Optional, TYPE_CHECKING, List, Tuple
if TYPE_CHECKING:
    from src.core.state import GroupRecord, ItemStack, EquipSlot, AttributeComponent, LocalScarState, ChestState, EntityState, GroundItemState, CorpseState, WoundState, ScarState
    from src.core.quests import QuestStatus
    from src.core.strategic import (
        ConcernState, CandidateZone, HypothesisState, SourceTrustEntry,
        CognitionProfile, BlockerState, LeadState, DirectiveState, ProjectState,
        ContractState, TurningPointState, CommittedIntention
    )
    from src.engine.policy import GovernorPolicy
    from src.core.models.quests import QuestOpportunity, QuestOpportunityStatus
from src.core.state import ItemStack, EquipSlot, AttributeComponent, LifeStage
from src.core.models.social import RelationshipRole
from src.core.movement_modes import MovementMode
from src.core.enums import ReasonCode, DiplomaticState
from src.core.update_models.inventory import InventoryUpdate
from src.core.update_models.quests import QuestUpdate
from src.core.update_models.resources import ResourceTransferIntent
from src.core.dirty import DirtySet


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

    def is_noop(self) -> bool:
        return not self.slot_updates and not self.durability_delta and not self.durability_set

    def merge(self, other: EquipmentUpdate) -> EquipmentUpdate:
        """Merge another EquipmentUpdate into this one."""
        if not other or other.is_noop():
            return self
        changes = {}
        if other.slot_updates:
            changes["slot_updates"] = {**self.slot_updates, **other.slot_updates}
        if other.durability_delta:
            new_deltas = dict(self.durability_delta)
            for s, d in other.durability_delta.items():
                new_deltas[s] = new_deltas.get(s, 0.0) + d
            changes["durability_delta"] = new_deltas
        if other.durability_set:
            changes["durability_set"] = {**self.durability_set, **other.durability_set}
        return replace(self, **changes)

@dataclass(frozen=True, slots=True)
class InteractionUpdate:
    """Multi-tick progress update."""
    target_node_id: Optional[int] = None
    progress_delta: float = 0.0
    reset: bool = False

    def is_noop(self) -> bool:
        return self.target_node_id is None and self.progress_delta == 0.0 and not self.reset

    def merge(self, other: InteractionUpdate) -> InteractionUpdate:
        if not other or other.is_noop():
            return self
        changes = {}
        if other.target_node_id is not None: changes["target_node_id"] = other.target_node_id
        if other.progress_delta != 0.0: changes["progress_delta"] = self.progress_delta + other.progress_delta
        if other.reset: changes["reset"] = True
        return replace(self, **changes)

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

    def is_noop(self) -> bool:
        return (self.damage_taken == 0 and self.hp_delta == 0 and self.attacker_id is None and 
                self.alive_set is None and self.max_hp_delta == 0 and self.atk_delta == 0 and 
                self.def_delta == 0 and self.speed_delta == 0 and self.generation_delta == 0 and 
                not self.simultaneous_intents and not self.resource_transfers)

    def merge(self, other: CombatUpdate) -> CombatUpdate:
        """Merges another CombatUpdate into this one, aggregating results."""
        if not other or other.is_noop():
            return self
        changes = {}
        if other.damage_taken != 0: changes["damage_taken"] = self.damage_taken + other.damage_taken
        if other.hp_delta != 0: changes["hp_delta"] = self.hp_delta + other.hp_delta
        if other.attacker_id is not None: changes["attacker_id"] = other.attacker_id
        if other.is_opportunity_attack: changes["is_opportunity_attack"] = True
        if other.alive_set is not None: changes["alive_set"] = other.alive_set
        if other.outcome_kind != "SURVIVE":
             changes["outcome_kind"] = other.outcome_kind if (self.outcome_kind == "SURVIVE" or other.outcome_kind == "KILL") else self.outcome_kind
        if other.is_lethal: changes["is_lethal"] = True
        if other.max_hp_delta != 0: changes["max_hp_delta"] = self.max_hp_delta + other.max_hp_delta
        if other.atk_delta != 0: changes["atk_delta"] = self.atk_delta + other.atk_delta
        if other.def_delta != 0: changes["def_delta"] = self.def_delta + other.def_delta
        if other.speed_delta != 0: changes["speed_delta"] = self.speed_delta + other.speed_delta
        if other.generation_delta != 0: changes["generation_delta"] = self.generation_delta + other.generation_delta
        if other.is_permadeath_set is not None: changes["is_permadeath_set"] = other.is_permadeath_set
        if other.simultaneous_intents: changes["simultaneous_intents"] = self.simultaneous_intents + other.simultaneous_intents
        if other.resource_transfers: changes["resource_transfers"] = self.resource_transfers + other.resource_transfers
        if other.equipment_upd: changes["equipment_upd"] = other.equipment_upd
        if other.attacker_equipment_upd: changes["attacker_equipment_upd"] = other.attacker_equipment_upd
        if other.wound_update: changes["wound_update"] = other.wound_update
        if other.social_upd: changes["social_upd"] = self.social_upd.merge(other.social_upd) if self.social_upd else other.social_upd
        if other.strategic_upd: changes["strategic_upd"] = self.strategic_upd.merge(other.strategic_upd) if self.strategic_upd else other.strategic_upd
        if other.trace: changes["trace"] = {**self.trace, **other.trace}
        return replace(self, **changes)

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
    region_id_set: Optional[str] = None

    def is_noop(self) -> bool:
        return (self.target_set is None and not self.target_clear and self.path_set is None and 
                self.moved_recently_set is None and self.movement_mode_set is None and 
                self.failure_reason is None and not self.clear_target and not self.clear_path and 
                self.wait_count_delta == 0 and self.oscillation_count_delta == 0 and 
                self.last_position_set is None and self.region_id_set is None)

    def merge(self, other: NavigationUpdate) -> NavigationUpdate:
        if not other or other.is_noop():
            return self
        changes = {}
        if other.target_set is not None: changes["target_set"] = other.target_set
        if other.target_clear: changes["target_clear"] = True
        if other.path_set is not None: changes["path_set"] = other.path_set
        if other.moved_recently_set is not None: changes["moved_recently_set"] = other.moved_recently_set
        if other.movement_mode_set is not None: changes["movement_mode_set"] = other.movement_mode_set
        if other.failure_reason is not None: changes["failure_reason"] = other.failure_reason
        if other.clear_target: changes["clear_target"] = True
        if other.clear_path: changes["clear_path"] = True
        if other.wait_count_delta != 0: changes["wait_count_delta"] = self.wait_count_delta + other.wait_count_delta
        if other.oscillation_count_delta != 0: changes["oscillation_count_delta"] = self.oscillation_count_delta + other.oscillation_count_delta
        if other.last_position_set is not None: changes["last_position_set"] = other.last_position_set
        if other.region_id_set is not None: changes["region_id_set"] = other.region_id_set
        return replace(self, **changes)

@dataclass(frozen=True, slots=True)
class TaskUpdate:
    """Updates to next-tick work intent."""
    work_kind_set: Optional[str] = None
    payload_set: Optional[Dict[str, Any]] = None

    def is_noop(self) -> bool:
        return self.work_kind_set is None and not self.payload_set

    def merge(self, other: TaskUpdate) -> TaskUpdate:
        if not other or other.is_noop():
            return self
        changes = {}
        if other.work_kind_set is not None: changes["work_kind_set"] = other.work_kind_set
        if other.payload_set:
            new_payload = dict(self.payload_set or {})
            new_payload.update(other.payload_set)
            changes["payload_set"] = new_payload
        return replace(self, **changes)
    
@dataclass(frozen=True, slots=True)
class IdentityUpdate:
    """Updates to characteristics or knowledge."""
    role_set: Optional[int] = None
    faction_set: Optional[int] = None
    recipes_learned: list[str] = field(default_factory=list)
    craft_target: Optional[str] = None
    evolution_level_set: Optional[int] = None
    life_stage_set: Optional[LifeStage] = None
    evolution_points_delta: int = 0
    veterancy_points_delta: int = 0
    breakthroughs_add: list[str] = field(default_factory=list)
    unspent_ap_delta: int = 0
    unspent_ap_set: Optional[int] = None
    learned_skills: list[str] = field(default_factory=list)
    traits_add: list[str] = field(default_factory=list)
    traits_remove: list[str] = field(default_factory=list)
    cooldown_updates: Dict[str, int] = field(default_factory=dict) # skill_id -> tick_ready
    
    def is_noop(self) -> bool:
        return (self.role_set is None and self.faction_set is None and not self.recipes_learned and
                self.craft_target is None and self.evolution_level_set is None and
                self.life_stage_set is None and
                self.evolution_points_delta == 0 and self.veterancy_points_delta == 0 and
                not self.breakthroughs_add and self.unspent_ap_delta == 0 and
                self.unspent_ap_set is None and not self.learned_skills and
                not self.traits_add and not self.traits_remove and not self.cooldown_updates)

    def merge(self, other: IdentityUpdate) -> IdentityUpdate:
        if not other or other.is_noop():
            return self
        changes = {}
        if other.role_set is not None: changes["role_set"] = other.role_set
        if other.faction_set is not None: changes["faction_set"] = other.faction_set
        if other.recipes_learned: changes["recipes_learned"] = list(set(self.recipes_learned + other.recipes_learned))
        if other.craft_target is not None: changes["craft_target"] = other.craft_target
        if other.evolution_level_set is not None: changes["evolution_level_set"] = other.evolution_level_set
        if other.life_stage_set is not None: changes["life_stage_set"] = other.life_stage_set
        if other.evolution_points_delta != 0: changes["evolution_points_delta"] = self.evolution_points_delta + other.evolution_points_delta
        if other.veterancy_points_delta != 0: changes["veterancy_points_delta"] = self.veterancy_points_delta + other.veterancy_points_delta
        if other.breakthroughs_add: changes["breakthroughs_add"] = list(set(self.breakthroughs_add + other.breakthroughs_add))
        if other.unspent_ap_delta != 0: changes["unspent_ap_delta"] = self.unspent_ap_delta + other.unspent_ap_delta
        if other.unspent_ap_set is not None: changes["unspent_ap_set"] = other.unspent_ap_set
        if other.learned_skills: changes["learned_skills"] = list(set(self.learned_skills + other.learned_skills))
        if other.traits_add: changes["traits_add"] = list(set(self.traits_add + other.traits_add))
        if other.traits_remove: changes["traits_remove"] = list(set(self.traits_remove + other.traits_remove))
        if other.cooldown_updates: changes["cooldown_updates"] = {**self.cooldown_updates, **other.cooldown_updates}
        return replace(self, **changes)

@dataclass(frozen=True, slots=True)
class SocialBondUpdate:
    """Updates to a first-class directed relationship record."""
    target_id: int
    familiarity_delta: float = 0.0
    sentiment_delta: float = 0.0
    last_interaction_tick_set: Optional[int] = None
    role_set: Optional[RelationshipRole] = None

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
    combat_loss_delta: Dict[int, int] = field(default_factory=dict) # EntityID -> +1 per defeat by that entity
    
    contracts_add: List[ContractState] = field(default_factory=list)
    contracts_remove: List[str] = field(default_factory=list) # IDs
    
    def is_noop(self) -> bool:
        return (not self.bond_updates and not self.trust_delta and not self.familiarity_delta and 
                not self.debt_delta and not self.fear_delta and not self.grudge_delta and 
                not self.salience_delta and self.betrayal_increment == 0 and 
                not self.betrayal_records_add and self.reputation_set is None and 
                self.heroism_delta == 0.0 and self.notoriety_delta == 0.0 and 
                self.last_offer_tick_set is None and not self.rejection_increment and 
                not self.nemesis_promotion and not self.place_attachment_delta and
                not self.combat_loss_delta and not self.contracts_add and not self.contracts_remove)

    def merge(self, other: SocialUpdate) -> SocialUpdate:
        """Merges another SocialUpdate into this one."""
        if not other or other.is_noop():
            return self
        
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

        new_combat_loss = dict(self.combat_loss_delta)
        for k, v in other.combat_loss_delta.items():
            new_combat_loss[k] = new_combat_loss.get(k, 0) + v

        return SocialUpdate(
            bond_updates=self.bond_updates + other.bond_updates,
            trust_delta=new_trust,
            familiarity_delta={**self.familiarity_delta, **other.familiarity_delta},
            debt_delta={**self.debt_delta, **other.debt_delta},
            fear_delta={**self.fear_delta, **other.fear_delta},
            grudge_delta=new_grudge,
            salience_delta={**self.salience_delta, **other.salience_delta},
            betrayal_increment=self.betrayal_increment + other.betrayal_increment,
            betrayal_records_add=self.betrayal_records_add + other.betrayal_records_add,
            reputation_set=other.reputation_set if other.reputation_set is not None else self.reputation_set,
            heroism_delta=self.heroism_delta + other.heroism_delta,
            notoriety_delta=self.notoriety_delta + other.notoriety_delta,
            last_offer_tick_set=other.last_offer_tick_set if other.last_offer_tick_set is not None else self.last_offer_tick_set,
            rejection_increment={**self.rejection_increment, **other.rejection_increment},
            nemesis_promotion=self.nemesis_promotion + other.nemesis_promotion,
            place_attachment_delta=new_places,
            combat_loss_delta=new_combat_loss,
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
    
    def is_noop(self) -> bool:
        return (self.sleep_debt_delta == 0.0 and self.sleep_debt_set is None and 
                self.hunger_delta == 0.0 and self.hunger_set is None and 
                self.rest_pressure_delta == 0.0 and self.last_meal_tick_set is None and 
                self.last_sleep_tick_set is None and self.well_rested_until_set is None)

    def merge(self, other: BiologicalUpdate) -> BiologicalUpdate:
        if not other or other.is_noop():
            return self
        return BiologicalUpdate(
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
    
    def is_noop(self) -> bool:
        return (self.strength_delta == 0 and self.agility_delta == 0 and self.vitality_delta == 0 and 
                self.endurance_delta == 0 and self.intelligence_delta == 0 and 
                self.spirit_delta == 0 and self.wisdom_delta == 0 and 
                self.perception_delta == 0 and self.charisma_delta == 0)

    def merge(self, other: AttributeUpdate) -> AttributeUpdate:
        if not other or other.is_noop():
            return self
        changes = {}
        if other.strength_delta != 0: changes["strength_delta"] = self.strength_delta + other.strength_delta
        if other.agility_delta != 0: changes["agility_delta"] = self.agility_delta + other.agility_delta
        if other.vitality_delta != 0: changes["vitality_delta"] = self.vitality_delta + other.vitality_delta
        if other.endurance_delta != 0: changes["endurance_delta"] = self.endurance_delta + other.endurance_delta
        if other.intelligence_delta != 0: changes["intelligence_delta"] = self.intelligence_delta + other.intelligence_delta
        if other.spirit_delta != 0: changes["spirit_delta"] = self.spirit_delta + other.spirit_delta
        if other.wisdom_delta != 0: changes["wisdom_delta"] = self.wisdom_delta + other.wisdom_delta
        if other.perception_delta != 0: changes["perception_delta"] = self.perception_delta + other.perception_delta
        if other.charisma_delta != 0: changes["charisma_delta"] = self.charisma_delta + other.charisma_delta
        return replace(self, **changes)

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

    def is_noop(self) -> bool:
        return (self.age_delta == 0 and self.generation_delta == 0 and 
                self.is_permadeath_set is None and self.death_tick_set is None and 
                self.death_reason_set is None and self.heir_entity_id_set is None and 
                not self.heirlooms_add)

    def merge(self, other: LifecycleUpdate) -> LifecycleUpdate:
        if not other or other.is_noop():
            return self
        changes = {}
        if other.age_delta != 0: changes["age_delta"] = self.age_delta + other.age_delta
        if other.generation_delta != 0: changes["generation_delta"] = self.generation_delta + other.generation_delta
        if other.is_permadeath_set is not None: changes["is_permadeath_set"] = other.is_permadeath_set
        if other.death_tick_set is not None: changes["death_tick_set"] = other.death_tick_set
        if other.death_reason_set is not None: changes["death_reason_set"] = other.death_reason_set
        if other.heir_entity_id_set is not None: changes["heir_entity_id_set"] = other.heir_entity_id_set
        if other.heirlooms_add: changes["heirlooms_add"] = self.heirlooms_add + other.heirlooms_add
        return replace(self, **changes)

@dataclass(frozen=True, slots=True)
class RewardUpdate:
    """
    Non-inventory progression rewards (XP, evolution points).
    Authority: Allowed from workers for pure progression, but verified by ApplyGate.
    Law: Gold and Items must use ResourceTransferIntent for authoritative conservation.
    """
    xp_gain: int = 0
    evolution_points_delta: int = 0
    
    def is_noop(self) -> bool:
        return self.xp_gain == 0 and self.evolution_points_delta == 0

    def merge(self, other: RewardUpdate) -> RewardUpdate:
        if not other or other.is_noop():
            return self
        changes = {}
        if other.xp_gain != 0: changes["xp_gain"] = self.xp_gain + other.xp_gain
        if other.evolution_points_delta != 0: changes["evolution_points_delta"] = self.evolution_points_delta + other.evolution_points_delta
        return replace(self, **changes)

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
    # Routing (adventure-route observability restore)
    last_routing_family_set: Optional[str] = None
    last_routing_tick_set: Optional[int] = None
    # Beliefs
    beliefs_add_or_update: list[Any] = field(default_factory=list)
    beliefs_remove: list[str] = field(default_factory=list)
    # Committed Intentions
    committed_intentions_add_or_update: list[CommittedIntention] = field(default_factory=list)
    committed_intentions_remove: list[str] = field(default_factory=list)  # by intention_id

    def is_noop(self) -> bool:
        return (not self.blockers_add_or_update and not self.blockers_remove and
                not self.leads_add_or_update and not self.leads_remove and
                not self.directives_add_or_update and not self.directives_remove and
                not self.projects_add_or_update and not self.projects_remove and
                self.current_project_id_set is None and self.current_objective_id_set is None and
                not self.boredom_delta and not self.concerns_add_or_update and
                not self.concerns_remove and not self.candidate_zones_add_or_update and
                not self.candidate_zones_remove and not self.hypotheses_add_or_update and
                not self.hypotheses_remove and not self.source_trust_updates and
                not self.contracts_add_or_update and not self.contracts_remove and
                not self.turning_points_add and self.overload_source_set is None and
                self.overload_tick_set is None and self.last_routing_family_set is None and
                self.last_routing_tick_set is None and not self.beliefs_add_or_update and
                not self.beliefs_remove and not self.committed_intentions_add_or_update and
                not self.committed_intentions_remove)

    def merge(self, other: StrategicUpdate) -> StrategicUpdate:
        """Merges another StrategicUpdate into this one."""
        if not other or other.is_noop():
            return self
            
        # Dictionaries sum deltas
        new_boredom = dict(self.boredom_delta)
        for k, v in other.boredom_delta.items():
            new_boredom[k] = new_boredom.get(k, 0.0) + v
            
        return StrategicUpdate(
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
            overload_tick_set=other.overload_tick_set if other.overload_tick_set is not None else self.overload_tick_set,
            last_routing_family_set=other.last_routing_family_set if other.last_routing_family_set is not None else self.last_routing_family_set,
            last_routing_tick_set=other.last_routing_tick_set if other.last_routing_tick_set is not None else self.last_routing_tick_set,
            beliefs_add_or_update=self.beliefs_add_or_update + other.beliefs_add_or_update,
            beliefs_remove=self.beliefs_remove + other.beliefs_remove,
            committed_intentions_add_or_update=self.committed_intentions_add_or_update + other.committed_intentions_add_or_update,
            committed_intentions_remove=self.committed_intentions_remove + other.committed_intentions_remove
        )

@dataclass(frozen=True, slots=True)
class StaminaUpdate:
    """Updates to stamina resource."""
    current_delta: float = 0.0
    current_set: Optional[float] = None
    max_stamina_set: Optional[float] = None

    def is_noop(self) -> bool:
        return self.current_delta == 0.0 and self.current_set is None and self.max_stamina_set is None

    def merge(self, other: StaminaUpdate) -> StaminaUpdate:
        if not other or other.is_noop():
            return self
        changes = {}
        if other.current_delta != 0.0: changes["current_delta"] = self.current_delta + other.current_delta
        if other.current_set is not None: changes["current_set"] = other.current_set
        if other.max_stamina_set is not None: changes["max_stamina_set"] = other.max_stamina_set
        return replace(self, **changes)

@dataclass(frozen=True, slots=True)
class WoundUpdate:
    """New wounds and scar transitions."""
    wounds_add: List[WoundState] = field(default_factory=list)
    wounds_heal: List[str] = field(default_factory=list)  # wound IDs to heal
    scars_add: List[ScarState] = field(default_factory=list)

    def is_noop(self) -> bool:
        return not self.wounds_add and not self.wounds_heal and not self.scars_add

    def merge(self, other: WoundUpdate) -> WoundUpdate:
        if not other or other.is_noop():
            return self
        changes = {}
        if other.wounds_add: changes["wounds_add"] = self.wounds_add + other.wounds_add
        if other.wounds_heal: changes["wounds_heal"] = self.wounds_heal + other.wounds_heal
        if other.scars_add: changes["scars_add"] = self.scars_add + other.scars_add
        return replace(self, **changes)

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
    self_model_bundle_set: Optional[Any] = None
    cognition_bundle_set: Optional[Any] = None
    intent_results: List[IntentResult] = field(default_factory=list)
    property_updates: Dict[str, Any] = field(default_factory=dict)

    def is_noop(self) -> bool:
        return (self.kind_set is None and self.new_position is None and 
                not self.moved_this_tick and self.readiness_delta == 0.0 and 
                self.active is None and (self.interaction is None or self.interaction.is_noop()) and 
                not self.resource_transfers and (self.identity is None or self.identity.is_noop()) and 
                (self.attributes is None or self.attributes.is_noop()) and 
                (self.inventory is None or self.inventory.is_noop()) and 
                (self.strategic is None or self.strategic.is_noop()) and 
                (self.biological is None or self.biological.is_noop()) and 
                (self.social is None or self.social.is_noop()) and 
                (self.quest is None or self.quest.is_noop()) and 
                (self.reward is None or self.reward.is_noop()) and 
                (self.lifecycle is None or self.lifecycle.is_noop()) and 
                (self.combat is None or self.combat.is_noop()) and 
                (self.equipment is None or self.equipment.is_noop()) and 
                (self.navigation is None or self.navigation.is_noop()) and 
                (self.task is None or self.task.is_noop()) and 
                (self.stamina_update is None or self.stamina_update.is_noop()) and 
                (self.wound_update is None or self.wound_update.is_noop()) and 
                self.group_id_set is None and self.self_model_bundle_set is None and
                self.cognition_bundle_set is None and not self.intent_results and
                not self.property_updates)

    def merge(self, other: EntityUpdate) -> EntityUpdate:
        """Merges another EntityUpdate into this one, summing deltas and preferring non-None sets."""
        if not other or other.is_noop():
            return self
        if self.entity_id != other.entity_id:
            raise ValueError("Cannot merge EntityUpdates for different entities")
            
        changes = {}
        if other.kind_set is not None: changes["kind_set"] = other.kind_set
        if other.new_position is not None: changes["new_position"] = other.new_position
        if other.moved_this_tick: changes["moved_this_tick"] = True
        if other.readiness_delta != 0.0: changes["readiness_delta"] = self.readiness_delta + other.readiness_delta
        if other.active is not None: changes["active"] = other.active
        if other.interaction: changes["interaction"] = self.interaction.merge(other.interaction) if self.interaction else other.interaction
        if other.resource_transfers: changes["resource_transfers"] = self.resource_transfers + other.resource_transfers
        if other.identity: changes["identity"] = self.identity.merge(other.identity) if self.identity else other.identity
        if other.attributes: changes["attributes"] = self.attributes.merge(other.attributes) if self.attributes else other.attributes
        if other.inventory: changes["inventory"] = self.inventory.merge(other.inventory) if self.inventory else other.inventory
        if other.strategic: changes["strategic"] = self.strategic.merge(other.strategic) if self.strategic else other.strategic
        if other.biological: changes["biological"] = self.biological.merge(other.biological) if self.biological else other.biological
        if other.social: changes["social"] = self.social.merge(other.social) if self.social else other.social
        if other.quest: changes["quest"] = self.quest.merge(other.quest) if self.quest else other.quest
        if other.reward: changes["reward"] = self.reward.merge(other.reward) if self.reward else other.reward
        if other.lifecycle: changes["lifecycle"] = self.lifecycle.merge(other.lifecycle) if self.lifecycle else other.lifecycle
        if other.combat: changes["combat"] = self.combat.merge(other.combat) if self.combat else other.combat
        if other.equipment: changes["equipment"] = self.equipment.merge(other.equipment) if self.equipment else other.equipment
        if other.navigation: changes["navigation"] = self.navigation.merge(other.navigation) if self.navigation else other.navigation
        if other.task: changes["task"] = self.task.merge(other.task) if self.task else other.task
        if other.stamina_update: changes["stamina_update"] = self.stamina_update.merge(other.stamina_update) if self.stamina_update else other.stamina_update
        if other.wound_update: changes["wound_update"] = self.wound_update.merge(other.wound_update) if self.wound_update else other.wound_update
        if other.group_id_set is not None: changes["group_id_set"] = other.group_id_set
        if other.self_model_bundle_set is not None: changes["self_model_bundle_set"] = other.self_model_bundle_set
        if other.cognition_bundle_set is not None: changes["cognition_bundle_set"] = other.cognition_bundle_set
        if other.intent_results: changes["intent_results"] = self.intent_results + other.intent_results
        if other.property_updates: changes["property_updates"] = {**self.property_updates, **other.property_updates}
        return replace(self, **changes)


@dataclass(frozen=True, slots=True)
class ResourceNodeUpdate:
    """Updates to a harvestable node."""
    node_id: int
    charges_delta: int = 0
    cooldown_set: Optional[int] = None

    def merge(self, other: ResourceNodeUpdate) -> ResourceNodeUpdate:
        if self.node_id != other.node_id:
            raise ValueError("Cannot merge ResourceNodeUpdates for different nodes")
        return replace(self,
            charges_delta=self.charges_delta + other.charges_delta,
            cooldown_set=other.cooldown_set if other.cooldown_set is not None else self.cooldown_set
        )


@dataclass(frozen=True, slots=True)
class BuildingUpdate:
    """Updates to building health/status."""
    building_id: int
    hp_delta: int = 0
    functional_set: Optional[bool] = None
    inventory: Optional[InventoryUpdate] = None
    price_modifiers_set: Optional[Dict[str, float]] = None

    def merge(self, other: BuildingUpdate) -> BuildingUpdate:
        if self.building_id != other.building_id:
            raise ValueError("Cannot merge BuildingUpdates for different buildings")
        
        merged_inventory = self.inventory
        if self.inventory and other.inventory:
            merged_inventory = self.inventory.merge(other.inventory)
        elif other.inventory:
            merged_inventory = other.inventory

        return replace(self,
            hp_delta=self.hp_delta + other.hp_delta,
            functional_set=other.functional_set if other.functional_set is not None else self.functional_set,
            inventory=merged_inventory,
            price_modifiers_set=other.price_modifiers_set if other.price_modifiers_set is not None else self.price_modifiers_set
        )



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
    # E52A: Per-region demographic cohort state (Dict[bracket, PopulationCohort])
    population_cohorts_set: Optional[Dict[str, Any]] = None
    # E53Cb: Siege mechanics
    service_availability_delta: float = 0.0
    siege_state_set: Optional[Any] = None   # Optional[SiegeState] — Any to avoid circular import
    siege_state_clear: bool = False          # True = remove existing siege_state (None is no-op sentinel)
    siege_progress_delta: float = 0.0

    def merge(self, other: WorldUpdate) -> WorldUpdate:
        """Merges another WorldUpdate into this one, summing deltas and preferring non-None sets."""
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
            price_modifiers_set=other.price_modifiers_set if other.price_modifiers_set is not None else self.price_modifiers_set,
            population_cohorts_set=other.population_cohorts_set if other.population_cohorts_set is not None else self.population_cohorts_set,
            service_availability_delta=self.service_availability_delta + other.service_availability_delta,
            siege_state_set=other.siege_state_set if other.siege_state_set is not None else self.siege_state_set,
            siege_state_clear=self.siege_state_clear or other.siege_state_clear,
            siege_progress_delta=self.siege_progress_delta + other.siege_progress_delta,
        )


@dataclass(frozen=True, slots=True)
class ChestUpdate:
    """Updates to a world chest."""
    chest_id: int
    cooldown_set: Optional[int] = None
    items_set: Optional[List[ItemStack]] = None

    def merge(self, other: ChestUpdate) -> ChestUpdate:
        if self.chest_id != other.chest_id:
            raise ValueError("Cannot merge ChestUpdates for different chests")
        return replace(self,
            cooldown_set=other.cooldown_set if other.cooldown_set is not None else self.cooldown_set,
            items_set=other.items_set if other.items_set is not None else self.items_set
        )

@dataclass(frozen=True, slots=True)
class CampUpdate:
    """Updates to a persistent encampment."""
    id: str
    maturity_delta: float = 0.0
    active_set: Optional[bool] = None
    last_raid_tick_set: Optional[int] = None

    def merge(self, other: CampUpdate) -> CampUpdate:
        if self.id != other.id:
            raise ValueError("Cannot merge CampUpdates for different camps")
        return replace(self,
            maturity_delta=self.maturity_delta + other.maturity_delta,
            active_set=other.active_set if other.active_set is not None else self.active_set,
            last_raid_tick_set=other.last_raid_tick_set if other.last_raid_tick_set is not None else self.last_raid_tick_set
        )



@dataclass(frozen=True, slots=True)
class QuestOpportunityRewardIntent:
    """
    Signal that the named entity should receive the reward for the named
    QuestOpportunity.  The actual reward amounts are read from
    state.quest_registry[quest_id].reward_spec inside the enforce stage.
    """
    entity_id: int
    quest_id: str


@dataclass(frozen=True, slots=True)
class FactionUpdate:
    """Typed mutation record for a single faction's durable state (E53Aa)."""
    faction_id: str
    tension_delta: float = 0.0
    military_strength_set: Optional[float] = None
    territory_add: Tuple[str, ...] = ()
    territory_remove: Tuple[str, ...] = ()
    resources_delta: Dict[str, int] = field(default_factory=dict)
    diplomatic_relations_set: Dict[str, DiplomaticState] = field(default_factory=dict)
    active_doctrines_set: Optional[Tuple[str, ...]] = None

    def is_noop(self) -> bool:
        return (
            self.tension_delta == 0.0
            and self.military_strength_set is None
            and not self.territory_add
            and not self.territory_remove
            and not self.resources_delta
            and not self.diplomatic_relations_set
            and self.active_doctrines_set is None
        )


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
    current_policy_set: Optional[GovernorPolicy] = None
    rejection_events: List[RejectionEvent] = field(default_factory=list) # Detailed rejection audit
    processed_transaction_ids: List[str] = field(default_factory=list)
    next_node_id_set: Optional[int] = None
    next_entity_id_set: Optional[int] = None
    dirty_set: Optional[DirtySet] = None
    force_full_scan: bool = False
    sub_phase_costs: Dict[str, float] = field(default_factory=dict)
    metric_counters: Dict[str, int] = field(default_factory=dict)
    world_events_add: List["WorldEvent"] = field(default_factory=list)
    quest_registry_add: List["QuestOpportunity"] = field(default_factory=list)
    quest_registry_remove: List[str] = field(default_factory=list)
    quest_status_updates: Dict[str, "QuestOpportunityStatus"] = field(default_factory=dict)
    quest_opportunity_reward_intents: List["QuestOpportunityRewardIntent"] = field(default_factory=list)
    # E42D: provider reliability updates keyed by entity_id
    information_providers_update: Dict[int, "InformationProviderState"] = field(default_factory=dict)
    # E53Aa: Faction durable-state mutation records
    faction_updates: List[FactionUpdate] = field(default_factory=list)

    def is_noop(self) -> bool:
        """True if this update contains absolutely no changes."""
        return (not self.entity_updates and not self.entities_add and not self.entities_remove and
                not self.nodes_add and not self.node_updates and not self.ground_items_add_or_update and
                not self.ground_items_remove and not self.corpses_add_or_update and
                not self.corpses_remove and not self.scars_add_or_update and
                not self.scars_remove and not self.chest_updates and
                not self.chest_add_or_update and not self.building_updates and
                not self.camp_updates and not self.world_updates and
                not self.resource_updates and not self.home_storage_updates and
                not self.periodic_updates and not self.work_debt_updates and
                not self.groups_add_or_update and not self.groups_remove and
                self.maturity_set is None and self.last_calamity_tick_set is None and
                self.rng_checkpoint is None and not self.transaction_trace and
                not self.rejections_delta and self.pressure_signals_set is None and
                self.current_mode_set is None and self.current_policy_set is None and
                not self.rejection_events and
                not self.processed_transaction_ids and self.next_node_id_set is None and
                self.next_entity_id_set is None and not self.force_full_scan and
                not self.sub_phase_costs and not self.metric_counters and
                not self.world_events_add and not self.quest_registry_add and
                not self.quest_registry_remove and not self.quest_status_updates and
                not self.quest_opportunity_reward_intents and
                not self.information_providers_update and
                not self.faction_updates)
    def merge(self, other: StateUpdate) -> StateUpdate:
        """Merge another StateUpdate into this one."""
        if not other or other.is_noop():
            return self
        return self.merge_many([other])

    def merge_many(self, others: Iterable[StateUpdate]) -> StateUpdate:
        """
        Merge multiple updates into this one with minimal intermediate allocations.
        Logic ID: TOWN-204 (Batch merge optimization)
        """
        # Filter no-ops
        valid_others = [o for o in others if o and not o.is_noop()]
        if not valid_others:
            return self

        
        # 1. Merge dictionaries
        new_entity_updates = dict(self.entity_updates)
        new_world_updates = dict(self.world_updates)
        new_node_updates = dict(self.node_updates)
        new_building_updates = dict(self.building_updates)
        new_camp_updates = dict(self.camp_updates)
        new_chest_updates = dict(self.chest_updates)
        new_home_storage_updates = dict(self.home_storage_updates)
        new_rejections_delta = dict(self.rejections_delta)
        new_resource_updates = dict(self.resource_updates)
        new_periodic_updates = dict(self.periodic_updates)
        new_work_debt_updates = dict(self.work_debt_updates)

        # Non-dict collections
        new_entities_add = list(self.entities_add)
        new_entities_remove = set(self.entities_remove)
        new_nodes_add = list(self.nodes_add)
        new_groups_add_or_update = list(self.groups_add_or_update)
        new_groups_remove = set(self.groups_remove)
        new_ground_items_add_or_update = list(self.ground_items_add_or_update)
        new_ground_items_remove = set(self.ground_items_remove)
        new_corpses_add_or_update = list(self.corpses_add_or_update)
        new_corpses_remove = set(self.corpses_remove)
        new_chest_add_or_update = list(self.chest_add_or_update)
        new_scars_add_or_update = list(self.scars_add_or_update)
        new_scars_remove = set(self.scars_remove)
        new_trace = list(self.transaction_trace)
        new_processed_ids = set(self.processed_transaction_ids)
        new_rejection_events = list(self.rejection_events)
        new_world_events_add = list(self.world_events_add)
        new_quest_registry_add = list(self.quest_registry_add)
        new_quest_registry_remove = list(self.quest_registry_remove)
        new_quest_status_updates = dict(self.quest_status_updates)
        new_quest_opportunity_reward_intents = list(self.quest_opportunity_reward_intents)
        new_information_providers_update = dict(self.information_providers_update)
        new_faction_updates = list(self.faction_updates)

        # Single values
        maturity = self.maturity_set
        calamity = self.last_calamity_tick_set
        node_id = self.next_node_id_set
        ent_id = self.next_entity_id_set
        rng = self.rng_checkpoint
        pressure = self.pressure_signals_set
        mode = self.current_mode_set
        policy = self.current_policy_set
        dirty = self.dirty_set
        sub_costs = dict(self.sub_phase_costs)

        new_metric_counters = dict(self.metric_counters)

        for other in valid_others:
            # Dictionaries
            for e_id, upd in other.entity_updates.items():
                new_entity_updates[e_id] = new_entity_updates[e_id].merge(upd) if e_id in new_entity_updates else upd
            for r_id, upd in other.world_updates.items():
                new_world_updates[r_id] = new_world_updates[r_id].merge(upd) if r_id in new_world_updates else upd
            for n_id, upd in other.node_updates.items():
                new_node_updates[n_id] = new_node_updates[n_id].merge(upd) if n_id in new_node_updates else upd
            for b_id, upd in other.building_updates.items():
                new_building_updates[b_id] = new_building_updates[b_id].merge(upd) if b_id in new_building_updates else upd
            for c_id, upd in other.camp_updates.items():
                new_camp_updates[c_id] = new_camp_updates[c_id].merge(upd) if c_id in new_camp_updates else upd
            for ch_id, upd in other.chest_updates.items():
                new_chest_updates[ch_id] = new_chest_updates[ch_id].merge(upd) if ch_id in new_chest_updates else upd
            for s_id, upd in other.home_storage_updates.items():
                new_home_storage_updates[s_id] = new_home_storage_updates[s_id].merge(upd) if s_id in new_home_storage_updates else upd
            for k, v in other.rejections_delta.items():
                new_rejections_delta[k] = new_rejections_delta.get(k, 0) + v
            for k, v in other.resource_updates.items():
                new_resource_updates[k] = new_resource_updates.get(k, 0.0) + v
            for k, v in other.periodic_updates.items():
                new_periodic_updates[k] = v
            for k, v in other.work_debt_updates.items():
                new_work_debt_updates[k] = new_work_debt_updates.get(k, 0) + v
            if other.metric_counters:
                for k, v in other.metric_counters.items():
                    new_metric_counters[k] = new_metric_counters.get(k, 0) + v

            # Lists / Sets
            new_entities_add.extend(other.entities_add)
            new_entities_remove.update(other.entities_remove)
            new_nodes_add.extend(other.nodes_add)
            new_groups_add_or_update.extend(other.groups_add_or_update)
            new_groups_remove.update(other.groups_remove)
            new_ground_items_add_or_update.extend(other.ground_items_add_or_update)
            new_ground_items_remove.update(other.ground_items_remove)
            new_corpses_add_or_update.extend(other.corpses_add_or_update)
            new_corpses_remove.update(other.corpses_remove)
            new_chest_add_or_update.extend(other.chest_add_or_update)
            new_scars_add_or_update.extend(other.scars_add_or_update)
            new_scars_remove.update(other.scars_remove)
            new_trace.extend(other.transaction_trace)
            new_processed_ids.update(other.processed_transaction_ids)
            new_rejection_events.extend(other.rejection_events)
            new_world_events_add.extend(other.world_events_add)
            new_quest_registry_add.extend(other.quest_registry_add)
            new_quest_registry_remove.extend(other.quest_registry_remove)
            new_quest_status_updates.update(other.quest_status_updates)
            new_quest_opportunity_reward_intents.extend(other.quest_opportunity_reward_intents)
            new_information_providers_update.update(other.information_providers_update)
            new_faction_updates.extend(
                fu for fu in other.faction_updates if not fu.is_noop()
            )

            # Single values
            if other.maturity_set is not None: maturity = other.maturity_set
            if other.last_calamity_tick_set is not None: calamity = other.last_calamity_tick_set
            if other.next_node_id_set is not None: node_id = other.next_node_id_set
            if other.next_entity_id_set is not None: ent_id = other.next_entity_id_set
            if other.rng_checkpoint: rng = other.rng_checkpoint
            if other.pressure_signals_set is not None: pressure = other.pressure_signals_set
            if other.current_mode_set is not None: mode = other.current_mode_set
            if other.current_policy_set is not None: policy = other.current_policy_set
            if other.dirty_set: dirty = dirty.merge(other.dirty_set) if dirty else other.dirty_set
            if other.sub_phase_costs:
                for k, v in other.sub_phase_costs.items():
                    sub_costs[k] = sub_costs.get(k, 0.0) + v

        return replace(self,
            entity_updates=new_entity_updates,
            world_updates=new_world_updates,
            node_updates=new_node_updates,
            building_updates=new_building_updates,
            camp_updates=new_camp_updates,
            chest_updates=new_chest_updates,
            home_storage_updates=new_home_storage_updates,
            rejections_delta=new_rejections_delta,
            resource_updates=new_resource_updates,
            periodic_updates=new_periodic_updates,
            work_debt_updates=new_work_debt_updates,
            entities_add=new_entities_add,
            entities_remove=list(new_entities_remove),
            nodes_add=new_nodes_add,
            groups_add_or_update=new_groups_add_or_update,
            groups_remove=list(new_groups_remove),
            ground_items_add_or_update=new_ground_items_add_or_update,
            ground_items_remove=list(new_ground_items_remove),
            corpses_add_or_update=new_corpses_add_or_update,
            corpses_remove=list(new_corpses_remove),
            chest_add_or_update=new_chest_add_or_update,
            scars_add_or_update=new_scars_add_or_update,
            scars_remove=list(new_scars_remove),
            transaction_trace=new_trace,
            rejection_events=new_rejection_events,
            processed_transaction_ids=list(new_processed_ids),
            maturity_set=maturity,
            last_calamity_tick_set=calamity,
            next_node_id_set=node_id,
            next_entity_id_set=ent_id,
            rng_checkpoint=rng,
            pressure_signals_set=pressure,
            current_mode_set=mode,
            current_policy_set=policy,
            dirty_set=dirty,
            sub_phase_costs=sub_costs,
            metric_counters=new_metric_counters,
            world_events_add=new_world_events_add,
            quest_registry_add=new_quest_registry_add,
            quest_registry_remove=new_quest_registry_remove,
            quest_status_updates=new_quest_status_updates,
            quest_opportunity_reward_intents=new_quest_opportunity_reward_intents,
            information_providers_update=new_information_providers_update,
            faction_updates=new_faction_updates,
        )

    def compact(self) -> StateUpdate:
        """Remove no-op entity updates to reduce processing overhead."""
        compacted_entity_updates = {
            e_id: upd for e_id, upd in self.entity_updates.items()
            if not upd.is_noop()
        }
        if len(compacted_entity_updates) == len(self.entity_updates):
            return self
        return replace(self, entity_updates=compacted_entity_updates)
    
    def replace(self, **kwargs) -> StateUpdate:
        return replace(self, **kwargs)

# Logic ID: CORE-PERF-018 (Singleton for no-op entity updates)
EMPTY_ENTITY_UPDATE = EntityUpdate(entity_id=-1)
