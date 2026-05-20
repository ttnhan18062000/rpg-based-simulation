import logging
import requests
import json
import time
from abc import ABC, abstractmethod
from concurrent.futures import ThreadPoolExecutor
from typing import Optional
from src.observability.alerts.models import AlertEvent

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
    def __init__(self, webhook_url: str, enabled: bool = False, timeout_seconds: float = 5.0, max_retries: int = 3):
        self.webhook_url = webhook_url
        self.enabled = enabled
        self.timeout_seconds = timeout_seconds
        self.max_retries = max_retries
        # Dedicated thread pool for async POST delivery
        self._executor = ThreadPoolExecutor(max_workers=2, thread_name_prefix="webhook-alert")

    def send(self, alert: AlertEvent) -> bool:
        if not self.enabled or not self.webhook_url:
            return False
        
        # Enqueue request to the executor to prevent blocking
        self._executor.submit(self._dispatch_with_retry, alert)
        return True

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
            
            # Short sleep before retry (exponential backoff)
            if attempt < self.max_retries:
                time.sleep(0.5 * attempt)
                
        logger.error(f"Failed to deliver webhook alert {alert.alert_id} after {self.max_retries} attempts.")
        return False

    def shutdown(self, wait: bool = True) -> None:
        """Shutdown the background thread pool executor."""
        self._executor.shutdown(wait=wait)
