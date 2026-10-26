"""Engine state reads: the state view, the full snapshot and the entity list and lookup."""
from __future__ import annotations

from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends

from src.api.admission_control import require_admission
from src.api.dependencies import get_engine_manager
from src.api.engine_manager import V2EngineManager

router = APIRouter(dependencies=[Depends(require_admission)])


@router.get("/api/v1/state", response_model=Dict[str, Any])
async def get_state(manager: V2EngineManager = Depends(get_engine_manager)):  # noqa: ANN201, D103  # no docstring or annotation: both feed the pinned OpenAPI document
    state = manager.get_state()
    if not state:
        return {"error": "State not available"}
    return state


@router.get("/api/v1/inspect", response_model=Dict[str, Any])
async def inspect_state(manager: V2EngineManager = Depends(get_engine_manager)):  # noqa: ANN201  # a return annotation would change the pinned OpenAPI document
    """Complete state view (Deprecated: Use granular endpoints for large worlds)."""
    snapshot = manager.get_full_snapshot()
    if not snapshot:
        return {"error": "State not available"}
    return snapshot


@router.get("/api/v1/entities", response_model=Dict[str, Any])
async def get_entities(  # noqa: ANN201  # a return annotation would change the pinned OpenAPI document
    offset: int = 0,
    limit: int = 100,
    manager: V2EngineManager = Depends(get_engine_manager),
):
    """Paged entity SUMMARIES: bounded fields plus counts, independent of an entity's age. The full model is GET /entities/{id}; quest history is paged at /entities/{id}/quests."""
    return manager.get_entities_paged(offset, limit)


@router.get("/api/v1/entities/{entity_id}", response_model=Optional[Dict[str, Any]])
async def get_entity(  # noqa: ANN201  # a return annotation would change the pinned OpenAPI document
    entity_id: int,
    manager: V2EngineManager = Depends(get_engine_manager),
):
    """Single entity lookup."""
    entity = manager.get_entity(entity_id)
    if not entity:
        return {"error": f"Entity {entity_id} not found"}
    return entity
