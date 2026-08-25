"""Manifest REST route.

GET /api/v1/manifest -- versioned ID-to-meaning content dictionary (terrain_types,
entity_kinds, building_types).
Ticket: TCK-20260821-MANIFEST-ID-LOOKUP-ENDPOINT
"""
from __future__ import annotations

from typing import Any, Dict

from fastapi import APIRouter, HTTPException

from src.api.dependencies import get_engine_manager, get_catalog_repository
from src.api.presenters.manifest_presenter import ManifestPresenter

router = APIRouter(tags=["Manifest"])


@router.get(
    "/manifest",
    response_model=Dict[str, Any],
    summary="ID-to-meaning content dictionary",
    description=(
        "Returns a versioned lookup table (terrain_types, entity_kinds, building_types) "
        "populated live from the loaded content catalog. terrain_types is keyed by the same "
        "int codes present_map's RLE grid uses. Read-only -- no state mutation."
    ),
)
async def get_manifest() -> Dict[str, Any]:
    catalog = get_catalog_repository()
    if catalog is None:
        raise HTTPException(status_code=503, detail="Catalog not ready — no content loaded")
    manager = get_engine_manager()
    state = manager.latest_state
    return ManifestPresenter.present_manifest(state, catalog)
