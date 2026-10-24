"""Live health reads: the anomaly-based health score and the event-stream adapter health."""
from __future__ import annotations

from typing import Any, Dict

from fastapi import APIRouter, Depends

from src.api.admission_control import require_admission
from src.api.dependencies import get_engine_manager
from src.observability.live.anomaly_counter import LiveAnomalyCounter
from src.observability.stream.factory import get_event_stream_adapter

router = APIRouter(dependencies=[Depends(require_admission)])


@router.get("/api/v1/observability/live/health", response_model=Dict[str, Any])
async def get_live_health():  # noqa: ANN201, D103  # no docstring or annotation: both feed the pinned OpenAPI document
    try:
        manager = get_engine_manager()
    except RuntimeError:
        manager = None

    counter = LiveAnomalyCounter.get_instance()
    return counter.calculate_health(manager)


@router.get("/api/v1/observability/live/stream-health", response_model=Dict[str, Any])
async def get_stream_health():  # noqa: ANN201, D103  # no docstring or annotation: both feed the pinned OpenAPI document
    adapter = get_event_stream_adapter()
    return adapter.health()
