from __future__ import annotations
from dataclasses import dataclass, field
from typing import Set, Dict, TYPE_CHECKING

if TYPE_CHECKING:
    from src.core.updates import StateUpdate
    from src.core.state import AuthoritativeState

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
    
    group_ids: Set[int] = field(default_factory=set)
    region_ids: Set[str] = field(default_factory=set)
    resource_node_ids: Set[int] = field(default_factory=set)

    @property
    def all_dirty_entities(self) -> Set[int]:
        return self.movement_entities | self.combat_entities | self.inventory_entities | self.strategic_entities | self.social_entities | self.lifecycle_entities

    @staticmethod
    def from_update(state: AuthoritativeState, update: StateUpdate) -> DirtySet:
        """
        Derive a DirtySet from a StateUpdate.
        M3 Law: This must be deterministic and exhaustive for modified fields.
        """
        movement = set()
        combat = set()
        inventory = set()
        strategic = set()
        social = set()
        lifecycle = set()
        
        # Optimization: Only clone town membership if it actually changes
        town = state.town_entity_ids
        town_cloned = False
        
        groups = set(update.groups_remove)
        for g in update.groups_add_or_update:
            groups.add(g.id)
            
        regions = set(update.world_updates.keys())
        nodes = set(update.node_updates.keys())
        for n in update.nodes_add:
            nodes.add(n.id)

        # 1. Single loop for all entity updates
        for e_id, e_upd in update.entity_updates.items():
            if e_upd.new_position:
                movement.add(e_id)
                # Town movement check
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
                if e_upd.combat.hp_delta < 0 or e_upd.combat.alive_set is False:
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
                
            # Propagate to group
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
        
        return DirtySet(
            movement_entities=movement | union_ids,
            combat_entities=combat | union_ids,
            inventory_entities=inventory | union_ids,
            strategic_entities=strategic | union_ids,
            social_entities=social | union_ids,
            lifecycle_entities=lifecycle | union_ids,
            town_entities=town,
            group_ids=groups,
            region_ids=regions,
            resource_node_ids=nodes
        )

    def merge(self, other: DirtySet) -> DirtySet:
        """Merges another DirtySet into this one via set unions."""
        return DirtySet(
            movement_entities=self.movement_entities | other.movement_entities,
            combat_entities=self.combat_entities | other.combat_entities,
            inventory_entities=self.inventory_entities | other.inventory_entities,
            strategic_entities=self.strategic_entities | other.strategic_entities,
            social_entities=self.social_entities | other.social_entities,
            lifecycle_entities=self.lifecycle_entities | other.lifecycle_entities,
            town_entities=self.town_entities | other.town_entities,
            group_ids=self.group_ids | other.group_ids,
            region_ids=self.region_ids | other.region_ids,
            resource_node_ids=self.resource_node_ids | other.resource_node_ids
        )
