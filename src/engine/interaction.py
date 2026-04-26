from __future__ import annotations
from dataclasses import replace
from typing import TYPE_CHECKING, Dict, List

from src.core.updates import InteractionUpdate, InventoryUpdate, ResourceNodeUpdate, IdentityUpdate

if TYPE_CHECKING:
    from src.core.state import AuthoritativeState, EntityState
    from src.core.updates import StateUpdate, EntityUpdate


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
                
                # Identify interaction target kind
                node = state.resource_nodes.get(target_id)
                ground_item = state.ground_items.get(target_id) if not node else None
                corpse = state.corpses.get(target_id) if not node and not ground_item else None
                
                if not node and not ground_item and not corpse:
                    # Target gone: Reset
                    refined_entity_updates[e_id] = replace(ent_upd, interaction=InteractionUpdate(reset=True))
                    continue

                # 3. Resource Transfer & Pressure Law
                new_progress = entity.interaction.progress + ent_upd.interaction.progress_delta
                required_ticks = node.required_ticks if node else 10 # Default for ground/corpse
                
                intents = list(ent_upd.resource_transfers)
                if not intents and new_progress >= required_ticks:
                    # Implicit completion: Create intent from current target
                    from src.core.updates import ResourceTransferIntent
                    from src.core.state import ItemStack
                    items = []
                    source_kind = ""
                    if node:
                        items = [ItemStack(node.yields_item, 1)]
                        source_kind = "NODE"
                    elif ground_item:
                        items = [ItemStack(ground_item.item_id, ground_item.quantity)]
                        source_kind = "GROUND_ITEM"
                    elif corpse:
                        items = list(corpse.items)
                        source_kind = "CORPSE"
                    
                    intents = [ResourceTransferIntent(
                        source_id=target_id,
                        source_kind=source_kind,
                        items_add=items,
                        transfer_kind="AUTO"
                    )]

                if intents:
                    from src.core.conservation import ResourceTransactionResolver
                    from src.core.inventory import InventoryService
                    
                    # Compute pending inventory state (Entity State + proposed updates in this tick)
                    pending_inv = entity.inventory
                    if ent_upd.inventory:
                        pending_inv = InventoryService.apply_update(entity.inventory, ent_upd.inventory)
                    
                    # Process the first intent for now (simulating existing behavior but list-safe)
                    intent = intents[0]
                    result = ResourceTransactionResolver.resolve(state, entity, intent, inventory_override=pending_inv)
                    
                    if result.accepted:
                        # 4. Successful Handoff
                        existing_inv = ent_upd.inventory or InventoryUpdate()
                        new_inv = replace(existing_inv, 
                            items_add=list(existing_inv.items_add) + result.inventory_update.items_add,
                            items_remove=list(existing_inv.items_remove) + (result.inventory_update.items_remove if result.inventory_update else []),
                            gold_delta=existing_inv.gold_delta + (result.inventory_update.gold_delta if result.inventory_update else 0)
                        )
                        
                        existing_id = ent_upd.identity or IdentityUpdate()
                        new_id = replace(existing_id,
                            evolution_points_delta=existing_id.evolution_points_delta + (result.identity_update.evolution_points_delta if result.identity_update else 0)
                        )
                        
                        refined_entity_updates[e_id] = replace(
                            ent_upd,
                            interaction=InteractionUpdate(reset=True),
                            inventory=new_inv,
                            identity=new_id,
                            resource_transfers=[]
                        )
                        
                        # 5. Source Depletion
                        if result.node_update:
                            refined_node_updates[target_id] = result.node_update
                        elif result.ground_item_remove:
                            update = replace(update, ground_items_remove=list(update.ground_items_remove) + [target_id])
                        elif result.corpse_remove:
                            update = replace(update, corpses_remove=list(update.corpses_remove) + [target_id])
                    else:
                        # Pressure Failure: Reset
                        refined_entity_updates[e_id] = replace(ent_upd, 
                            interaction=InteractionUpdate(reset=True),
                            resource_transfers=[]
                        )
                        # STRIP any proposed source updates to ensure atomicity
                        if target_id in refined_node_updates:
                             del refined_node_updates[target_id]
                        # (Ground items and corpses are in lists in the 'update' object itself, 
                        # which we are replacing via 'replace(update, ...)')
                        continue
                else:
                    # Continue progress
                    pass

        return replace(
            update,
            entity_updates=refined_entity_updates,
            node_updates=refined_node_updates
        )
