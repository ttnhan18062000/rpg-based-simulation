# Compliance IDs: DATA-092
# Compliance IDs: PROG-085, SUB-007
from __future__ import annotations

from dataclasses import fields, is_dataclass
from typing import Any, Dict, Iterable, List, Mapping, Optional, Set

from src.core.state import (
    EntityState,
    IdentityComponent,
    CombatComponent,
    InventoryComponent,
    LifecycleComponent,
    BiologicalComponent,
    SocialComponent,
    NavigationComponent,
    InteractionComponent,
    TaskComponent,
    AptitudeComponent,
    AttributeComponent,
    EquipmentComponent,
    EquipSlot,
    ItemStack,
    StaminaComponent,
    PersonalityComponent,
    LifeStage,
    SocialBond,
    BetrayalRecord,
    WoundState,
    ScarState,
)

from src.core.strategic import (
    StrategicComponent,
    CognitionProfile,
    ProjectState,
    BlockerState,
    LeadState,
    DirectiveState,
    ConcernState,
    CandidateZone,
    HypothesisState,
    SourceTrustEntry,
    TurningPointState,
    ContractState,
)

from src.core.enums import EntityRole, Faction
from src.core.movement_modes import MovementMode
from src.core.self_model import SelfModelBundle
from src.core.cognition import CognitionModel


def _component(cls: type, **kwargs):
    """
    Build a dataclass component using only fields supported by the current model.
    """
    if not is_dataclass(cls):
        raise TypeError(f"{cls!r} is not a dataclass component")

    valid_fields = {f.name for f in fields(cls) if f.init}
    filtered = {k: v for k, v in kwargs.items() if k in valid_fields}
    return cls(**filtered)


def _copy_dict(value: Optional[Mapping]) -> dict:
    return dict(value) if value is not None else {}


def _copy_list(value: Optional[Iterable]) -> list:
    return list(value) if value is not None else []


def _copy_set(value: Optional[Iterable]) -> set:
    return set(value) if value is not None else set()


