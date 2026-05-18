# Compliance IDs: PERF-005, PERF-015
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Set, Dict, TYPE_CHECKING

if TYPE_CHECKING:
    from src.core.updates import StateUpdate
    from src.core.state import AuthoritativeState

class DirtySetLeakError(Exception):
    """Raised when a mutation is detected that was not captured by the DirtySet."""
    pass

def get_relevant_entity_ids(state: AuthoritativeState, update: StateUpdate, domain: str) -> Set[int]:
    """
    Safely filter candidate entity IDs for a given pipeline domain.
    Ensures that if force_full_scan is active or no dirty set exists, all entity IDs are returned.
    Otherwise, returns the domain-specific dirty entity subset.
    """
    if update.force_full_scan or update.dirty_set is None:
        return set(state.entities.keys())
        
    ds = update.dirty_set
    if domain == "interactions":
        return ds.movement_entities | ds.strategic_entities
    elif domain == "redirection":
        return ds.strategic_entities
    elif domain == "groups":
        return ds.movement_entities | ds.combat_entities | ds.social_entities
    elif domain == "shop":
        return ds.movement_entities | ds.inventory_entities
    elif domain == "capacity":
        return ds.strategic_entities
    elif domain == "town":
        return ds.town_entities | ds.movement_entities | ds.combat_entities
    elif domain == "all":
        return ds.all_dirty_entities
    else:
        return set(state.entities.keys())

def get_relevant_group_ids(state: AuthoritativeState, update: Optional[StateUpdate]) -> Set[int]:
    """
    Safely filter candidate group IDs.
    Ensures that if force_full_scan is active or no dirty set exists, all group IDs are returned.
    """
    if not update or update.force_full_scan or update.dirty_set is None:
        return set(state.groups.keys())
    return update.dirty_set.group_ids

def get_dirty_set(update: Optional[StateUpdate]) -> Optional[DirtySet]:
    """
    Safely retrieve the DirtySet from a StateUpdate without triggering direct access warnings.
    """
    if not update:
        return None
    return getattr(update, "dirty_set", None)

class DirtySetBuilder:
    """
    Mutable builder for DirtySet to avoid excessive object creation and set copying.
    """
    def __init__(self, base: Optional[DirtySet] = None):
        self._processed_upd_ids = set()
        if base:
            self.movement = set(base.movement_entities)
            self.combat = set(base.combat_entities)
            self.inventory = set(base.inventory_entities)
            self.strategic = set(base.strategic_entities)
            self.social = set(base.social_entities)
            self.lifecycle = set(base.lifecycle_entities)
            self.biological = set(base.biological_entities)
            self.attributes = set(base.attribute_entities)
            self.town = set(base.town_entities)
            self.groups = set(base.group_ids)
            self.regions = set(base.region_ids)
            self.nodes = set(base.resource_node_ids)
            self.buildings = set(base.building_ids)
            self.chests = set(base.chest_ids)
            self.ground_items = set(base.ground_item_ids)
            self.corpses = set(base.corpse_ids)
            self.camps = set(base.camp_ids)
        else:
            self.movement = set()
            self.combat = set()
            self.inventory = set()
            self.strategic = set()
            self.social = set()
            self.lifecycle = set()
            self.biological = set()
            self.attributes = set()
            self.town = set()
            self.groups = set()
            self.regions = set()
            self.nodes = set()
            self.buildings = set()
            self.chests = set()
            self.ground_items = set()
            self.corpses = set()
            self.camps = set()

    def mark_entity(self, e_id: int, tags: List[str]):
        for tag in tags:
            if tag == "movement": self.movement.add(e_id)
            elif tag == "combat": self.combat.add(e_id)
            elif tag == "inventory": self.inventory.add(e_id)
            elif tag == "strategic": self.strategic.add(e_id)
            elif tag == "social": self.social.add(e_id)
            elif tag == "lifecycle": self.lifecycle.add(e_id)
            elif tag == "biological": self.biological.add(e_id)
            elif tag == "attributes": self.attributes.add(e_id)

    def mark_from_update(self, state: AuthoritativeState, update: StateUpdate):
        """Incremental update from a StateUpdate."""
        self.groups.update(update.groups_remove)
        for g in update.groups_add_or_update:
            self.groups.add(g.id)
            
        self.regions.update(update.world_updates.keys())
        self.nodes.update(update.node_updates.keys())
        for n in update.nodes_add:
            self.nodes.add(n.id)
            
        self.buildings.update(update.building_updates.keys())
        self.chests.update(update.chest_updates.keys())
        for c in update.chest_add_or_update:
            self.chests.add(c.id)
            
        self.ground_items.update(update.ground_items_remove)
        for i in update.ground_items_add_or_update:
            self.ground_items.add(i.id)
            
        self.corpses.update(update.corpses_remove)
        for c in update.corpses_add_or_update:
            self.corpses.add(c.id)
            
        self.camps.update(update.camp_updates.keys())

        # Entity updates
        for e_id, e_upd in update.entity_updates.items():
            upd_id = id(e_upd)
            if upd_id in self._processed_upd_ids:
                continue
            self._processed_upd_ids.add(upd_id)
            if e_upd.new_position:
                self.movement.add(e_id)
                # Town movement check
                tile_pos = (int(e_upd.new_position[0]), int(e_upd.new_position[1]))
                if tile_pos in state.town_tiles:
                    self.town.add(e_id)
                else:
                    self.town.discard(e_id)
            
            if e_upd.combat:
                self.combat.add(e_id)
                self.strategic.add(e_id)
            
            if e_upd.inventory or e_upd.resource_transfers:
                self.inventory.add(e_id)
                self.strategic.add(e_id)
            
            if e_upd.strategic:
                self.strategic.add(e_id)
            
            if e_upd.social:
                self.social.add(e_id)
                
            if e_upd.lifecycle:
                self.lifecycle.add(e_id)
            
            if e_upd.biological:
                self.biological.add(e_id)
                self.strategic.add(e_id)
                
            if e_upd.attributes:
                self.attributes.add(e_id)
                
            ent = state.entities.get(e_id)
            if ent and ent.identity.group_id is not None:
                self.groups.add(ent.identity.group_id)

    def build(self) -> DirtySet:
        ds = DirtySet(
            movement_entities=self.movement,
            combat_entities=self.combat,
            inventory_entities=self.inventory,
            strategic_entities=self.strategic,
            social_entities=self.social,
            lifecycle_entities=self.lifecycle,
            biological_entities=self.biological,
            attribute_entities=self.attributes,
            town_entities=self.town,
            group_ids=self.groups,
            region_ids=self.regions,
            resource_node_ids=self.nodes,
            building_ids=self.buildings,
            chest_ids=self.chests,
            ground_item_ids=self.ground_items,
            corpse_ids=self.corpses,
            camp_ids=self.camps
        )
        return DirtyDependencyGraph.expand(ds)

