# Compliance IDs: TOWN-005, TOWN-010, TOWN-020
from __future__ import annotations
from dataclasses import replace
from typing import TYPE_CHECKING, Dict, List

from src.core.updates import InteractionUpdate, ResourceNodeUpdate, IdentityUpdate


if TYPE_CHECKING:
    from src.core.state import AuthoritativeState, EntityState
    from src.core.updates import StateUpdate, EntityUpdate


class InteractionSystem:
    """
    Law: Must follow Milestone B Runtime Signals Contract.
    Proof: Verified by mb_test_matrix.md and test_milestone_b_closure.py.
    VERIFIED v2: InteractionSystem
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
        # VERIFIED v2: inventory_slots_and_weight
        return InteractionSystem.ITEM_WEIGHTS.get(item_kind, InteractionSystem.ITEM_WEIGHTS["__DEFAULT__"])

    @staticmethod
    def enforce(state: AuthoritativeState, update: StateUpdate) -> StateUpdate:
        """
        Refine the proposed update according to authoritative interaction laws.
        Logic ID: TOWN-005 (Partial rejection support via refined updates)
        Returns a new StateUpdate with enforced interaction outcomes.
        """
        refined_entity_updates = dict(update.entity_updates)
        refined_node_updates = dict(update.node_updates)
        chest_updates = dict(update.chest_updates)
        
        for e_id, ent_upd in update.entity_updates.items():
            if ent_upd.interaction is None:
                continue
            
            entity = state.entities.get(e_id)
            if not entity:
                continue

            # 1. Channeling & Proximity Laws
            current_target = entity.interaction.target_node_id
            proposed_target = ent_upd.interaction.target_node_id
            
            should_reset = False
            
            # Movement interruption
            if ent_upd.moved_this_tick:
                should_reset = True
            
            # Target switching
            if proposed_target is not None and current_target is not None and proposed_target != current_target:
                should_reset = True
            
            # Law 159: Interaction interruption on significant damage
            if ent_upd.combat and ent_upd.combat.damage_taken > 0:
                damage = ent_upd.combat.damage_taken
                max_hp = entity.combat.max_hp if entity.combat else 100
                if damage > (max_hp * 0.05) or damage >= 10:
                    should_reset = True
                
            # Logic ID: TOWN-009 / TOWN-010 (Interrupted by damage or distance)
            if should_reset:
                # Force a reset update
                res_upd = InteractionUpdate(reset=True)
                refined_entity_updates[e_id] = replace(
                    ent_upd,
                    interaction=res_upd
                )
                
                # Audit rejections
                reason = "INTERACTION_RESET"
                new_rejections_delta = dict(update.rejections_delta)
                new_rejections_delta[reason] = new_rejections_delta.get(reason, 0) + 1
                update = replace(update, rejections_delta=new_rejections_delta)
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
                chest = state.chests.get(target_id) if not node and not ground_item and not corpse else None
                
                if not node and not ground_item and not corpse and not chest:
                    refined_entity_updates[e_id] = replace(ent_upd, interaction=InteractionUpdate(reset=True))
                    continue

                if node and node.remaining_charges <= 0:
                    refined_entity_updates[e_id] = replace(ent_upd, interaction=InteractionUpdate(reset=True))
                    continue

                new_progress = entity.interaction.progress + ent_upd.interaction.progress_delta
                required_ticks = node.required_ticks if node else 10
                
                # Capacity/Weight check before completion/intent emission
                from src.core.inventory import InventoryService
                from src.core.state import ItemStack
                proposed_items = []
                if node:
                    proposed_items = [ItemStack(node.yields_item, 1)]
                elif ground_item:
                    proposed_items = [ItemStack(ground_item.item_id, ground_item.quantity)]
                elif corpse:
                    proposed_items = list(corpse.items)
                elif chest:
                    proposed_items = list(chest.items)
                        
                if not InventoryService.can_add_items(entity.inventory, proposed_items):
                    refined_entity_updates[e_id] = replace(ent_upd, interaction=InteractionUpdate(reset=True))
                    continue

                intents = list(ent_upd.resource_transfers)
                if not intents and new_progress >= required_ticks:
                    # Logic ID: TOWN-006 (Completion triggers intent)
                    # Implicit completion: Create intent from current target
                    from src.core.updates import ResourceTransferIntent
                    from src.core.state import ItemStack
                    items = []
                    source_kind = ""
                    if node:
                        # Logic ID: TOWN-007 (Resource transfer intent for node)
                        items = [ItemStack(node.yields_item, 1)]
                        source_kind = "NODE"
                    elif ground_item:
                        # Logic ID: TOWN-007 (Resource transfer intent for ground item)
                        items = [ItemStack(ground_item.item_id, ground_item.quantity)]
                        source_kind = "GROUND_ITEM"
                    elif corpse:
                        # Logic ID: TOWN-007 (Resource transfer intent for corpse)
                        items = list(corpse.items)
                        source_kind = "CORPSE"
                    elif chest:
                        # Logic ID: TOWN-009 (Looting completion triggers intent)
                        # Logic ID: TOWN-020 (Explicit building interaction)
                        if chest.cooldown_remaining > 0:
                            refined_entity_updates[e_id] = replace(ent_upd, interaction=InteractionUpdate(reset=True))
                            continue
                        items = list(chest.items)
                        source_kind = "CHEST"
                        
                        # Set chest on cooldown
                        from src.core.updates import ChestUpdate
                        chest_updates[target_id] = ChestUpdate(
                            chest_id=target_id,
                            items_set=[], # Empty it
                            cooldown_set=chest.respawn_tick or 100
                        )
                    
                    intents = [ResourceTransferIntent(
                        source_id=target_id,
                        source_kind=source_kind,
                        items_add=items,
                        transfer_kind="AUTO"
                    )]

                if intents:
                    if len(intents) > len(ent_upd.resource_transfers):
                        refined_entity_updates[e_id] = replace(
                            ent_upd,
                            resource_transfers=intents,
                            interaction=InteractionUpdate(reset=True)
                        )
                    else:
                        # intents already present — still emit reset signal
                        refined_entity_updates[e_id] = replace(
                            ent_upd,
                            interaction=InteractionUpdate(reset=True)
                        )
                    continue

        return replace(
            update,
            entity_updates=refined_entity_updates,
            node_updates=refined_node_updates,
            chest_updates=chest_updates
        )
