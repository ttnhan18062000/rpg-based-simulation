import threading
import time
from typing import Dict

class AlertDeduplicator:
    """
    Thread-safe in-memory alert deduplicator that suppresses identical alerts
    within a sliding window duration (in seconds).
    """
    def __init__(self, suppression_window_seconds: float = 60.0):
        self.suppression_window_seconds = suppression_window_seconds
        self._seen_alerts: Dict[str, float] = {}  # Map of dedup_key -> epoch timestamp when seen
        self._lock = threading.RLock()

    def should_suppress(self, dedup_key: str, current_time: float = None) -> bool:
        """
        Check if the alert with the given dedup_key should be suppressed.
        If not suppressed, records the alert presence and returns False.
        If suppressed, returns True.
        """
        if current_time is None:
            current_time = time.time()

        with self._lock:
            # First, prune expired records
            self.prune(current_time)

            last_seen = self._seen_alerts.get(dedup_key)
            if last_seen is not None:
                # Still within the suppression window
                return True

            # Register/update timestamp
            self._seen_alerts[dedup_key] = current_time
            return False

    def prune(self, current_time: float = None) -> None:
        """Remove any entries from the seen map that are older than the suppression window."""
        if current_time is None:
            current_time = time.time()

        with self._lock:
            expired_keys = [
                key for key, timestamp in self._seen_alerts.items()
                if (current_time - timestamp) >= self.suppression_window_seconds
            ]
            for key in expired_keys:
                del self._seen_alerts[key]

    def clear(self) -> None:
        """Clear all registered alerts."""
        with self._lock:
            self._seen_alerts.clear()

    @property
    def seen_count(self) -> int:
        """Returns the current number of unique non-expired alerts tracked."""
        with self._lock:
            return len(self._seen_alerts)
