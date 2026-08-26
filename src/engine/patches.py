# Compliance IDs: PERF-015
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional, Self, TYPE_CHECKING

if TYPE_CHECKING:
    from src.core.state import EntityState, IntentResult
    from src.core.updates import (
        EntityUpdate, InteractionUpdate, IdentityUpdate, NavigationUpdate,
        CombatUpdate, StaminaUpdate, InventoryUpdate, EquipmentUpdate,
        StrategicUpdate, QuestUpdate, SocialUpdate, TaskUpdate,
        AttributeUpdate, RewardUpdate, WoundUpdate
    )
    from src.core.update_models.resources import ResourceTransferIntent


@dataclass(frozen=True, slots=True)
class ComponentPatch:
    """
    Abstract base class for component-specific state deltas.
    Milestone 15: Component-Level Patch Model.
    """
    entity_id: int

    def is_noop(self) -> bool:
        """Returns True if this patch contains absolutely no changes."""
        raise NotImplementedError

    def merge(self, other: Self) -> Self:
        """Merges another patch of the same type into this one."""
        raise NotImplementedError

    def apply(self, entity: EntityState, changes: Dict[str, Any]) -> None:
        """Applies the patch deltas to the entity/changes dictionary."""
        raise NotImplementedError


@dataclass(frozen=True, slots=True)
class KindPatch(ComponentPatch):
    kind_set: Optional[str] = None

    def is_noop(self) -> bool:
        return self.kind_set is None

    def merge(self, other: KindPatch) -> KindPatch:
        if not other or other.is_noop():
            return self
        return KindPatch(entity_id=self.entity_id, kind_set=other.kind_set if other.kind_set is not None else self.kind_set)

    def apply(self, entity: EntityState, changes: Dict[str, Any]) -> None:
        if self.kind_set is not None and self.kind_set != entity.kind:
            changes["kind"] = self.kind_set


@dataclass(frozen=True, slots=True)
class LifecyclePatch(ComponentPatch):
    lifecycle: Optional[Any] = None # LifecycleUpdate
    active: Optional[bool] = None

    def is_noop(self) -> bool:
        return (self.lifecycle is None or self.lifecycle.is_noop()) and self.active is None

    def merge(self, other: LifecyclePatch) -> LifecyclePatch:
        if not other or other.is_noop():
            return self
        merged_life = self.lifecycle.merge(other.lifecycle) if self.lifecycle and other.lifecycle else (other.lifecycle or self.lifecycle)
        return LifecyclePatch(entity_id=self.entity_id, lifecycle=merged_life, active=other.active if other.active is not None else self.active)

    def apply(self, entity: EntityState, changes: Dict[str, Any]) -> None:
        from src.engine.apply import replace
        new_lifecycle = changes.get("lifecycle", entity.lifecycle)
        if self.active is not None and self.active != new_lifecycle.active:
            new_lifecycle = replace(new_lifecycle, active=self.active)
        if self.lifecycle:
            u_life = self.lifecycle
            new_heirlooms = list(new_lifecycle.heirlooms)
            new_heirlooms.extend(u_life.heirlooms_add)
            new_lifecycle = replace(new_lifecycle,
                age_ticks=new_lifecycle.age_ticks + u_life.age_delta,
                generation=new_lifecycle.generation + u_life.generation_delta,
                is_permadeath=u_life.is_permadeath_set if u_life.is_permadeath_set is not None else new_lifecycle.is_permadeath,
                death_tick=u_life.death_tick_set if u_life.death_tick_set is not None else new_lifecycle.death_tick,
                death_reason=u_life.death_reason_set if u_life.death_reason_set is not None else new_lifecycle.death_reason,
                heir_entity_id=u_life.heir_entity_id_set if u_life.heir_entity_id_set is not None else new_lifecycle.heir_entity_id,
                heirlooms=tuple(new_heirlooms)
            )
        if new_lifecycle is not entity.lifecycle:
            changes["lifecycle"] = new_lifecycle


