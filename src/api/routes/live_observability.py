"""Live observability reads: engine status, the live snapshot and single-entity inspection."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException

from src.api.admission_control import require_admission
from src.api.dependencies import get_engine_manager
from src.observability.live.entity_inspector import EntityInspector
from src.observability.live.snapshot_provider import LiveSnapshotProvider

router = APIRouter(dependencies=[Depends(require_admission)])


@router.get("/api/v1/observability/live/status")
async def get_live_status():  # noqa: ANN201, D103  # no docstring or annotation: both feed the pinned OpenAPI document
    try:
        manager = get_engine_manager()
    except RuntimeError:
        manager = None

    return LiveSnapshotProvider.get_status(manager)


@router.get("/api/v1/observability/live/snapshot")
async def get_live_snapshot():  # noqa: ANN201, D103  # no docstring or annotation: both feed the pinned OpenAPI document
    try:
        manager = get_engine_manager()
    except RuntimeError:
        manager = None

    return LiveSnapshotProvider.get_snapshot(manager)


@router.get("/api/v1/observability/live/entities/{entity_id}")
async def inspect_live_entity(entity_id: int, timeline_limit: int = 20):  # noqa: ANN201, D103  # no docstring or annotation: both feed the pinned OpenAPI document
    try:
        manager = get_engine_manager()
    except RuntimeError:
        manager = None

    snapshot = EntityInspector.inspect_entity(manager, entity_id, timeline_limit)
    if not snapshot.exists:
        raise HTTPException(status_code=404, detail=f"Entity {entity_id} not found or engine idle")
    return snapshot
