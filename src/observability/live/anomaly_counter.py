from __future__ import annotations
import threading
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field

from src.observability.live.event_publisher import LiveEventSubscriber, SubscriptionFilter, LiveEventPublisher

class LiveAnomalyCounters(BaseModel):
    hard_law_violation_count: int = 0
    navigation_stuck_count: int = 0
    governor_degraded_ticks: int = 0
    dropped_event_count: int = 0
    error_event_count: int = 0
    critical_event_count: int = 0

class LiveAnomalyCounter(LiveEventSubscriber):
    """
    In-process thread-safe live anomaly and event counter.
    Subscribes to the LiveEventPublisher to dynamically aggregate real-time counts.
    """
    _instance: Optional[LiveAnomalyCounter] = None
    _instance_lock = threading.Lock()

    @classmethod
    def get_instance(cls) -> LiveAnomalyCounter:
        with cls._instance_lock:
            if cls._instance is None:
                cls._instance = cls()
            return cls._instance

    @classmethod
    def reset_instance(cls) -> None:
        with cls._instance_lock:
            if cls._instance is not None:
                # Unregister from publisher if registered
                publisher = LiveEventPublisher.get_instance()
                publisher.unregister(cls._instance)
                cls._instance = None

    def __init__(self) -> None:
        # Match all events
        super().__init__(filter_obj=SubscriptionFilter(), capacity=999999)
        self.hard_law_violation_count = 0
        self.navigation_stuck_count = 0
        self.error_event_count = 0
        self.critical_event_count = 0
        self.last_updated_tick = 0
        self.current_run_id = None
        self._counter_lock = threading.Lock()

    def push(self, event: Any) -> bool:
        """Process simulation event live and thread-safely increment rolling counters."""
        with self._counter_lock:
            # Detect new simulation run to auto-reset counters
            if event.run_id and event.run_id != self.current_run_id:
                self._reset_counters(event.run_id)
            
            self.last_updated_tick = max(self.last_updated_tick, event.tick)
            
            if event.event_category == "hard_law" or event.event_type == "InvariantViolation":
                self.hard_law_violation_count += 1
            if event.event_type == "NavigationStuck" or event.event_type == "stuck":
                self.navigation_stuck_count += 1
            if event.severity == "ERROR":
                self.error_event_count += 1
            if event.severity == "CRITICAL":
                self.critical_event_count += 1
                
        return True

    def _reset_counters(self, run_id: Optional[str]) -> None:
        self.current_run_id = run_id
        self.hard_law_violation_count = 0
        self.navigation_stuck_count = 0
        self.error_event_count = 0
        self.critical_event_count = 0
        self.last_updated_tick = 0

    def reset(self) -> None:
        """Exposed method to manually reset counters."""
        with self._counter_lock:
            self._reset_counters(None)

    def get_counters(self, manager: Optional[Any] = None) -> Dict[str, int]:
        """Resolves current counter states, dynamically factoring in live manager metrics."""
        with self._counter_lock:
            dropped = 0
            try:
                publisher = LiveEventPublisher.get_instance()
                dropped = publisher.total_dropped
            except Exception:
                pass

            degraded_ticks = 0
            if manager and getattr(manager, "kernel", None):
                kernel = manager.kernel
                if getattr(kernel, "status", None) and kernel.status:
                    status = kernel.status
                    if getattr(status, "current_mode", None) and status.current_mode.name != "NORMAL":
                        degraded_ticks = getattr(status, "mode_dwell_ticks", 0)

            return {
                "hard_law_violation_count": self.hard_law_violation_count,
                "navigation_stuck_count": self.navigation_stuck_count,
                "governor_degraded_ticks": degraded_ticks,
                "dropped_event_count": dropped,
                "error_event_count": self.error_event_count,
                "critical_event_count": self.critical_event_count,
            }

    def calculate_health(self, manager: Optional[Any] = None) -> Dict[str, Any]:
        """
        Computes current overall health state using defined threshold rules.
        Returns:
            {
                "health_state": "HEALTHY" | "WARNING" | "DEGRADED" | "CRITICAL" | "UNKNOWN",
                "reasons": List[str],
                "counters": Dict[str, int],
                "last_updated_tick": int
            }
        """
        counters = self.get_counters(manager)
        reasons: List[str] = []
        
        # Determine status string
        status_str = "IDLE"
        if manager:
            if getattr(manager, "is_stopping", False):
                status_str = "STOPPING"
            elif getattr(manager, "is_paused", False):
                status_str = "PAUSED"
            elif getattr(manager, "is_running", False):
                status_str = "RUNNING"

        # Apply evaluation rules from highest severity to lowest
        if counters["hard_law_violation_count"] > 0:
            health = "CRITICAL"
            reasons.append(f"Critical hard law violation(s) detected: count={counters['hard_law_violation_count']}")
        elif counters["critical_event_count"] > 0:
            health = "CRITICAL"
            reasons.append(f"Critical simulation event(s) recorded: count={counters['critical_event_count']}")
        elif counters["governor_degraded_ticks"] > 5:
            health = "DEGRADED"
            reasons.append(f"Governor has been in degraded/survival mode for {counters['governor_degraded_ticks']} ticks")
        elif counters["navigation_stuck_count"] > 3:
            health = "WARNING"
            reasons.append(f"Excessive stuck navigation events detected: count={counters['navigation_stuck_count']}")
        elif counters["dropped_event_count"] > 10:
            health = "WARNING"
            reasons.append(f"Observability pipeline dropping events due to slow subscribers: count={counters['dropped_event_count']}")
        elif counters["error_event_count"] > 0:
            health = "WARNING"
            reasons.append(f"Tick loop errors recorded: count={counters['error_event_count']}")
        elif status_str in ("RUNNING", "PAUSED"):
            health = "HEALTHY"
        else:
            health = "UNKNOWN"

        if not reasons:
            if health == "HEALTHY":
                reasons.append("Simulation running smoothly with zero anomalies detected")
            else:
                reasons.append("Simulation is currently idle or initializing")

        with self._counter_lock:
            tick = self.last_updated_tick

        return {
            "health_state": health,
            "reasons": reasons,
            "counters": counters,
            "last_updated_tick": tick
        }
