# src/engine/quests.py
from __future__ import annotations
from typing import TYPE_CHECKING, List, Dict, Optional

from src.core.quests import QuestState, QuestKind, QuestStatus
from src.core.updates import QuestUpdate

if TYPE_CHECKING:
    from src.core.state import AuthoritativeState, EntityState

class QuestResolutionSystem:
    """
    Authoritative logic for quest progression and completion.
    Emits QuestUpdates that are processed by ApplyPath.
    """

    @staticmethod
    def evaluate_explore(state: AuthoritativeState, entity: EntityState) -> List[QuestUpdate]:
        """Check EXPLORE quests for proximity to target."""
        updates = []
        
        # In V2, active quests are stored as ProjectState inside entity.strategic.projects
        for q_id in sorted(entity.strategic.projects.keys()):
            project = entity.strategic.projects[q_id]
            if not isinstance(project, QuestState):
                continue
                
            if project.quest_status != QuestStatus.ACTIVE:
                continue
                
            if project.quest_kind != QuestKind.EXPLORE:
                continue
                
            target_pos = project.metadata.get("target_pos")
            if target_pos:
                dist = abs(entity.navigation.position[0] - target_pos[0]) + abs(entity.navigation.position[1] - target_pos[1])
                
                # If within 2 manhattan distance, quest completes
                if dist <= 2.0:
                    # Setting progress_delta to goal_value ensures it finishes
                    delta = max(0.0, project.goal_value - project.current_value)
                    updates.append(QuestUpdate(
                        quest_id=q_id,
                        progress_delta=delta
                    ))
                    
        return updates

    @staticmethod
    def evaluate_combat_victory(
        attacker: EntityState, 
        victim_kind: str
    ) -> List[QuestUpdate]:
        """Advance HUNT quests when an enemy is defeated."""
        updates = []
        
        # Phase 9 Fix: Sort projects by ID for deterministic progress evaluation
        for q_id, project in sorted(attacker.strategic.projects.items()):
            if not isinstance(project, QuestState):
                continue
                
            if project.quest_status != QuestStatus.ACTIVE:
                continue
                
            if project.quest_kind != QuestKind.HUNT:
                continue
                
            target_kind = project.metadata.get("target_kind")
            if target_kind == victim_kind:
                updates.append(QuestUpdate(
                    quest_id=q_id,
                    progress_delta=1.0 # Standard kill progress
                ))
                
        return updates

    @staticmethod
    def enforce(state: AuthoritativeState, update: StateUpdate) -> StateUpdate:
        """
        Enforces quest completion rules and emits authoritative reward intents.
        Ensures that quest rewards are capacity-aware.
        """
        from src.core.updates import ResourceTransferIntent, EntityUpdate
        from dataclasses import replace
        from src.core.quests import QuestStatus
        from src.quests.service import QuestService
        
        refined_entity_updates = dict(update.entity_updates)
        
        # Phase 9 Fix: Sort by entity ID for deterministic reward intent emission
        for e_id in sorted(list(update.entity_updates.keys())):
            ent_upd = update.entity_updates[e_id]
            if not ent_upd.quest:
                continue
                
            entity = state.entities.get(e_id)
            if not entity: continue
            
            q_updates = ent_upd.quest.multi_updates if ent_upd.quest.multi_updates else [ent_upd.quest]
            
            current_quest_updates = []
            current_resource_transfers = list(ent_upd.resource_transfers)
            
            for qu in q_updates:
                q_id = qu.quest_id
                project = entity.strategic.projects.get(q_id)
                if not project or not isinstance(project, QuestState):
                    current_quest_updates.append(qu)
                    continue
                    
                # Simulate what the new state will be
                updated_quest = QuestService.add_progress(project, qu.progress_delta)
                if qu.status_set is not None:
                    updated_quest = replace(updated_quest, quest_status=qu.status_set)
                    
                # 1. If transition to COMPLETED is happening OR quest is already REWARD_PENDING
                # we emit an authoritative reward intent.
                is_newly_completed = (updated_quest.quest_status == QuestStatus.COMPLETED and project.quest_status == QuestStatus.ACTIVE)
                is_retry_pending = (project.quest_status == QuestStatus.REWARD_PENDING)
                
                if is_newly_completed or is_retry_pending:
                    from src.core.state import ItemStack
                    items = [ItemStack(item_id=tid, quantity=1) for tid in updated_quest.reward.items]
                    
                    from src.core.updates import RewardUpdate
                    reward_intent = ResourceTransferIntent(
                        source_id=q_id,
                        source_kind="QUEST",
                        items_add=items,
                        gold_delta=updated_quest.reward.gold,
                        reward_upd=RewardUpdate(xp_gain=updated_quest.reward.xp),
                        transfer_kind="QUEST_REWARD",
                        transaction_id=f"quest:{q_id}:reward",
                        group_id=f"quest:{q_id}:reward",
                        is_group_required=True
                    )
                    
                    # Transition to REWARD_PENDING (if not already)
                    current_resource_transfers.append(reward_intent)
                    current_quest_updates.append(replace(qu, status_set=QuestStatus.REWARD_PENDING))
                else:
                    current_quest_updates.append(qu)

            # Reconstruct the merged quest update if we have multiple
            new_q_upd = current_quest_updates[0]
            for i in range(1, len(current_quest_updates)):
                new_q_upd = new_q_upd.merge(current_quest_updates[i])
                
            refined_entity_updates[e_id] = replace(ent_upd, 
                resource_transfers=current_resource_transfers,
                quest=new_q_upd
            )
                
        return replace(update, entity_updates=refined_entity_updates)
