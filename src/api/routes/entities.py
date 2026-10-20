"""Entity read-model sub-resources.

`GET /api/v1/entities` is a bounded summary list and `GET /api/v1/entities/{id}` the bounded detail (both in `server.py`); the history that grows with an entity's age,
its quests, is paged here (TCK-20261020-ENTITY-LIST-RETURNS-A-BOUNDED-SUMMARY-NOT-THE-FULL-DETAIL). Presenters only: no domain model leaves the API.
"""
from __future__ import annotations

from typing import Any, Dict, Literal

from fastapi import APIRouter, Depends

from src.api.dependencies import get_engine_manager
from src.api.engine_manager import V2EngineManager

router = APIRouter(tags=["Entities"])


@router.get("/entities/{entity_id}/quests", response_model=Dict[str, Any])
async def get_entity_quests(
    entity_id: int,
    status: Literal["live", "terminal", "all"] = "all",
    offset: int = 0,
    limit: int = 50,
    manager: V2EngineManager = Depends(get_engine_manager),
) -> Dict[str, Any]:
    """Paged quest history of one entity, newest first. `status`: live, terminal or all (anything else is a 422). `limit` is capped at the list page ceiling."""
    result = manager.get_entity_quests(entity_id, status, offset, limit)
    return result if result is not None else {"error": f"Entity {entity_id} not found"}
