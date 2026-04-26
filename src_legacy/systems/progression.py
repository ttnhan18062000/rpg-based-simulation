from __future__ import annotations
from dataclasses import replace
from typing import Dict, List, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from src_legacy.core.state import AuthoritativeState, EntityState
    from src_legacy.core.updates import StateUpdate, EntityUpdate

class ProgressionSystem:
    """
    Authoritative logic for XP resolution, leveling, and attribute growth.
    Law: Rewards must flow through authoritative apply paths.
    """

    @staticmethod
    def resolve_rewards(state: AuthoritativeState, update: StateUpdate) -> StateUpdate:
        """
        Phase 8: Process RewardUpdates into concrete Identity and Inventory updates.
        """
        from src_legacy.core.updates import IdentityUpdate, InventoryUpdate
        
        refined_entity_updates = dict(update.entity_updates)
        
        for e_id, ent_upd in update.entity_updates.items():
            if not ent_upd.reward:
                continue
                
            reward = ent_upd.reward
            entity = state.entities.get(e_id)
            if not entity:
                continue
                
            # 1. Convert XP to Evolution Points
            identity_up = ent_upd.identity or IdentityUpdate()
            identity_up = replace(identity_up,
                evolution_points_delta=identity_up.evolution_points_delta + reward.xp_gain
            )
            
            # 2. Convert Gold to Inventory Update
            inventory_up = ent_upd.inventory or InventoryUpdate()
            inventory_up = replace(inventory_up,
                gold_delta=inventory_up.gold_delta + reward.gold_gain
            )
            
            # 3. Handle Items Gain (if any)
            if reward.items_gain:
                from src_legacy.core.state import ItemStack
                items_to_add = [ItemStack(item_id=iid, quantity=1) for iid in reward.items_gain]
                inventory_up = replace(inventory_up,
                    items_add=inventory_up.items_add + items_to_add
                )
            
            # Update the EntityUpdate
            refined_entity_updates[e_id] = replace(ent_upd,
                identity=identity_up,
                inventory=inventory_up,
                reward=None # Clear reward once processed
            )
            
        return replace(update, entity_updates=refined_entity_updates)

    @staticmethod
    def evaluate_level_up(entity: EntityState, points_gained: int) -> Optional[IdentityUpdate]:
        """
        Check if the entity reached a new evolution level.
        Threshold: 100 * current_level
        """
        current_points = entity.identity.evolution_points + points_gained
        current_level = entity.identity.evolution_level
        
        threshold = 100 * current_level
        
        if current_points >= threshold:
            # Level up!
            from src_legacy.core.updates import IdentityUpdate
            return IdentityUpdate(
                evolution_level_set=current_level + 1,
                evolution_points_delta=-threshold, # Consume points for level up
                unspent_ap_delta=5 # Grant attribute points
            )
        return None

    @staticmethod
    def process_progression(state: AuthoritativeState, update: StateUpdate) -> StateUpdate:
        """
        Check for level-ups and apply auto-investment for entities that gained points.
        """
        refined_entity_updates = dict(update.entity_updates)
        
        for e_id, ent_upd in update.entity_updates.items():
            if not ent_upd.identity or ent_upd.identity.evolution_points_delta <= 0:
                continue
                
            entity = state.entities.get(e_id)
            if not entity:
                continue
                
            # Check Level Up
            lvl_up = ProgressionSystem.evaluate_level_up(entity, ent_upd.identity.evolution_points_delta)
            if lvl_up:
                # Merge into current identity update
                new_identity = replace(ent_upd.identity,
                    evolution_level_set=lvl_up.evolution_level_set,
                    evolution_points_delta=ent_upd.identity.evolution_points_delta + lvl_up.evolution_points_delta,
                    unspent_ap_delta=ent_upd.identity.unspent_ap_delta + lvl_up.unspent_ap_delta
                )
                
                # Auto-invest AP
                attr_up = ProgressionSystem.auto_invest_attributes(entity, new_identity.unspent_ap_delta)
                if attr_up:
                    # Grant attributes and consume AP
                    new_identity = replace(new_identity, unspent_ap_delta=0)
                    
                    refined_entity_updates[e_id] = replace(ent_upd,
                        identity=new_identity,
                        attributes=attr_up
                    )
                else:
                    refined_entity_updates[e_id] = replace(ent_upd, identity=new_identity)
                    
        return replace(update, entity_updates=refined_entity_updates)

    @staticmethod
    def auto_invest_attributes(entity: EntityState, unspent_ap: int) -> Optional[AttributeUpdate]:
        """
        Basic AI logic to invest unspent AP into attributes based on role.
        """
        from src_legacy.core.updates import AttributeUpdate
        if unspent_ap <= 0:
            return None
            
        # Role-based investment
        role = entity.identity.role
        if role == 0: # HERO
            return AttributeUpdate(strength_delta=2, vitality_delta=2, agility_delta=1)
        elif role == 1: # SHOPKEEPER
            return AttributeUpdate(wisdom_delta=2, charisma_delta=3)
        elif role == 2: # MONSTER
            return AttributeUpdate(strength_delta=3, vitality_delta=2)
        else: # CITIZEN
            return AttributeUpdate(endurance_delta=5)
            
        return None
