from __future__ import annotations
import logging
from contextlib import asynccontextmanager
from typing import Any, AsyncIterator, Dict, Optional

from fastapi import FastAPI, Request, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse

from src.api.auth import (
    configure_api_keys, require_api_key, require_api_key_ws,
)
from src.api.admission_control import (
    configure_admission_control, require_admission, require_admission_ws,
)
from src.api.dependencies import (
    set_engine_manager, get_engine_manager,
    set_quality_hub, set_quality_persistence,
    set_catalog_repository,
)
from src.api.engine_manager import V2EngineManager
from src.api.http_metrics import RequestDurationMiddleware
from src.api.routes import entities as entity_routes
from src.api.routes import observability_ui
from src.api.schemas import WorldStateResponse, EntityPageResponse, EntityDetailResponse
from src.config.profiles import RuntimeProfile

logger = logging.getLogger(__name__)

def create_v2_app(
    profile: RuntimeProfile,
    seed: Optional[int] = None,
    world_id: Optional[str] = None,
) -> FastAPI:
    """Build and return the V2 FastAPI application.

    seed/world_id are optional overrides for V2EngineManager's own defaults --
    None (the default here, matching every existing caller) means "use V2EngineManager's class
    default for that field," so this stays a fully backward-compatible signature extension.
    """
    configure_api_keys(profile)
    configure_admission_control(profile)

    manager_kwargs: Dict[str, Any] = {}
    if seed is not None:
        manager_kwargs["seed"] = seed
    if world_id is not None:
        manager_kwargs["world_id"] = world_id

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        manager = V2EngineManager(profile, **manager_kwargs)
        set_engine_manager(manager)
        manager.start()

        from src.content.repository import CatalogRepository
        catalog = CatalogRepository()
        catalog.load_all()
        set_catalog_repository(catalog)

        # G2 fix: wire quality hub into dependency container after kernel is ready
        _k = manager.kernel
        if _k is not None and _k.quality_hub is not None:
            set_quality_hub(_k.quality_hub)
            set_quality_persistence(getattr(_k.quality_hub, "_persistence", None))

        # Register LiveAnomalyCounter as subscriber to publisher
        from src.observability.live.event_publisher import LiveEventPublisher
        from src.observability.live.anomaly_counter import LiveAnomalyCounter
        publisher = LiveEventPublisher.get_instance()
        counter = LiveAnomalyCounter.get_instance()
        publisher.register(counter)
        
        logger.info("V2 API server started.")
        yield
        
        try:
            publisher.unregister(counter)
        except Exception:
            pass
        LiveAnomalyCounter.reset_instance()
        
        # Write quality_report.json at run-end alongside other run artifacts
        from src.api.dependencies import get_quality_hub, get_quality_persistence
        _hub = get_quality_hub()
        _persistence = get_quality_persistence()
        if _hub is not None and _persistence is not None:
            try:
                _report = _hub.get_quality_report()
                _persistence.write_report(_report)
            except Exception as _exc:
                logger.warning("quality report write failed at shutdown: %s", _exc)

        manager.stop()
        logger.info("V2 API server shutting down.")

    app = FastAPI(
        title="V2 RPG Simulation Engine",
        version="2.0.0",
        lifespan=lifespan,
    )

    # allow_credentials intentionally omitted (defaults False): the CORS spec forbids combining
    # a wildcard origin with credentialed requests, and no real caller sends credentials today
    # (frontend/'s fetch() calls carry no `credentials` option, and dev traffic is proxied
    # same-origin) -- see TCK-20260819-HOTFIX-CORS-WILDCARD-CREDENTIALS-MISCONFIG.
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.add_middleware(GZipMiddleware, minimum_size=512)
    app.add_middleware(RequestDurationMiddleware)  # outermost: times the whole stack (issue #622 R2)

    from src.api.ws import stream
    app.include_router(stream.router, prefix="/api/v1", dependencies=[Depends(require_api_key_ws), Depends(require_admission_ws)])

    from src.api.routes import history
    app.include_router(history.router, prefix="/api/v1", dependencies=[Depends(require_admission)])

    from src.api.routes import search
    app.include_router(search.router, prefix="/api/v1", dependencies=[Depends(require_admission)])

    # TCK-20260912-BEHAVIOR-ANALYTICS-PIPELINE-NEVER-STARTED-API-INERT: gated off by default --
    # BehaviorWorker is never started, so every real request against these 7 endpoints returns
    # empty/404 today. Not registering the router at all makes that honest (404 = "not exposed")
    # rather than misleading (404/empty = "exposed but its data source was never populated").
    if profile.enable_behavior_analytics_api:
        from src.api.routes import behavior
        app.include_router(behavior.router, prefix="/api/v1", dependencies=[Depends(require_admission)])

    from src.api.routes import decisions
    app.include_router(decisions.router, prefix="/api/v1", dependencies=[Depends(require_admission)])
    app.include_router(entity_routes.router, prefix="/api/v1", dependencies=[Depends(require_admission)])

    from src.api.routes import scenarios
    app.include_router(scenarios.router, prefix="/api/v1", dependencies=[Depends(require_admission)])

    # TCK-20260912-CAMPAIGN-CHRONICLE-API-REGISTRY-NEVER-POPULATED-IN-PRODUCTION: gated off by
    # default -- CampaignOrchestrator/ChronicleCompiler never populate these registries in
    # production, so every real request against these endpoints returns empty/404 today. Same
    # honest-404-vs-misleading-404 reasoning as the behavior-analytics gate above.
    if profile.enable_campaign_chronicle_api:
        from src.api.routes import campaigns
        app.include_router(campaigns.router, prefix="/api/v1", dependencies=[Depends(require_admission)])

        from src.api.routes import chronicle
        app.include_router(chronicle.router, prefix="/api/v1", dependencies=[Depends(require_admission)])

    from src.api.routes import economy
    app.include_router(economy.router, prefix="/api/v1", dependencies=[Depends(require_admission)])

    from src.api.routes import manifest
    app.include_router(manifest.router, prefix="/api/v1", dependencies=[Depends(require_admission)])

    from src.api.routes import metadata
    app.include_router(metadata.router, prefix="/api/v1", dependencies=[Depends(require_admission)])

    from src.api.routes import map as map_routes
    app.include_router(map_routes.router, prefix="/api/v1", dependencies=[Depends(require_admission)])

    from src.api.routes import static as static_routes
    app.include_router(static_routes.router, prefix="/api/v1", dependencies=[Depends(require_admission)])

    from src.api.routes import stats as stats_routes
    app.include_router(stats_routes.router, prefix="/api/v1", dependencies=[Depends(require_admission)])

    from src.simulation_quality.api import routes as quality_routes
    app.include_router(quality_routes.router, prefix="/api/v1", dependencies=[Depends(require_admission)])

    from prometheus_client import generate_latest, CONTENT_TYPE_LATEST
    from fastapi import Response

    @app.get("/metrics", dependencies=[Depends(require_admission)])
    async def get_metrics(manager: V2EngineManager = Depends(get_engine_manager)):
        """Expose Prometheus text format metrics from V2EngineManager."""
        try:
            data = generate_latest(manager.metrics_registry)
            return Response(content=data, media_type=CONTENT_TYPE_LATEST)
        except Exception as e:
            logger.exception("Failed to generate metrics")
            return Response(content=f"# Error: {e}", status_code=500, media_type="text/plain")

    @app.get("/health", response_model=Dict[str, Any])
    async def health_check(manager: V2EngineManager = Depends(get_engine_manager)):
        payload = manager.get_health_status()
        status_code = 503 if payload["status"] == "unhealthy" else 200
        return JSONResponse(content=payload, status_code=status_code)

    @app.get("/api/v1/observability/live/status", dependencies=[Depends(require_admission)])
    async def get_live_status():
        try:
            manager = get_engine_manager()
        except RuntimeError:
            manager = None
            
        from src.observability.live.snapshot_provider import LiveSnapshotProvider
        return LiveSnapshotProvider.get_status(manager)

    @app.get("/api/v1/observability/live/snapshot", dependencies=[Depends(require_admission)])
    async def get_live_snapshot():
        try:
            manager = get_engine_manager()
        except RuntimeError:
            manager = None
            
        from src.observability.live.snapshot_provider import LiveSnapshotProvider
        return LiveSnapshotProvider.get_snapshot(manager)

    @app.get("/api/v1/observability/live/entities/{entity_id}", dependencies=[Depends(require_admission)])
    async def inspect_live_entity(entity_id: int, timeline_limit: int = 20):
        try:
            manager = get_engine_manager()
        except RuntimeError:
            manager = None
            
        from src.observability.live.entity_inspector import EntityInspector
        snapshot = EntityInspector.inspect_entity(manager, entity_id, timeline_limit)
        if not snapshot.exists:
            from fastapi import HTTPException
            raise HTTPException(status_code=404, detail=f"Entity {entity_id} not found or engine idle")
        return snapshot

    @app.get("/api/v1/state", response_model=Dict[str, Any], dependencies=[Depends(require_admission)])
    async def get_state(manager: V2EngineManager = Depends(get_engine_manager)):
        state = manager.get_state()
        if not state:
            return {"error": "State not available"}
        return state

    @app.get("/api/v1/inspect", response_model=Dict[str, Any], dependencies=[Depends(require_admission)])
    async def inspect_state(manager: V2EngineManager = Depends(get_engine_manager)):
        """Complete state view (Deprecated: Use granular endpoints for large worlds)."""
        snapshot = manager.get_full_snapshot()
        if not snapshot:
            return {"error": "State not available"}
        return snapshot

    @app.get("/api/v1/entities", response_model=Dict[str, Any], dependencies=[Depends(require_admission)])
    async def get_entities(
        offset: int = 0, 
        limit: int = 100, 
        manager: V2EngineManager = Depends(get_engine_manager)
    ):
        """Paged entity SUMMARIES: bounded fields plus counts, independent of an entity's age. The full model is GET /entities/{id}; quest history is paged at /entities/{id}/quests."""
        return manager.get_entities_paged(offset, limit)

    @app.get("/api/v1/entities/{entity_id}", response_model=Optional[Dict[str, Any]], dependencies=[Depends(require_admission)])
    async def get_entity(
        entity_id: int, 
        manager: V2EngineManager = Depends(get_engine_manager)
    ):
        """Single entity lookup."""
        entity = manager.get_entity(entity_id)
        if not entity:
            return {"error": f"Entity {entity_id} not found"}
        return entity

    @app.post("/api/v1/control/pause", response_model=Dict[str, Any], dependencies=[Depends(require_admission)])
    async def pause_sim(manager: V2EngineManager = Depends(get_engine_manager)):
        manager.pause()
        return {"status": "paused"}

    @app.post("/api/v1/control/resume", response_model=Dict[str, Any], dependencies=[Depends(require_admission)])
    async def resume_sim(manager: V2EngineManager = Depends(get_engine_manager)):
        manager.resume()
        return {"status": "resumed"}

    @app.post("/api/v1/test/publish_event", response_model=Dict[str, Any], dependencies=[Depends(require_admission)])
    async def publish_test_event(event_data: dict):
        from src.observability.events import SimulationEvent
        from src.observability.live.event_publisher import LiveEventPublisher
        
        if "event_type" not in event_data:
            event_data["event_type"] = "test_event"
        if "event_category" not in event_data:
            event_data["event_category"] = "movement"
        if "severity" not in event_data:
            event_data["severity"] = "INFO"
        if "source_system" not in event_data:
            event_data["source_system"] = "test"
        if "message" not in event_data:
            event_data["message"] = "test message"
        if "tick" not in event_data:
            event_data["tick"] = 0
            
        event = SimulationEvent(**event_data)
        LiveEventPublisher.get_instance().publish(event)
        return {"status": "published"}

    @app.get("/api/v1/observability/live/health", response_model=Dict[str, Any], dependencies=[Depends(require_admission)])
    async def get_live_health():
        try:
            manager = get_engine_manager()
        except RuntimeError:
            manager = None
            
        from src.observability.live.anomaly_counter import LiveAnomalyCounter
        counter = LiveAnomalyCounter.get_instance()
        return counter.calculate_health(manager)

    @app.get("/api/v1/observability/live/stream-health", response_model=Dict[str, Any], dependencies=[Depends(require_admission)])
    async def get_stream_health():
        from src.observability.stream.factory import get_event_stream_adapter
        adapter = get_event_stream_adapter()
        return adapter.health()

    @app.get("/api/v1/observability/history/runs/{run_id}/report", dependencies=[Depends(require_admission)])
    async def get_run_report(run_id: str):
        """Helper endpoint to dynamically retrieve compile run report markdown."""
        try:
            import os
            from fastapi import Response
            from src.observability.reporting.history_query import sanitize_id
            from src.observability.reporting.artifact_repository import RunArtifactRepository
            
            run_id = sanitize_id(run_id)
            repo = RunArtifactRepository()
            report_path = repo.resolve_path(run_id, "report_md")
            if os.path.exists(report_path):
                with open(report_path, "r", encoding="utf-8") as f:
                    return Response(content=f.read(), media_type="text/markdown")
            else:
                return Response(
                    content="# Executive Summary Run Report\n\nNo compiled markdown report found for this run.",
                    media_type="text/markdown"
                )
        except Exception as e:
            from fastapi import Response
            return Response(content=f"# Error\n\nFailed to load run report: {e}", media_type="text/markdown")

    # The dashboard page and its two redirects: registered last, as the inline routes were.
    app.include_router(observability_ui.router)

    return app
