import os
import threading
from typing import Optional
from src.observability.alerts.router import AlertRouter
from src.observability.alerts.deduplicator import AlertDeduplicator
from src.observability.alerts.sinks import LogAlertSink, WebhookAlertSink

class AlertsManager:
    """
    Central coordinator for initializing, configuring, and exposing the
    Alert Routing system globally.
    """
    _router: Optional[AlertRouter] = None
    _lock = threading.Lock()

    @classmethod
    def get_router(cls) -> AlertRouter:
        """Resolves and returns the globally shared thread-safe AlertRouter instance."""
        with cls._lock:
            if cls._router is None:
                # 1. Resolve configuration
                severity_threshold = os.environ.get("SIM_ALERTS_SEVERITY_THRESHOLD") or os.environ.get("RPG_ALERTS_SEVERITY_THRESHOLD") or "INFO"
                
                dedup_window_str = os.environ.get("SIM_ALERTS_DEDUP_WINDOW_SECONDS") or os.environ.get("RPG_ALERTS_DEDUP_WINDOW_SECONDS")
                try:
                    dedup_window = float(dedup_window_str) if dedup_window_str else 60.0
                except ValueError:
                    dedup_window = 60.0

                webhook_url = os.environ.get("SIM_ALERTS_WEBHOOK_URL") or os.environ.get("RPG_ALERTS_WEBHOOK_URL") or ""
                webhook_enabled_str = os.environ.get("SIM_ALERTS_WEBHOOK_ENABLED") or os.environ.get("RPG_ALERTS_WEBHOOK_ENABLED") or "false"
                webhook_enabled = webhook_enabled_str.lower().strip() in ("true", "1", "yes")
                if webhook_url and not webhook_enabled_str:
                    webhook_enabled = True # Enable automatically if URL is set but enabled not explicitly set to false

                webhook_timeout_str = os.environ.get("SIM_ALERTS_WEBHOOK_TIMEOUT") or os.environ.get("RPG_ALERTS_WEBHOOK_TIMEOUT")
                try:
                    webhook_timeout = float(webhook_timeout_str) if webhook_timeout_str else 5.0
                except ValueError:
                    webhook_timeout = 5.0

                webhook_retries_str = os.environ.get("SIM_ALERTS_WEBHOOK_RETRIES") or os.environ.get("RPG_ALERTS_WEBHOOK_RETRIES")
                try:
                    webhook_retries = int(webhook_retries_str) if webhook_retries_str else 3
                except ValueError:
                    webhook_retries = 3

                # 2. Build router and deduplicator
                dedup = AlertDeduplicator(suppression_window_seconds=dedup_window)
                router = AlertRouter(severity_threshold=severity_threshold, deduplicator=dedup)

                # 3. Add default Log sink
                log_sink = LogAlertSink()
                router.register_sink(log_sink)

                # 4. Add optional Webhook sink
                webhook_sink = WebhookAlertSink(
                    webhook_url=webhook_url,
                    enabled=webhook_enabled,
                    timeout_seconds=webhook_timeout,
                    max_retries=webhook_retries
                )
                router.register_sink(webhook_sink)

                cls._router = router

            return cls._router

    @classmethod
    def reset(cls) -> None:
        """Reset the shared singleton (mainly useful for testing configurations)."""
        with cls._lock:
            if cls._router:
                # Properly shut down any running sinks
                for sink in cls._router._sinks:
                    if hasattr(sink, "shutdown"):
                        try:
                            sink.shutdown()
                        except Exception:
                            pass
            cls._router = None
