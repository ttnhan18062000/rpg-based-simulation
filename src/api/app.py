"""FastAPI application factory with lifespan management."""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from pathlib import Path
from typing import AsyncIterator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

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
        setup_logging(_config.log_level)
        manager = EngineManager(_config)
        set_engine_manager(manager)
        manager.start()
        logger.info("API server started — simulation running.")
        yield
        manager.stop()
        logger.info("API server shutting down.")

    app = FastAPI(
        title="RPG Simulation Engine",
        description="Deterministic Concurrent RPG Engine — Real-Time Visualization API",
        version="0.1.0",
        lifespan=lifespan,
    )

    # CORS — allow any origin in dev
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # API routes
    app.include_router(api_router)

    # Serve frontend static files
    if STATIC_DIR.exists():
        app.mount("/", StaticFiles(directory=str(STATIC_DIR), html=True), name="frontend")

    return app