@dataclass(frozen=True, slots=True)
class BiologicalPatch(ComponentPatch):
    biological: Optional[Any] = None # BiologicalUpdate

    def is_noop(self) -> bool:
        return self.biological is None or self.biological.is_noop()

    def merge(self, other: BiologicalPatch) -> BiologicalPatch:
        if not other or other.is_noop():
            return self
        merged_bio = self.biological.merge(other.biological) if self.biological and other.biological else (other.biological or self.biological)
        return BiologicalPatch(entity_id=self.entity_id, biological=merged_bio)

    def apply(self, entity: EntityState, changes: Dict[str, Any]) -> None:
        from src.engine.apply import replace
        if self.biological:
            u_bio = self.biological
            new_bio = changes.get("biological", entity.biological)
            changes["biological"] = replace(new_bio,
                sleep_debt=u_bio.sleep_debt_set if u_bio.sleep_debt_set is not None else max(0.0, min(100.0, new_bio.sleep_debt + u_bio.sleep_debt_delta)),
                hunger=u_bio.hunger_set if u_bio.hunger_set is not None else max(0.0, min(100.0, new_bio.hunger + u_bio.hunger_delta)),
                rest_pressure=new_bio.rest_pressure + u_bio.rest_pressure_delta,
                last_meal_tick=u_bio.last_meal_tick_set if u_bio.last_meal_tick_set is not None else new_bio.last_meal_tick,
                last_sleep_tick=u_bio.last_sleep_tick_set if u_bio.last_sleep_tick_set is not None else new_bio.last_sleep_tick,
                well_rested_until=u_bio.well_rested_until_set if u_bio.well_rested_until_set is not None else new_bio.well_rested_until
            )


@dataclass(frozen=True, slots=True)
class InteractionPatch(ComponentPatch):
    interaction: Optional[Any] = None # InteractionUpdate

    def is_noop(self) -> bool:
        return self.interaction is None or self.interaction.is_noop()

    def merge(self, other: InteractionPatch) -> InteractionPatch:
        if not other or other.is_noop():
            return self
        merged_int = self.interaction.merge(other.interaction) if self.interaction and other.interaction else (other.interaction or self.interaction)
        return InteractionPatch(entity_id=self.entity_id, interaction=merged_int)

    def apply(self, entity: EntityState, changes: Dict[str, Any]) -> None:
        from src.engine.apply import replace
        from src.core.state import InteractionComponent
        if self.interaction:
            u_int = self.interaction
            if u_int.reset:
                changes["interaction"] = InteractionComponent()
            else:
                new_int = changes.get("interaction", entity.interaction)
                changes["interaction"] = replace(new_int,
                    target_node_id=u_int.target_node_id if u_int.target_node_id is not None else new_int.target_node_id,
                    progress=new_int.progress + u_int.progress_delta
                )


@dataclass(frozen=True, slots=True)
class IdentityPatch(ComponentPatch):
    identity: Optional[Any] = None # IdentityUpdate
    group_id_set: Optional[int] = None
    intent_results: List[Any] = field(default_factory=list) # List[IntentResult]
    property_updates: Dict[str, Any] = field(default_factory=dict)

    def is_noop(self) -> bool:
        return ((self.identity is None or self.identity.is_noop()) and 
                self.group_id_set is None and not self.intent_results and not self.property_updates)

    def merge(self, other: IdentityPatch) -> IdentityPatch:
        if not other or other.is_noop():
            return self
        merged_id = self.identity.merge(other.identity) if self.identity and other.identity else (other.identity or self.identity)
        return IdentityPatch(
            entity_id=self.entity_id,
            identity=merged_id,
            group_id_set=other.group_id_set if other.group_id_set is not None else self.group_id_set,
            intent_results=self.intent_results + other.intent_results,
            property_updates={**self.property_updates, **other.property_updates}
        )

    def apply(self, entity: EntityState, changes: Dict[str, Any]) -> None:
        from src.engine.apply import replace, ApplyPath
        from src.core.state import ReadOnlyDict
        from src.progression.veterancy import VeterancyService
        
        new_id = changes.get("identity", entity.identity)
        rl = new_id.role
        fac = new_id.faction
        rec = set(new_id.known_recipes)
        tgt = new_id.craft_target
        lvl = new_id.evolution_level
        ep = new_id.evolution_points
        vp = new_id.veterancy_points
        vrank = new_id.veterancy_rank
        ap = new_id.unspent_ap
        sk = set(new_id.learned_skills)
        tr = set(new_id.traits)
        brk = set(new_id.active_breakthroughs)
        cds = dict(new_id.cooldowns)
        
        if self.identity:
            u_id = self.identity
            if u_id.role_set is not None: rl = u_id.role_set
            if u_id.faction_set is not None: fac = u_id.faction_set
            rec |= set(u_id.recipes_learned)
            if u_id.craft_target is not None: tgt = u_id.craft_target
            if u_id.evolution_level_set is not None: lvl = u_id.evolution_level_set
            ep += u_id.evolution_points_delta
            if u_id.veterancy_points_delta != 0:
                proc_id = VeterancyService.process_points(new_id, u_id.veterancy_points_delta)
                vp = proc_id.veterancy_points
                vrank = proc_id.veterancy_rank
            if u_id.unspent_ap_set is not None: ap = u_id.unspent_ap_set
            else: ap += u_id.unspent_ap_delta
            sk |= set(u_id.learned_skills)
            tr = (tr | set(u_id.traits_add)) - set(u_id.traits_remove)
            brk |= set(u_id.breakthroughs_add)
            cds.update(u_id.cooldown_updates)
            
        gid = new_id.group_id
        if self.group_id_set is not None:
            gid = None if self.group_id_set == -1 else self.group_id_set
        
        props = dict(new_id.properties)
        if self.property_updates:
            props.update(self.property_updates)
            
        intents = tuple(self.intent_results) if self.intent_results else new_id.latest_intent_results
        if not self.identity and self.group_id_set is None and not self.property_updates and self.intent_results:
            changes["identity"] = ApplyPath._fast_replace_identity(new_id, intents)
        else:
            changes["identity"] = replace(new_id, role=rl, faction=fac, known_recipes=frozenset(rec),
                                          craft_target=tgt, evolution_level=lvl, evolution_points=ep,
                                          veterancy_points=vp, veterancy_rank=vrank, unspent_ap=ap, learned_skills=frozenset(sk),
                                          traits=frozenset(tr), active_breakthroughs=frozenset(brk),
                                          cooldowns=ReadOnlyDict(cds), group_id=gid, properties=ReadOnlyDict(props),
                                          latest_intent_results=intents)


