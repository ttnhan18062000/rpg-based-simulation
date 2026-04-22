from __future__ import annotations
from typing import TYPE_CHECKING, List, Optional
from dataclasses import replace
from src_v2.core.updates import StateUpdate, EntityUpdate, LifecycleUpdate, InventoryUpdate

if TYPE_CHECKING:
    from src_v2.core.state import AuthoritativeState, EntityState

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
        
        for e_id, entity in state.entities.items():
            if not entity.active: continue
            
            ent_upd = refined_entity_updates.get(e_id, EntityUpdate(entity_id=e_id))
            
            # Check for natural death (old age)
            is_dead = False
            death_reason = None
            
            # Note: entity.lifecycle.age_ticks is already incremented in ApplyPath.apply_generation
            # so we are checking the state as it was at the START of the tick.
            if entity.lifecycle.age_ticks >= entity.lifecycle.max_age_ticks:
                is_dead = True
                death_reason = "OLD_AGE"
            
            # Check for combat death
            if ent_upd.combat and ent_upd.combat.outcome_kind == "KILL":
                is_dead = True
                death_reason = "COMBAT"
            
            if is_dead:
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
                        refined_entity_updates[heir_id] = replace(heir_upd,
                            inventory=replace(heir_inv,
                                items_added=heir_inv.items_added + entity.lifecycle.heirlooms
                            )
                        )
                        
        return replace(update, entity_updates=refined_entity_updates)