@dataclass(frozen=True, slots=True)
class DirtySet:
    """
    Tracks which entities or world objects were modified during the tick.
    Used to optimize systems by avoiding O(N) scans.
    Logic ID: PERF-006 (Dirty Entity Tracking)
    """
    movement_entities: Set[int] = field(default_factory=set)
    combat_entities: Set[int] = field(default_factory=set)
    inventory_entities: Set[int] = field(default_factory=set)
    strategic_entities: Set[int] = field(default_factory=set)
    social_entities: Set[int] = field(default_factory=set)
    lifecycle_entities: Set[int] = field(default_factory=set)
    town_entities: Set[int] = field(default_factory=set)
    biological_entities: Set[int] = field(default_factory=set)
    attribute_entities: Set[int] = field(default_factory=set)
    
    group_ids: Set[int] = field(default_factory=set)
    region_ids: Set[str] = field(default_factory=set)
    resource_node_ids: Set[int] = field(default_factory=set)
    building_ids: Set[int] = field(default_factory=set)
    chest_ids: Set[int] = field(default_factory=set)
    ground_item_ids: Set[int] = field(default_factory=set)
    corpse_ids: Set[int] = field(default_factory=set)
    camp_ids: Set[str] = field(default_factory=set)

    @property
    def all_dirty_entities(self) -> Set[int]:
        return (self.movement_entities | self.combat_entities | self.inventory_entities | 
                self.strategic_entities | self.social_entities | self.lifecycle_entities | 
                self.biological_entities | self.attribute_entities)

    @staticmethod
    def from_update(state: AuthoritativeState, update: StateUpdate, base_dirty: Optional[DirtySet] = None) -> DirtySet:
        """
        Derive a DirtySet from a StateUpdate.
        M3 Law: This must be deterministic and exhaustive for modified fields.
        M7 Optimization: Support incremental updates from a base_dirty set.
        """
        if base_dirty is None:
            movement = set()
            combat = set()
            inventory = set()
            strategic = set()
            social = set()
            lifecycle = set()
            biological = set()
            attributes = set()
            groups = set()
            regions = set()
            nodes = set()
            buildings = set()
            chests = set()
            ground_items = set()
            corpses = set()
            camps = set()
            town = state.town_entity_ids
            town_cloned = False
        else:
            movement = set(base_dirty.movement_entities)
            combat = set(base_dirty.combat_entities)
            inventory = set(base_dirty.inventory_entities)
            strategic = set(base_dirty.strategic_entities)
            social = set(base_dirty.social_entities)
            lifecycle = set(base_dirty.lifecycle_entities)
            biological = set(base_dirty.biological_entities)
            attributes = set(base_dirty.attribute_entities)
            groups = set(base_dirty.group_ids)
            regions = set(base_dirty.region_ids)
            nodes = set(base_dirty.resource_node_ids)
            buildings = set(base_dirty.building_ids)
            chests = set(base_dirty.chest_ids)
            ground_items = set(base_dirty.ground_item_ids)
            corpses = set(base_dirty.corpse_ids)
            camps = set(base_dirty.camp_ids)
            town = base_dirty.town_entities
            town_cloned = False
        
        groups.update(update.groups_remove)
        for g in update.groups_add_or_update:
            groups.add(g.id)
            
        regions.update(update.world_updates.keys())
        
        nodes.update(update.node_updates.keys())
        for n in update.nodes_add:
            nodes.add(n.id)
            
        buildings.update(update.building_updates.keys())
        
        chests.update(update.chest_updates.keys())
        for c in update.chest_add_or_update:
            chests.add(c.id)
            
        ground_items.update(update.ground_items_remove)
        for i in update.ground_items_add_or_update:
            ground_items.add(i.id)
            
        corpses.update(update.corpses_remove)
        for c in update.corpses_add_or_update:
            corpses.add(c.id)
            
        camps.update(update.camp_updates.keys())

        for e_id, e_upd in update.entity_updates.items():
            if e_upd.new_position:
                movement.add(e_id)
                if not town_cloned:
                    town = set(town)
                    town_cloned = True
                new_pos = e_upd.new_position
                tile_pos = (int(new_pos[0]), int(new_pos[1]))
                if tile_pos in state.town_tiles:
                    town.add(e_id)
                else:
                    town.discard(e_id)
            
            if e_upd.combat:
                combat.add(e_id)
                strategic.add(e_id)
            
            if e_upd.inventory or e_upd.resource_transfers:
                inventory.add(e_id)
                strategic.add(e_id)
            
            if e_upd.strategic:
                strategic.add(e_id)
            
            if e_upd.social:
                social.add(e_id)
                
            if e_upd.lifecycle:
                lifecycle.add(e_id)
            
            if e_upd.biological:
                biological.add(e_id)
                strategic.add(e_id)
                
            if e_upd.attributes:
                attributes.add(e_id)
                
            ent = state.entities.get(e_id)
            if ent and ent.identity.group_id is not None:
                groups.add(ent.identity.group_id)
            if e_upd.group_id_set is not None:
                if ent and ent.identity.group_id is not None:
                    groups.add(ent.identity.group_id)
                groups.add(e_upd.group_id_set)

        union_ids = {e.id for e in update.entities_add}
        if update.entities_remove:
            union_ids.update(update.entities_remove)
        
        ds = DirtySet(
            movement_entities=movement | union_ids,
            combat_entities=combat | union_ids,
            inventory_entities=inventory | union_ids,
            strategic_entities=strategic | union_ids,
            social_entities=social | union_ids,
            lifecycle_entities=lifecycle | union_ids,
            biological_entities=biological | union_ids,
            attribute_entities=attributes | union_ids,
            town_entities=town,
            group_ids=groups,
            region_ids=regions,
            resource_node_ids=nodes,
            building_ids=buildings,
            chest_ids=chests,
            ground_item_ids=ground_items,
            corpse_ids=corpses,
            camp_ids=camps
        )
        return DirtyDependencyGraph.expand(ds)

    def merge(self, other: DirtySet) -> DirtySet:
        """Merges another DirtySet into this one via set unions."""
        ds = DirtySet(
            movement_entities=self.movement_entities | other.movement_entities,
            combat_entities=self.combat_entities | other.combat_entities,
            inventory_entities=self.inventory_entities | other.inventory_entities,
            strategic_entities=self.strategic_entities | other.strategic_entities,
            social_entities=self.social_entities | other.social_entities,
            lifecycle_entities=self.lifecycle_entities | other.lifecycle_entities,
            town_entities=self.town_entities | other.town_entities,
            group_ids=self.group_ids | other.group_ids,
            region_ids=self.region_ids | other.region_ids,
            resource_node_ids=self.resource_node_ids | other.resource_node_ids,
            building_ids=self.building_ids | other.building_ids,
            chest_ids=self.chest_ids | other.chest_ids,
            ground_item_ids=self.ground_item_ids | other.ground_item_ids,
            corpse_ids=self.corpse_ids | other.corpse_ids,
            camp_ids=self.camp_ids | other.camp_ids,
            biological_entities=self.biological_entities | other.biological_entities,
            attribute_entities=self.attribute_entities | other.attribute_entities
        )
        return DirtyDependencyGraph.expand(ds)


