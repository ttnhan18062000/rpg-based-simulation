from __future__ import annotations

from typing import TYPE_CHECKING

from src.engine.economy import ResourceTransactionSystem

if TYPE_CHECKING:
    from src.core.state import AuthoritativeState
    from src.core.updates import StateUpdate


class ResourceTransactionPhase:
    """
    Resolves ResourceTransferIntent objects into inventory, identity, node,
    corpse, chest, or rejection updates.
    """

    @staticmethod
    def resolve(state: AuthoritativeState, update: StateUpdate) -> StateUpdate:
        """
        Resolve all resource transactions.
        """
        return ResourceTransactionSystem.resolve_all(state, update)
