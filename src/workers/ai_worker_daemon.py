import logging
import os
import pickle
import time
from typing import Any

import pika

from src.ai.brain import AIBrain
from src.config import SimulationConfig
from src.core.faction import FactionRegistry
from src.systems.rng import DeterministicRNG

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("ai_worker")

class AIWorkerDaemon:
    """Daemon that listens for broadcast snapshots and processes AI tasks."""
    
    def __init__(self):
        self.config = SimulationConfig()
        # The AI Brain is stateless, we can instantiate one per worker
        self.rng = DeterministicRNG(seed=999) # Seed doesn't deeply matter here because RNG is Domain-based with tick/eid seeds
        self.brain = AIBrain(self.config, self.rng, FactionRegistry.default())
        
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
                logger.info("Worker successfully connected to RabbitMQ at %s", url)
                break
            except Exception as e:
                logger.error("Waiting for RabbitMQ... %s", e)
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

    def on_snapshot(self, ch, method, properties, body):
        """Receive pickled snapshot from main engine."""
        try:
            snapshot = pickle.loads(body)
            self.current_snapshot = snapshot
            self.current_tick = snapshot.tick
            logger.debug("Worker received Snapshot for tick %d", snapshot.tick)
        except Exception as e:
            logger.error("Failed to unpickle snapshot: %s", e)

    def on_task(self, ch, method, properties, body):
        """Receive an entity task."""
        try:
            task = pickle.loads(body)
            tick = task["tick"]
            entity_id = task["entity_id"]
            
            # If the task is from an old tick, ignore it. 
            if tick > self.current_tick:
                # We haven't received the snapshot for this tick yet. Basic rejection with requeue.
                ch.basic_reject(delivery_tag=method.delivery_tag, requeue=True)
                return
            if tick < self.current_tick:
                # Obsolete task
                ch.basic_ack(delivery_tag=method.delivery_tag)
                return
                
            if not self.current_snapshot:
                ch.basic_reject(delivery_tag=method.delivery_tag, requeue=True)
                return

            entity = self.current_snapshot.entities.get(entity_id)
            if not entity or not entity.alive:
                self._send_result(tick, entity_id, None, None)
                ch.basic_ack(delivery_tag=method.delivery_tag)
                return
                
            # Run the AI logic
            try:
                from dataclasses import replace
                new_state, proposal = self.brain.decide(entity, self.current_snapshot)
                proposal = replace(proposal, new_ai_state=int(new_state))
                
                self._send_result(tick, entity_id, int(new_state), proposal)
            except Exception as e:
                logger.exception("AI crashed for entity %d", entity_id)
                self._send_result(tick, entity_id, None, None)
            
            ch.basic_ack(delivery_tag=method.delivery_tag)
            
        except Exception as e:
            logger.error("Failed to process task: %s", e)
            ch.basic_reject(delivery_tag=method.delivery_tag, requeue=False)

    def _send_result(self, tick: int, entity_id: int, new_state: int | None, proposal: Any | None):
        """Send the result back to engine."""
        payload = {
            "tick": tick,
            "entity_id": entity_id,
            "new_state": new_state,
            "proposal": proposal
        }
        self.channel.basic_publish(
            exchange='',
            routing_key='ai_results',
            body=pickle.dumps(payload)
        )

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
        
        logger.info("AI Worker Daemon started, listening for tasks...")
        try:
            self.channel.start_consuming()
        except KeyboardInterrupt:
            self.channel.stop_consuming()
            self.conn.close()

if __name__ == "__main__":
    daemon = AIWorkerDaemon()
    daemon.run()
