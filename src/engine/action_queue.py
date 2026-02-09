"""Thread-safe action queue connecting workers to the WorldLoop."""

from __future__ import annotations

import queue
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from src.actions.base import ActionProposal


class ActionQueue:
    """MPSC (multiple-producer, single-consumer) queue for ActionProposals.

    Workers push proposals; the WorldLoop drains them each tick.
    """

    __slots__ = ("_queue",)

    def __init__(self) -> None:
        self._queue: queue.Queue[ActionProposal] = queue.Queue()

    def push(self, proposal: ActionProposal) -> None:
        """Thread-safe enqueue."""
        self._queue.put_nowait(proposal)

    def drain(self) -> list[ActionProposal]:
        """Drain all pending proposals (called by WorldLoop on the main thread)."""
        proposals: list[ActionProposal] = []
        while True:
            try:
                proposals.append(self._queue.get_nowait())
            except queue.Empty:
                break
        return proposals

    @property
    def empty(self) -> bool:
        return self._queue.empty()