@dataclass(frozen=True, slots=True)
class NavigationPatch(ComponentPatch):
    navigation: Optional[Any] = None # NavigationUpdate
    new_position: Optional[tuple[float, float]] = None
    moved_this_tick: bool = False

    def is_noop(self) -> bool:
        return (self.navigation is None or self.navigation.is_noop()) and self.new_position is None and not self.moved_this_tick

    def merge(self, other: NavigationPatch) -> NavigationPatch:
        if not other or other.is_noop():
            return self
        merged_nav = self.navigation.merge(other.navigation) if self.navigation and other.navigation else (other.navigation or self.navigation)
        return NavigationPatch(
            entity_id=self.entity_id,
            navigation=merged_nav,
            new_position=other.new_position if other.new_position is not None else self.new_position,
            moved_this_tick=self.moved_this_tick or other.moved_this_tick
        )

    def apply(self, entity: EntityState, changes: Dict[str, Any]) -> None:
        from src.engine.apply import replace, ApplyPath
        new_nav = changes.get("navigation", entity.navigation)
        if self.navigation:
            u_nav = self.navigation
            new_nav = replace(
                new_nav,
                target=u_nav.target_set if u_nav.target_set is not None else (None if u_nav.target_clear else new_nav.target),
                movement_mode=u_nav.movement_mode_set if u_nav.movement_mode_set is not None else new_nav.movement_mode,
                path=u_nav.path_set if u_nav.path_set is not None else (None if u_nav.clear_path else new_nav.path),
                moved_recently=u_nav.moved_recently_set if u_nav.moved_recently_set is not None else new_nav.moved_recently,
                last_failure_reason=u_nav.failure_reason if u_nav.failure_reason is not None else new_nav.last_failure_reason,
                region_id=u_nav.region_id_set if u_nav.region_id_set is not None else new_nav.region_id,
                wait_count=new_nav.wait_count + u_nav.wait_count_delta,
                oscillation_count=new_nav.oscillation_count + u_nav.oscillation_count_delta,
                last_position=u_nav.last_position_set if u_nav.last_position_set is not None else new_nav.last_position
            )
        if self.new_position:
            if self.new_position != entity.navigation.position:
                new_nav = ApplyPath._fast_replace_navigation(new_nav, self.new_position, None)
        
        if new_nav is not entity.navigation:
            changes["navigation"] = new_nav


