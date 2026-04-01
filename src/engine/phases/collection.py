from __future__ import annotations
import logging
from typing import TYPE_CHECKING
from src.engine.phases.base import EnginePhase
from src.actions.base import ActionProposal
from src.core.models.enums import ActionType
from src.core.models.snapshot import Snapshot
from src.engine.phase_guard import ActionProposalGuard

if TYPE_CHECKING:
    from src.engine.phases.context import EngineContext

logger = logging.getLogger(__name__)

class CollectionPhase(EnginePhase):
    """Wait and collect action proposals from identifying workers."""
    
    def execute(self, ctx: EngineContext) -> None:
        if not ctx.tick_ready_entities:
            ctx.tick_proposals = []
            return

        # Snapshot for AI decisions
        snapshot = Snapshot.from_world(ctx.world)
        
        # Dispatch to workers with Phase Boundary Protection
        with ActionProposalGuard(snapshot):
            ctx.worker_pool.dispatch(ctx.tick_ready_entities, snapshot, ctx.action_queue)
            proposals = ctx.action_queue.drain()

        # Chaos Resilience (Identify and handle worker timeouts/dropouts)
        if len(proposals) < len(ctx.tick_ready_entities):
            acted_ids = {p.actor_id for p in proposals}
            for entity in ctx.tick_ready_entities:
                if entity.id not in acted_ids:
                    from src.utils.metrics import SIM_INVALID_ACTIONS_TOTAL
                    SIM_INVALID_ACTIONS_TOTAL.labels(action_type="rest", reason="timeout").inc()
                    
                    proposals.append(ActionProposal(
                        actor_id=entity.id,
                        verb=ActionType.REST,
                        target=None,
                        reason="Chaos Drop / Worker Timeout",
                        new_ai_state=int(entity.mind.decision.ai_state)
                    ))
        
        ctx.tick_proposals = proposals
