"""Versioned API route modules."""

from fastapi import APIRouter

from src.api.routes.control import router as control_router
from src.api.routes.map import router as map_router
from src.api.routes.state import router as state_router
from src.api.routes.config import router as config_router
from src.api.routes.metadata import router as metadata_router

api_router = APIRouter(prefix="/api/v1")
api_router.include_router(map_router, tags=["Map"])
api_router.include_router(state_router, tags=["State"])
api_router.include_router(control_router, tags=["Control"])
api_router.include_router(config_router, tags=["Config"])
api_router.include_router(metadata_router)

__all__ = ["api_router"]
