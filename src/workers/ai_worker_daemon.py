import logging
import os
import time
from typing import Any

import pika

from src.ai.brain import AIBrain
from src.config import SimulationConfig
from src.core.gameplay.faction import FactionRegistry
from src.platform.rng import DeterministicRNG
from src.utils.serialization import SimulationSerializer
from src.core.models.snapshot import Snapshot

from src.utils.logging import setup_logging
setup_logging(os.environ.get("LOG_LEVEL", "INFO"))
logger = logging.getLogger("ai_worker")

class AIWorkerDaemon:
    """Daemon that listens for broadcast snapshots and processes AI tasks."""
    
    def __init__(self):
        self.config = SimulationConfig()
        # The AI Brain is stateless, we can instantiate one per worker
        self.rng = DeterministicRNG(seed=999) # Seed doesn't deeply matter here because RNG is Domain-based with tick/eid seeds
        self.brain = AIBrain(self.config, self.rng, FactionRegistry.default())
        
        # Wrapped logger (Phase L3 Logging)
        self.worker_id = f"worker_{os.getpid()}"
        from src.utils.logging import RobustLoggerAdapter
        self._logger = RobustLoggerAdapter(logger, {'component': 'ai_worker', 'worker_id': self.worker_id, 'tick': -1})
        
        # Local state
        self.current_tick: int = -1
        self.current_snapshot: Any | None = None
        
        # RabbitMQ setup
        url = os.environ.get("RABBITMQ_URL", "amqp://guest:guest@localhost:5672/")
        parameters = pika.URLParameters(url)
        parameters.heartbeat = 600
        parameters.blocked_connection_timeout = 300
        
        while True:
            try:
                self.conn = pika.BlockingConnection(parameters)
                self.channel = self.conn.channel()
                self._logger.info("Worker successfully connected to RabbitMQ at %s", url)
                break
            except Exception as e:
                self._logger.error("Waiting for RabbitMQ... %s", e)
                time.sleep(2)
        
        # 1. Setup Snapshot Broadcast (Fanout)
        self.channel.exchange_declare(exchange='ai_snapshots', exchange_type='fanout')
        # Exclusive queue bound to fanout exchange so it gets deleted if worker dies
        result = self.channel.queue_declare(queue='', exclusive=True)
        self.snapshot_queue_name = result.method.queue
        self.channel.queue_bind(exchange='ai_snapshots', queue=self.snapshot_queue_name)
        
        # 2. Setup Task Queue (Direct/Round robin)
        self.channel.queue_declare(queue='ai_tasks', durable=False)
        self.channel.basic_qos(prefetch_count=10) # Process 10 tasks at a time
        
        # 3. Setup Results Queue (Direct back to engine)
        self.channel.queue_declare(queue='ai_results', durable=False)
        
        # 4. Setup Isolated Chaos Queues for throughput testing
        self.channel.queue_declare(queue='ai_tasks_test', durable=False)
        self.channel.queue_declare(queue='ai_results_test', durable=False)

    def on_snapshot(self, ch, method, properties, body):
        """Receive serialized snapshot from main engine."""
        try:
            snapshot = SimulationSerializer.loads(body, Snapshot)
            self.current_snapshot = snapshot
            self.current_tick = snapshot.tick
            self._logger.debug("Worker received Snapshot for tick %d", snapshot.tick, extra={'tick': snapshot.tick})
        except Exception as e:
            self._logger.error("Failed to deserialize snapshot: %s", e)

    def on_task(self, ch, method, properties, body):
        """Receive a batch of entity tasks."""
        try:
            batch = SimulationSerializer.loads(body, dict)
            tick = batch["tick"]
            entity_ids = batch["entity_ids"]
            self._logger.info("Worker received Batch for tick %d (%d entities)", tick, len(entity_ids))
            
            if tick > self.current_tick:
                self._logger.warning("Batch for tick %d arrived before snapshot (current %d). Requeueing.", tick, self.current_tick)
                ch.basic_reject(delivery_tag=method.delivery_tag, requeue=True)
                return
            if tick < self.current_tick:
                self._logger.debug("Obsolete batch for tick %d (current %d)", tick, self.current_tick)
                ch.basic_ack(delivery_tag=method.delivery_tag)
                return
            if not self.current_snapshot:
                self._logger.warning("No snapshot available for batch at tick %d", tick)
                ch.basic_reject(delivery_tag=method.delivery_tag, requeue=True)
                return

            results = []
            for eid in entity_ids:
                res = self._process_single_entity(eid, tick)
                results.append(res)
                
            self._send_batch_result(tick, results)
            ch.basic_ack(delivery_tag=method.delivery_tag)
            
        except Exception as e:
            self._logger.error("Failed to process batch task: %s", e)
            ch.basic_reject(delivery_tag=method.delivery_tag, requeue=False)

    def _process_single_entity(self, entity_id: int, tick: int) -> dict:
        """Helper to run AI for a single ID within a batch."""
        entity = self.current_snapshot.entities.get(entity_id)
        if not entity or not entity.combat.alive:
            return {"entity_id": entity_id, "new_state": None, "proposal": None}
            
        try:
            new_state, proposal = self.brain.decide(entity, self.current_snapshot)
            proposal = proposal.model_copy(update={"new_ai_state": int(new_state)})
            return {
                "entity_id": entity_id,
                "new_state": int(new_state),
                "proposal": proposal
            }
        except Exception as e:
            self._logger.exception("AI crashed for entity %d", entity_id, extra={'tick': tick})
            return {"entity_id": entity_id, "new_state": None, "proposal": None}

    def _send_batch_result(self, tick: int, results: list[dict]):
        """Send the batched results back to engine."""
        payload = {
            "tick": tick,
            "results": results
        }
        self.channel.basic_publish(
            exchange='',
            routing_key='ai_results',
            body=SimulationSerializer.dumps(payload)
        )

    def on_test_task(self, ch, method, properties, body):
        """Blindly reflect chaos test payloads to simulate rapid physical queue consumption."""
        try:
            self.channel.basic_publish(exchange='', routing_key='ai_results_test', body=body)
            ch.basic_ack(delivery_tag=method.delivery_tag)
        except Exception as e:
            self._logger.error("Chaos test bounce failed: %s", e)
            ch.basic_reject(delivery_tag=method.delivery_tag, requeue=False)

    def run(self):
        """Start consuming."""
        self.channel.basic_consume(
            queue=self.snapshot_queue_name, 
            on_message_callback=self.on_snapshot, 
            auto_ack=True
        )
        self.channel.basic_consume(
            queue='ai_tasks', 
            on_message_callback=self.on_task,
            auto_ack=False
        )
        self.channel.basic_consume(
            queue='ai_tasks_test', 
            on_message_callback=self.on_test_task,
            auto_ack=False
        )
        
        self._logger.info("AI Worker Daemon started, listening for tasks...")
        try:
            self.channel.start_consuming()
        except KeyboardInterrupt:
            self.channel.stop_consuming()
            self.conn.close()

if __name__ == "__main__":
    daemon = AIWorkerDaemon()
    daemon.run()
