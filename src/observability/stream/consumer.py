from __future__ import annotations
import json
import logging
import random
import time
from datetime import datetime, timezone
from typing import Any, Callable, Dict, Optional, Tuple
from src.observability.events import SimulationEvent

logger = logging.getLogger(__name__)


class RedisStreamConsumer:
    """
    Minimal, reliable consumer for reading and acking events from a Redis Stream.
    Uses consumer groups to track delivery status.
    """

    BACKOFF_BASE_SECONDS = 0.2
    BACKOFF_CAP_SECONDS = 30.0
    BACKOFF_JITTER_RATIO = 0.2
    RECLAIM_IDLE_MS = 30000
    MAX_DELIVERY_ATTEMPTS = 3

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
        self.dlq_stream_name = f"{self.stream_name}:dlq"
        self.client: Optional[Any] = None
        self._connected = False
        self._consecutive_failures = 0

    def _compute_backoff_delay(self, attempt: int, rng: Optional["random.Random"] = None) -> float:
        capped = min(self.BACKOFF_CAP_SECONDS, self.BACKOFF_BASE_SECONDS * (2 ** max(0, attempt - 1)))
        jitter = capped * self.BACKOFF_JITTER_RATIO
        r = rng or random
        return max(0.0, capped + r.uniform(-jitter, jitter))

    def connect(self) -> bool:
        if self._consecutive_failures > 0:
            time.sleep(self._compute_backoff_delay(self._consecutive_failures))

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
            self._consecutive_failures = 0
            return True
        except Exception as e:
            logger.error(f"RedisStreamConsumer failed to connect/create group: {e}")
            self._connected = False
            self._consecutive_failures += 1
            return False

    def _send_to_dlq(self, msg_id: str, original_fields: Dict[str, Any], reason: str, delivery_count: int) -> bool:
        try:
            dlq_fields = {
                **original_fields,
                "dlq_reason": str(reason)[:500],
                "dlq_source_id": str(msg_id),
                "dlq_delivery_count": str(delivery_count),
                "dlq_failed_at": datetime.now(timezone.utc).isoformat(),
            }
            self.client.xadd(self.dlq_stream_name, dlq_fields, maxlen=1000, approximate=True)
            return True
        except Exception as e:
            logger.error(f"RedisStreamConsumer failed to write DLQ entry for {msg_id}: {e}")
            return False

    def _handle_message(
        self,
        msg_id: str,
        payload: Dict[str, Any],
        handler: Callable[[SimulationEvent], None]
    ) -> Tuple[bool, bool]:
        """
        Returns (acked, handler_ran). `acked` is True if the message was removed from the
        PEL (either successfully processed, or correctly identified as malformed and dropped).
        `handler_ran` is True only when the caller-supplied handler was actually invoked.
        """
        raw_payload = payload.get("payload")
        if not raw_payload:
            logger.warning(f"Malformed stream event missing 'payload': {msg_id}")
            # ACK anyway to clear malformed messages from the stream delivery pipeline
            self.client.xack(self.stream_name, self.group_name, msg_id)
            return True, False

        try:
            event_dict = json.loads(raw_payload)
            event = SimulationEvent(**event_dict)
        except (json.JSONDecodeError, ValueError, TypeError) as ex:
            logger.error(f"Malformed stream event payload {msg_id}: {ex}")
            self.client.xack(self.stream_name, self.group_name, msg_id)
            return True, False

        try:
            handler(event)
        except Exception as ex:
            logger.error(f"Handler failed for stream event {msg_id} (will remain pending for reclaim): {ex}")
            return False, True

        self.client.xack(self.stream_name, self.group_name, msg_id)
        return True, True

    def _reclaim_pending(self, handler: Callable[[SimulationEvent], None]) -> None:
        try:
            pending = self.client.xpending_range(
                self.stream_name,
                self.group_name,
                min="-",
                max="+",
                count=50,
                idle=self.RECLAIM_IDLE_MS
            )
            if not pending:
                return

            retry_entries = [e for e in pending if e["times_delivered"] < self.MAX_DELIVERY_ATTEMPTS]
            exhausted_entries = [e for e in pending if e["times_delivered"] >= self.MAX_DELIVERY_ATTEMPTS]

            if retry_entries:
                retry_ids = [e["message_id"] for e in retry_entries]
                claimed = self.client.xclaim(
                    self.stream_name,
                    self.group_name,
                    consumername=self.consumer_name,
                    min_idle_time=self.RECLAIM_IDLE_MS,
                    message_ids=retry_ids
                )
                for msg_id, fields in claimed:
                    self._handle_message(msg_id, fields, handler)

            for entry in exhausted_entries:
                msg_id = entry["message_id"]
                entries = self.client.xrange(self.stream_name, min=msg_id, max=msg_id, count=1)
                if entries:
                    self._send_to_dlq(
                        msg_id,
                        entries[0][1],
                        "max delivery attempts exceeded",
                        entry["times_delivered"]
                    )
                self.client.xack(self.stream_name, self.group_name, msg_id)
        except Exception as e:
            logger.error(f"RedisStreamConsumer reclaim sweep failed: {e}")

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
            if streams:
                for _, messages in streams:
                    for msg_id, payload in messages:
                        acked, handler_ran = self._handle_message(msg_id, payload, handler)
                        if acked and handler_ran:
                            processed_count += 1

            self._reclaim_pending(handler)
            return processed_count
        except Exception as e:
            logger.error(f"RedisStreamConsumer read error: {e}")
            # If server goes offline, mark connection degraded
            self._connected = False
            self._consecutive_failures += 1
            return 0

    def close(self) -> None:
        if self.client:
            try:
                self.client.close()
            except Exception:
                pass
            self.client = None
            self._connected = False
