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
        for q_id, project in entity.strategic.projects.items():
            if not isinstance(project, QuestState):
                continue
                
            if project.quest_status != QuestStatus.ACTIVE:
                continue
                
            if project.quest_kind != QuestKind.EXPLORE:
                continue
                
            target_pos = project.metadata.get("target_pos")
            if target_pos:
                dist = abs(entity.position[0] - target_pos[0]) + abs(entity.position[1] - target_pos[1])
                
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
        
        for q_id, project in attacker.strategic.projects.items():
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
        
        for e_id, ent_upd in update.entity_updates.items():
            if not ent_upd.quest:
                continue
                
            entity = state.entities.get(e_id)
            if not entity: continue
            
            q_id = ent_upd.quest.quest_id
            project = entity.strategic.projects.get(q_id)
            if not project or not isinstance(project, QuestState):
                continue
                
            # Simulate what the new state will be
            updated_quest = QuestService.add_progress(project, ent_upd.quest.progress_delta)
            if ent_upd.quest.status_set is not None:
                updated_quest = replace(updated_quest, quest_status=ent_upd.quest.status_set)
                
            # If transition to COMPLETED is happening, emit reward intent
            if updated_quest.quest_status == QuestStatus.COMPLETED and project.quest_status == QuestStatus.ACTIVE:
                from src.core.state import ItemStack
                items = [ItemStack(item_id=tid, quantity=1) for tid in updated_quest.reward.items]
                
                intent = ResourceTransferIntent(
                    source_id=q_id,
                    source_kind="QUEST",
                    items_add=items,
                    gold_delta=updated_quest.reward.gold,
                    xp_reward=updated_quest.reward.xp,
                    transfer_kind="QUEST_REWARD"
                )
                
                # Merge into entity update
                refined_entity_updates[e_id] = replace(ent_upd, 
                    resource_transfers=ent_upd.resource_transfers + [intent],
                    quest=replace(ent_upd.quest, status_set=QuestStatus.REWARDED)
                )
                
        return replace(update, entity_updates=refined_entity_updates)
