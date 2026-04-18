"""Parallel worker pool for AI decision-making (RabbitMQ Distributed AMQP)."""

from __future__ import annotations

import logging
import time
from typing import TYPE_CHECKING, Any

# Infrastructure imports handled lazily or via TYPE_CHECKING

from src.core.models.enums import AIState, Domain
from src.api.rabbitmq_client import get_rabbitmq
from src.utils.serialization import SimulationSerializer

if TYPE_CHECKING:
    import pika
    from pika.exceptions import AMQPError
    from src.actions.base import ActionProposal
    from src.config import SimulationConfig
    from src.core.entities.entity import Entity
    from src.core.models.snapshot import Snapshot
    from src.engine.action_queue import ActionQueue

from src.ai.brain import AIBrain
from src.platform.rng import DeterministicRNG

logger = logging.getLogger(__name__)


class WorkerPool:
    """Distributes AI decisions to external RabbitMQ Docker workers.

    Picks the complete immutable Snapshot once per tick and broadcasts
    it to all workers. Then publishes lightweight `(tick, entity_id)` tasks to a 
    round-robin work queue, and consumes the resulting ActionProposals.
    """

    __slots__ = ("_config", "_brain", "_rng", "_channel", "_snapshot_exchange", "_tasks_queue", "_results_queue", "_logger")

    def __init__(self, config: SimulationConfig, brain: AIBrain, rng: DeterministicRNG) -> None:
        self._config = config
        self._brain = brain
        self._rng = rng
        
        # We only use RabbitMQ if num_workers > 1
        self._channel: 'pika.adapters.blocking_connection.BlockingChannel' | None = None
        self._snapshot_exchange = 'ai_snapshots'
        self._tasks_queue = 'ai_tasks'
        self._results_queue = 'ai_results'

        if self._config.num_workers > 1:
            self._init_rabbitmq()
            
        # Wrapped logger (Phase L3 Logging)
        from src.utils.logging import RobustLoggerAdapter
        self._logger = RobustLoggerAdapter(logger, {'component': 'worker_pool', 'worker_id': 'master', 'tick': 0})

    def _init_rabbitmq(self) -> None:
        try:
            conn = get_rabbitmq()
            if conn is not None:
                self._channel = conn.channel()
                # Declare infrastructure
                self._channel.exchange_declare(exchange=self._snapshot_exchange, exchange_type='fanout')
                self._channel.queue_declare(queue=self._tasks_queue, durable=False)
                self._channel.queue_declare(queue=self._results_queue, durable=False)
                logger.info("WorkerPool initialized RabbitMQ connection.")
            else:
                logger.warning("WorkerPool: RabbitMQ connection unavailable. Falling back to inline.")
                self._channel = None
        except Exception as e:
            from src.utils.metrics import SIM_ERRORS_TOTAL
            SIM_ERRORS_TOTAL.labels(exception_type=type(e).__name__, component="worker_pool").inc()
            logger.error("WorkerPool failed to connect to RabbitMQ: %s. Falling back to inline execution.", e)
            self._channel = None

    def dispatch(
        self,
        entities: list[Entity],
        snapshot: Snapshot,
        action_queue: ActionQueue,
    ) -> None:
        """Submit AI tasks for all *entities* and collect results into *action_queue*."""
        if not entities:
            return

        # Fast path: single-worker mode or unrecoverable RMQ error — run inline
        if self._config.num_workers <= 1 or not self._channel:
            from src.utils.metrics import SIM_WORKER_HEALTH
            SIM_WORKER_HEALTH.labels(worker_id="inline", state="busy").set(1)
            self._dispatch_inline(entities, snapshot, action_queue)
            SIM_WORKER_HEALTH.labels(worker_id="inline", state="busy").set(0)
            return

        # Distributed path
        try:
            from src.utils.metrics import SIM_WORKER_HEALTH
            SIM_WORKER_HEALTH.labels(worker_id="rabbitmq", state="busy").set(1)
            self._dispatch_rabbitmq(entities, snapshot, action_queue)
            SIM_WORKER_HEALTH.labels(worker_id="rabbitmq", state="busy").set(0)
            SIM_WORKER_HEALTH.labels(worker_id="rabbitmq", state="error").set(0)
        except Exception as e:
            from src.utils.metrics import SIM_ERRORS_TOTAL, SIM_WORKER_HEALTH
            SIM_ERRORS_TOTAL.labels(exception_type=type(e).__name__, component="rabbitmq_dispatch").inc()
            SIM_WORKER_HEALTH.labels(worker_id="rabbitmq", state="busy").set(0)
            SIM_WORKER_HEALTH.labels(worker_id="rabbitmq", state="error").set(1)
            self._logger.exception("RabbitMQ dispatch crashed, falling back to inline.", extra={'tick': snapshot.tick})
            # Reconnect for next tick
            self._channel = None
            self._init_rabbitmq()
            self._dispatch_inline(entities, snapshot, action_queue)

    def _dispatch_inline(
        self,
        entities: list[Entity],
        snapshot: Snapshot,
        action_queue: ActionQueue,
    ) -> None:
        """Fallback inline execution loop (No GIL workaround)."""
        for entity in entities:
            # --- Chaos Mode: Fault Injection ---
            if self._config.chaos_enabled and self._rng.next_float(Domain.AI_DECISION, entity.id, snapshot.tick + 77) < self._config.chaos_drop_rate:
                logger.warning("Chaos Mode (Inline): Dropping AI result for entity %d", entity.id)
                continue

            # AOA PILLAR: Resolve acting entity from the snapshot to ensure absolute isolation.
            # This prevents any accidental mutation of the live WorldState during the decision phase.
            snapshot_actor = snapshot.entities.get(entity.id)
            if not snapshot_actor:
                logger.debug("Entity %d not found in snapshot, skipping decision.", entity.id)
                continue

            try:
                from src.core.models.base import DecisionPhase
                with DecisionPhase():
                    _eid, new_state, proposal = self._think(snapshot_actor, snapshot)
                action_queue.push(proposal)
            except Exception as e:
                from src.utils.metrics import SIM_ERRORS_TOTAL
                SIM_ERRORS_TOTAL.labels(exception_type=type(e).__name__, component="ai_think_inline").inc()
                import traceback
                tb_str = traceback.format_exc()
                logger.error("AI failed for entity %d: %s\n%s", entity.id, e, tb_str)
                # Explicitly clear context to assist GC
                del tb_str
                del e
    def _dispatch_rabbitmq(
        self,
        entities: list[Entity],
        snapshot: Snapshot,
        action_queue: ActionQueue,
    ) -> None:
        """Distribute workloads across RabbitMQ nodes using batching."""
        assert self._channel is not None
        
        # 1. Broadcast the tick's snapshot to all workers
        snapshot_bytes = SimulationSerializer.dumps(snapshot)
        self._channel.basic_publish(
            exchange=self._snapshot_exchange,
            routing_key='',
            body=snapshot_bytes,
        )

        # 2. Publish batches to parallelize deliberation (AOA Phase 6)
        batch_size = self._config.ai_batch_size if hasattr(self._config, "ai_batch_size") else 20
        entity_ids = [e.id for e in entities]
        batches_sent = 0
        
        for i in range(0, len(entity_ids), batch_size):
            chunk = entity_ids[i:i + batch_size]
            batch_task = {"tick": snapshot.tick, "entity_ids": chunk, "batch_id": batches_sent}
            
            self._channel.basic_publish(
                exchange='',
                routing_key=self._tasks_queue,
                body=SimulationSerializer.dumps(batch_task),
            )
            batches_sent += 1

        logger.info("WorkerPool dispatched %d batches for tick %d (%d entities total)", batches_sent, snapshot.tick, len(entity_ids))

        # 3. Synchronously collect all batches
        batches_received = 0
        timeout = float(self._config.worker_timeout_seconds)
        start_time = time.time()
        
        while batches_received < batches_sent:
            if time.time() - start_time > timeout:
                from src.utils.metrics import SIM_ERRORS_TOTAL
                SIM_ERRORS_TOTAL.labels(exception_type="TimeoutError", component="worker_pool_multi_batch").inc()
                logger.warning("WorkerPool timed out! Received %d/%d batches. Tick: %d", batches_received, batches_sent, snapshot.tick)
                break
                
            method_frame, header_frame, body = self._channel.basic_get(queue=self._results_queue, auto_ack=True)
            if method_frame:
                try:
                    result_batch = SimulationSerializer.loads(body, dict)
                    tick = result_batch.get("tick")
                    
                    if tick == snapshot.tick:
                        results = result_batch.get("results", [])
                        for res in results:
                            eid = res.get("entity_id")
                            proposal_data = res.get("proposal")
                            
                            # Reconstruct ActionProposal from dict if serialized as one
                            from src.actions.base import ActionProposal
                            proposal = ActionProposal.model_validate(proposal_data) if proposal_data else None
                            
                            # --- Chaos Mode: Fault Injection ---
                            if self._config.chaos_enabled and self._rng.next_float(Domain.AI_DECISION, eid or 0, tick + 99) < self._config.chaos_drop_rate:
                                continue

                            if proposal:
                                action_queue.push(proposal)
                        
                        batches_received += 1
                    else:
                        # Stale result from a previous timed-out tick, keep looking
                        continue
                except Exception as e:
                    from src.utils.metrics import SIM_ERRORS_TOTAL
                    SIM_ERRORS_TOTAL.labels(exception_type=type(e).__name__, component="worker_deserialize_batch").inc()
                    logger.error("Failed to deserialize worker batch response: %s", e)
                    break 
            else:
                # Polling interval - slightly more aggressive wait than 5ms if we know we are waiting for a big batch
                time.sleep(0.002)


    def _think(self, entity: Entity, snapshot: Snapshot) -> tuple[int, AIState, ActionProposal]:
        """Run AI for a single entity (executed inline)."""
        new_state, proposal = self._brain.decide(entity, snapshot)
        proposal = proposal.model_copy(update={"new_ai_state": int(new_state)})
        return entity.id, new_state, proposal

    def shutdown(self) -> None:
        """Close RabbitMQ channels and clear internal references (Idempotent). [Milestone 6]"""
        if hasattr(self, "_channel") and self._channel and self._channel.is_open:
            try:
                self._channel.close()
            except Exception: # Avoid top-level AMQPError dependency
                pass
        
        # Aggressive Slot Clearing (Idempotent)
        self._channel = None
        self._brain = None
        self._rng = None
        self._config = None
        self._logger = None
