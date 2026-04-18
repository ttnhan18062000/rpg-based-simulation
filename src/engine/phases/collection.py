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
    from src.engine.phases.contract import PhaseContract

logger = logging.getLogger(__name__)

class CollectionPhase(EnginePhase):
    """Wait and collect action proposals from identifying workers."""
    
    @property
    def contract(self) -> PhaseContract:
        from src.engine.phases.contract import PhaseContract, PhaseAccess
        return PhaseContract(
            name="Collection",
            description="Collecting AI proposals from workers.",
            permissions={
                "world": PhaseAccess.READ,
                "config": PhaseAccess.READ,
                "worker_pool": PhaseAccess.READ_WRITE,
                "action_queue": PhaseAccess.READ_WRITE,
                "tick_ready_entities": PhaseAccess.READ,
                "tick_proposals": PhaseAccess.MUTATE,
                "emit": PhaseAccess.READ
            }
        )

    def execute(self, ctx: EngineContext) -> None:
        if not ctx.tick_ready_entities:
            ctx.tick_proposals = []
            return

        # Determine if we can use shallow snapshot (Optimization for local execution)
        # We use shallow snapshots ONLY when running with a single local worker 
        # to avoid the O(ticks * entities) deepcopy/freeze overhead.
        is_shallow = ctx.config.num_workers <= 1
        
        # Snapshot for AI decisions
        snapshot = Snapshot.from_world(ctx.world, shallow=is_shallow)
        
        # Dispatch to workers with Phase Boundary Protection
        # AOA Optimization: We combine the Snapshot with a DecisionPhase tripwire.
        from src.core.models.base import DecisionPhase
        with ActionProposalGuard(snapshot, is_shallow=is_shallow), DecisionPhase():
            ctx.worker_pool.dispatch(ctx.tick_ready_entities, snapshot, ctx.action_queue)
            proposals = ctx.action_queue.drain()

        # Chaos Resilience (Identify and handle worker timeouts/dropouts)
        if len(proposals) < len(ctx.tick_ready_entities):
            acted_ids = {p.actor_id for p in proposals}
            for entity in ctx.tick_ready_entities:
                if entity.id not in acted_ids:
                    from src.utils.metrics import SIM_INVALID_ACTIONS_TOTAL
                    SIM_INVALID_ACTIONS_TOTAL.labels(action_type="rest", reason="timeout").inc()
                    
                    from src.core.models.reason_codes import ActionReason, ReasonCode
                    proposals.append(ActionProposal(
                        actor_id=entity.id,
                        verb=ActionType.REST,
                        target=None,
                        reason=ActionReason(
                            code=ReasonCode.INTERACTION_REJECTED, 
                            metadata={"detail": "Chaos Drop / Worker Timeout"},
                            is_rejection=True
                        ),
                        new_ai_state=int(entity.mind.decision.ai_state)
                    ))
        
        ctx.tick_proposals = proposals