class V2EntityBuilder:
    """
    Fresh V2 entity builder.

    Rules:
    - component methods construct component state from explicit fields
    - replace_* methods inject exact existing components
    - no legacy aliases
    - no hidden conversion of ItemStack into plain strings
    """

    def __init__(self, entity_id: int) -> None:
        self._entity_id = entity_id
        self._kind = "hero"

        self._location = (0.0, 0.0)

        self._identity = IdentityComponent()
        self._inventory = InventoryComponent()
        self._combat = CombatComponent()
        self._navigation = NavigationComponent()
        self._strategic = StrategicComponent()
        self._social = SocialComponent()
        self._biological = BiologicalComponent()
        self._lifecycle = LifecycleComponent()
        self._attributes = AttributeComponent()
        self._aptitude = AptitudeComponent()
        self._equipment = EquipmentComponent()
        self._interaction = InteractionComponent()
        self._task = TaskComponent()
        self._stamina = StaminaComponent()
        self._self_model = SelfModelBundle()
        self._cognition = CognitionModel()

    def kind(self, value: str) -> V2EntityBuilder:
        self._kind = value
        return self
 
    def location(self, x: float, y: float) -> V2EntityBuilder:
        self._location = (float(x), float(y))
 
        self._navigation = _component(
            NavigationComponent,
            **{
                **self._navigation_to_dict(),
                "position": self._location,
            },
        )
        return self

    def replace_cognition(self, component: CognitionModel) -> V2EntityBuilder:
        self._cognition = component
        return self

    def build(self) -> EntityState:
        navigation = _component(
            NavigationComponent,
            **{
                **self._navigation_to_dict(),
                "position": self._location,
            },
        )

        return EntityState(
            id=self._entity_id,
            kind=self._kind,
            interaction=self._interaction,
            identity=self._identity,
            attributes=self._attributes,
            inventory=self._inventory,
            strategic=self._strategic,
            social=self._social,
            biological=self._biological,
            lifecycle=self._lifecycle,
            aptitude=self._aptitude,
            combat=self._combat,
            equipment=self._equipment,
            navigation=navigation,
            task=self._task,
            stamina=self._stamina,
            self_model=self._self_model,
            cognition=self._cognition,
        )


    def identity(
        self,
        *,
        role: int | EntityRole | None = None,
        faction: int | Faction | None = None,
        known_recipes: Optional[Set[str]] = None,
        craft_target: Optional[str] = None,
        evolution_level: Optional[int] = None,
        evolution_points: Optional[int] = None,
        veterancy_points: Optional[int] = None,
        veterancy_rank: Optional[int] = None,
        unspent_ap: Optional[int] = None,
        class_id: Optional[str] = None,
        learned_skills: Optional[Set[str]] = None,
        traits: Optional[Set[str]] = None,
        active_breakthroughs: Optional[Set[str]] = None,
        cooldowns: Optional[Dict[str, int]] = None,
        personality: Optional[PersonalityComponent] = None,
        life_stage: Optional[LifeStage] = None,
        group_id: Optional[int] = None,
        properties: Optional[Dict[str, Any]] = None,
    ) -> V2EntityBuilder:
        current = self._identity_to_dict()

        updates = {
            "role": role,
            "faction": faction,
            "known_recipes": _copy_set(known_recipes) if known_recipes is not None else None,
            "craft_target": craft_target,
            "evolution_level": evolution_level,
            "evolution_points": evolution_points,
            "veterancy_points": veterancy_points,
            "veterancy_rank": veterancy_rank,
            "unspent_ap": unspent_ap,
            "class_id": class_id,
            "learned_skills": _copy_set(learned_skills) if learned_skills is not None else None,
            "traits": _copy_set(traits) if traits is not None else None,
            "active_breakthroughs": _copy_set(active_breakthroughs) if active_breakthroughs is not None else None,
            "cooldowns": _copy_dict(cooldowns) if cooldowns is not None else None,
            "personality": personality,
            "life_stage": life_stage,
            "group_id": group_id,
            "properties": _copy_dict(properties) if properties is not None else None,
        }

        for key, value in updates.items():
            if value is not None:
                current[key] = value

        self._identity = _component(IdentityComponent, **current)
        return self

    def inventory(
        self,
        *,
        items: Optional[List[ItemStack]] = None,
        gold: Optional[int] = None,
        max_slots: Optional[int] = None,
        max_weight: Optional[float] = None,
    ) -> V2EntityBuilder:
        current = self._inventory_to_dict()

        if items is not None:
            current["items"] = list(items)
        if gold is not None:
            current["gold"] = int(gold)
        if max_slots is not None:
            current["max_slots"] = int(max_slots)
        if max_weight is not None:
            current["max_weight"] = float(max_weight)

        self._inventory = _component(InventoryComponent, **current)
        return self

    def combat(
        self,
        *,
        hp: Optional[int] = None,
        max_hp: Optional[int] = None,
        atk: Optional[int] = None,
        def_stat: Optional[int] = None,
        speed: Optional[int] = None,
        attack_range: Optional[int] = None,
        evasion: Optional[float] = None,
        move_cost: Optional[float] = None,
        tactical_role: Optional[str] = None,
        action_style: Optional[int] = None,
        alive: Optional[bool] = None,
        readiness: Optional[float] = None,
        wounds: Optional[List[WoundState]] = None,
        scars: Optional[List[ScarState]] = None,
    ) -> V2EntityBuilder:
        current = self._combat_to_dict()

        updates = {
            "hp": hp,
            "max_hp": max_hp,
            "atk": atk,
            "def_stat": def_stat,
            "speed": speed,
            "range": attack_range,
            "evasion": evasion,
            "move_cost": move_cost,
            "tactical_role": tactical_role,
            "action_style": action_style,
            "alive": alive,
            "readiness": readiness,
            "wounds": list(wounds) if wounds is not None else None,
            "scars": list(scars) if scars is not None else None,
        }

        for key, value in updates.items():
            if value is not None:
                current[key] = value

        self._combat = _component(CombatComponent, **current)
        return self

    def attributes(
        self,
        *,
        strength: Optional[int] = None,
        agility: Optional[int] = None,
        vitality: Optional[int] = None,
        endurance: Optional[int] = None,
        intelligence: Optional[int] = None,
        spirit: Optional[int] = None,
        wisdom: Optional[int] = None,
        perception: Optional[int] = None,
        charisma: Optional[int] = None,
    ) -> V2EntityBuilder:
        current = self._attributes_to_dict()

        updates = {
            "strength": strength,
            "agility": agility,
            "vitality": vitality,
            "endurance": endurance,
            "intelligence": intelligence,
            "spirit": spirit,
            "wisdom": wisdom,
            "perception": perception,
            "charisma": charisma,
        }

        for key, value in updates.items():
            if value is not None:
                current[key] = int(value)

        self._attributes = _component(AttributeComponent, **current)
        return self

    def aptitude(
        self,
        *,
        learning_rate: Optional[float] = None,
        stamina_efficiency: Optional[float] = None,
        str_apt: Optional[float] = None,
        agi_apt: Optional[float] = None,
        vit_apt: Optional[float] = None,
        end_apt: Optional[float] = None,
        int_apt: Optional[float] = None,
        spi_apt: Optional[float] = None,
        wis_apt: Optional[float] = None,
        per_apt: Optional[float] = None,
        cha_apt: Optional[float] = None,
    ) -> V2EntityBuilder:
        current = self._aptitude_to_dict()

        updates = {
            "learning_rate": learning_rate,
            "stamina_efficiency": stamina_efficiency,
            "str_apt": str_apt,
            "agi_apt": agi_apt,
            "vit_apt": vit_apt,
            "end_apt": end_apt,
            "int_apt": int_apt,
            "spi_apt": spi_apt,
            "wis_apt": wis_apt,
            "per_apt": per_apt,
            "cha_apt": cha_apt,
        }

        for key, value in updates.items():
            if value is not None:
                current[key] = float(value)

        self._aptitude = _component(AptitudeComponent, **current)
        return self

    def navigation(
        self,
        *,
        position: Optional[tuple[float, float]] = None,
        target: Optional[tuple[float, float]] = None,
        path: Optional[List[tuple[float, float]]] = None,
        moved_recently: Optional[bool] = None,
        movement_mode: Optional[MovementMode] = None,
        last_failure_reason: Optional[str] = None,
        wait_count: Optional[int] = None,
        oscillation_count: Optional[int] = None,
        last_position: Optional[tuple[float, float]] = None,
        home_position: Optional[tuple[float, float]] = None,
        leash_radius: Optional[float] = None,
        chase_ticks: Optional[int] = None,
        max_chase_ticks: Optional[int] = None,
        returning_home: Optional[bool] = None,
        region_id: Optional[str] = None,
    ) -> V2EntityBuilder:
        current = self._navigation_to_dict()

        updates = {
            "position": position,
            "target": target,
            "path": list(path) if path is not None else None,
            "moved_recently": moved_recently,
            "movement_mode": movement_mode,
            "last_failure_reason": last_failure_reason,
            "wait_count": wait_count,
            "oscillation_count": oscillation_count,
            "last_position": last_position,
            "home_position": home_position,
            "leash_radius": leash_radius,
            "chase_ticks": chase_ticks,
            "max_chase_ticks": max_chase_ticks,
            "returning_home": returning_home,
            "region_id": region_id,
        }

        for key, value in updates.items():
            if value is not None:
                current[key] = value

        self._navigation = _component(NavigationComponent, **current)

        if position is not None:
            self._location = (float(position[0]), float(position[1]))

        return self

    def cognition(
        self,
        *,
        max_active_projects: Optional[int] = None,
        max_leads: Optional[int] = None,
        max_concerns: Optional[int] = None,
        max_candidate_zones: Optional[int] = None,
        max_hypotheses: Optional[int] = None,
        interruption_resistance: Optional[float] = None,
        detour_breadth: Optional[int] = None,
        reserved_detour_depth: Optional[int] = None,
    ) -> V2EntityBuilder:
        current = self._cognition_to_dict(self._strategic.profile)

        updates = {
            "max_active_projects": max_active_projects,
            "max_leads": max_leads,
            "max_concerns": max_concerns,
            "max_candidate_zones": max_candidate_zones,
            "max_hypotheses": max_hypotheses,
            "interruption_resistance": interruption_resistance,
            "detour_breadth": detour_breadth,
            "reserved_detour_depth": reserved_detour_depth,
        }

        for key, value in updates.items():
            if value is not None:
                current[key] = value

        profile = _component(CognitionProfile, **current)

        self._strategic = _component(
            StrategicComponent,
            **{
                **self._strategic_to_dict(),
                "profile": profile,
            },
        )
        return self

    def strategic(
        self,
        *,
        home_region_id: Optional[str] = None,
        blockers: Optional[Dict[str, BlockerState]] = None,
        leads: Optional[Dict[str, LeadState]] = None,
        directives: Optional[Dict[str, DirectiveState]] = None,
        projects: Optional[Dict[str, ProjectState]] = None,
        concerns: Optional[Dict[str, ConcernState]] = None,
        candidate_zones: Optional[Dict[str, CandidateZone]] = None,
        hypotheses: Optional[Dict[str, HypothesisState]] = None,
        source_trust: Optional[Dict[int, SourceTrustEntry]] = None,
        contracts: Optional[Dict[str, ContractState]] = None,
        turning_points: Optional[List[TurningPointState]] = None,
        current_project_id: Optional[str] = None,
        current_objective_id: Optional[str] = None,
        primary_overload_source: Optional[str] = None,
        last_overload_tick: Optional[int] = None,
        boredom: Optional[Dict[str, float]] = None,
    ) -> V2EntityBuilder:
        current = self._strategic_to_dict()

        updates = {
            "home_region_id": home_region_id,
            "blockers": _copy_dict(blockers) if blockers is not None else None,
            "leads": _copy_dict(leads) if leads is not None else None,
            "directives": _copy_dict(directives) if directives is not None else None,
            "projects": _copy_dict(projects) if projects is not None else None,
            "concerns": _copy_dict(concerns) if concerns is not None else None,
            "candidate_zones": _copy_dict(candidate_zones) if candidate_zones is not None else None,
            "hypotheses": _copy_dict(hypotheses) if hypotheses is not None else None,
            "source_trust": _copy_dict(source_trust) if source_trust is not None else None,
            "contracts": _copy_dict(contracts) if contracts is not None else None,
            "turning_points": _copy_list(turning_points) if turning_points is not None else None,
            "current_project_id": current_project_id,
            "current_objective_id": current_objective_id,
            "primary_overload_source": primary_overload_source,
            "last_overload_tick": last_overload_tick,
            "boredom": _copy_dict(boredom) if boredom is not None else None,
        }

        for key, value in updates.items():
            if value is not None:
                current[key] = value

        self._strategic = _component(StrategicComponent, **current)
        return self

    def social(
        self,
        *,
        trust_history: Optional[Dict[int, float]] = None,
        familiarity_history: Optional[Dict[int, float]] = None,
        debt_history: Optional[Dict[int, float]] = None,
        fear_history: Optional[Dict[int, float]] = None,
        grudge_history: Optional[Dict[int, float]] = None,
        salience_history: Optional[Dict[int, float]] = None,
        bonds: Optional[Dict[int, SocialBond]] = None,
        nemesis_ids: Optional[Set[int]] = None,
        place_attachment: Optional[Dict[str, float]] = None,
        betrayal_count: Optional[int] = None,
        betrayal_records: Optional[List[BetrayalRecord]] = None,
        public_reputation: Optional[float] = None,
        heroism_score: Optional[float] = None,
        notoriety_score: Optional[float] = None,
        last_offer_tick: Optional[int] = None,
        rejection_count: Optional[Dict[int, int]] = None,
    ) -> V2EntityBuilder:
        current = self._social_to_dict()

        updates = {
            "trust_history": _copy_dict(trust_history) if trust_history is not None else None,
            "familiarity_history": _copy_dict(familiarity_history) if familiarity_history is not None else None,
            "debt_history": _copy_dict(debt_history) if debt_history is not None else None,
            "fear_history": _copy_dict(fear_history) if fear_history is not None else None,
            "grudge_history": _copy_dict(grudge_history) if grudge_history is not None else None,
            "salience_history": _copy_dict(salience_history) if salience_history is not None else None,
            "bonds": _copy_dict(bonds) if bonds is not None else None,
            "nemesis_ids": _copy_set(nemesis_ids) if nemesis_ids is not None else None,
            "place_attachment": _copy_dict(place_attachment) if place_attachment is not None else None,
            "betrayal_count": betrayal_count,
            "betrayal_records": _copy_list(betrayal_records) if betrayal_records is not None else None,
            "public_reputation": public_reputation,
            "heroism_score": heroism_score,
            "notoriety_score": notoriety_score,
            "last_offer_tick": last_offer_tick,
            "rejection_count": _copy_dict(rejection_count) if rejection_count is not None else None,
        }

        for key, value in updates.items():
            if value is not None:
                current[key] = value

        self._social = _component(SocialComponent, **current)
        return self

    def biological(
        self,
        *,
        sleep_debt: Optional[float] = None,
        hunger: Optional[float] = None,
        rest_pressure: Optional[float] = None,
        last_meal_tick: Optional[int] = None,
        last_sleep_tick: Optional[int] = None,
        well_rested_until: Optional[int] = None,
    ) -> V2EntityBuilder:
        current = self._biological_to_dict()

        updates = {
            "sleep_debt": sleep_debt,
            "hunger": hunger,
            "rest_pressure": rest_pressure,
            "last_meal_tick": last_meal_tick,
            "last_sleep_tick": last_sleep_tick,
            "well_rested_until": well_rested_until,
        }

        for key, value in updates.items():
            if value is not None:
                current[key] = value

        self._biological = _component(BiologicalComponent, **current)
        return self

    def lifecycle(
        self,
        *,
        active: Optional[bool] = None,
        age_ticks: Optional[int] = None,
        max_age_ticks: Optional[int] = None,
        is_permadeath: Optional[bool] = None,
        death_tick: Optional[int] = None,
        death_reason: Optional[str] = None,
        generation: Optional[int] = None,
        heir_entity_id: Optional[int] = None,
        heirlooms: Optional[List[str]] = None,
    ) -> V2EntityBuilder:
        current = self._lifecycle_to_dict()

        updates = {
            "active": active,
            "age_ticks": age_ticks,
            "max_age_ticks": max_age_ticks,
            "is_permadeath": is_permadeath,
            "death_tick": death_tick,
            "death_reason": death_reason,
            "generation": generation,
            "heir_entity_id": heir_entity_id,
            "heirlooms": _copy_list(heirlooms) if heirlooms is not None else None,
        }

        for key, value in updates.items():
            if value is not None:
                current[key] = value

        self._lifecycle = _component(LifecycleComponent, **current)
        return self

    def interaction(
        self,
        *,
        target_node_id: Optional[int] = None,
        progress: Optional[int] = None,
        start_tick: Optional[int] = None,
    ) -> V2EntityBuilder:
        current = self._interaction_to_dict()

        updates = {
            "target_node_id": target_node_id,
            "progress": progress,
            "start_tick": start_tick,
        }

        for key, value in updates.items():
            if value is not None:
                current[key] = value

        self._interaction = _component(InteractionComponent, **current)
        return self

    def task(
        self,
        *,
        work_kind: Optional[str] = None,
        payload: Optional[Dict[str, Any]] = None,
    ) -> V2EntityBuilder:
        current = self._task_to_dict()

        if work_kind is not None:
            current["work_kind"] = work_kind
        if payload is not None:
            current["payload"] = dict(payload)

        self._task = _component(TaskComponent, **current)
        return self

    def stamina(
        self,
        *,
        current: Optional[float] = None,
        max_stamina: Optional[float] = None,
        regen_rate: Optional[float] = None,
        rest_regen_rate: Optional[float] = None,
        exhaustion_threshold: Optional[float] = None,
        exhaustion_penalty: Optional[float] = None,
    ) -> V2EntityBuilder:
        current_values = self._stamina_to_dict()

        updates = {
            "current": current,
            "max_stamina": max_stamina,
            "regen_rate": regen_rate,
            "rest_regen_rate": rest_regen_rate,
            "exhaustion_threshold": exhaustion_threshold,
            "exhaustion_penalty": exhaustion_penalty,
        }

        for key, value in updates.items():
            if value is not None:
                current_values[key] = value

        self._stamina = _component(StaminaComponent, **current_values)
        return self

    def equipment(
        self,
        *,
        slots: Optional[Dict[EquipSlot, str | None]] = None,
        durability: Optional[Dict[EquipSlot, float]] = None,
    ) -> V2EntityBuilder:
        current = self._equipment_to_dict()

        if slots is not None:
            current["slots"] = dict(slots)
        if durability is not None:
            current["durability"] = dict(durability)

        self._equipment = _component(EquipmentComponent, **current)
        return self

    def properties(self, values: Dict[str, Any]) -> V2EntityBuilder:
        current = self._identity_to_dict()
        current["properties"] = dict(values)
        self._identity = _component(IdentityComponent, **current)
        return self

    def replace_identity(self, component: IdentityComponent) -> V2EntityBuilder:
        self._identity = component
        return self

    def replace_inventory(self, component: InventoryComponent) -> V2EntityBuilder:
        self._inventory = component
        return self

    def replace_combat(self, component: CombatComponent) -> V2EntityBuilder:
        self._combat = component
        return self

    def replace_navigation(self, component: NavigationComponent) -> V2EntityBuilder:
        self._navigation = component

        if hasattr(component, "position"):
            self._location = component.position

        return self

    def replace_strategic(self, component: StrategicComponent) -> V2EntityBuilder:
        self._strategic = component
        return self

    def replace_social(self, component: SocialComponent) -> V2EntityBuilder:
        self._social = component
        return self

    def replace_biological(self, component: BiologicalComponent) -> V2EntityBuilder:
        self._biological = component
        return self

    def replace_lifecycle(self, component: LifecycleComponent) -> V2EntityBuilder:
        self._lifecycle = component
        return self

    def replace_attributes(self, component: AttributeComponent) -> V2EntityBuilder:
        self._attributes = component
        return self

    def replace_aptitude(self, component: AptitudeComponent) -> V2EntityBuilder:
        self._aptitude = component
        return self

    def replace_equipment(self, component: EquipmentComponent) -> V2EntityBuilder:
        self._equipment = component
        return self

    def replace_interaction(self, component: InteractionComponent) -> V2EntityBuilder:
        self._interaction = component
        return self

    def replace_task(self, component: TaskComponent) -> V2EntityBuilder:
        self._task = component
        return self

    def replace_stamina(self, component: StaminaComponent) -> V2EntityBuilder:
        self._stamina = component
        return self

    def replace_self_model(self, component: SelfModelBundle) -> V2EntityBuilder:
        self._self_model = component
        return self

    def _identity_to_dict(self) -> Dict[str, Any]:
        return self._to_dict(self._identity)

    def _inventory_to_dict(self) -> Dict[str, Any]:
        return self._to_dict(self._inventory)

    def _combat_to_dict(self) -> Dict[str, Any]:
        return self._to_dict(self._combat)

    def _navigation_to_dict(self) -> Dict[str, Any]:
        return self._to_dict(self._navigation)

    def _strategic_to_dict(self) -> Dict[str, Any]:
        return self._to_dict(self._strategic)

    def _cognition_to_dict(self, profile: CognitionProfile) -> Dict[str, Any]:
        return self._to_dict(profile)

    def _social_to_dict(self) -> Dict[str, Any]:
        return self._to_dict(self._social)

    def _biological_to_dict(self) -> Dict[str, Any]:
        return self._to_dict(self._biological)

    def _lifecycle_to_dict(self) -> Dict[str, Any]:
        return self._to_dict(self._lifecycle)

    def _attributes_to_dict(self) -> Dict[str, Any]:
        return self._to_dict(self._attributes)

    def _aptitude_to_dict(self) -> Dict[str, Any]:
        return self._to_dict(self._aptitude)

    def _equipment_to_dict(self) -> Dict[str, Any]:
        return self._to_dict(self._equipment)

    def _interaction_to_dict(self) -> Dict[str, Any]:
        return self._to_dict(self._interaction)

    def _task_to_dict(self) -> Dict[str, Any]:
        return self._to_dict(self._task)

    def _stamina_to_dict(self) -> Dict[str, Any]:
        return self._to_dict(self._stamina)

    @staticmethod
    def _to_dict(component: Any) -> Dict[str, Any]:
        if not is_dataclass(component):
            raise TypeError(f"{component!r} is not a dataclass instance")

        return {
            f.name: getattr(component, f.name)
            for f in fields(component)
            if f.init
        }
