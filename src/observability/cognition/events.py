"""
Strategic cognition simulation event models and schema contracts.
"""
from typing import Any, Dict, Optional
from src.observability.events import SimulationEvent, EventCategory, EventSeverity


class StrategicCognitionEvent(SimulationEvent):
    """Base event for strategic cognition observability shifts."""
    event_category: EventCategory = "strategy"
    source_system: str = "strategy_system"

    def __init__(self, **data: Any) -> None:
        # Populate payload with all custom strategic fields passed to __init__
        # to ensure compatibility with warehouse ingest and direct payload dictionary access
        if "payload" not in data or not data["payload"]:
            payload = {}
            for k, v in data.items():
                if k not in {
                    "event_id", "event_type", "event_category", "tick", "severity",
                    "source_system", "message", "timestamp", "run_id", "scenario_id",
                    "entity_id", "related_entity_ids", "target_id", "region_id",
                    "faction_id", "quest_id", "transaction_id", "causal_id", "created_at"
                }:
                    payload[k] = v
            data["payload"] = payload
        super().__init__(**data)


class StrategicProjectChanged(StrategicCognitionEvent):
    """Emitted when an entity switches its current active strategic project."""
    event_type: str = "StrategicProjectChanged"
    severity: EventSeverity = "INFO"
    previous_project_id: Optional[str] = None
    new_project_id: Optional[str] = None
    reason: str = ""
    source_goal_score: Optional[float] = None
    resulting_action: Optional[str] = None
    target_pos: Optional[list[float]] = None

    def __init__(self, **data: Any) -> None:
        if "message" not in data:
            ent = data.get("entity_id")
            prev = data.get("previous_project_id")
            new = data.get("new_project_id")
            reason_str = f" due to: {data.get('reason')}" if data.get("reason") else ""
            extra = ""
            if "source_goal_score" in data and data["source_goal_score"] is not None:
                extra += f" (score: {data['source_goal_score']:.1f})"
            if "resulting_action" in data and data["resulting_action"] is not None:
                extra += f" resulting in action: {data['resulting_action']}"
            data["message"] = f"Entity {ent} project shifted from {prev} to {new}{reason_str}{extra}"
        super().__init__(**data)


class StrategicObjectiveChanged(StrategicCognitionEvent):
    """Emitted when an entity switches its active objective within a project."""
    event_type: str = "StrategicObjectiveChanged"
    severity: EventSeverity = "INFO"
    previous_objective_id: Optional[str] = None
    new_objective_id: Optional[str] = None

    def __init__(self, **data: Any) -> None:
        if "message" not in data:
            ent = data.get("entity_id")
            prev = data.get("previous_objective_id")
            new = data.get("new_objective_id")
            data["message"] = f"Entity {ent} objective shifted from {prev} to {new}"
        super().__init__(**data)


class StrategicBlockerAdded(StrategicCognitionEvent):
    """Emitted when a strategic blocker is registered on an entity."""
    event_type: str = "StrategicBlockerAdded"
    severity: EventSeverity = "WARNING"
    blocker_id: str
    blocker_kind: str
    blocker_label: str

    def __init__(self, **data: Any) -> None:
        if "message" not in data:
            ent = data.get("entity_id")
            bid = data.get("blocker_id")
            lbl = data.get("blocker_label")
            data["message"] = f"Entity {ent} registered strategic blocker {bid} ({lbl})"
        super().__init__(**data)


class StrategicBlockerResolved(StrategicCognitionEvent):
    """Emitted when a strategic blocker is successfully resolved/removed."""
    event_type: str = "StrategicBlockerResolved"
    severity: EventSeverity = "INFO"
    blocker_id: str
    blocker_label: str

    def __init__(self, **data: Any) -> None:
        if "message" not in data:
            ent = data.get("entity_id")
            bid = data.get("blocker_id")
            data["message"] = f"Entity {ent} resolved strategic blocker {bid}"
        super().__init__(**data)


class StrategicLeadExhausted(StrategicCognitionEvent):
    """Emitted when a strategic investigation lead is exhausted/invalidated."""
    event_type: str = "StrategicLeadExhausted"
    severity: EventSeverity = "INFO"
    lead_id: str
    lead_label: str

    def __init__(self, **data: Any) -> None:
        if "message" not in data:
            ent = data.get("entity_id")
            lid = data.get("lead_id")
            data["message"] = f"Entity {ent} exhausted strategic lead {lid}"
        super().__init__(**data)


class StrategicConcernRaised(StrategicCognitionEvent):
    """Emitted when a strategic threat/concern is appraised."""
    event_type: str = "StrategicConcernRaised"
    severity: EventSeverity = "INFO"
    concern_id: str
    concern_label: str

    def __init__(self, **data: Any) -> None:
        if "message" not in data:
            ent = data.get("entity_id")
            cid = data.get("concern_id")
            data["message"] = f"Entity {ent} raised strategic concern {cid}"
        super().__init__(**data)


class StrategicOverloadDetected(StrategicCognitionEvent):
    """Emitted when strategic overload gates are breached."""
    event_type: str = "StrategicOverloadDetected"
    severity: EventSeverity = "WARNING"
    overload_source: str

    def __init__(self, **data: Any) -> None:
        if "message" not in data:
            ent = data.get("entity_id")
            src = data.get("overload_source")
            data["message"] = f"Entity {ent} breached strategic profile constraints: {src}"
        super().__init__(**data)


class StrategicDetourCreated(StrategicCognitionEvent):
    """Emitted when a detour project is spawned to resolve a blocker."""
    event_type: str = "StrategicDetourCreated"
    severity: EventSeverity = "INFO"
    blocker_id: str
    detour_project_id: str

    def __init__(self, **data: Any) -> None:
        if "message" not in data:
            ent = data.get("entity_id")
            bid = data.get("blocker_id")
            dpid = data.get("detour_project_id")
            data["message"] = f"Entity {ent} created detour project {dpid} to resolve blocker {bid}"
        super().__init__(**data)


class StrategicDetourLoopSuspected(StrategicCognitionEvent):
    """Emitted when repeated detours without progress imply a loop."""
    event_type: str = "StrategicDetourLoopSuspected"
    severity: EventSeverity = "CRITICAL"
    blocker_id: str
    detour_count: int

    def __init__(self, **data: Any) -> None:
        if "message" not in data:
            ent = data.get("entity_id")
            bid = data.get("blocker_id")
            cnt = data.get("detour_count")
            data["message"] = f"Entity {ent} suspected detour loop on blocker {bid} ({cnt} detours spawned)"
        super().__init__(**data)
