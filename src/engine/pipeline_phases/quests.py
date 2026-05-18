from __future__ import annotations

from typing import TYPE_CHECKING

from src.engine.quests import QuestResolutionSystem

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
        return QuestResolutionSystem.enforce(state, update)
