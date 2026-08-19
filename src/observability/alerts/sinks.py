import logging
import requests
import json
import threading
import time
from abc import ABC, abstractmethod
from concurrent.futures import ThreadPoolExecutor
from typing import Optional
from src.observability.alerts.models import AlertEvent
from src.platform.rng import new_random_source

logger = logging.getLogger(__name__)

class AlertSink(ABC):
    """Abstract base class for all Alert Sinks."""
    @abstractmethod
    def send(self, alert: AlertEvent) -> bool:
        """
        Synchronously or asynchronously process and route the alert event.
        Returns True if the event was successfully handled, False otherwise.
        """
        pass

class LogAlertSink(AlertSink):
    """Sink that logs alerts to the local logging stream with correct level formatting."""
    def send(self, alert: AlertEvent) -> bool:
        msg = f"[ALERT] type={alert.alert_type} run={alert.run_id} severity={alert.severity} tick={alert.tick or 'N/A'}: {alert.message} (evidence={alert.evidence})"
        
        # Maps severity to logging module levels
        if alert.severity == "CRITICAL":
            logger.critical(msg)
        elif alert.severity in ("ERROR", "HIGH"):
            logger.error(msg)
        elif alert.severity in ("WARNING", "MEDIUM"):
            logger.warning(msg)
        else:
            logger.info(msg)
            
        return True

class WebhookAlertSink(AlertSink):
    """
    Sink that routes structured alert JSON payloads asynchronously to an external
    HTTPS/HTTP endpoint. Delivery runs on a background thread pool to safeguard main
    simulation loop performance.
    """
    BACKOFF_BASE_SECONDS = 0.5
    BACKOFF_CAP_SECONDS = 10.0
    BACKOFF_JITTER_RATIO = 0.2

    CIRCUIT_BREAKER_FAILURE_THRESHOLD = 5   # consecutive failed full-dispatch cycles to open
    CIRCUIT_BREAKER_COOLDOWN_SECONDS = 60.0  # time in OPEN before a half-open probe is allowed

    def __init__(self, webhook_url: str, enabled: bool = False, timeout_seconds: float = 5.0, max_retries: int = 3):
        self.webhook_url = webhook_url
        self.enabled = enabled
        self.timeout_seconds = timeout_seconds
        self.max_retries = max_retries
        # Dedicated thread pool for async POST delivery
        self._executor = ThreadPoolExecutor(max_workers=2, thread_name_prefix="webhook-alert")

        self._circuit_state = "closed"          # "closed" | "open" | "half_open"
        self._consecutive_failures = 0
        self._circuit_opened_at = 0.0
        self._circuit_lock = threading.Lock()

    def send(self, alert: AlertEvent) -> bool:
        if not self.enabled or not self.webhook_url:
            return False

        if not self._circuit_allows_dispatch():
            return False

        # Enqueue request to the executor to prevent blocking
        self._executor.submit(self._dispatch_with_retry, alert)
        return True

    def _compute_backoff_delay(self, attempt: int, rng: Optional["random.Random"] = None) -> float:
        capped = min(self.BACKOFF_CAP_SECONDS, self.BACKOFF_BASE_SECONDS * (2 ** max(0, attempt - 1)))
        jitter = capped * self.BACKOFF_JITTER_RATIO
        r = rng or new_random_source()
        return max(0.0, capped + r.uniform(-jitter, jitter))

    def _circuit_allows_dispatch(self) -> bool:
        with self._circuit_lock:
            if self._circuit_state == "closed":
                return True
            if self._circuit_state == "open":
                if time.time() - self._circuit_opened_at >= self.CIRCUIT_BREAKER_COOLDOWN_SECONDS:
                    self._circuit_state = "half_open"
                    return True
                return False
            # half_open: a probe is already in flight, don't let a second call race it
            return False

    def _record_outcome(self, success: bool) -> None:
        with self._circuit_lock:
            if success:
                self._consecutive_failures = 0
                if self._circuit_state == "half_open":
                    self._circuit_state = "closed"
                return

            self._consecutive_failures += 1
            if self._circuit_state == "half_open":
                self._circuit_state = "open"
                self._circuit_opened_at = time.time()
            elif self._circuit_state == "closed" and self._consecutive_failures >= self.CIRCUIT_BREAKER_FAILURE_THRESHOLD:
                self._circuit_state = "open"
                self._circuit_opened_at = time.time()

    def _dispatch_with_retry(self, alert: AlertEvent) -> bool:
        payload = alert.to_dict()
        headers = {"Content-Type": "application/json"}

        for attempt in range(1, self.max_retries + 1):
            try:
                response = requests.post(
                    self.webhook_url,
                    json=payload,
                    headers=headers,
                    timeout=self.timeout_seconds
                )
                if response.status_code in (200, 201, 202, 204):
                    logger.debug(f"Webhook alert successfully delivered on attempt {attempt}")
                    self._record_outcome(success=True)
                    return True
                else:
                    logger.warning(
                        f"Webhook alert server returned error {response.status_code} "
                        f"on attempt {attempt} for alert {alert.alert_id}"
                    )
            except requests.RequestException as e:
                logger.warning(
                    f"Webhook alert post failed on attempt {attempt} "
                    f"for alert {alert.alert_id}: {e}"
                )

            # Exponential backoff with jitter before retry (capped)
            if attempt < self.max_retries:
                time.sleep(self._compute_backoff_delay(attempt))

        logger.error(f"Failed to deliver webhook alert {alert.alert_id} after {self.max_retries} attempts.")
        self._record_outcome(success=False)
        return False

    def shutdown(self, wait: bool = True) -> None:
        """Shutdown the background thread pool executor."""
        self._executor.shutdown(wait=wait)
