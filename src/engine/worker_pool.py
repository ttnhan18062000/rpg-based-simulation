"""Parallel worker pool for AI decision-making (RabbitMQ Distributed AMQP)."""

from __future__ import annotations

import logging
import pickle
import time
from typing import TYPE_CHECKING, Any

import pika
from pika.exceptions import AMQPError

from src.core.enums import AIState, Domain
from src.api.rabbitmq_client import get_rabbitmq

if TYPE_CHECKING:
    from src.actions.base import ActionProposal
    from src.ai.brain import AIBrain
    from src.config import SimulationConfig
    from src.core.models import Entity
    from src.core.snapshot import Snapshot
    from src.engine.action_queue import ActionQueue

logger = logging.getLogger(__name__)


class WorkerPool:
    """Distributes AI decisions to external RabbitMQ Docker workers.

    Picks the complete immutable Snapshot once per tick and broadcasts
    it to all workers. Then publishes lightweight `(tick, entity_id)` tasks to a 
    round-robin work queue, and consumes the resulting ActionProposals.
    """

    __slots__ = ("_config", "_brain", "_rng", "_channel", "_snapshot_exchange", "_tasks_queue", "_results_queue")

    def __init__(self, config: SimulationConfig, brain: AIBrain, rng: DeterministicRNG) -> None:
        self._config = config
        self._brain = brain
        self._rng = rng
        
        # We only use RabbitMQ if num_workers > 1
        self._channel: pika.adapters.blocking_connection.BlockingChannel | None = None
        self._snapshot_exchange = 'ai_snapshots'
        self._tasks_queue = 'ai_tasks'
        self._results_queue = 'ai_results'

        if self._config.num_workers > 1:
            self._init_rabbitmq()

    def _init_rabbitmq(self) -> None:
        try:
            conn = get_rabbitmq()
            self._channel = conn.channel()
            # Declare infrastructure
            self._channel.exchange_declare(exchange=self._snapshot_exchange, exchange_type='fanout')
            self._channel.queue_declare(queue=self._tasks_queue, durable=False)
            self._channel.queue_declare(queue=self._results_queue, durable=False)
            logger.info("WorkerPool initialized RabbitMQ connection.")
        except Exception as e:
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
            self._dispatch_inline(entities, snapshot, action_queue)
            return

        # Distributed path
        try:
            self._dispatch_rabbitmq(entities, snapshot, action_queue)
        except Exception as e:
            logger.exception("RabbitMQ dispatch crashed for tick %d, falling back to inline.", snapshot.tick)
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

            try:
                _eid, new_state, proposal = self._think(entity, snapshot)
                action_queue.push(proposal)
            except Exception:
                logger.exception("AI failed for entity %d", entity.id)

    def _dispatch_rabbitmq(
        self,
        entities: list[Entity],
        snapshot: Snapshot,
        action_queue: ActionQueue,
    ) -> None:
        """Distribute workloads across RabbitMQ nodes."""
        assert self._channel is not None
        
        # 1. Broadcast the tick's snapshot to all workers
        snapshot_bytes = pickle.dumps(snapshot)
        self._channel.basic_publish(
            exchange=self._snapshot_exchange,
            routing_key='',
            body=snapshot_bytes,
        )

        # 2. Publish all tasks
        for entity in entities:
            task = {"tick": snapshot.tick, "entity_id": entity.id}
            self._channel.basic_publish(
                exchange='',
                routing_key=self._tasks_queue,
                body=pickle.dumps(task),
            )

        # 3. Synchronously wait and collect results
        expected_responses = len(entities)
        collected = 0
        timeout = float(self._config.worker_timeout_seconds)
        start_time = time.time()
        
        # We manually poll the results queue so we don't block forever
        while collected < expected_responses:
            if time.time() - start_time > timeout:
                logger.warning("WorkerPool timed out waiting for AI workers. Collected %d/%d", collected, expected_responses)
                break
                
            method_frame, header_frame, body = self._channel.basic_get(queue=self._results_queue, auto_ack=True)
            if method_frame:
                try:
                    result = pickle.loads(body)
                    tick = result.get("tick")
                    
                    if tick == snapshot.tick:
                        # --- Chaos Mode: Fault Injection ---
                        # Use Domain.AI_DECISION or a dedicated one for chaos
                        if self._config.chaos_enabled and self._rng.next_float(Domain.AI_DECISION, result.get("entity_id", 0), tick + 99) < self._config.chaos_drop_rate:
                            logger.warning("Chaos Mode: Dropping AI result for entity %d", result.get("entity_id", -1))
                            collected += 1 # Count as "responded" but don't push the proposal
                            continue

                        proposal = result.get("proposal")
                        if proposal:
                            action_queue.push(proposal)
                        collected += 1
                    else:
                        # Stale result from previous timeout
                        pass
                except Exception as e:
                    logger.error("Failed to unpickle worker response: %s", e)
                    collected += 1 # Avoid infinite looping on bad payloads
            else:
                # Slight sleep to yield CPU while waiting
                time.sleep(0.005)

    def _think(self, entity: Entity, snapshot: Snapshot) -> tuple[int, AIState, ActionProposal]:
        """Run AI for a single entity (executed inline)."""
        from dataclasses import replace

        new_state, proposal = self._brain.decide(entity, snapshot)
        proposal = replace(proposal, new_ai_state=int(new_state))
        return entity.id, new_state, proposal

    def shutdown(self) -> None:
        """Close RabbitMQ channels."""
        if self._channel and self._channel.is_open:
            try:
                self._channel.close()
            except AMQPError:
                pass
            self._channel = None
