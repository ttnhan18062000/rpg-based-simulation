# src/engine/quests.py
from __future__ import annotations
from typing import TYPE_CHECKING, List, Dict, Optional, Any
from dataclasses import replace

from src_legacy.core.quests import QuestState, QuestKind, QuestStatus
from src_legacy.core.updates import QuestUpdate

if TYPE_CHECKING:
    from src_legacy.core.state import AuthoritativeState, EntityState
    from src_legacy.core.updates import StateUpdate

class QuestResolutionSystem:
    """
    Authoritative logic for quest progression and completion.
    Emits QuestUpdates that are processed by ApplyPath.
    """
    @staticmethod
    def evaluate_state_updates(state: AuthoritativeState, update: StateUpdate) -> StateUpdate:
        """
        Produce QuestUpdates based on current world state (exploration).
        """
        from src_legacy.core.updates import EntityUpdate
        refined_entity_updates = dict(update.entity_updates)
        
        for e_id, entity in state.entities.items():
            if not entity.active: continue
            
            quest_updates = QuestResolutionSystem.evaluate_explore(state, entity)
            if quest_updates:
                ent_upd = refined_entity_updates.get(e_id, EntityUpdate(entity_id=e_id))
                # For now, we take the first quest update if multiple exist
                # In a more robust system, we would merge them
                refined_entity_updates[e_id] = replace(ent_upd, quest=quest_updates[0])
                
        return replace(update, entity_updates=refined_entity_updates)


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
                    progress_delta=1.0
                ))
                
        return updates
