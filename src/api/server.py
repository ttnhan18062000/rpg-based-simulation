"""The V2 FastAPI application factory.

`create_v2_app` wires authentication, admission control, the engine lifespan, the middleware stack and the routers.
The routes live in `src/api/routes/` (and `src/api/ws/`, `src/simulation_quality/api/`); registration order below is
behaviour, because FastAPI serves the first route that matches, and `tests/api/test_server_http_surface_characterization.py`
pins it.
"""
from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from typing import Any, AsyncIterator, Dict, Optional

from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware

from src.api.admission_control import (
    configure_admission_control,
    require_admission,
    require_admission_ws,
)
from src.api.auth import configure_api_keys, require_api_key_ws
from src.api.cors import cors_origins_from_env
from src.api.dependencies import (
    get_quality_hub,
    get_quality_persistence,
    set_catalog_repository,
    set_engine_manager,
    set_quality_hub,
    set_quality_persistence,
)
from src.api.engine_manager import V2EngineManager
from src.api.http_metrics import RequestDurationMiddleware
from src.api.routes import (
    behavior,
    campaigns,
    chronicle,
    decisions,
    economy,
    engine_control,
    engine_probes,
    engine_state,
    history,
    live_health,
    live_observability,
    manifest,
    metadata,
    observability_ui,
    run_reports,
    scenarios,
    search,
)
from src.api.routes import entities as entity_routes
from src.api.routes import map as map_routes
from src.api.routes import static as static_routes
from src.api.routes import stats as stats_routes
from src.api.ws import stream
from src.config.profiles import RuntimeProfile
from src.content.repository import CatalogRepository
from src.observability.live.anomaly_counter import LiveAnomalyCounter
from src.observability.live.event_publisher import LiveEventPublisher
from src.simulation_quality.api import routes as quality_routes

logger = logging.getLogger(__name__)


def _register_routers(app: FastAPI, profile: RuntimeProfile) -> None:
    """Include every router in the order the app has always registered them."""
    admitted = [Depends(require_admission)]
    app.include_router(stream.router, prefix="/api/v1", dependencies=[Depends(require_api_key_ws), Depends(require_admission_ws)])
    app.include_router(history.router, prefix="/api/v1", dependencies=admitted)
    app.include_router(search.router, prefix="/api/v1", dependencies=admitted)

    # TCK-20260912-BEHAVIOR-ANALYTICS-PIPELINE-NEVER-STARTED-API-INERT: gated off by default --
    # BehaviorWorker is never started, so every real request against these 7 endpoints returns
    # empty/404 today. Not registering the router at all makes that honest (404 = "not exposed")
    # rather than misleading (404/empty = "exposed but its data source was never populated").
    if profile.enable_behavior_analytics_api:
        app.include_router(behavior.router, prefix="/api/v1", dependencies=admitted)

    app.include_router(decisions.router, prefix="/api/v1", dependencies=admitted)
    app.include_router(entity_routes.router, prefix="/api/v1", dependencies=admitted)
    app.include_router(scenarios.router, prefix="/api/v1", dependencies=admitted)

    # TCK-20260912-CAMPAIGN-CHRONICLE-API-REGISTRY-NEVER-POPULATED-IN-PRODUCTION: gated off by
    # default -- CampaignOrchestrator/ChronicleCompiler never populate these registries in
    # production, so every real request against these endpoints returns empty/404 today. Same
    # honest-404-vs-misleading-404 reasoning as the behavior-analytics gate above.
    if profile.enable_campaign_chronicle_api:
        app.include_router(campaigns.router, prefix="/api/v1", dependencies=admitted)
        app.include_router(chronicle.router, prefix="/api/v1", dependencies=admitted)

    app.include_router(economy.router, prefix="/api/v1", dependencies=admitted)
    app.include_router(manifest.router, prefix="/api/v1", dependencies=admitted)
    app.include_router(metadata.router, prefix="/api/v1", dependencies=admitted)
    app.include_router(map_routes.router, prefix="/api/v1", dependencies=admitted)
    app.include_router(static_routes.router, prefix="/api/v1", dependencies=admitted)
    app.include_router(stats_routes.router, prefix="/api/v1", dependencies=admitted)
    app.include_router(quality_routes.router, prefix="/api/v1", dependencies=admitted)

    # Routes that carry their own full path; the observability page and its redirects come last.
    app.include_router(engine_probes.router)
    app.include_router(live_observability.router)
    app.include_router(engine_state.router)
    app.include_router(engine_control.router)
    app.include_router(live_health.router)
    app.include_router(run_reports.router)
    app.include_router(observability_ui.router)


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

        catalog = CatalogRepository()
        catalog.load_all()
        set_catalog_repository(catalog)

        # G2 fix: wire quality hub into dependency container after kernel is ready
        _k = manager.kernel
        if _k is not None and _k.quality_hub is not None:
            set_quality_hub(_k.quality_hub)
            set_quality_persistence(getattr(_k.quality_hub, "_persistence", None))

        # Register LiveAnomalyCounter as subscriber to publisher
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

    # allow_credentials intentionally omitted (defaults False): no real caller sends credentials today
    # (frontend/'s fetch() calls carry no `credentials` option, and dev traffic is proxied
    # same-origin) -- see TCK-20260819-HOTFIX-CORS-WILDCARD-CREDENTIALS-MISCONFIG.
    app.add_middleware(
        CORSMiddleware,
        allow_origins=cors_origins_from_env(),
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.add_middleware(GZipMiddleware, minimum_size=512)
    app.add_middleware(RequestDurationMiddleware)  # outermost: times the whole stack (issue #622 R2)

    _register_routers(app, profile)

    return app