@dataclass(frozen=True, slots=True)
class CombatPatch(ComponentPatch):
    combat: Optional[Any] = None # CombatUpdate
    readiness_delta: float = 0.0

    def is_noop(self) -> bool:
        return (self.combat is None or self.combat.is_noop()) and self.readiness_delta == 0.0

    def merge(self, other: CombatPatch) -> CombatPatch:
        if not other or other.is_noop():
            return self
        merged_com = self.combat.merge(other.combat) if self.combat and other.combat else (other.combat or self.combat)
        return CombatPatch(
            entity_id=self.entity_id,
            combat=merged_com,
            readiness_delta=self.readiness_delta + other.readiness_delta
        )

    def apply(self, entity: EntityState, changes: Dict[str, Any]) -> None:
        from src.engine.apply import replace
        new_combat = changes.get("combat", entity.combat)
        if self.combat:
            u_com = self.combat
            new_hp = max(0, new_combat.hp + u_com.hp_delta)
            new_combat = replace(new_combat, 
                hp=new_hp, 
                max_hp=new_combat.max_hp + u_com.max_hp_delta,
                alive=(new_hp > 0) if u_com.alive_set is None else u_com.alive_set,
                atk=new_combat.atk + u_com.atk_delta,
                def_stat=new_combat.def_stat + u_com.def_delta,
                speed=new_combat.speed + u_com.speed_delta,
            )
        if self.readiness_delta != 0.0:
            new_combat = replace(new_combat, readiness=max(0.0, min(100.0, new_combat.readiness + self.readiness_delta)))
        
        if new_combat is not entity.combat:
            changes["combat"] = new_combat


@dataclass(frozen=True, slots=True)
class StaminaPatch(ComponentPatch):
    stamina_update: Optional[Any] = None # StaminaUpdate

    def is_noop(self) -> bool:
        return self.stamina_update is None or self.stamina_update.is_noop()

    def merge(self, other: StaminaPatch) -> StaminaPatch:
        if not other or other.is_noop():
            return self
        merged_stam = self.stamina_update.merge(other.stamina_update) if self.stamina_update and other.stamina_update else (other.stamina_update or self.stamina_update)
        return StaminaPatch(entity_id=self.entity_id, stamina_update=merged_stam)

    def apply(self, entity: EntityState, changes: Dict[str, Any]) -> None:
        from src.engine.apply import ApplyPath
        if self.stamina_update:
            u_stam = self.stamina_update
            new_stamina = changes.get("stamina", entity.stamina)
            new_stamina = ApplyPath._fast_replace_stamina(
                new_stamina,
                max(0.0, min(u_stam.max_stamina_set or new_stamina.max_stamina, (u_stam.current_set if u_stam.current_set is not None else new_stamina.current) + u_stam.current_delta)),
                u_stam.max_stamina_set
            )
            if new_stamina is not entity.stamina:
                changes["stamina"] = new_stamina


@dataclass(frozen=True, slots=True)
class InventoryPatch(ComponentPatch):
    inventory: Optional[Any] = None # InventoryUpdate
    resource_transfers: List[Any] = field(default_factory=list) # List[ResourceTransferIntent]

    def is_noop(self) -> bool:
        return (self.inventory is None or self.inventory.is_noop()) and not self.resource_transfers

    def merge(self, other: InventoryPatch) -> InventoryPatch:
        if not other or other.is_noop():
            return self
        merged_inv = self.inventory.merge(other.inventory) if self.inventory and other.inventory else (other.inventory or self.inventory)
        return InventoryPatch(
            entity_id=self.entity_id,
            inventory=merged_inv,
            resource_transfers=self.resource_transfers + other.resource_transfers
        )

    def apply(self, entity: EntityState, changes: Dict[str, Any]) -> None:
        from src.core.inventory import InventoryService
        new_inv = changes.get("inventory", entity.inventory)
        if self.inventory:
            new_inv = InventoryService.apply_update(new_inv, self.inventory)
        if self.resource_transfers:
            for transfer in self.resource_transfers:
                new_inv = InventoryService.apply_transfer(new_inv, transfer)
        
        if new_inv is not entity.inventory:
            changes["inventory"] = new_inv


