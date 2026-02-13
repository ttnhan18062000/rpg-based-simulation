"""Parallel worker pool for AI decision-making."""

from __future__ import annotations

import logging
from concurrent.futures import Future, ThreadPoolExecutor, as_completed
from typing import TYPE_CHECKING

from src.core.enums import AIState

if TYPE_CHECKING:
    from src.actions.base import ActionProposal
    from src.ai.brain import AIBrain
    from src.config import SimulationConfig
    from src.core.models import Entity
    from src.core.snapshot import Snapshot
    from src.engine.action_queue import ActionQueue

logger = logging.getLogger(__name__)


class WorkerPool:
    """Manages a ThreadPoolExecutor that runs AI decisions in parallel.

    Workers receive an immutable Snapshot and push ActionProposals
    into the shared ActionQueue.
    """

    __slots__ = ("_config", "_brain", "_executor")

    def __init__(self, config: SimulationConfig, brain: AIBrain) -> None:
        self._config = config
        self._brain = brain
        self._executor = ThreadPoolExecutor(
            max_workers=config.num_workers,
            thread_name_prefix="ai-worker",
        )

    def dispatch(
        self,
        entities: list[Entity],
        snapshot: Snapshot,
        action_queue: ActionQueue,
    ) -> None:
        """Submit AI tasks for all *entities* and collect results into *action_queue*.

        Blocks until all workers finish or timeout.
        Uses inline execution when num_workers == 1 to avoid threading overhead.
        """
        if not entities:
            return

        # Fast path: single-worker mode — run inline, no thread overhead
        if self._config.num_workers <= 1:
            for entity in entities:
                try:
                    _eid, new_state, proposal = self._think(entity, snapshot)
                    action_queue.push(proposal)
                except Exception:
                    logger.exception("AI failed for entity %d — skipping turn", entity.id)
            return

        futures: dict[Future[tuple[int, AIState, ActionProposal]], int] = {}
        for entity in entities:
            future = self._executor.submit(self._think, entity, snapshot)
            futures[future] = entity.id

        timeout = self._config.worker_timeout_seconds
        for future in as_completed(futures, timeout=timeout):
            entity_id = futures[future]
            try:
                eid, new_state, proposal = future.result()
                action_queue.push(proposal)
            except Exception:
                logger.exception("Worker failed for entity %d — skipping turn", entity_id)

    def _think(self, entity: Entity, snapshot: Snapshot) -> tuple[int, AIState, ActionProposal]:
        """Run AI for a single entity (executed in a worker thread)."""
        from dataclasses import replace

        new_state, proposal = self._brain.decide(entity, snapshot)
        proposal = replace(proposal, new_ai_state=int(new_state))
        return entity.id, new_state, proposal

    def shutdown(self) -> None:
        self._executor.shutdown(wait=False, cancel_futures=True)
