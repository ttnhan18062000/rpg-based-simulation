"""FastAPI application factory with lifespan management."""

from __future__ import annotations

import time
import logging
from contextlib import asynccontextmanager
from pathlib import Path
from typing import AsyncIterator

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from prometheus_client import make_asgi_app

from src.api.dependencies import set_engine_manager
from src.api.engine_manager import EngineManager
from src.api.routes import api_router
from src.config import SimulationConfig
from src.utils.logging import setup_logging

logger = logging.getLogger(__name__)

FRONTEND_DIR = Path(__file__).resolve().parent.parent.parent / "frontend"
STATIC_DIR = FRONTEND_DIR / "dist"


def create_app(config: SimulationConfig | None = None) -> FastAPI:
    """Build and return the fully-configured FastAPI application."""
    if config is None:
        config = SimulationConfig()

    _config = config

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        from src.core.registry_loader import load_all_registries
        setup_logging(_config.log_level)
        load_all_registries()
        manager = EngineManager(_config)
        set_engine_manager(manager)
        manager.start()
        logger.info("API server started — simulation running.")
        yield
        manager.stop()
        logger.info("API server shutting down.")


    app = FastAPI(
        title="RPG Simulation Engine",
        description=(
            "Deterministic Concurrent RPG Engine — Real-Time Visualization API.\n\n"
            "## API Groups\n\n"
            "- **State** — Live simulation state: entities, events, buildings, ground items\n"
            "- **Map** — Static grid data (fetch once at startup)\n"
            "- **Control** — Simulation lifecycle: start, pause, resume, step, reset\n"
            "- **Config** — Read-only simulation configuration\n"
            "- **Metadata** — Game definitions (items, classes, traits, skills, etc.) — single source of truth\n"
        ),
        version="0.1.0",
        lifespan=lifespan,
        openapi_tags=[
            {"name": "State", "description": "Live simulation state polled by the frontend: entities, events, buildings, ground items, resource nodes."},
            {"name": "Map", "description": "Static grid/map data. Fetched once at startup — the tile layout does not change during a run."},
            {"name": "Control", "description": "Simulation lifecycle controls: start, pause, resume, single-step, and reset."},
            {"name": "Config", "description": "Read-only simulation configuration parameters (world size, tick rate, hero settings, etc.)."},
            {"name": "Metadata", "description": "All game definitions — items, classes, skills, traits, attributes, buildings, resources, recipes, enums. These are pydantic dataclasses from src/core/ serialized directly — the single source of truth for both engine and frontend."},
        ],
    )

    # CORS — allow any origin in dev
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    from src.utils.metrics import API_REQUEST_DURATION

    @app.middleware("http")
    async def metrics_middleware(request: Request, call_next):
        start_time = time.perf_counter()
        response = await call_next(request)
        duration = time.perf_counter() - start_time
        
        # We don't want to track the intense /stream or /metrics polling endpoint itself as heavily
        path = request.url.path
        if path not in ("/metrics", "/api/v1/stream"):
            API_REQUEST_DURATION.labels(method=request.method, endpoint=path).observe(duration)
            
        return response

    # Mount Prometheus metrics
    metrics_app = make_asgi_app()
    app.mount("/metrics", metrics_app)

    # API routes
    app.include_router(api_router)

    # Serve frontend static files
    if STATIC_DIR.exists():
        app.mount("/", StaticFiles(directory=str(STATIC_DIR), html=True), name="frontend")

    return app