@dataclass(frozen=True, slots=True)
class EquipmentPatch(ComponentPatch):
    equipment: Optional[Any] = None # EquipmentUpdate

    def is_noop(self) -> bool:
        return self.equipment is None or self.equipment.is_noop()

    def merge(self, other: EquipmentPatch) -> EquipmentPatch:
        if not other or other.is_noop():
            return self
        merged_eq = self.equipment.merge(other.equipment) if self.equipment and other.equipment else (other.equipment or self.equipment)
        return EquipmentPatch(entity_id=self.entity_id, equipment=merged_eq)

    def apply(self, entity: EntityState, changes: Dict[str, Any]) -> None:
        from src.engine.apply import replace
        from src.core.state import ReadOnlyDict
        if self.equipment:
            u_eq = self.equipment
            new_eq = changes.get("equipment", entity.equipment)
            new_slots = dict(new_eq.slots)
            new_slots.update(u_eq.slot_updates)
            
            new_durability = dict(new_eq.durability)
            for slot, delta in u_eq.durability_delta.items():
                new_durability[slot] = max(0.0, min(100.0, new_durability.get(slot, 100.0) + delta))
            for slot, val in u_eq.durability_set.items():
                new_durability[slot] = max(0.0, min(100.0, val))
                
            changes["equipment"] = replace(new_eq, slots=ReadOnlyDict(new_slots), durability=ReadOnlyDict(new_durability))


@dataclass(frozen=True, slots=True)
class StrategicPatch(ComponentPatch):
    strategic: Optional[Any] = None # StrategicUpdate

    def is_noop(self) -> bool:
        return self.strategic is None or self.strategic.is_noop()

    def merge(self, other: StrategicPatch) -> StrategicPatch:
        if not other or other.is_noop():
            return self
        merged_strat = self.strategic.merge(other.strategic) if self.strategic and other.strategic else (other.strategic or self.strategic)
        return StrategicPatch(entity_id=self.entity_id, strategic=merged_strat)

    def apply(self, entity: EntityState, changes: Dict[str, Any]) -> None:
        from src.engine.apply import replace, shallow_freeze
        if self.strategic:
            u_strat = self.strategic
            new_strat = changes.get("strategic", entity.strategic)
            
            def merge_dict(current_dict, add_list, remove_list):
                if not add_list and not remove_list:
                    return current_dict
                res = dict(current_dict)
                for item in add_list:
                    res[item.id] = item
                for item_id in remove_list:
                    res.pop(item_id, None)
                return res

            def merge_committed_intentions(current_tuple, add_list, remove_list):
                if not add_list and not remove_list:
                    return current_tuple
                by_id = {ci.intention_id: ci for ci in current_tuple}
                for item in add_list:
                    by_id[item.intention_id] = item
                for item_id in remove_list:
                    by_id.pop(item_id, None)
                return tuple(sorted(by_id.values(), key=lambda ci: ci.sequence_index))

            nb = merge_dict(new_strat.blockers, u_strat.blockers_add_or_update, u_strat.blockers_remove)
            nl = merge_dict(new_strat.leads, u_strat.leads_add_or_update, u_strat.leads_remove)
            nd = merge_dict(new_strat.directives, u_strat.directives_add_or_update, u_strat.directives_remove)
            np = merge_dict(new_strat.projects, u_strat.projects_add_or_update, u_strat.projects_remove)
            nc = merge_dict(new_strat.concerns, u_strat.concerns_add_or_update, u_strat.concerns_remove)
            ncz = merge_dict(new_strat.candidate_zones, u_strat.candidate_zones_add_or_update, u_strat.candidate_zones_remove)
            nh = merge_dict(new_strat.hypotheses, u_strat.hypotheses_add_or_update, u_strat.hypotheses_remove)
            ncon = merge_dict(new_strat.contracts, u_strat.contracts_add_or_update, u_strat.contracts_remove)
            nbel = merge_dict(new_strat.beliefs, u_strat.beliefs_add_or_update, u_strat.beliefs_remove)
            ntp = list(new_strat.turning_points) + u_strat.turning_points_add
            
            max_tps = getattr(new_strat.profile, "max_turning_points", 20)
            if len(ntp) > max_tps:
                ntp = ntp[-max_tps:]
                
            nbor = new_strat.boredom
            if u_strat.boredom_delta:
                nbor = dict(nbor)
                for k, d in u_strat.boredom_delta.items():
                    nbor[k] = nbor.get(k, 0.0) + d

            ntrust = new_strat.source_trust
            if u_strat.source_trust_updates:
                ntrust = dict(ntrust)
                for entry in u_strat.source_trust_updates:
                    ntrust[entry.entity_id] = entry

            nci = merge_committed_intentions(new_strat.committed_intentions, u_strat.committed_intentions_add_or_update, u_strat.committed_intentions_remove)

            new_strat = replace(new_strat,
                blockers=shallow_freeze(nb), leads=shallow_freeze(nl), directives=shallow_freeze(nd),
                projects=shallow_freeze(np), concerns=shallow_freeze(nc), candidate_zones=shallow_freeze(ncz),
                hypotheses=shallow_freeze(nh), contracts=shallow_freeze(ncon), turning_points=tuple(ntp),
                boredom=shallow_freeze(nbor), source_trust=shallow_freeze(ntrust), beliefs=shallow_freeze(nbel),
                committed_intentions=nci,
                current_project_id=u_strat.current_project_id_set if u_strat.current_project_id_set is not None else new_strat.current_project_id,
                current_objective_id=u_strat.current_objective_id_set if u_strat.current_objective_id_set is not None else new_strat.current_objective_id
            )
            changes["strategic"] = new_strat


