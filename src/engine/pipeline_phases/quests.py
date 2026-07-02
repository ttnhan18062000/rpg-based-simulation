from __future__ import annotations

from typing import TYPE_CHECKING

from src.engine.quests import QuestResolutionSystem
from src.engine.pipeline_phases.quest_opportunity_rewards import QuestOpportunityRewardSystem

if TYPE_CHECKING:
    from src.core.state import AuthoritativeState
    from src.core.updates import StateUpdate


class QuestRewardPhase:
    """
    Converts quest completion/retry state into authoritative reward intents.

    Does not directly mutate inventory or XP.
    ResourceTransactionPhase decides final success.
    """

    @staticmethod
    def resolve(state: AuthoritativeState, update: StateUpdate) -> StateUpdate:
        """
        Enforce quest rewards.
        """
        update = QuestResolutionSystem.enforce(state, update)
        update = QuestOpportunityRewardSystem.enforce(state, update)
        return update
