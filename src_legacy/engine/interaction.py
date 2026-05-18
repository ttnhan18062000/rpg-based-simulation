from __future__ import annotations
from dataclasses import replace
from typing import TYPE_CHECKING, Dict, List

from src_legacy.core.updates import InteractionUpdate, InventoryUpdate, ResourceNodeUpdate

if TYPE_CHECKING:
    from src_legacy.core.state import AuthoritativeState, EntityState
    from src_legacy.core.updates import StateUpdate, EntityUpdate


class InteractionSystem:
    """
    Law: Must follow Milestone B Runtime Signals Contract.
    Proof: Verified by mb_test_matrix.md and test_milestone_b_closure.py.
    """

    # V2 Engine Policy: Authoritative item weights for pressure enforcement
    ITEM_WEIGHTS: Dict[str, float] = {
        "WOOD": 2.0,
        "ORE": 5.0,
        "FISH": 1.0,
        "GOLD": 0.01,
        "__DEFAULT__": 1.0
    }

    @staticmethod
    def get_weight(item_kind: str) -> float:
        return InteractionSystem.ITEM_WEIGHTS.get(item_kind, InteractionSystem.ITEM_WEIGHTS["__DEFAULT__"])

    @staticmethod
    def enforce(state: AuthoritativeState, update: StateUpdate) -> StateUpdate:
        """
        Refine the proposed update according to authoritative interaction laws.
        Returns a new StateUpdate with enforced interaction outcomes.
        """
        refined_entity_updates = dict(update.entity_updates)
        refined_node_updates = dict(update.node_updates)
        
        for e_id, ent_upd in update.entity_updates.items():
            if ent_upd.interaction is None:
                continue
            
            entity = state.entities.get(e_id)
            if not entity:
                continue

            # 1. Channeling & Proximity Laws
            # Reset progress if moved or changed target
            current_target = entity.interaction.target_node_id
            proposed_target = ent_upd.interaction.target_node_id
            
            should_reset = False
            
            # Movement interruption
            if ent_upd.moved_this_tick:
                should_reset = True
            
            # Target switching
            if proposed_target is not None and current_target is not None and proposed_target != current_target:
                should_reset = True
                
            if should_reset:
                # Force a reset update
                refined_entity_updates[e_id] = replace(
                    ent_upd,
                    interaction=InteractionUpdate(reset=True)
                )
                continue

            # 2. Progress Advancement
            if ent_upd.interaction.progress_delta >= 0:
                target_id = proposed_target if proposed_target is not None else current_target
                if target_id is None:
                    continue
                
                node = state.resource_nodes.get(target_id)
                if not node or not node.remaining_charges > 0 or node.cooldown_remaining > 0:
                    # Node gone or depleted: Reset
                    refined_entity_updates[e_id] = replace(
                        ent_upd,
                        interaction=InteractionUpdate(reset=True)
                    )
                    continue

                new_progress = entity.interaction.progress + ent_upd.interaction.progress_delta
                
                if new_progress >= node.required_ticks:
                    # 3. Pressure Law (Slot & Weight Check)
                    from src_legacy.core.inventory import InventoryService
                    item_kind = node.yields_item
                    
                    if not InventoryService.can_add_item(entity.inventory, item_kind, 1):
                        # Pressure Failure: Cannot carry more
                        refined_entity_updates[e_id] = replace(
                            ent_upd,
                            interaction=InteractionUpdate(reset=True)
                        )
                        continue
                    
                    # 4. Successful Harvest/Loot Completion
                    # Update Entity: Reset progress, Add item
                    from src_legacy.core.state import ItemStack
                    from src_legacy.core.updates import InventoryUpdate
                    
                    existing_inv = ent_upd.inventory or InventoryUpdate()
                    new_inv = replace(existing_inv, items_add=list(existing_inv.items_add) + [ItemStack(item_kind, 1)])
                    
                    refined_entity_updates[e_id] = replace(
                        ent_upd,
                        interaction=InteractionUpdate(reset=True),
                        inventory=new_inv
                    )
                    
                    # 5. Node Depletion (Looting Law)
                    # For normal nodes, decrement charges. 
                    # For 'LOOT' nodes, they are typically one-shot or ground-items.
                    charges_delta = -1
                    is_loot = node.kind == "LOOT"
                    if is_loot:
                        # Looting a ground item consumes all charges immediately
                        charges_delta = -node.remaining_charges
                    
                    node_upd = refined_node_updates.get(node.id, ResourceNodeUpdate(node_id=node.id))
                    refined_node_updates[node.id] = replace(
                        node_upd,
                        charges_delta=node_upd.charges_delta + charges_delta,
                        cooldown_set=node.respawn_cooldown if (not is_loot and node.remaining_charges + charges_delta <= 0) else None
                    )
                else:
                    # Just middle-of-channeling progress
                    # (Refined update is same as proposed)
                    pass

        return replace(
            update,
            entity_updates=refined_entity_updates,
            node_updates=refined_node_updates
        )