@dataclass(frozen=True, slots=True)
class QuestPatch(ComponentPatch):
    quest: Optional[Any] = None # QuestUpdate

    def is_noop(self) -> bool:
        return self.quest is None or self.quest.is_noop()

    def merge(self, other: QuestPatch) -> QuestPatch:
        if not other or other.is_noop():
            return self
        merged_q = self.quest.merge(other.quest) if self.quest and other.quest else (other.quest or self.quest)
        return QuestPatch(entity_id=self.entity_id, quest=merged_q)

    def apply(self, entity: EntityState, changes: Dict[str, Any]) -> None:
        from src.engine.apply import replace, shallow_freeze
        from src.core.quests import QuestState
        from src.quests.service import QuestService
        if self.quest:
            new_strat = changes.get("strategic", entity.strategic)
            np = dict(new_strat.projects)
            q_updates = self.quest.multi_updates if self.quest.multi_updates else [self.quest]
            for qu in q_updates:
                q_id = qu.quest_id
                project = np.get(q_id)
                if project and isinstance(project, QuestState):
                    updated_quest = QuestService.add_progress(project, qu.progress_delta)
                    if qu.status_set is not None:
                        updated_quest = replace(updated_quest, quest_status=qu.status_set)
                    np[q_id] = updated_quest
            changes["strategic"] = replace(new_strat, projects=shallow_freeze(np))


@dataclass(frozen=True, slots=True)
class SocialPatch(ComponentPatch):
    social: Optional[Any] = None # SocialUpdate

    def is_noop(self) -> bool:
        return self.social is None or self.social.is_noop()

    def merge(self, other: SocialPatch) -> SocialPatch:
        if not other or other.is_noop():
            return self
        merged_soc = self.social.merge(other.social) if self.social and other.social else (other.social or self.social)
        return SocialPatch(entity_id=self.entity_id, social=merged_soc)

    def apply(self, entity: EntityState, changes: Dict[str, Any]) -> None:
        from src.systems.social_systems.relationships import RelationshipService
        if self.social:
            changes["social"] = RelationshipService.process_update(changes.get("social", entity.social), self.social)


@dataclass(frozen=True, slots=True)
class TaskPatch(ComponentPatch):
    task: Optional[Any] = None # TaskUpdate

    def is_noop(self) -> bool:
        return self.task is None or self.task.is_noop()

    def merge(self, other: TaskPatch) -> TaskPatch:
        if not other or other.is_noop():
            return self
        merged_task = self.task.merge(other.task) if self.task and other.task else (other.task or self.task)
        return TaskPatch(entity_id=self.entity_id, task=merged_task)

    def apply(self, entity: EntityState, changes: Dict[str, Any]) -> None:
        from src.engine.apply import replace
        if self.task:
            new_task = replace(entity.task, 
                work_kind=self.task.work_kind_set if self.task.work_kind_set is not None else entity.task.work_kind,
                payload=self.task.payload_set if self.task.payload_set is not None else entity.task.payload
            )
            if new_task != entity.task:
                changes["task"] = new_task


