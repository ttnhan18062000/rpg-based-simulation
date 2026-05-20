from dataclasses import dataclass, field
from typing import Dict, Any, Optional
import uuid
from datetime import datetime, timezone

@dataclass
class AlertEvent:
    alert_type: str
    severity: str
    run_id: str
    message: str
    dedup_key: str
    evidence: Dict[str, Any] = field(default_factory=dict)
    alert_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    sweep_id: Optional[str] = None
    tick: Optional[int] = None
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def to_dict(self) -> Dict[str, Any]:
        """Convert the alert event into a dictionary representation ready for JSON serialization."""
        return {
            "alert_id": self.alert_id,
            "alert_type": self.alert_type,
            "severity": self.severity,
            "run_id": self.run_id,
            "sweep_id": self.sweep_id,
            "tick": self.tick,
            "message": self.message,
            "evidence": self.evidence,
            "dedup_key": self.dedup_key,
            "created_at": self.created_at
        }

    @classmethod
    def create_hard_law_violation(cls, run_id: str, tick: int, violation: Any) -> "AlertEvent":
        """Factory to create a Hard Law violation alert event."""
        law_id = getattr(violation, "law_id", "UnknownLaw")
        entity_id = getattr(violation, "entity_id", None)
        message = getattr(violation, "message", "Hard law violation observed")
        severity = getattr(violation, "severity", "CRITICAL")
        details = getattr(violation, "details", {})
        
        # Deduplication key maps directly to the specific law and entity
        dedup_key = f"hard_law:{law_id}:{entity_id or 'global'}"
        
        evidence = {
            "law_id": law_id,
            "entity_id": entity_id,
            "details": details
        }
        
        return cls(
            alert_type="HardLawViolation",
            severity=severity,
            run_id=run_id,
            tick=tick,
            message=message,
            evidence=evidence,
            dedup_key=dedup_key
        )

    @classmethod
    def create_watchdog_trip(cls, run_id: str, tick: int, message: str, details: Dict[str, Any]) -> "AlertEvent":
        """Factory to create a watchdog trip alert event."""
        return cls(
            alert_type="WatchdogTrip",
            severity="CRITICAL",
            run_id=run_id,
            tick=tick,
            message=message,
            evidence=details,
            dedup_key=f"watchdog:{run_id}"
        )

    @classmethod
    def create_critical_anomaly(cls, run_id: str, tick: Optional[int], message: str, details: Dict[str, Any]) -> "AlertEvent":
        """Factory to create a critical anomaly alert event from the worker/rules engine."""
        rule_id = details.get("rule_id", "UnknownRule")
        return cls(
            alert_type="CriticalAnomaly",
            severity="ERROR",
            run_id=run_id,
            tick=tick,
            message=message,
            evidence=details,
            dedup_key=f"anomaly:{rule_id}:{details.get('entity_id', 'global')}"
        )

    @classmethod
    def create_stream_backpressure(cls, run_id: str, tick: Optional[int], message: str, details: Dict[str, Any]) -> "AlertEvent":
        """Factory to create an event stream backpressure alert event."""
        return cls(
            alert_type="StreamBackpressureHigh",
            severity="WARNING",
            run_id=run_id,
            tick=tick,
            message=message,
            evidence=details,
            dedup_key=f"backpressure:{run_id}"
        )
