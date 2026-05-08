from __future__ import annotations
from typing import TYPE_CHECKING, Dict, List, Optional
from dataclasses import replace

from src.core.conservation import ResourceTransactionResolver
from src.core.updates import EntityUpdate, StateUpdate, InventoryUpdate

if TYPE_CHECKING:
    from src.core.state import AuthoritativeState

class ResourceTransactionSystem:
    """
    Engine-level system for resolving batch resource transfers.
    Coordinates between the Core Conservation laws and the Authoritative State.
    """

    @staticmethod
    def resolve_all(state: AuthoritativeState, update: StateUpdate) -> StateUpdate:
        """
        Processes all ResourceTransferIntents for all entities in the update.
        VERIFIED v2: resource_transaction_resolution
        """
        refined_entity_updates = dict(update.entity_updates)
        new_node_updates = dict(update.node_updates)
        new_chest_updates = dict(update.chest_updates)
        new_building_updates = dict(update.building_updates)
        new_ground_items_remove = list(update.ground_items_remove)
        new_corpses_remove = list(update.corpses_remove)
        processed_ids = set(update.processed_transaction_ids)
        from src.core.state import IntentResult

        # In-tick reservations to prevent double-spending/double-harvesting
        # Format: (kind, id) -> quantity_consumed
        reservations = {}

        # Phase E5.8 Fix: Deterministic resolution order (by ID)
        for e_id in sorted(list(state.entities.keys())):
            entity = state.entities[e_id]
            ent_upd = refined_entity_updates.get(e_id)
            if not ent_upd or not ent_upd.resource_transfers:
                continue

            current_inventory = entity.inventory
            # If there was a sliding inventory update already (e.g. from previous intent)
            if ent_upd.inventory:
                from src.core.inventory import InventoryService
                current_inventory = InventoryService.apply_update(entity.inventory, ent_upd.inventory)

            # Phase 8: Transaction Grouping (LEG-RPG-1697)
            # Group intents by group_id. Independent intents get a unique group.
            groups: Dict[Optional[str], List[ResourceTransferIntent]] = {}
            group_order: List[Optional[str]] = []
            
            for intent in ent_upd.resource_transfers:
                gid = intent.group_id
                if gid not in groups:
                    groups[gid] = []
                    group_order.append(gid)
                groups[gid].append(intent)

            accumulated_inv_upd = ent_upd.inventory
            final_accumulated_inv_upd = accumulated_inv_upd
            final_intent_results = list(ent_upd.intent_results)

            for gid in group_order:
                group_intents = groups[gid]
                
                # If gid is None, these are independent intents
                if gid is None:
                    for intent in group_intents:
                        result = ResourceTransactionResolver.resolve(
                            state, entity, intent,
                            inventory_override=current_inventory,
                            node_overrides=new_node_updates,
                            reservations=reservations
                        )
                        
                        if result.accepted:
                            # Apply success (sliding)
                            if result.inventory_update:
                                final_accumulated_inv_upd = result.inventory_update.merge(final_accumulated_inv_upd) if final_accumulated_inv_upd else result.inventory_update
                                from src.core.inventory import InventoryService
                                current_inventory = InventoryService.apply_update(current_inventory, result.inventory_update)
                            
                            # Merge ALL contingent updates (Phase 8: Atomic Consistency)
                            ent_upd = ResourceTransactionSystem._merge_contingent_updates(ent_upd, result)
                            
                            # World effects
                            ResourceTransactionSystem._apply_world_effects(result, new_node_updates, new_building_updates, new_ground_items_remove, new_corpses_remove, reservations)
                            
                            if intent.transaction_id:
                                processed_ids.add(intent.transaction_id)
                                
                            final_intent_results.append(IntentResult(
                                transaction_id=intent.transaction_id, accepted=True, reason=result.reason,
                                source_kind=intent.source_kind, source_id=intent.source_id
                            ))
                        else:
                            final_intent_results.append(IntentResult(
                                transaction_id=intent.transaction_id, accepted=False, reason=result.reason,
                                source_kind=intent.source_kind, source_id=intent.source_id
                            ))
                else:
                    # Grouped logic: Trial run
                    trial_results = []
                    all_accepted = True
                    trial_inventory = current_inventory
                    
                    for intent in group_intents:
                        res = ResourceTransactionResolver.resolve(
                            state, entity, intent,
                            inventory_override=trial_inventory,
                            node_overrides=new_node_updates,
                            reservations=reservations
                        )
                        trial_results.append((intent, res))
                        if not res.accepted:
                            all_accepted = False
                            break
                        
                        if res.inventory_update:
                            from src.core.inventory import InventoryService
                            trial_inventory = InventoryService.apply_update(trial_inventory, res.inventory_update)

                    if all_accepted:
                        # Commit all
                        for intent, res in trial_results:
                            if res.inventory_update:
                                final_accumulated_inv_upd = res.inventory_update.merge(final_accumulated_inv_upd) if final_accumulated_inv_upd else res.inventory_update
                                from src.core.inventory import InventoryService
                                current_inventory = InventoryService.apply_update(current_inventory, res.inventory_update)
                            
                            # Merge ALL contingent updates
                            ent_upd = ResourceTransactionSystem._merge_contingent_updates(ent_upd, res)
                            
                            ResourceTransactionSystem._apply_world_effects(res, new_node_updates, new_building_updates, new_ground_items_remove, new_corpses_remove, reservations)
                            
                            if intent.transaction_id:
                                processed_ids.add(intent.transaction_id)
                                
                            final_intent_results.append(IntentResult(
                                transaction_id=intent.transaction_id, accepted=True, reason=res.reason,
                                source_kind=intent.source_kind, source_id=intent.source_id
                            ))
                    else:
                        # Rollback all (Reject all with GROUP_ROLLBACK or original reason)
                        from src.core.enums import ReasonCode
                        for intent in group_intents:
                            # Find if this specific intent failed or was just rolled back
                            fail_res = next((r for i, r in trial_results if i == intent), None)
                            # If this was the one that failed, keep its reason. Otherwise, it's a group rollback.
                            reason = fail_res.reason if (fail_res and not fail_res.accepted) else ReasonCode.GROUP_ROLLBACK
                            
                            final_intent_results.append(IntentResult(
                                transaction_id=intent.transaction_id, accepted=False, reason=reason,
                                source_kind=intent.source_kind, source_id=intent.source_id
                            ))

            # Update the refined update for this entity
            refined_entity_updates[e_id] = replace(ent_upd, 
                inventory=final_accumulated_inv_upd,
                intent_results=final_intent_results,
                resource_transfers=[] # Clear intents after resolution
            )
        return replace(update,
            entity_updates=refined_entity_updates,
            node_updates=new_node_updates,
            building_updates=new_building_updates,
            ground_items_remove=new_ground_items_remove,
            corpses_remove=new_corpses_remove,
            processed_transaction_ids=processed_ids
        )

    @staticmethod
    def _merge_contingent_updates(ent_upd, res):
        """Helper to merge all contingent updates from a transaction result into an entity update."""
        if res.identity_update:
            ent_upd = replace(ent_upd, identity=ent_upd.identity.merge(res.identity_update) if ent_upd.identity else res.identity_update)
        if res.biological_update:
            ent_upd = replace(ent_upd, biological=ent_upd.biological.merge(res.biological_update) if ent_upd.biological else res.biological_update)
        if res.attributes_update:
            ent_upd = replace(ent_upd, attributes=ent_upd.attributes.merge(res.attributes_update) if ent_upd.attributes else res.attributes_update)
        if res.combat_update:
            ent_upd = replace(ent_upd, combat=ent_upd.combat.merge(res.combat_update) if ent_upd.combat else res.combat_update)
        if res.strategic_update:
            ent_upd = replace(ent_upd, strategic=ent_upd.strategic.merge(res.strategic_update) if ent_upd.strategic else res.strategic_update)
        if res.equipment_update:
            ent_upd = replace(ent_upd, equipment=ent_upd.equipment.merge(res.equipment_update) if ent_upd.equipment else res.equipment_update) 
        if res.reward_update:
            ent_upd = replace(ent_upd, reward=ent_upd.reward.merge(res.reward_update) if ent_upd.reward else res.reward_update)
        return ent_upd

    @staticmethod
    def _apply_world_effects(result, nodes, buildings, ground_rem, corpses_rem, reservations):
        """Helper to apply world side effects from a successful resolution."""
        if result.node_update:
            node_id = result.node_update.node_id
            existing = nodes.get(node_id)
            if existing:
                nodes[node_id] = replace(existing, charges_delta=existing.charges_delta + result.node_update.charges_delta)
            else:
                nodes[node_id] = result.node_update
            reservations[("NODE", node_id)] = reservations.get(("NODE", node_id), 0) + 1

        if result.building_update:
            b_id = result.building_update.building_id
            existing = buildings.get(b_id)
            if existing:
                new_inv = existing.inventory
                if result.building_update.inventory:
                    new_inv = new_inv.merge(result.building_update.inventory) if new_inv else result.building_update.inventory
                buildings[b_id] = replace(existing, inventory=new_inv)
            else:
                buildings[b_id] = result.building_update

        if result.ground_item_remove is not None:
            ground_rem.append(result.ground_item_remove)
            reservations[("GROUND_ITEM", result.ground_item_remove)] = 1
        
        if result.corpse_remove is not None:
            corpses_rem.append(result.corpse_remove)
            reservations[("CORPSE", result.corpse_remove)] = 1
