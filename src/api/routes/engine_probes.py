"""Process-level probes: Prometheus metrics and the liveness/health payload.

`/metrics` sits behind admission control; `/health` is the one route open to an unauthenticated caller
(`tests/api/server_readiness.py` depends on that). Both keep their dependencies on the route itself, because the two
differ and the characterization snapshot pins the dependency list per route.
"""
from __future__ import annotations

import logging
from typing import Any, Dict

from fastapi import APIRouter, Depends, Response
from fastapi.responses import JSONResponse
from prometheus_client import CONTENT_TYPE_LATEST, generate_latest

from src.api.admission_control import require_admission
from src.api.dependencies import get_engine_manager
from src.api.engine_manager import V2EngineManager

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/metrics", dependencies=[Depends(require_admission)])
async def get_metrics(manager: V2EngineManager = Depends(get_engine_manager)):  # noqa: ANN201  # a return annotation would become the OpenAPI response model, which is pinned
    """Expose Prometheus text format metrics from V2EngineManager."""
    try:
        data = generate_latest(manager.metrics_registry)
        return Response(content=data, media_type=CONTENT_TYPE_LATEST)
    except Exception as e:  # noqa: BLE001  # a metrics failure answers 500 with the message instead of failing the scrape route
        logger.exception("Failed to generate metrics")
        return Response(content=f"# Error: {e}", status_code=500, media_type="text/plain")


@router.get("/health", response_model=Dict[str, Any])
async def health_check(manager: V2EngineManager = Depends(get_engine_manager)):  # noqa: ANN201, D103  # no docstring or annotation: both feed the pinned OpenAPI document
    payload = manager.get_health_status()
    status_code = 503 if payload["status"] == "unhealthy" else 200
    return JSONResponse(content=payload, status_code=status_code)