@dataclass(frozen=True, slots=True)
class AttributePatch(ComponentPatch):
    attributes: Optional[Any] = None # AttributeUpdate

    def is_noop(self) -> bool:
        return self.attributes is None or self.attributes.is_noop()

    def merge(self, other: AttributePatch) -> AttributePatch:
        if not other or other.is_noop():
            return self
        merged_att = self.attributes.merge(other.attributes) if self.attributes and other.attributes else (other.attributes or self.attributes)
        return AttributePatch(entity_id=self.entity_id, attributes=merged_att)

    def apply(self, entity: EntityState, changes: Dict[str, Any]) -> None:
        from src.engine.apply import replace
        if self.attributes:
            u_att = self.attributes
            new_att = changes.get("attributes", entity.attributes)
            changes["attributes"] = replace(new_att,
                strength=min(100, new_att.strength + u_att.strength_delta),
                agility=min(100, new_att.agility + u_att.agility_delta),
                vitality=min(100, new_att.vitality + u_att.vitality_delta),
                endurance=min(100, new_att.endurance + u_att.endurance_delta),
                intelligence=min(100, new_att.intelligence + u_att.intelligence_delta),
                spirit=min(100, new_att.spirit + u_att.spirit_delta),
                wisdom=min(100, new_att.wisdom + u_att.wisdom_delta),
                perception=min(100, new_att.perception + u_att.perception_delta),
                charisma=min(100, new_att.charisma + u_att.charisma_delta)
            )


@dataclass(frozen=True, slots=True)
class RewardPatch(ComponentPatch):
    reward: Optional[Any] = None # RewardUpdate

    def is_noop(self) -> bool:
        return self.reward is None or self.reward.is_noop()

    def merge(self, other: RewardPatch) -> RewardPatch:
        if not other or other.is_noop():
            return self
        merged_rew = self.reward.merge(other.reward) if self.reward and other.reward else (other.reward or self.reward)
        return RewardPatch(entity_id=self.entity_id, reward=merged_rew)

    def apply(self, entity: EntityState, changes: Dict[str, Any]) -> None:
        from src.engine.apply import replace
        from src.progression.leveling import LevelingService
        if self.reward and self.reward.xp_gain > 0:
            new_id = changes.get("identity", entity.identity)
            prog_upd = LevelingService.process_progression(new_id, self.reward.xp_gain)
            changes["identity"] = replace(new_id,
                evolution_level=prog_upd.evolution_level_set if prog_upd.evolution_level_set is not None else new_id.evolution_level,
                evolution_points=new_id.evolution_points + prog_upd.evolution_points_delta,
                unspent_ap=new_id.unspent_ap + prog_upd.unspent_ap_delta
            )


@dataclass(frozen=True, slots=True)
class WoundPatch(ComponentPatch):
    wound_update: Optional[Any] = None # WoundUpdate

    def is_noop(self) -> bool:
        return self.wound_update is None or self.wound_update.is_noop()

    def merge(self, other: WoundPatch) -> WoundPatch:
        if not other or other.is_noop():
            return self
        merged_w = self.wound_update.merge(other.wound_update) if self.wound_update and other.wound_update else (other.wound_update or self.wound_update)
        return WoundPatch(entity_id=self.entity_id, wound_update=merged_w)

    def apply(self, entity: EntityState, changes: Dict[str, Any]) -> None:
        from src.engine.apply import replace
        if self.wound_update:
            new_com = changes.get("combat", entity.combat)
            new_wounds = list(new_com.wounds)
            new_scars = list(new_com.scars)
            new_wounds.extend(self.wound_update.wounds_add)
            new_scars.extend(self.wound_update.scars_add)
            if self.wound_update.wounds_heal:
                new_wounds = [w if w.id not in self.wound_update.wounds_heal else replace(w, healed=True) for w in new_wounds]
            new_com = replace(new_com, wounds=tuple(new_wounds), scars=tuple(new_scars))
            changes["combat"] = new_com


@dataclass(frozen=True, slots=True)
class SelfModelPatch(ComponentPatch):
    self_model_bundle_set: Optional[Any] = None  # SelfModelBundle

    def is_noop(self) -> bool:
        return self.self_model_bundle_set is None

    def merge(self, other: SelfModelPatch) -> SelfModelPatch:
        if not other or other.is_noop():
            return self
        return SelfModelPatch(
            entity_id=self.entity_id,
            self_model_bundle_set=other.self_model_bundle_set if other.self_model_bundle_set is not None else self.self_model_bundle_set,
        )

    def apply(self, entity: EntityState, changes: Dict[str, Any]) -> None:
        if self.self_model_bundle_set is not None:
            changes["self_model"] = self.self_model_bundle_set


