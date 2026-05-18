from __future__ import annotations
from typing import TYPE_CHECKING, List, Optional
from dataclasses import replace
from src_legacy.core.updates import StateUpdate, EntityUpdate, LifecycleUpdate, InventoryUpdate

if TYPE_CHECKING:
    from src_legacy.core.state import AuthoritativeState, EntityState

class LifecycleSystem:
    """
    Handles entity lifecycle transitions: Aging, Death, Succession, and Heirlooms.
    Phase 9: Hero Lifecycle.
    """

    @staticmethod
    def resolve_lifecycle(state: AuthoritativeState, update: StateUpdate) -> StateUpdate:
        """
        Identify entities that have died and process succession/permadeath.
        """
        refined_entity_updates = dict(update.entity_updates)
        
        # Collect deaths for influence processing (Task 11.4)
        recent_deaths: List[EntityState] = []
        
        for e_id, entity in state.entities.items():
            if not entity.active: continue
            
            ent_upd = refined_entity_updates.get(e_id, EntityUpdate(entity_id=e_id))
            
            # Check for natural death (old age)
            is_dead = False
            death_reason = None
            
            if entity.lifecycle.age_ticks >= entity.lifecycle.max_age_ticks:
                is_dead = True
                death_reason = "OLD_AGE"
            
            # Check for combat death
            if ent_upd.combat and ent_upd.combat.outcome_kind == "KILL":
                is_dead = True
                death_reason = "COMBAT"
            
            if is_dead:
                recent_deaths.append(entity)
                # Mark as inactive and record death truth
                life_upd = ent_upd.lifecycle or LifecycleUpdate()
                refined_entity_updates[e_id] = replace(ent_upd,
                    active=False,
                    lifecycle=replace(life_upd,
                        is_permadeath_set=True,
                        death_tick_set=state.tick,
                        death_reason_set=death_reason
                    )
                )
                
                # Process Succession / Heirlooms
                if entity.lifecycle.heir_entity_id is not None:
                    heir_id = entity.lifecycle.heir_entity_id
                    heir = state.entities.get(heir_id)
                    if heir:
                        heir_upd = refined_entity_updates.get(heir_id, EntityUpdate(entity_id=heir_id))
                        # Transfer heirlooms
                        heir_inv = heir_upd.inventory or InventoryUpdate()
                        # Legacy Law: Heirlooms are transferred instantly upon death truth.
                        from src_legacy.core.state import ItemStack
                        new_items = [ItemStack(item_id=tid, quantity=1) for tid in entity.lifecycle.heirlooms]
                        refined_entity_updates[heir_id] = replace(heir_upd,
                            inventory=replace(heir_inv,
                                items_add=heir_inv.items_add + new_items
                            )
                        )

        # Apply Influence Shifts and Conquest Lifecycle
        if recent_deaths:
            from src_legacy.world.influence import FactionInfluenceService
            # Influence Shift
            inf_update = FactionInfluenceService.process_influence_shift(state, recent_deaths)
            # Conquest/Stronghold Lifecycle (Requires generator)
            from src_legacy.systems.generator import EntityGenerator
            generator = EntityGenerator(state.seed + state.tick)
            inf_update = FactionInfluenceService.process_conquest_lifecycle(state, inf_update, generator)
            
            # Merge world updates and new entities
            new_world_updates = dict(update.world_updates)
            for r_id, extra_upd in inf_update.world_updates.items():
                if r_id in new_world_updates:
                    new_world_updates[r_id] = new_world_updates[r_id].merge(extra_upd)
                else:
                    new_world_updates[r_id] = extra_upd
            
            update = replace(update,
                world_updates=new_world_updates,
                entities_add=list(update.entities_add) + list(inf_update.entities_add),
                entities_remove=list(update.entities_remove) + list(inf_update.entities_remove)
            )
                        
        return replace(update, entity_updates=refined_entity_updates)