class DirtyDependencyGraph:
    """
    Expands direct dirtiness into derived dirtiness across related simulation domains.
    Logic ID: PERF-008 (Dirty Dependency Expansion)
    """
    @staticmethod
    def expand(dirty: DirtySet) -> DirtySet:
        movement = set(dirty.movement_entities)
        combat = set(dirty.combat_entities)
        inventory = set(dirty.inventory_entities)
        strategic = set(dirty.strategic_entities)
        social = set(dirty.social_entities)
        lifecycle = set(dirty.lifecycle_entities)
        town = set(dirty.town_entities)
        biological = set(dirty.biological_entities)
        attributes = set(dirty.attribute_entities)

        # 1. Movement implies strategic (positional proximity/pathfinding) and social (encounters)
        if movement:
            strategic.update(movement)
            social.update(movement)

        # 2. Inventory implies strategic (evaluating item usage, capacity, and shop transactions)
        if inventory:
            strategic.update(inventory)

        # 3. Combat implies lifecycle (health/near-death checks), social (group morale/fleeing), and strategic
        if combat:
            lifecycle.update(combat)
            social.update(combat)
            strategic.update(combat)

        # 4. Biological and Attributes imply strategic and lifecycle evaluation
        if biological or attributes:
            strategic.update(biological | attributes)
            lifecycle.update(biological | attributes)

        return DirtySet(
            movement_entities=movement,
            combat_entities=combat,
            inventory_entities=inventory,
            strategic_entities=strategic,
            social_entities=social,
            lifecycle_entities=lifecycle,
            town_entities=town,
            biological_entities=biological,
            attribute_entities=attributes,
            group_ids=set(dirty.group_ids),
            region_ids=set(dirty.region_ids),
            resource_node_ids=set(dirty.resource_node_ids),
            building_ids=set(dirty.building_ids),
            chest_ids=set(dirty.chest_ids),
            ground_item_ids=set(dirty.ground_item_ids),
            corpse_ids=set(dirty.corpse_ids),
            camp_ids=set(dirty.camp_ids)
        )


