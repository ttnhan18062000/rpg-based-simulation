"""Base action proposal — the universal currency between AI and World."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from src.core.enums import ActionType


@dataclass(frozen=True, slots=True)
class ActionProposal:
    """An intent produced by a worker thread.

    The WorldLoop validates and applies (or rejects) each proposal.
    """

    actor_id: int
    verb: ActionType
    target: Any = None
    reason: str = ""
    new_ai_state: int | None = None

    def __repr__(self) -> str:
        return f"Proposal(entity={self.actor_id}, {self.verb.name}, target={self.target}, reason={self.reason!r})"
