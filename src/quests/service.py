from __future__ import annotations
from dataclasses import replace
from src.core.quests import QuestState, QuestStatus

class QuestService:
    """
    Business logic for quest lifecycle management.
    Handles non-mutating calculations and state transitions.
    """
    
    @staticmethod
    def add_progress(quest: QuestState, delta: float) -> QuestState:
        """
        Produce a new QuestState with updated progress.
        Handles auto-completion if goal is met.
        """
        if quest.quest_status != QuestStatus.ACTIVE:
            # Cannot progress completed or rewarded quests
            return quest
            
        new_value = quest.current_value + delta
        new_status = quest.quest_status
        
        # Auto-complete check
        if new_value >= quest.goal_value:
            new_status = QuestStatus.COMPLETED
            
        return replace(
            quest,
            current_value=new_value,
            quest_status=new_status
        )

    @staticmethod
    def mark_rewarded(quest: QuestState) -> QuestState:
        """
        Transition a quest to REWARDED status.
        Ensures rewards can only be granted once.
        """
        if quest.quest_status not in (QuestStatus.COMPLETED, QuestStatus.REWARD_PENDING):
            # Only completed or pending quests can be rewarded
            return quest
            
        return replace(
            quest,
            quest_status=QuestStatus.REWARDED
        )
