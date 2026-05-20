import threading
import logging
from typing import List, Dict
from src.observability.alerts.models import AlertEvent
from src.observability.alerts.sinks import AlertSink
from src.observability.alerts.deduplicator import AlertDeduplicator

logger = logging.getLogger(__name__)

# Severity mapping to order them for threshold filtering
SEVERITY_LEVELS = {
    "DEBUG": 10,
    "INFO": 20,
    "WARNING": 30,
    "ERROR": 40,
    "CRITICAL": 50
}

class AlertRouter:
    """
    Core Alert dispatcher that deduplicates alerts, filters by severity,
    and routes valid alerts to all registered active sinks.
    """
    def __init__(self, severity_threshold: str = "INFO", deduplicator: AlertDeduplicator = None):
        self.severity_threshold = severity_threshold.upper()
        self.deduplicator = deduplicator or AlertDeduplicator()
        self._sinks: List[AlertSink] = []
        self._lock = threading.RLock()
        
        # Delivery metrics
        self._routed_count = 0
        self._suppressed_count = 0
        self._delivered_count = 0
        self._failure_count = 0

    def register_sink(self, sink: AlertSink) -> None:
        """Register a new routing sink."""
        with self._lock:
            if sink not in self._sinks:
                self._sinks.append(sink)

    def unregister_sink(self, sink: AlertSink) -> None:
        """Unregister an existing routing sink."""
        with self._lock:
            if sink in self._sinks:
                self._sinks.remove(sink)

    def route(self, alert: AlertEvent) -> bool:
        """
        Processes and routes an incoming alert event.
        Returns True if the alert passed filters/deduplication and was dispatched to sinks,
        and False otherwise.
        """
        # 1. Filter by severity threshold
        alert_sev = alert.severity.upper()
        threshold_val = SEVERITY_LEVELS.get(self.severity_threshold, 20)
        alert_val = SEVERITY_LEVELS.get(alert_sev, 20)
        
        if alert_val < threshold_val:
            logger.debug(f"Alert {alert.alert_id} ignored (severity {alert.severity} below threshold {self.severity_threshold})")
            return False

        # 2. Apply deduplication
        if self.deduplicator.should_suppress(alert.dedup_key):
            with self._lock:
                self._suppressed_count += 1
            logger.debug(f"Alert {alert.alert_id} suppressed by deduplicator (key={alert.dedup_key})")
            return False

        # 3. Route to registered sinks
        with self._lock:
            self._routed_count += 1

        dispatched = False
        with self._lock:
            sinks_snapshot = list(self._sinks)

        for sink in sinks_snapshot:
            try:
                success = sink.send(alert)
                if success:
                    with self._lock:
                        self._delivered_count += 1
                    dispatched = True
                else:
                    with self._lock:
                        self._failure_count += 1
            except Exception as e:
                with self._lock:
                    self._failure_count += 1
                logger.error(f"Error executing alert sink {sink.__class__.__name__}: {e}")

        return dispatched

    @property
    def metrics(self) -> Dict[str, int]:
        """Return a dictionary of routing metrics."""
        with self._lock:
            return {
                "routed_total": self._routed_count,
                "suppressed_total": self._suppressed_count,
                "delivered_total": self._delivered_count,
                "failures_total": self._failure_count
            }

    def reset_metrics(self) -> None:
        """Reset routing counts."""
        with self._lock:
            self._routed_count = 0
            self._suppressed_count = 0
            self._delivered_count = 0
            self._failure_count = 0
