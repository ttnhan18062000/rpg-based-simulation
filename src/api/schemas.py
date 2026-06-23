"""
Response schemas for src/api/server.py inline routes.

TypedDict classes are used as response_model= targets for the 4 highest-risk
engine_manager routes. Dict[str, Any] is used as a typed placeholder for
the remaining 9 actionable inline routes.

Do not use strict Pydantic validation here until the actual response shapes
are fully contract-tested (tracked in open_audit_findings_backlog §1G).
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional
from typing_extensions import TypedDict


class WorldStateResponse(TypedDict, total=False):
    """Shape for /api/v1/state (engine_manager.get_state())."""
    tick: int
    status: str
    entity_count: int
    region_count: int
    metadata: Dict[str, Any]


class EntityPageResponse(TypedDict, total=False):
    """Shape for /api/v1/entities (engine_manager.get_entities_paged())."""
    entities: List[Dict[str, Any]]
    total: int
    offset: int
    limit: int


class EntityDetailResponse(TypedDict, total=False):
    """Shape for /api/v1/entities/{entity_id} (engine_manager.get_entity())."""
    id: int
    name: str
    attributes: Dict[str, Any]
    metadata: Dict[str, Any]
