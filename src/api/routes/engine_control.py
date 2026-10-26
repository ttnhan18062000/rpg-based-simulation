"""Engine control: pause, resume, and the test-event publisher."""
from __future__ import annotations

from typing import Any, Dict

from fastapi import APIRouter, Depends

from src.api.admission_control import require_admission
from src.api.dependencies import get_engine_manager
from src.api.engine_manager import V2EngineManager
from src.observability.events import SimulationEvent
from src.observability.live.event_publisher import LiveEventPublisher

router = APIRouter(dependencies=[Depends(require_admission)])


@router.post("/api/v1/control/pause", response_model=Dict[str, Any])
async def pause_sim(manager: V2EngineManager = Depends(get_engine_manager)):  # noqa: ANN201, D103  # no docstring or annotation: both feed the pinned OpenAPI document
    manager.pause()
    return {"status": "paused"}


@router.post("/api/v1/control/resume", response_model=Dict[str, Any])
async def resume_sim(manager: V2EngineManager = Depends(get_engine_manager)):  # noqa: ANN201, D103  # no docstring or annotation: both feed the pinned OpenAPI document
    manager.resume()
    return {"status": "resumed"}


@router.post("/api/v1/test/publish_event", response_model=Dict[str, Any])
async def publish_test_event(event_data: dict):  # noqa: ANN201, D103  # no docstring or annotation: both feed the pinned OpenAPI document
    if "event_type" not in event_data:
        event_data["event_type"] = "test_event"
    if "event_category" not in event_data:
        event_data["event_category"] = "movement"
    if "severity" not in event_data:
        event_data["severity"] = "INFO"
    if "source_system" not in event_data:
        event_data["source_system"] = "test"
    if "message" not in event_data:
        event_data["message"] = "test message"
    if "tick" not in event_data:
        event_data["tick"] = 0

    event = SimulationEvent(**event_data)
    LiveEventPublisher.get_instance().publish(event)
    return {"status": "published"}