@dataclass(frozen=True, slots=True)
class CognitionPatch(ComponentPatch):
    cognition_bundle_set: Optional[Any] = None  # CognitionModel

    def is_noop(self) -> bool:
        return self.cognition_bundle_set is None

    def merge(self, other: CognitionPatch) -> CognitionPatch:
        if not other or other.is_noop():
            return self
        return CognitionPatch(
            entity_id=self.entity_id,
            cognition_bundle_set=other.cognition_bundle_set if other.cognition_bundle_set is not None else self.cognition_bundle_set,
        )

    def apply(self, entity: EntityState, changes: Dict[str, Any]) -> None:
        if self.cognition_bundle_set is not None:
            changes["cognition"] = self.cognition_bundle_set


def extract_patches(entity_id: int, update: EntityUpdate) -> List[ComponentPatch]:
    """
    Extracts all active component patches from a monolithic EntityUpdate.
    Preserves precise evaluation order for derived stats calculation.
    """
    patches = []
    if update.kind_set is not None:
        patches.append(KindPatch(entity_id, kind_set=update.kind_set))
    if update.lifecycle is not None or update.active is not None:
        p = LifecyclePatch(entity_id, lifecycle=update.lifecycle, active=update.active)
        if not p.is_noop(): patches.append(p)
    if update.biological is not None:
        p = BiologicalPatch(entity_id, biological=update.biological)
        if not p.is_noop(): patches.append(p)
    if update.interaction is not None:
        p = InteractionPatch(entity_id, interaction=update.interaction)
        if not p.is_noop(): patches.append(p)
    if update.identity is not None or update.group_id_set is not None or update.intent_results or update.property_updates:
        p = IdentityPatch(entity_id, identity=update.identity, group_id_set=update.group_id_set, intent_results=list(update.intent_results), property_updates=dict(update.property_updates))
        if not p.is_noop(): patches.append(p)
    if update.navigation is not None or update.new_position is not None or update.moved_this_tick:
        p = NavigationPatch(entity_id, navigation=update.navigation, new_position=update.new_position, moved_this_tick=update.moved_this_tick)
        if not p.is_noop(): patches.append(p)
    if update.combat is not None or update.readiness_delta != 0.0:
        p = CombatPatch(entity_id, combat=update.combat, readiness_delta=update.readiness_delta)
        if not p.is_noop(): patches.append(p)
    if update.stamina_update is not None:
        p = StaminaPatch(entity_id, stamina_update=update.stamina_update)
        if not p.is_noop(): patches.append(p)
    if update.inventory is not None or update.resource_transfers:
        p = InventoryPatch(entity_id, inventory=update.inventory, resource_transfers=list(update.resource_transfers))
        if not p.is_noop(): patches.append(p)
    if update.equipment is not None:
        p = EquipmentPatch(entity_id, equipment=update.equipment)
        if not p.is_noop(): patches.append(p)
    if update.strategic is not None:
        p = StrategicPatch(entity_id, strategic=update.strategic)
        if not p.is_noop(): patches.append(p)
    if update.quest is not None:
        p = QuestPatch(entity_id, quest=update.quest)
        if not p.is_noop(): patches.append(p)
    if update.social is not None:
        p = SocialPatch(entity_id, social=update.social)
        if not p.is_noop(): patches.append(p)
    if update.task is not None:
        p = TaskPatch(entity_id, task=update.task)
        if not p.is_noop(): patches.append(p)
    if update.attributes is not None:
        p = AttributePatch(entity_id, attributes=update.attributes)
        if not p.is_noop(): patches.append(p)
    if update.reward is not None:
        p = RewardPatch(entity_id, reward=update.reward)
        if not p.is_noop(): patches.append(p)
    if update.wound_update is not None:
        p = WoundPatch(entity_id, wound_update=update.wound_update)
        if not p.is_noop(): patches.append(p)
    if update.self_model_bundle_set is not None:
        p = SelfModelPatch(entity_id, self_model_bundle_set=update.self_model_bundle_set)
        if not p.is_noop(): patches.append(p)
    if update.cognition_bundle_set is not None:
        p = CognitionPatch(entity_id, cognition_bundle_set=update.cognition_bundle_set)
        if not p.is_noop(): patches.append(p)
    return patches
