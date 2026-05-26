from __future__ import annotations
import json
import logging
from typing import Any, Callable, Dict, Optional
from src.observability.events import SimulationEvent

logger = logging.getLogger(__name__)


class RedisStreamConsumer:
    """
    Minimal, reliable consumer for reading and acking events from a Redis Stream.
    Uses consumer groups to track delivery status.
    """
    def __init__(
        self,
        redis_url: str = "redis://localhost:6379/0",
        stream_name: str = "simulation:events",
        group_name: str = "observatory:consumers",
        consumer_name: str = "worker:1"
    ) -> None:
        self.redis_url = redis_url
        self.stream_name = stream_name
        self.group_name = group_name
        self.consumer_name = consumer_name
        self.client: Optional[Any] = None
        self._connected = False

    def connect(self) -> bool:
        try:
            import redis
            self.client = redis.from_url(
                self.redis_url,
                socket_connect_timeout=2.0,
                socket_timeout=2.0,
                decode_responses=True
            )
            self.client.ping()
            self._connected = True

            # Safely create the consumer group. If it exists, a ResponseError is raised.
            try:
                self.client.xgroup_create(self.stream_name, self.group_name, id="0", mkstream=True)
            except redis.exceptions.ResponseError as e:
                if "BUSYGROUP" not in str(e):
                    raise e
            return True
        except Exception as e:
            logger.error(f"RedisStreamConsumer failed to connect/create group: {e}")
            self._connected = False
            return False

    def read_and_process(self, handler: Callable[[SimulationEvent], None], block_ms: int = 1000) -> int:
        """
        Reads pending or new events from the stream, invokes the callback handler,
        and acknowledges the processing success via XACK.
        """
        if not self._connected or self.client is None:
            if not self.connect():
                return 0

        try:
            # Read messages assigned to this consumer group.
            # '>' signifies only new messages (not delivered to other group consumers).
            streams = self.client.xreadgroup(
                groupname=self.group_name,
                consumername=self.consumer_name,
                streams={self.stream_name: ">"},
                count=50,
                block=block_ms
            )

            processed_count = 0
            if not streams:
                return 0

            for _, messages in streams:
                for msg_id, payload in messages:
                    try:
                        raw_payload = payload.get("payload")
                        if not raw_payload:
                            logger.warning(f"Malformed stream event missing 'payload': {msg_id}")
                            # ACK anyway to clear malformed messages from the stream delivery pipeline
                            self.client.xack(self.stream_name, self.group_name, msg_id)
                            continue

                        event_dict = json.loads(raw_payload)
                        event = SimulationEvent(**event_dict)

                        # Invoke processing handler callback
                        handler(event)

                        # Acknowledge the message
                        self.client.xack(self.stream_name, self.group_name, msg_id)
                        processed_count += 1
                    except Exception as ex:
                        logger.error(f"Error processing stream event {msg_id}: {ex}")
                        # Acknowledge malformed/bad records to prevent head-of-line blocking on poison pills
                        try:
                            self.client.xack(self.stream_name, self.group_name, msg_id)
                        except Exception:
                            pass
            return processed_count
        except Exception as e:
            logger.error(f"RedisStreamConsumer read error: {e}")
            # If server goes offline, mark connection degraded
            self._connected = False
            return 0

    def close(self) -> None:
        if self.client:
            try:
                self.client.close()
            except Exception:
                pass
            self.client = None
            self._connected = False
