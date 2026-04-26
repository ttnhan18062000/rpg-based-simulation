"""Versioned API route modules."""

try:
    from fastapi import APIRouter
    from src_legacy.api.routes.control import router as control_router
    from src_legacy.api.routes.map import router as map_router
    from src_legacy.api.routes.state import router as state_router
    from src_legacy.api.routes.config import router as config_router
    from src_legacy.api.routes.metadata import router as metadata_router
    from src_legacy.api.routes.stream import router as stream_router

    api_router = APIRouter(prefix="/api/v1")
    api_router.include_router(map_router, tags=["Map"])
    api_router.include_router(stream_router, prefix="/stream", tags=["Stream"])
    api_router.include_router(state_router, tags=["State"])
    api_router.include_router(control_router, tags=["Control"])
    api_router.include_router(config_router, tags=["Config"])
    api_router.include_router(metadata_router)
except ImportError:
    # AOA Stabilization: Allow core engine tests to collect even if API deps are missing
    api_router = None

__all__ = ["api_router"]
