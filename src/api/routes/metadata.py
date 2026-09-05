"""Metadata REST routes.

8 GET routes under /api/v1/metadata/* matching frontend/src/types/metadata.ts's already-specified
response shapes (frontend/src/contexts/MetadataContext.tsx has called these since initial import;
none existed backend-side until now).
Ticket: TCK-20260825-METADATA-API-BACKEND-MISSING
"""
from __future__ import annotations

from typing import Any, Dict

from fastapi import APIRouter, HTTPException

from src.api.dependencies import get_catalog_repository
from src.api.presenters.metadata_presenter import MetadataPresenter

router = APIRouter(prefix="/metadata", tags=["Metadata"])


def _catalog():
    catalog = get_catalog_repository()
    if catalog is None:
        raise HTTPException(status_code=503, detail="Catalog not ready — no content loaded")
    return catalog


@router.get("/enums", response_model=Dict[str, Any], summary="Enum/lookup tables")
async def get_enums() -> Dict[str, Any]:
    return MetadataPresenter.present_enums(_catalog())


@router.get("/items", response_model=Dict[str, Any], summary="Item catalog")
async def get_items() -> Dict[str, Any]:
    return MetadataPresenter.present_items(_catalog())


@router.get("/classes", response_model=Dict[str, Any], summary="Class/skill catalog")
async def get_classes() -> Dict[str, Any]:
    return MetadataPresenter.present_classes()


@router.get("/traits", response_model=Dict[str, Any], summary="Entity trait catalog")
async def get_traits() -> Dict[str, Any]:
    return MetadataPresenter.present_traits(_catalog())


@router.get("/attributes", response_model=Dict[str, Any], summary="Attribute definitions")
async def get_attributes() -> Dict[str, Any]:
    return MetadataPresenter.present_attributes(_catalog())


@router.get("/buildings", response_model=Dict[str, Any], summary="Building type catalog")
async def get_buildings() -> Dict[str, Any]:
    return MetadataPresenter.present_buildings(_catalog())


@router.get("/resources", response_model=Dict[str, Any], summary="Resource node type catalog")
async def get_resources() -> Dict[str, Any]:
    return MetadataPresenter.present_resources(_catalog())


@router.get("/recipes", response_model=Dict[str, Any], summary="Crafting recipe catalog")
async def get_recipes() -> Dict[str, Any]:
    return MetadataPresenter.present_recipes(_catalog())
