"""Kafka Client for persistent event sourcing and epoch snapshots."""

import logging
import os
from typing import Any

from confluent_kafka import Producer, Consumer
from confluent_kafka.admin import AdminClient, NewTopic

logger = logging.getLogger(__name__)

# Kafka topics
KAFKA_TOPIC_EVENTS = "sim.events"
KAFKA_TOPIC_SNAPSHOTS = "sim.snapshots"

_PRODUCER_INSTANCE: Producer | None = None

def get_kafka_url() -> str:
    """Return the configured Kafka bootstrap servers."""
    return os.environ.get("KAFKA_URL", "localhost:9092")

def init_kafka_topics() -> None:
    """Idempotently create exactly the required topics with appropriate configurations."""
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


def get_kafka_producer() -> Producer | None:
    """Return a singleton, highly-durable Kafka Producer."""
    global _PRODUCER_INSTANCE
    
    if _PRODUCER_INSTANCE is not None:
        return _PRODUCER_INSTANCE
        
    bootstrap_servers = get_kafka_url()
    try:
        # We need strong durability for event sourcing
        conf = {
            'bootstrap.servers': bootstrap_servers,
            'acks': 'all',  # Wait for leader and all replicas
            'enable.idempotence': True, # Prevent duplicate messages on network retry
            'compression.type': 'lz4', # Heavy JSON payloads compress well
        }
        _PRODUCER_INSTANCE = Producer(conf)
        logger.info("Kafka Producer initialized at %s", bootstrap_servers)
        return _PRODUCER_INSTANCE
    except Exception as e:
        logger.error("Failed to initialize Kafka Producer: %s", e)
        return None

def flush_producer() -> None:
    """Wait for all messages in the Producer queue to be delivered."""
    global _PRODUCER_INSTANCE
    if _PRODUCER_INSTANCE:
        _PRODUCER_INSTANCE.flush(timeout=5.0)

def create_kafka_consumer(group_id: str = "sim_engine_recovery") -> Consumer | None:
    """Return a new Kafka Consumer configured for reading from the beginning."""
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
        logger.error("Failed to initialize Kafka Consumer: %s", e)
        return None
