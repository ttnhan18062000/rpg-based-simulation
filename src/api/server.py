from __future__ import annotations
import time
import logging
from contextlib import asynccontextmanager
from typing import AsyncIterator

from fastapi import FastAPI, Request, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware

from src.api.dependencies import set_engine_manager, get_engine_manager
from src.api.engine_manager import V2EngineManager
from src.config.profiles import RuntimeProfile

logger = logging.getLogger(__name__)

def create_v2_app(profile: RuntimeProfile) -> FastAPI:
    """Build and return the V2 FastAPI application."""
    
    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        manager = V2EngineManager(profile)
        set_engine_manager(manager)
        manager.start()
        logger.info("V2 API server started.")
        yield
        manager.stop()
        logger.info("V2 API server shutting down.")

    app = FastAPI(
        title="V2 RPG Simulation Engine",
        version="2.0.0",
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    app.add_middleware(GZipMiddleware, minimum_size=512)

    from src.api.ws import stream
    app.include_router(stream.router, prefix="/api/v1")

    @app.get("/health")
    async def health_check():
        return {"status": "ok", "version": "v2", "timestamp": time.time()}

    @app.get("/api/v1/state")
    async def get_state(manager: V2EngineManager = Depends(get_engine_manager)):
        state = manager.get_state()
        if not state:
            return {"error": "State not available"}
        from src.api.presenters.state_presenter import StatePresenter
        return StatePresenter.present_minimal(state)

    @app.get("/api/v1/inspect")
    async def inspect_state(manager: V2EngineManager = Depends(get_engine_manager)):
        state = manager.get_state()
        if not state:
            return {"error": "State not available"}
        from src.api.presenters.state_presenter import StatePresenter
        return StatePresenter.present_full(state)

    @app.post("/api/v1/control/pause")
    async def pause_sim(manager: V2EngineManager = Depends(get_engine_manager)):
        manager.pause()
        return {"status": "paused"}

    @app.post("/api/v1/control/resume")
    async def resume_sim(manager: V2EngineManager = Depends(get_engine_manager)):
        manager.resume()
        return {"status": "resumed"}

    return app