class CandidateSelector:
    """
    Central authoritative mechanism for determining which entities a simulation phase should process.
    Ensures deterministic ordering, full-scan fallback compliance, and correct domain-to-dirty-set mapping.
    Logic ID: PERF-007 (Authoritative Candidate Selection)
    """
    @staticmethod
    def entities(
        state: AuthoritativeState,
        update: StateUpdate,
        domains: Set[str],
        *,
        include_inactive: bool = False
    ) -> tuple[int, ...]:
        if update.force_full_scan or update.dirty_set is None:
            candidates = set(state.entities.keys())
        else:
            ds = update.dirty_set
            candidates = set()
            for d in domains:
                if d == "movement": candidates |= ds.movement_entities
                elif d == "combat": candidates |= ds.combat_entities
                elif d == "inventory": candidates |= ds.inventory_entities
                elif d == "strategic": candidates |= ds.strategic_entities
                elif d == "social": candidates |= ds.social_entities
                elif d == "lifecycle": candidates |= ds.lifecycle_entities
                elif d == "biological": candidates |= ds.biological_entities
                elif d == "attributes": candidates |= ds.attribute_entities
                elif d == "town": candidates |= ds.town_entities
                elif d == "interactions": candidates |= (ds.movement_entities | ds.strategic_entities)
                elif d == "groups": candidates |= (ds.movement_entities | ds.combat_entities | ds.social_entities)
                elif d == "shop": candidates |= (ds.movement_entities | ds.inventory_entities)
                elif d == "capacity": candidates |= ds.strategic_entities
                elif d == "redirection": candidates |= ds.strategic_entities
                elif d == "all": candidates |= ds.all_dirty_entities
                else: candidates |= set(state.entities.keys())
        
        if not include_inactive:
            filtered = []
            for e_id in candidates:
                ent = state.entities.get(e_id)
                if ent and ent.active:
                    filtered.append(e_id)
            return tuple(sorted(filtered))
        else:
            valid = [e_id for e_id in candidates if e_id in state.entities]
            return tuple(sorted(valid))

