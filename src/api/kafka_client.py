from __future__ import annotations

import logging
import os
from typing import Any, TYPE_CHECKING

try:
    from confluent_kafka import Producer, Consumer
    from confluent_kafka.admin import AdminClient, NewTopic
    HAS_KAFKA = True
except ImportError:
    HAS_KAFKA = False
    Producer = None
    Consumer = None
    AdminClient = None
    NewTopic = None

if TYPE_CHECKING:
    from confluent_kafka import Producer, Consumer
    from confluent_kafka.admin import AdminClient, NewTopic

logger = logging.getLogger(__name__)

# Kafka topics
KAFKA_TOPIC_EVENTS = "sim.events"
KAFKA_TOPIC_SNAPSHOTS = "sim.snapshots"

_PRODUCER_INSTANCE: Producer | None = None

def get_kafka_url() -> str:
    """Return the configured Kafka bootstrap servers."""
    return os.environ.get("KAFKA_URL", "127.0.0.1:9092")

def is_kafka_disabled() -> bool:
    """Return True if Kafka integration is explicitly disabled."""
    return os.environ.get("DISABLE_KAFKA", "0").lower() in ("1", "true", "yes")

def init_kafka_topics() -> None:
    """Idempotently create exactly the required topics with appropriate configurations."""
    if is_kafka_disabled() or not HAS_KAFKA or AdminClient is None:
        logger.info("Kafka integration disabled or package missing.")
        return
        
    admin_client = AdminClient({"bootstrap.servers": get_kafka_url()})
    
    # 1. Events Topic: We want this to be an immutable append-only log of deltas,
    # but practically we don't need infinite history locally, standard deletion is fine.
    # We'll use default retention (7 days usually) for safety.
    topic_events = NewTopic(KAFKA_TOPIC_EVENTS, num_partitions=1, replication_factor=1)
    
    # 2. Snapshots Topic: We only care about the relatively recent snapshots.
    # We use log compaction so we can aggressively prune old snapshots while keeping the newest.
    # The key will be "latest" so compaction automatically drops old snapshots.
    topic_snapshots = NewTopic(
        KAFKA_TOPIC_SNAPSHOTS, 
        num_partitions=1, 
        replication_factor=1,
        config={"cleanup.policy": "compact"}
    )
    
    to_create = [topic_events, topic_snapshots]
    
    try:
        # Create topics async
        futures = admin_client.create_topics(to_create)
        for topic, future in futures.items():
            try:
                future.result()  # blocking call to wait for creation
                logger.info("Kafka topic '%s' created successfully.", topic)
            except Exception as e:
                # 36 is topic_already_exists in confluent-kafka Error Codes
                if getattr(e, "args", [None])[0] and "TopicExists" in str(e):
                    logger.debug("Kafka topic '%s' already exists.", topic)
                else:
                    logger.warning("Failed to create topic '%s': %s", topic, e)
    except Exception as e:
        logger.error("Failed to connect to Kafka AdminClient: %s", e)


def get_kafka_producer() -> 'Producer' | None:
    """Return a singleton, highly-durable Kafka Producer."""
    global _PRODUCER_INSTANCE
    
    if is_kafka_disabled() or not HAS_KAFKA or Producer is None:
        return None
        
    if _PRODUCER_INSTANCE is not None:
        return _PRODUCER_INSTANCE
        
    bootstrap_servers = get_kafka_url()
    
    import time
    for i in range(40): # Increased to 40 attempts (120s) for slow Docker bootstrap on Windows
        try:
            conf = {
                'bootstrap.servers': bootstrap_servers,
                'client.id': 'sim-engine-producer',
                'message.max.bytes': 10000000, # 10MB to match broker
                'acks': 'all',
                'retries': 5,
                'retry.backoff.ms': 500
            }
            _PRODUCER_INSTANCE = Producer(conf)
            # Confirm connectivity by fetching metadata
            _PRODUCER_INSTANCE.list_topics(timeout=2.0)
            logger.info("Successfully connected to Kafka producer at %s", bootstrap_servers)
            return _PRODUCER_INSTANCE
        except Exception as e:
            if i == 39:
                from src.utils.metrics import SIM_ERRORS_TOTAL
                SIM_ERRORS_TOTAL.labels(exception_type=type(e).__name__, component="kafka_producer_init").inc()
                logger.error("Final attempt (40) failed to connect to Kafka at %s: %s", bootstrap_servers, e)
                raise # Re-raise the exception on final failure
            logger.warning("Attempt %d/40: Kafka not ready at %s, retrying in 3s...", i+1, bootstrap_servers)
            time.sleep(3)
    
    return None

def flush_producer() -> None:
    """Wait for all messages in the Producer queue to be delivered."""
    global _PRODUCER_INSTANCE
    if _PRODUCER_INSTANCE:
        _PRODUCER_INSTANCE.flush(timeout=5.0)

def create_kafka_consumer(group_id: str = "sim_engine_recovery") -> 'Consumer' | None:
    """Return a new Kafka Consumer configured for reading from the beginning."""
    if is_kafka_disabled() or not HAS_KAFKA or Consumer is None:
        return None
        
    bootstrap_servers = get_kafka_url()
    try:
        conf = {
            'bootstrap.servers': bootstrap_servers,
            'group.id': group_id,
            'auto.offset.reset': 'earliest',
            # We explicitly don't want to auto-commit during recovery until we successfully rehydrate
            'enable.auto.commit': False,
        }
        consumer = Consumer(conf)
        logger.info("Kafka Consumer initialized at %s", bootstrap_servers)
        return consumer
    except Exception as e:
        from src.utils.metrics import SIM_ERRORS_TOTAL
        SIM_ERRORS_TOTAL.labels(exception_type=type(e).__name__, component="kafka_consumer_init").inc()
        logger.error("Failed to initialize Kafka Consumer: %s", e)
        return None
