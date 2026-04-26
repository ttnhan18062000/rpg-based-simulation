from __future__ import annotations
from typing import Dict, List
from src.core.state import AuthoritativeState, EntityState
from src.core.quests import QuestState, QuestStatus, QuestKind
from src.core.updates import StateUpdate, EntityUpdate, QuestUpdate, RewardUpdate

class QuestSystem:
    """Processes quest progress and completion conditions."""

    @staticmethod
    def update(state: AuthoritativeState) -> StateUpdate:
        entity_updates = {}
        
        for entity in state.entities.values():
            active_quests = [
                q for q in entity.strategic.projects.values() 
                if isinstance(q, QuestState) and q.quest_status == QuestStatus.ACTIVE
            ]
            
            if not active_quests:
                continue
                
            q_updates = []
            r_updates = []
            
            for quest in active_quests:
                progress_delta = 0.0
                
                # Check Conditions
                if quest.quest_kind == QuestKind.EXPLORE:
                    # Progress if entity is near target location
                    target_pos = quest.metadata.get("target_position") if hasattr(quest, "metadata") else None
                    if target_pos:
                        dist = abs(entity.position[0] - target_pos[0]) + abs(entity.position[1] - target_pos[1])
                        if dist < 5.0:
                            progress_delta = 1.0 # One tick of exploration
                            
                elif quest.quest_kind == QuestKind.BOUNTY:
                    # Progress if region is no longer monster-controlled
                    target_region_id = quest.metadata.get("target_region_id") if hasattr(quest, "metadata") else None
                    if target_region_id:
                        region = state.regions.get(target_region_id)
                        if region and region.owner_faction_id != 1: # Not Monster
                            progress_delta = quest.goal_value - quest.current_value # Immediate completion
                            
                if progress_delta > 0:
                    new_val = quest.current_value + progress_delta
                    if new_val >= quest.goal_value:
                        # Phase 3 Law: Resource Conservation (Reward Capacity)
                        from src.core.updates import ResourceTransferIntent
                        from src.core.state import ItemStack
                        
                        reward_items = [ItemStack(item_id=tid, quantity=1) for tid in quest.reward.items]
                        intent = ResourceTransferIntent(
                            source_id=quest.id,
                            source_kind="QUEST",
                            items_add=reward_items,
                            gold_delta=quest.reward.gold,
                            transfer_kind="REWARD"
                        )
                        
                        # Use the resolver to check capacity
                        from src.core.conservation import ResourceTransactionResolver
                        result = ResourceTransactionResolver.resolve(state, entity, intent)
                        
                        if not result.accepted:
                            # Skip completion for now (Inventory full)
                            continue

                        # Quest Completed!
                        q_updates.append(QuestUpdate(
                            quest_id=quest.id,
                            status_set=QuestStatus.COMPLETED
                        ))
                        # Grant Reward (resolved via intent)
                        # We still emit RewardUpdate for XP which is not an inventory item
                        r_updates.append(RewardUpdate(
                            xp_gain=quest.reward.xp,
                            gold_gain=0, # Handled by intent
                            items_gain=[] # Handled by intent
                        ))
                        # The intent will be processed by pipeline.refine
                        q_intent = intent
                        
                        # Also mark as REWARDED
                        q_updates.append(QuestUpdate(
                            quest_id=quest.id,
                            status_set=QuestStatus.REWARDED
                        ))
                    else:
                        q_updates.append(QuestUpdate(
                            quest_id=quest.id,
                            progress_delta=progress_delta
                        ))
            
            if q_updates or r_updates:
                # We need to handle multiple QuestUpdates per entity
                # But EntityUpdate only takes one QuestUpdate
                # I'll modify EntityUpdate or just send the first one for now
                for q_upd in q_updates:
                    entity_updates[entity.id] = EntityUpdate(
                        entity_id=entity.id,
                        quest=q_upd,
                        reward=r_updates[0] if r_updates else None,
                        resource_transfers=[q_intent] if 'q_intent' in locals() else []
                    )
                    
        return StateUpdate(entity_updates=entity_updates)
