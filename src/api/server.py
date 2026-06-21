from __future__ import annotations
import time
import logging
from contextlib import asynccontextmanager
from typing import AsyncIterator

from fastapi import FastAPI, Request, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import HTMLResponse, RedirectResponse

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

    from src.api.routes import history
    app.include_router(history.router, prefix="/api/v1")

    from src.api.routes import search
    app.include_router(search.router, prefix="/api/v1")

    from src.api.routes import behavior
    app.include_router(behavior.router, prefix="/api/v1")

    from src.api.routes import decisions
    app.include_router(decisions.router, prefix="/api/v1")

    from src.api.routes import scenarios
    app.include_router(scenarios.router, prefix="/api/v1")

    from prometheus_client import generate_latest, CONTENT_TYPE_LATEST
    from fastapi import Response

    @app.get("/metrics")
    async def get_metrics(manager: V2EngineManager = Depends(get_engine_manager)):
        """Expose Prometheus text format metrics from V2EngineManager."""
        try:
            data = generate_latest(manager.metrics_registry)
            return Response(content=data, media_type=CONTENT_TYPE_LATEST)
        except Exception as e:
            logger.exception("Failed to generate metrics")
            return Response(content=f"# Error: {e}", status_code=500, media_type="text/plain")

    @app.get("/health")
    async def health_check():
        return {"status": "ok", "version": "v2", "timestamp": time.time()}

    @app.get("/api/v1/observability/live/status")
    async def get_live_status():
        try:
            manager = get_engine_manager()
        except RuntimeError:
            manager = None
            
        from src.observability.live.snapshot_provider import LiveSnapshotProvider
        return LiveSnapshotProvider.get_status(manager)

    @app.get("/api/v1/observability/live/snapshot")
    async def get_live_snapshot():
        try:
            manager = get_engine_manager()
        except RuntimeError:
            manager = None
            
        from src.observability.live.snapshot_provider import LiveSnapshotProvider
        return LiveSnapshotProvider.get_snapshot(manager)

    @app.get("/api/v1/observability/live/entities/{entity_id}")
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

    @app.get("/api/v1/state")
    async def get_state(manager: V2EngineManager = Depends(get_engine_manager)):
        state = manager.get_state()
        if not state:
            return {"error": "State not available"}
        return state

    @app.get("/api/v1/inspect")
    async def inspect_state(manager: V2EngineManager = Depends(get_engine_manager)):
        """Complete state view (Deprecated: Use granular endpoints for large worlds)."""
        snapshot = manager.get_full_snapshot()
        if not snapshot:
            return {"error": "State not available"}
        return snapshot

    @app.get("/api/v1/entities")
    async def get_entities(
        offset: int = 0, 
        limit: int = 100, 
        manager: V2EngineManager = Depends(get_engine_manager)
    ):
        """Paged entity retrieval."""
        return manager.get_entities_paged(offset, limit)

    @app.get("/api/v1/entities/{entity_id}")
    async def get_entity(
        entity_id: int, 
        manager: V2EngineManager = Depends(get_engine_manager)
    ):
        """Single entity lookup."""
        entity = manager.get_entity(entity_id)
        if not entity:
            return {"error": f"Entity {entity_id} not found"}
        return entity

    @app.post("/api/v1/control/pause")
    async def pause_sim(manager: V2EngineManager = Depends(get_engine_manager)):
        manager.pause()
        return {"status": "paused"}

    @app.post("/api/v1/control/resume")
    async def resume_sim(manager: V2EngineManager = Depends(get_engine_manager)):
        manager.resume()
        return {"status": "resumed"}

    @app.post("/api/v1/test/publish_event")
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

    @app.get("/api/v1/observability/live/health")
    async def get_live_health():
        try:
            manager = get_engine_manager()
        except RuntimeError:
            manager = None
            
        from src.observability.live.anomaly_counter import LiveAnomalyCounter
        counter = LiveAnomalyCounter.get_instance()
        return counter.calculate_health(manager)

    @app.get("/api/v1/observability/live/stream-health")
    async def get_stream_health():
        from src.observability.stream.factory import get_event_stream_adapter
        adapter = get_event_stream_adapter()
        return adapter.health()

    @app.get("/api/v1/observability/history/runs/{run_id}/report")
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

    @app.get("/api/v1/observability/ui", response_class=HTMLResponse)
    async def get_observability_ui():
        html_content = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>V2 Simulation Live Observatory Dashboard</title>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap" rel="stylesheet">
    <script src="https://cdn.jsdelivr.net/npm/marked/marked.min.js"></script>
    <style>
        * {
            box-sizing: border-box;
            margin: 0;
            padding: 0;
        }
        body {
            background: linear-gradient(135deg, #070a13 0%, #0f172a 100%);
            color: #F3F4F6;
            font-family: 'Outfit', sans-serif;
            min-height: 100vh;
            overflow-x: hidden;
            display: flex;
            flex-direction: column;
        }
        
        /* Glassmorphism Header */
        header {
            background: rgba(15, 23, 42, 0.7);
            backdrop-filter: blur(12px);
            -webkit-backdrop-filter: blur(12px);
            border-bottom: 1px solid rgba(255, 255, 255, 0.08);
            padding: 1rem 2rem;
            display: flex;
            justify-content: space-between;
            align-items: center;
            position: sticky;
            top: 0;
            z-index: 50;
            box-shadow: 0 4px 30px rgba(0, 0, 0, 0.4);
        }
        .logo-container {
            display: flex;
            align-items: center;
            gap: 0.75rem;
        }
        .logo-dot {
            width: 12px;
            height: 12px;
            border-radius: 50%;
            background-color: #10B981;
            box-shadow: 0 0 12px #10B981;
            animation: pulse 2s infinite;
        }
        @keyframes pulse {
            0% { transform: scale(0.9); opacity: 0.6; }
            50% { transform: scale(1.1); opacity: 1; box-shadow: 0 0 18px #10B981; }
            100% { transform: scale(0.9); opacity: 0.6; }
        }
        .logo-text h1 {
            font-size: 1.15rem;
            font-weight: 700;
            letter-spacing: 0.08em;
            background: linear-gradient(to right, #60a5fa, #34d399);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }
        .logo-text p {
            font-size: 0.7rem;
            color: #9CA3AF;
            letter-spacing: 0.05em;
        }
        
        /* Navigation Tabs Bar */
        .tab-nav {
            display: flex;
            gap: 0.5rem;
            background: rgba(15, 23, 42, 0.4);
            border: 1px solid rgba(255, 255, 255, 0.05);
            border-radius: 8px;
            padding: 0.25rem;
        }
        .nav-tab {
            background: transparent;
            border: none;
            color: #9CA3AF;
            padding: 0.5rem 1rem;
            border-radius: 6px;
            font-size: 0.85rem;
            font-weight: 500;
            cursor: pointer;
            transition: all 0.2s ease;
            display: flex;
            align-items: center;
            gap: 0.4rem;
        }
        .nav-tab:hover {
            color: #F3F4F6;
            background: rgba(255, 255, 255, 0.03);
        }
        .nav-tab.active {
            background: rgba(59, 130, 246, 0.15);
            color: #60A5FA;
            border: 1px solid rgba(59, 130, 246, 0.25);
            font-weight: 600;
            box-shadow: 0 0 8px rgba(59, 130, 246, 0.1);
        }
        
        .connection-status {
            font-size: 0.75rem;
            display: flex;
            align-items: center;
            gap: 0.4rem;
        }
        .conn-dot {
            width: 8px;
            height: 8px;
            border-radius: 50%;
            background: #EF4444;
        }
        .conn-dot.connected {
            background: #10B981;
            box-shadow: 0 0 8px #10B981;
        }
        
        /* Main Layout Content Area */
        main {
            flex: 1;
            padding: 1.5rem;
            max-width: 1800px;
            margin: 0 auto;
            width: 100%;
        }
        
        .view-container {
            display: none;
            animation: fadeIn 0.2s ease;
        }
        .view-container.active {
            display: block;
        }
        @keyframes fadeIn {
            from { opacity: 0; transform: translateY(5px); }
            to { opacity: 1; transform: translateY(0); }
        }
        
        /* Glassmorphic card styling */
        .card {
            background: rgba(15, 23, 42, 0.6);
            backdrop-filter: blur(8px);
            -webkit-backdrop-filter: blur(8px);
            border: 1px solid rgba(255, 255, 255, 0.06);
            border-radius: 12px;
            padding: 1.25rem;
            box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.25);
            display: flex;
            flex-direction: column;
            gap: 1rem;
            transition: border-color 0.2s ease;
        }
        .card:hover {
            border-color: rgba(59, 130, 246, 0.15);
        }
        .card-title {
            font-size: 0.9rem;
            font-weight: 600;
            color: #E5E7EB;
            display: flex;
            align-items: center;
            justify-content: space-between;
            border-bottom: 1px solid rgba(255, 255, 255, 0.05);
            padding-bottom: 0.5rem;
            letter-spacing: 0.03em;
        }
        .card-title-icon {
            color: #3B82F6;
        }
        
        /* Grid Layouts */
        .grid-two-col {
            display: grid;
            grid-template-columns: 450px 1fr;
            gap: 1.5rem;
        }
        .grid-split-pane {
            display: grid;
            grid-template-columns: 380px 1fr;
            gap: 1.5rem;
            height: calc(100vh - 150px);
            align-items: stretch;
        }
        
        /* Stats dashboard section */
        .stats-grid {
            display: grid;
            grid-template-columns: repeat(2, 1fr);
            gap: 0.75rem;
        }
        .stat-box {
            background: rgba(31, 41, 55, 0.35);
            border: 1px solid rgba(255, 255, 255, 0.04);
            border-radius: 8px;
            padding: 0.65rem 0.85rem;
        }
        .stat-label {
            font-size: 0.7rem;
            color: #9CA3AF;
            margin-bottom: 0.2rem;
            text-transform: uppercase;
            letter-spacing: 0.02em;
        }
        .stat-value {
            font-size: 1.1rem;
            font-weight: 700;
            font-family: 'JetBrains Mono', monospace;
            color: #F9FAFB;
        }
        
        /* Control Buttons */
        .btn-blue, .btn-secondary {
            background: #2563EB;
            color: white;
            border: none;
            border-radius: 6px;
            padding: 0.5rem 1rem;
            font-weight: 600;
            font-size: 0.825rem;
            cursor: pointer;
            transition: all 0.15s ease;
            display: inline-flex;
            align-items: center;
            justify-content: center;
            gap: 0.3rem;
        }
        .btn-blue:hover {
            background: #1D4ED8;
            box-shadow: 0 0 10px rgba(37, 99, 235, 0.3);
        }
        .btn-secondary {
            background: rgba(31, 41, 55, 0.6);
            border: 1px solid rgba(255, 255, 255, 0.08);
            color: #D1D5DB;
        }
        .btn-secondary:hover {
            background: rgba(31, 41, 55, 0.8);
            color: white;
        }
        .btn-xs {
            background: rgba(59, 130, 246, 0.1);
            border: 1px solid rgba(59, 130, 246, 0.2);
            color: #60A5FA;
            padding: 0.2rem 0.4rem;
            border-radius: 4px;
            font-size: 0.7rem;
            cursor: pointer;
            font-weight: 500;
        }
        .btn-xs:hover {
            background: rgba(59, 130, 246, 0.2);
            color: white;
        }
        
        /* Health Status box */
        .health-card {
            background: linear-gradient(135deg, rgba(16, 185, 129, 0.03) 0%, rgba(15, 23, 42, 0.6) 100%);
            border-left: 4px solid #10B981;
        }
        .health-card.warning {
            background: linear-gradient(135deg, rgba(245, 158, 11, 0.03) 0%, rgba(15, 23, 42, 0.6) 100%);
            border-left: 4px solid #F59E0B;
        }
        .health-card.degraded {
            background: linear-gradient(135deg, rgba(239, 68, 68, 0.03) 0%, rgba(15, 23, 42, 0.6) 100%);
            border-left: 4px solid #EF4444;
        }
        .health-card.critical {
            background: linear-gradient(135deg, rgba(220, 38, 38, 0.04) 0%, rgba(15, 23, 42, 0.6) 100%);
            border-left: 4px solid #DC2626;
        }
        .health-status-badge {
            display: inline-flex;
            align-items: center;
            padding: 0.25rem 0.6rem;
            border-radius: 9999px;
            font-size: 0.7rem;
            font-weight: 700;
            letter-spacing: 0.04em;
        }
        .badge-healthy { background: rgba(16, 185, 129, 0.15); color: #34D399; border: 1px solid rgba(16, 185, 129, 0.25); }
        .badge-warning { background: rgba(245, 158, 11, 0.15); color: #FBBF24; border: 1px solid rgba(245, 158, 11, 0.25); }
        .badge-degraded { background: rgba(239, 68, 68, 0.15); color: #FCA5A5; border: 1px solid rgba(239, 68, 68, 0.25); }
        .badge-critical { background: rgba(220, 38, 38, 0.15); color: #F87171; border: 1px solid rgba(220, 38, 38, 0.25); }
        .badge-unknown { background: rgba(107, 114, 128, 0.15); color: #D1D5DB; border: 1px solid rgba(107, 114, 128, 0.25); }
        
        .health-reasons {
            font-size: 0.775rem;
            color: #D1D5DB;
            padding-left: 1.1rem;
            line-height: 1.4;
        }
        .health-reasons li {
            margin-bottom: 0.25rem;
        }
        
        /* Anomaly list grid */
        .anomalies-list {
            display: grid;
            grid-template-columns: repeat(2, 1fr);
            gap: 0.75rem;
        }
        .anomaly-item {
            background: rgba(31, 41, 55, 0.35);
            border: 1px solid rgba(255, 255, 255, 0.03);
            border-radius: 8px;
            padding: 0.65rem 0.85rem;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        .anomaly-label {
            font-size: 0.75rem;
            color: #9CA3AF;
        }
        .anomaly-count {
            font-size: 1rem;
            font-weight: 700;
            font-family: 'JetBrains Mono', monospace;
        }
        .anomaly-count.has-count {
            color: #EF4444;
            text-shadow: 0 0 6px rgba(239, 68, 68, 0.3);
        }
        .anomaly-count.zero {
            color: #9CA3AF;
        }
        
        /* Inspector / Search Input Form */
        .input-dark, .select-dark {
            background: rgba(15, 23, 42, 0.8);
            border: 1px solid rgba(255, 255, 255, 0.1);
            border-radius: 6px;
            padding: 0.45rem 0.75rem;
            color: #F9FAFB;
            font-family: inherit;
            font-size: 0.85rem;
            outline: none;
            transition: all 0.15s;
        }
        .input-dark:focus, .select-dark:focus {
            border-color: #3B82F6;
            box-shadow: 0 0 0 2px rgba(59, 130, 246, 0.15);
        }
        .select-dark {
            cursor: pointer;
        }
        .inspector-search {
            display: flex;
            gap: 0.5rem;
        }
        .inspector-results {
            background: rgba(15, 23, 42, 0.3);
            border: 1px solid rgba(255, 255, 255, 0.04);
            border-radius: 8px;
            padding: 0.75rem;
            min-height: 80px;
            font-size: 0.8rem;
            display: flex;
            flex-direction: column;
            gap: 0.5rem;
        }
        .inspector-grid {
            display: grid;
            grid-template-columns: repeat(2, 1fr);
            gap: 0.5rem;
        }
        .inspector-val {
            font-family: 'JetBrains Mono', monospace;
            color: #F3F4F6;
        }
        .inspector-empty {
            color: #9CA3AF;
            text-align: center;
            padding: 1rem 0;
            font-style: italic;
        }
        .timeline-item-ui {
            padding: 0.3rem 0.45rem;
            background: rgba(255, 255, 255, 0.02);
            border-left: 2px solid #3B82F6;
            margin-bottom: 0.2rem;
            font-family: 'JetBrains Mono', monospace;
            font-size: 0.7rem;
        }
        
        /* Event Stream Terminal */
        .event-stream-container {
            display: flex;
            flex-direction: column;
            gap: 1rem;
            height: calc(100vh - 150px);
        }
        .filter-bar {
            background: rgba(15, 23, 42, 0.5);
            border: 1px solid rgba(255, 255, 255, 0.05);
            border-radius: 8px;
            padding: 0.5rem 1rem;
            display: flex;
            justify-content: space-between;
            align-items: center;
            gap: 1rem;
            flex-wrap: wrap;
        }
        .filter-group {
            display: flex;
            align-items: center;
            gap: 0.4rem;
        }
        .filter-label {
            font-size: 0.7rem;
            color: #9CA3AF;
            text-transform: uppercase;
            letter-spacing: 0.05em;
        }
        .filter-pill {
            background: rgba(31, 41, 55, 0.5);
            border: 1px solid rgba(255, 255, 255, 0.08);
            color: #9CA3AF;
            padding: 0.2rem 0.5rem;
            border-radius: 9999px;
            font-size: 0.7rem;
            cursor: pointer;
            transition: all 0.15s ease;
        }
        .filter-pill:hover {
            color: #F3F4F6;
            border-color: rgba(255, 255, 255, 0.2);
        }
        .filter-pill.active {
            background: rgba(59, 130, 246, 0.15);
            color: #60A5FA;
            border-color: rgba(59, 130, 246, 0.3);
            font-weight: 600;
        }
        .terminal {
            background: #04060d;
            border: 1px solid rgba(255, 255, 255, 0.05);
            border-radius: 10px;
            flex: 1;
            display: flex;
            flex-direction: column;
            overflow: hidden;
            box-shadow: inset 0 2px 8px rgba(0,0,0,0.8);
        }
        .terminal-header {
            background: rgba(15, 23, 42, 0.8);
            border-bottom: 1px solid rgba(255, 255, 255, 0.05);
            padding: 0.4rem 1rem;
            display: flex;
            justify-content: space-between;
            align-items: center;
            font-size: 0.7rem;
            color: #9CA3AF;
        }
        .terminal-body {
            flex: 1;
            padding: 0.75rem;
            overflow-y: auto;
            font-family: 'JetBrains Mono', monospace;
            font-size: 0.8rem;
            display: flex;
            flex-direction: column;
            gap: 0.3rem;
        }
        .event-line {
            display: flex;
            align-items: flex-start;
            gap: 0.5rem;
            padding: 0.25rem 0.4rem;
            border-radius: 4px;
            transition: background 0.1s ease;
            cursor: pointer;
            line-height: 1.35;
        }
        .event-line:hover {
            background: rgba(255, 255, 255, 0.03);
        }
        .event-time {
            color: #4B5563;
            font-size: 0.7rem;
            flex-shrink: 0;
            width: 75px;
        }
        .event-tick-badge {
            color: #3b82f6;
            background: rgba(59, 130, 246, 0.06);
            border: 1px solid rgba(59, 130, 246, 0.12);
            padding: 0.02rem 0.2rem;
            border-radius: 3px;
            font-size: 0.65rem;
            flex-shrink: 0;
        }
        .event-cat-badge {
            padding: 0.02rem 0.3rem;
            border-radius: 3px;
            font-size: 0.65rem;
            font-weight: 600;
            text-transform: uppercase;
            flex-shrink: 0;
        }
        .cat-movement { background: rgba(59, 130, 246, 0.1); color: #60A5FA; border: 1px solid rgba(59, 130, 246, 0.2); }
        .cat-combat { background: rgba(239, 68, 68, 0.1); color: #FCA5A5; border: 1px solid rgba(239, 68, 68, 0.2); }
        .cat-resource { background: rgba(16, 185, 129, 0.1); color: #34D399; border: 1px solid rgba(16, 185, 129, 0.2); }
        .cat-economy { background: rgba(245, 158, 11, 0.1); color: #FBBF24; border: 1px solid rgba(245, 158, 11, 0.2); }
        .cat-hard_law { background: rgba(220, 38, 38, 0.12); color: #F87171; border: 1px solid rgba(220, 38, 38, 0.25); font-weight: 700; }
        .cat-anomaly { background: rgba(139, 92, 246, 0.12); color: #C084FC; border: 1px solid rgba(139, 92, 246, 0.25); font-weight: 700; }
        .cat-other { background: rgba(107, 114, 128, 0.08); color: #D1D5DB; border: 1px solid rgba(107, 114, 128, 0.15); }
        .event-msg {
            color: #E5E7EB;
            word-break: break-word;
        }
        .event-sev-err { border-left: 2px solid #EF4444; background: rgba(239, 68, 68, 0.02); }
        .event-sev-err .event-msg { color: #FCA5A5; }
        .event-sev-crit { border-left: 3px solid #DC2626; background: rgba(220, 38, 38, 0.04); font-weight: 500; }
        .event-sev-crit .event-msg { color: #FECACA; }
        .event-sev-warn { border-left: 2px solid #F59E0B; }
        .event-sev-warn .event-msg { color: #FDE68A; }
        
        /* Split Pane / Listing Columns */
        .listing-sidebar {
            display: flex;
            flex-direction: column;
            gap: 1rem;
            background: rgba(15, 23, 42, 0.3);
            border: 1px solid rgba(255, 255, 255, 0.05);
            border-radius: 10px;
            padding: 1rem;
            overflow-y: auto;
        }
        .listing-header {
            font-size: 0.8rem;
            color: #9CA3AF;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.05em;
        }
        .run-card-item {
            background: rgba(31, 41, 55, 0.3);
            border: 1px solid rgba(255, 255, 255, 0.04);
            border-radius: 8px;
            padding: 0.75rem;
            cursor: pointer;
            transition: all 0.15s ease;
            display: flex;
            flex-direction: column;
            gap: 0.4rem;
        }
        .run-card-item:hover {
            background: rgba(31, 41, 55, 0.45);
            border-color: rgba(255, 255, 255, 0.15);
        }
        .run-card-item.active {
            background: rgba(59, 130, 246, 0.08);
            border-color: rgba(59, 130, 246, 0.3);
            box-shadow: 0 0 10px rgba(59, 130, 246, 0.08);
        }
        .run-card-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        .run-card-id {
            font-family: 'JetBrains Mono', monospace;
            font-size: 0.8rem;
            font-weight: 600;
            color: #60A5FA;
        }
        .run-card-badge {
            font-size: 0.65rem;
            padding: 0.1rem 0.35rem;
            border-radius: 9999px;
            font-weight: 700;
        }
        .run-card-detail {
            font-size: 0.75rem;
            color: #D1D5DB;
        }
        .run-card-footer {
            display: flex;
            justify-content: space-between;
            align-items: center;
            font-size: 0.7rem;
            color: #9CA3AF;
            border-top: 1px solid rgba(255, 255, 255, 0.03);
            padding-top: 0.25rem;
            margin-top: 0.25rem;
        }
        
        /* Details Display Pane */
        .details-display-pane {
            background: rgba(15, 23, 42, 0.4);
            border: 1px solid rgba(255, 255, 255, 0.05);
            border-radius: 10px;
            padding: 1.5rem;
            overflow-y: auto;
            display: flex;
            flex-direction: column;
            gap: 1.25rem;
        }
        .run-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            border-bottom: 1px solid rgba(255, 255, 255, 0.05);
            padding-bottom: 0.75rem;
        }
        .run-header h2 {
            font-size: 1.2rem;
            font-weight: 700;
            font-family: 'JetBrains Mono', monospace;
            color: #F3F4F6;
        }
        .run-meta-grid {
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: 1rem;
            background: rgba(31, 41, 55, 0.2);
            padding: 1rem;
            border-radius: 8px;
            border: 1px solid rgba(255, 255, 255, 0.03);
        }
        .run-meta-item {
            font-size: 0.8rem;
            color: #9CA3AF;
        }
        .run-meta-item strong {
            color: #F3F4F6;
        }
        
        /* Inner Subtabs inside Run Details */
        .details-tab-header {
            display: flex;
            gap: 0.5rem;
            border-bottom: 1px solid rgba(255, 255, 255, 0.05);
            padding-bottom: 0.5rem;
        }
        .details-subtab {
            background: transparent;
            border: none;
            color: #9CA3AF;
            padding: 0.4rem 0.75rem;
            font-size: 0.8rem;
            font-weight: 500;
            cursor: pointer;
            border-radius: 4px;
            transition: all 0.15s;
        }
        .details-subtab:hover {
            color: #F3F4F6;
            background: rgba(255,255,255,0.02);
        }
        .details-subtab.active {
            color: #3b82f6;
            background: rgba(59, 130, 246, 0.08);
            font-weight: 600;
        }
        .details-subview-panel {
            display: none;
        }
        .details-subview-panel.active {
            display: block;
        }
        .json-pre {
            background: #04060d;
            border: 1px solid rgba(255, 255, 255, 0.05);
            border-radius: 6px;
            padding: 1rem;
            font-family: 'JetBrains Mono', monospace;
            font-size: 0.775rem;
            color: #D1D5DB;
            overflow-x: auto;
            max-height: 400px;
        }
        
        /* Tables general styles */
        .data-table {
            width: 100%;
            border-collapse: collapse;
            font-size: 0.8rem;
            text-align: left;
        }
        .data-table th {
            color: #9CA3AF;
            font-weight: 600;
            text-transform: uppercase;
            font-size: 0.7rem;
            letter-spacing: 0.04em;
            border-bottom: 1px solid rgba(255,255,255,0.08);
            padding: 0.5rem 0.75rem;
        }
        .data-table td {
            border-bottom: 1px solid rgba(255,255,255,0.03);
            padding: 0.6rem 0.75rem;
            vertical-align: middle;
        }
        .text-center {
            text-align: center;
        }
        
        /* Markdown Compiled Report */
        .report-markdown-body {
            font-size: 0.875rem;
            line-height: 1.6;
            color: #E5E7EB;
            overflow-y: auto;
            max-height: 450px;
            padding-right: 0.5rem;
        }
        .report-markdown-body h1, .report-markdown-body h2, .report-markdown-body h3 {
            color: #60A5FA;
            margin-top: 1.25rem;
            margin-bottom: 0.5rem;
            font-weight: 700;
        }
        .report-markdown-body h1 { font-size: 1.25rem; border-bottom: 1px solid rgba(255,255,255,0.08); padding-bottom: 0.25rem; }
        .report-markdown-body h2 { font-size: 1.05rem; }
        .report-markdown-body p { margin-bottom: 0.75rem; }
        .report-markdown-body ul { padding-left: 1.25rem; margin-bottom: 0.75rem; }
        .report-markdown-body li { margin-bottom: 0.25rem; }
        .report-markdown-body pre {
            background: #04060d;
            border: 1px solid rgba(255,255,255,0.05);
            padding: 0.75rem;
            border-radius: 6px;
            font-family: 'JetBrains Mono', monospace;
            font-size: 0.75rem;
            overflow-x: auto;
            margin: 0.75rem 0;
        }
        
        /* Search interface components */
        .search-form-grid {
            display: grid;
            grid-template-columns: repeat(5, 1fr) auto;
            gap: 0.5rem;
            align-items: end;
            background: rgba(15, 23, 42, 0.4);
            border: 1px solid rgba(255,255,255,0.04);
            padding: 1rem;
            border-radius: 8px;
            margin-bottom: 1rem;
        }
        .search-field-group {
            display: flex;
            flex-direction: column;
            gap: 0.3rem;
        }
        .search-field-group label {
            font-size: 0.675rem;
            color: #9CA3AF;
            text-transform: uppercase;
            font-weight: 600;
        }
        .event-row-clickable {
            cursor: pointer;
            transition: background 0.1s;
        }
        .event-row-clickable:hover {
            background: rgba(255, 255, 255, 0.02);
        }
        .detail-drawer-row pre {
            margin: 0.5rem 0;
            max-height: 250px;
        }
        .cat-pill {
            font-size: 0.65rem;
            font-weight: 700;
            padding: 0.1rem 0.35rem;
            border-radius: 3px;
            text-transform: uppercase;
        }
        
        /* Timeline Interface Nodes */
        .timeline-vertical-flow {
            position: relative;
            padding: 1rem 0;
            max-height: calc(100vh - 280px);
            overflow-y: auto;
        }
        .timeline-vertical-flow::before {
            content: '';
            position: absolute;
            left: 120px;
            top: 0;
            bottom: 0;
            width: 2px;
            background: rgba(255, 255, 255, 0.06);
        }
        .timeline-node-item {
            display: flex;
            margin-bottom: 1.5rem;
            position: relative;
        }
        .timeline-left {
            width: 100px;
            text-align: right;
            padding-right: 1.25rem;
            display: flex;
            flex-direction: column;
            justify-content: center;
        }
        .timeline-tick {
            font-family: 'JetBrains Mono', monospace;
            font-size: 0.8rem;
            font-weight: 700;
            color: #60A5FA;
        }
        .timeline-date {
            font-size: 0.65rem;
            color: #6B7280;
            margin-top: 0.15rem;
        }
        .timeline-center {
            position: relative;
            width: 40px;
            display: flex;
            justify-content: center;
            align-items: center;
        }
        .timeline-bullet {
            width: 24px;
            height: 24px;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 0.7rem;
            z-index: 2;
            border: 2px solid #0f172a;
        }
        .node-event { background: #2563EB; color: white; box-shadow: 0 0 6px rgba(37,99,235,0.4); }
        .node-anomaly { background: #DC2626; color: white; box-shadow: 0 0 6px rgba(220,38,38,0.4); }
        .timeline-right {
            flex: 1;
            padding-left: 1.25rem;
        }
        .timeline-card-content {
            background: rgba(15, 23, 42, 0.4);
            border: 1px solid rgba(255, 255, 255, 0.05);
            border-radius: 8px;
            padding: 0.75rem 1rem;
        }
        .timeline-card-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            border-bottom: 1px solid rgba(255, 255, 255, 0.04);
            padding-bottom: 0.35rem;
            margin-bottom: 0.35rem;
        }
        .timeline-item-title {
            font-weight: 600;
            font-size: 0.8rem;
            color: #E5E7EB;
            font-family: 'JetBrains Mono', monospace;
        }
        .timeline-item-msg {
            font-size: 0.775rem;
            color: #9CA3AF;
            line-height: 1.4;
        }
        .detail-json-drawer {
            background: #04060d;
            padding: 0.5rem;
            border-radius: 4px;
            border: 1px solid rgba(255,255,255,0.05);
            font-family: 'JetBrains Mono', monospace;
            font-size: 0.7rem;
            overflow-x: auto;
        }
        
        .loader {
            color: #60a5fa;
            font-weight: 500;
            text-align: center;
            padding: 2rem 0;
            animation: pulse 1.5s infinite;
        }
        .empty-state {
            color: #9CA3AF;
            text-align: center;
            padding: 3rem 0;
            font-style: italic;
            font-size: 0.85rem;
        }
        .error-state {
            color: #F87171;
            text-align: center;
            padding: 2rem 0;
            font-weight: 500;
            font-size: 0.85rem;
        }
        
        /* Scrollbars custom styling */
        ::-webkit-scrollbar {
            width: 5px;
            height: 5px;
        }
        ::-webkit-scrollbar-track {
            background: transparent;
        }
        ::-webkit-scrollbar-thumb {
            background: rgba(255, 255, 255, 0.1);
            border-radius: 9999px;
        }
        ::-webkit-scrollbar-thumb:hover {
            background: rgba(255, 255, 255, 0.2);
        }
    </style>
</head>
<body>
    <header>
        <div class="logo-container">
            <div class="logo-dot" id="header-pulse"></div>
            <div class="logo-text">
                <h1>V2 RPG SIMULATION ENGINE</h1>
                <p>LIVE DEVELOPER OBSERVATORY SUITE</p>
            </div>
        </div>
        
        <div class="tab-nav">
            <button class="nav-tab active" id="tab-btn-live" onclick="switchTab('live')">
                <span>📡</span> Live Run
            </button>
            <button class="nav-tab" id="tab-btn-runs" onclick="switchTab('runs')">
                <span>📁</span> Completed Runs
            </button>
            <button class="nav-tab" id="tab-btn-sweeps" onclick="switchTab('sweeps')">
                <span>📊</span> Sweeps & Baselines
            </button>
            <button class="nav-tab" id="tab-btn-search" onclick="switchTab('search')">
                <span>🔍</span> Event Search
            </button>
            <button class="nav-tab" id="tab-btn-timeline" onclick="switchTab('timeline')">
                <span>⏳</span> Entity Timeline
            </button>
        </div>
        
        <div class="connection-status">
            <div class="conn-dot" id="conn-indicator"></div>
            <span id="conn-text" style="color: #9CA3AF; font-weight: 500;">DISCONNECTED</span>
        </div>
    </header>
    
    <main>
        <!-- Tab 1: Live Overview View -->
        <div id="view-live" class="view-container active">
            <div class="grid-two-col">
                <!-- Left stats & control column -->
                <div style="display: flex; flex-direction: column; gap: 1.25rem;">
                    <!-- Running telemetry metrics -->
                    <div class="card">
                        <div class="card-title">
                            <span>ENGINE LIVE TELEMETRY</span>
                            <span class="card-title-icon">📊</span>
                        </div>
                        <div class="stats-grid">
                            <div class="stat-box">
                                <div class="stat-label">ENGINE STATUS</div>
                                <div class="stat-value" id="val-status" style="color: #3B82F6;">IDLE</div>
                            </div>
                            <div class="stat-box">
                                <div class="stat-label">CURRENT TICK</div>
                                <div class="stat-value" id="val-tick">0</div>
                            </div>
                            <div class="stat-box">
                                <div class="stat-label">TICK COMPUTE TIME</div>
                                <div class="stat-value" id="val-compute">0.00 ms</div>
                            </div>
                            <div class="stat-box">
                                <div class="stat-label">SYSTEM MEMORY</div>
                                <div class="stat-value" id="val-memory">0.0 MB</div>
                            </div>
                            <div class="stat-box">
                                <div class="stat-label">GOVERNOR MODE</div>
                                <div class="stat-value" id="val-governor" style="color: #10B981;">NORMAL</div>
                            </div>
                            <div class="stat-box">
                                <div class="stat-label">OBSERVATION MODE</div>
                                <div class="stat-value" id="val-obs-mode" style="color: #60A5FA;">DEBUG</div>
                            </div>
                        </div>
                        <div style="display: flex; gap: 0.5rem; margin-top: 0.25rem;">
                            <button class="btn-blue" style="flex: 1; background: #059669;" onclick="triggerSimControl('resume')">RESUME</button>
                            <button class="btn-blue" style="flex: 1; background: #D97706;" onclick="triggerSimControl('pause')">PAUSE</button>
                        </div>
                    </div>
                    
                    <!-- Health assessment card -->
                    <div class="card health-card" id="health-card-container">
                        <div class="card-title">
                            <span>HEALTH MONITOR ASSESSMENT</span>
                            <span id="health-badge-slot">
                                <span class="health-status-badge badge-unknown">UNKNOWN</span>
                            </span>
                        </div>
                        <ul class="health-reasons" id="health-reasons-list">
                            <li>Waiting for simulation status updates...</li>
                        </ul>
                    </div>
                    
                    <!-- Live Anomaly counters -->
                    <div class="card">
                        <div class="card-title">
                            <span>LIVE ANOMALY TRIAGE</span>
                            <span class="card-title-icon">⚠️</span>
                        </div>
                        <div class="anomalies-list">
                            <div class="anomaly-item">
                                <span class="anomaly-label">Hard Law Violations</span>
                                <span class="anomaly-count zero" id="cnt-law">0</span>
                            </div>
                            <div class="anomaly-item">
                                <span class="anomaly-label">Stuck Navigation</span>
                                <span class="anomaly-count zero" id="cnt-stuck">0</span>
                            </div>
                            <div class="anomaly-item">
                                <span class="anomaly-label">Degraded Ticks</span>
                                <span class="anomaly-count zero" id="cnt-degraded">0</span>
                            </div>
                            <div class="anomaly-item">
                                <span class="anomaly-label">Dropped Events</span>
                                <span class="anomaly-count zero" id="cnt-dropped">0</span>
                            </div>
                            <div class="anomaly-item">
                                <span class="anomaly-label">Severity Errors</span>
                                <span class="anomaly-count zero" id="cnt-error">0</span>
                            </div>
                            <div class="anomaly-item">
                                <span class="anomaly-label">Severity Critical</span>
                                <span class="anomaly-count zero" id="cnt-critical">0</span>
                            </div>
                        </div>
                    </div>
                    
                    <!-- Quick Entity Inspector panel -->
                    <div class="card">
                        <div class="card-title">
                            <span>LIVE ENTITY LOOKUP</span>
                            <span class="card-title-icon">🔍</span>
                        </div>
                        <div class="inspector-search">
                            <input type="number" id="inspector-input" class="input-dark" placeholder="Enter Entity ID..." min="0">
                            <button class="btn-blue" onclick="performEntityInspection()">INSPECT</button>
                        </div>
                        <div class="inspector-results" id="inspector-results-container">
                            <div class="inspector-empty">Quick inspection panel. Type a live entity ID above to audit details.</div>
                        </div>
                    </div>
                </div>
                
                <!-- Live Event Stream Column -->
                <div class="event-stream-container">
                    <div class="filter-bar">
                        <div class="filter-group">
                            <span class="filter-label">Category:</span>
                            <button class="filter-pill active" onclick="setCategoryFilter('', this)">ALL</button>
                            <button class="filter-pill" onclick="setCategoryFilter('hard_law', this)">HARD LAW</button>
                            <button class="filter-pill" onclick="setCategoryFilter('anomaly', this)">ANOMALY</button>
                            <button class="filter-pill" onclick="setCategoryFilter('movement', this)">MOVEMENT</button>
                            <button class="filter-pill" onclick="setCategoryFilter('combat', this)">COMBAT</button>
                            <button class="filter-pill" onclick="setCategoryFilter('resource', this)">RESOURCE</button>
                            <button class="filter-pill" onclick="setCategoryFilter('economy', this)">ECONOMY</button>
                        </div>
                        <div class="filter-group">
                            <span class="filter-label">Severity:</span>
                            <button class="filter-pill active" onclick="setSeverityFilter('DEBUG', this)">DEBUG</button>
                            <button class="filter-pill" onclick="setSeverityFilter('INFO', this)">INFO</button>
                            <button class="filter-pill" onclick="setSeverityFilter('WARNING', this)">WARNING</button>
                            <button class="filter-pill" onclick="setSeverityFilter('ERROR', this)">ERROR</button>
                        </div>
                    </div>
                    
                    <div class="terminal">
                        <div class="terminal-header">
                            <span>REALTIME WEBSOCKET EVENTS</span>
                            <div style="display: flex; gap: 1rem; align-items: center;">
                                <label style="cursor: pointer; display: flex; align-items: center; gap: 0.25rem;">
                                    <input type="checkbox" id="autoscroll-chk" checked> Auto-Scroll
                                </label>
                                <span id="events-count" style="color: #60A5FA; font-weight: 600;">0 events</span>
                            </div>
                        </div>
                        <div class="terminal-body" id="event-ticker-body">
                            <!-- Events append here -->
                        </div>
                    </div>
                </div>
            </div>
        </div>
        
        <!-- Tab 2: Completed Runs Browser -->
        <div id="view-runs" class="view-container">
            <div class="grid-split-pane">
                <!-- Sidebar checklist of runs -->
                <div class="listing-sidebar">
                    <div class="listing-header">Completed Runs</div>
                    
                    <!-- Search and filters for completed runs -->
                    <div style="display:flex; flex-direction:column; gap:0.5rem; border-bottom: 1px solid rgba(255,255,255,0.06); padding-bottom: 0.75rem;">
                        <input type="text" id="run-filter-scenario" class="input-dark" placeholder="Filter scenario..." oninput="loadRunsList(this.value, document.getElementById('run-filter-status').value)">
                        <div style="display:flex; gap:0.5rem;">
                            <select id="run-filter-status" class="select-dark" style="flex:1;" onchange="loadRunsList(document.getElementById('run-filter-scenario').value, this.value)">
                                <option value="">All Status</option>
                                <option value="COMPLETED">Completed</option>
                                <option value="FAILED">Failed</option>
                                <option value="RUNNING">Running</option>
                            </select>
                            <button class="btn-secondary" onclick="loadRunsList()"><span style="font-size:0.75rem;">🔄</span></button>
                        </div>
                    </div>
                    
                    <div id="runs-list-container" style="display:flex; flex-direction:column; gap:0.5rem; flex:1; overflow-y:auto;">
                        <!-- Dynamically populated runs list -->
                    </div>
                </div>
                
                <!-- Detailed display pane of selected run -->
                <div class="details-display-pane" id="run-details-pane">
                    <div class="empty-state">Select a simulation run from the left panel to inspect detailed manifest, health reports, anomalies, and laws compliance.</div>
                </div>
            </div>
        </div>
        
        <!-- Tab 3: Sweeps & Baselines -->
        <div id="view-sweeps" class="view-container">
            <div class="grid-split-pane">
                <div class="listing-sidebar">
                    <div class="listing-header">Historical Sweeps</div>
                    <div id="sweeps-list-container" style="display:flex; flex-direction:column; gap:0.5rem; flex:1; overflow-y:auto; margin-top: 0.5rem;">
                        <!-- Populate dynamically -->
                    </div>
                </div>
                
                <div class="details-display-pane" id="sweep-details-pane">
                    <div class="empty-state">Select a multi-seed scenario sweep from the sidebar to visualize delta scores, worst seeds, anomalies distribution, and expectations.</div>
                </div>
            </div>
        </div>
        
        <!-- Tab 4: Event Search -->
        <div id="view-search" class="view-container">
            <!-- Search inputs form -->
            <div class="search-form-grid">
                <div class="search-field-group">
                    <label>Run Identifier</label>
                    <input type="text" id="search-run-id" class="input-dark" placeholder="Enter target Run ID...">
                </div>
                <div class="search-field-group">
                    <label>Entity ID</label>
                    <input type="text" id="search-entity-id" class="input-dark" placeholder="e.g. 1004 (Optional)">
                </div>
                <div class="search-field-group">
                    <label>Tick Start</label>
                    <input type="number" id="search-tick-start" class="input-dark" placeholder="0" min="0">
                </div>
                <div class="search-field-group">
                    <label>Tick End</label>
                    <input type="number" id="search-tick-end" class="input-dark" placeholder="Optional" min="0">
                </div>
                <div class="search-field-group">
                    <label>Severity Level</label>
                    <select id="search-severity" class="select-dark">
                        <option value="ALL">ALL LEVELS</option>
                        <option value="DEBUG">DEBUG</option>
                        <option value="INFO">INFO</option>
                        <option value="WARNING">WARNING</option>
                        <option value="ERROR">ERROR</option>
                        <option value="CRITICAL">CRITICAL</option>
                    </select>
                </div>
                <button class="btn-blue" onclick="performHistoricalSearch()"><span style="font-size:0.9rem;">🔎</span> QUERY WAREHOUSE</button>
            </div>
            
            <!-- Results table -->
            <div class="card" style="height: calc(100vh - 250px); overflow-y: auto;">
                <div class="card-title">
                    <span>Warehouse Query Results</span>
                    <div style="display:flex; gap:0.5rem; align-items:center;">
                        <button class="btn-xs" id="search-prev-btn" onclick="searchNavigate('prev')" disabled>Previous</button>
                        <span id="search-page-indicator" style="font-size:0.7rem; color:#9CA3AF;">Showing offset 0</span>
                        <button class="btn-xs" id="search-next-btn" onclick="searchNavigate('next')" disabled>Next</button>
                    </div>
                </div>
                
                <table class="data-table">
                    <thead>
                        <tr>
                            <th style="width: 100px;">Tick</th>
                            <th style="width: 150px;">Category</th>
                            <th style="width: 120px;">Severity</th>
                            <th>Description</th>
                            <th style="width: 80px;">Action</th>
                        </tr>
                    </thead>
                    <tbody id="search-results-table-body">
                        <tr>
                            <td colspan="5" class="text-center empty-state">Enter a valid target Run ID and click Query Warehouse to retrieve records from the active warehouse.</td>
                        </tr>
                    </tbody>
                </table>
            </div>
        </div>
        
        <!-- Tab 5: Entity Timeline -->
        <div id="view-timeline" class="view-container">
            <div class="card" style="height: calc(100vh - 150px); overflow-y: auto;">
                <div class="card-title">
                    <span>Chronological Entity Timeline Aggregation</span>
                    <div style="display:flex; gap:0.5rem;">
                        <input type="text" id="timeline-run-id" class="input-dark" placeholder="Enter target Run ID..." style="width: 250px;">
                        <input type="number" id="timeline-entity-id" class="input-dark" placeholder="Enter Entity ID..." style="width: 150px;" min="0">
                        <button class="btn-blue" onclick="loadEntityTimeline()">GENERATE TIMELINE</button>
                    </div>
                </div>
                
                <div class="timeline-vertical-flow" id="timeline-vertical-flow">
                    <div class="empty-state">Provide both a target Run ID and Entity ID, then click Generate Timeline to aggregate all chronological events and anomalies for this entity.</div>
                </div>
            </div>
        </div>
    </main>
    
    <script>
        let wsClient = null;
        let activeCategory = '';
        let activeSeverity = 'DEBUG';
        let eventsArray = [];
        let selectedRunId = '';
        let currentTab = 'live';
        let searchOffset = 0;
        const searchLimit = 25;
        
        // Startup connection and loops
        window.addEventListener('DOMContentLoaded', () => {
            initWebSocket();
            startPollingLoops();
        });
        
        function initWebSocket() {
            if (wsClient) {
                wsClient.close();
            }
            
            const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
            const host = window.location.host;
            let url = `${protocol}//${host}/api/v1/ws/observability/events`;
            
            const params = [];
            if (activeSeverity && activeSeverity !== 'DEBUG') {
                params.push(`severity_min=${activeSeverity}`);
            }
            if (activeCategory) {
                params.push(`category=${activeCategory}`);
            }
            if (params.length > 0) {
                url += `?${params.join('&')}`;
            }
            
            console.log(`Connecting WebSocket to: ${url}`);
            
            wsClient = new WebSocket(url);
            
            wsClient.onopen = () => {
                document.getElementById('conn-indicator').classList.add('connected');
                document.getElementById('conn-text').textContent = 'CONNECTED';
                document.getElementById('conn-text').style.color = '#10B981';
            };
            
            wsClient.onclose = () => {
                document.getElementById('conn-indicator').classList.remove('connected');
                document.getElementById('conn-text').textContent = 'DISCONNECTED';
                document.getElementById('conn-text').style.color = '#EF4444';
                // Auto-reconnect after 3 seconds
                setTimeout(initWebSocket, 3000);
            };
            
            wsClient.onerror = (err) => {
                console.error("WebSocket error:", err);
            };
            
            wsClient.onmessage = (msgEvent) => {
                try {
                    const data = JSON.parse(msgEvent.data);
                    if (data.type === 'event' && data.event) {
                        appendEvent(data.event);
                    }
                } catch (e) {
                    console.error("Failed to parse event message:", e);
                }
            };
        }
        
        function appendEvent(event) {
            eventsArray.push(event);
            if (eventsArray.length > 200) {
                eventsArray.shift();
            }
            document.getElementById('events-count').textContent = `${eventsArray.length} events`;
            
            const ticker = document.getElementById('event-ticker-body');
            
            const line = document.createElement('div');
            line.className = `event-line event-sev-${event.severity.toLowerCase()}`;
            
            // Auto inspect on click
            if (event.entity_id) {
                line.onclick = () => {
                    document.getElementById('inspector-input').value = event.entity_id;
                    performEntityInspection();
                };
            }
            
            const timeStr = new Date(event.timestamp * 1000).toLocaleTimeString();
            const catClass = `cat-${event.event_category}`;
            
            line.innerHTML = `
                <span class="event-time">[${timeStr}]</span>
                <span class="event-tick-badge">TICK ${event.tick}</span>
                <span class="event-cat-badge ${catClass}">${event.event_category}</span>
                <span class="event-msg">${event.message}</span>
            `;
            
            ticker.appendChild(line);
            
            // Maintain limit inside DOM
            while (ticker.children.length > 200) {
                ticker.removeChild(ticker.firstChild);
            }
            
            if (document.getElementById('autoscroll-chk').checked) {
                ticker.scrollTop = ticker.scrollHeight;
            }
        }
        
        function setCategoryFilter(category, buttonEl) {
            activeCategory = category;
            updateFilterActivePills(buttonEl);
            initWebSocket();
        }
        
        function setSeverityFilter(severity, buttonEl) {
            activeSeverity = severity;
            updateFilterActivePills(buttonEl);
            initWebSocket();
        }
        
        function updateFilterActivePills(buttonEl) {
            const parent = buttonEl.parentNode;
            parent.querySelectorAll('.filter-pill').forEach(btn => btn.classList.remove('active'));
            buttonEl.classList.add('active');
        }
        
        function startPollingLoops() {
            // Poll Telemetry & Health every 1.5 seconds
            setInterval(pollTelemetryAndHealth, 1500);
            pollTelemetryAndHealth();
        }
        
        async function pollTelemetryAndHealth() {
            try {
                // 1. Fetch live status
                const resStatus = await fetch('/api/v1/observability/live/status');
                if (resStatus.ok) {
                    const status = await resStatus.json();
                    
                    document.getElementById('val-status').textContent = status.status;
                    if (status.status === 'RUNNING') {
                        document.getElementById('val-status').style.color = '#10B981';
                        document.getElementById('header-pulse').style.backgroundColor = '#10B981';
                    } else if (status.status === 'PAUSED') {
                        document.getElementById('val-status').style.color = '#F59E0B';
                        document.getElementById('header-pulse').style.backgroundColor = '#F59E0B';
                    } else {
                        document.getElementById('val-status').style.color = '#6B7280';
                        document.getElementById('header-pulse').style.backgroundColor = '#6B7280';
                    }
                    
                    const tickVal = status.current_tick !== undefined ? status.current_tick : (status.tick_count !== undefined ? status.tick_count : 0);
                    document.getElementById('val-tick').textContent = tickVal;
                    document.getElementById('val-compute').textContent = `${(status.tick_compute_time_ms || 0).toFixed(2)} ms`;
                    document.getElementById('val-memory').textContent = `${(status.memory_rss_mb || 0).toFixed(1)} MB`;
                    
                    // New fields: Cadence and Governor mode
                    document.getElementById('val-governor').textContent = status.governor_mode || 'NORMAL';
                    if (status.governor_mode === 'CRITICAL' || status.governor_mode === 'DEGRADED') {
                        document.getElementById('val-governor').style.color = '#EF4444';
                    } else {
                        document.getElementById('val-governor').style.color = '#10B981';
                    }
                    document.getElementById('val-obs-mode').textContent = status.observability_mode || 'DEBUG';
                }
                
                // 2. Fetch live health
                const resHealth = await fetch('/api/v1/observability/live/health');
                if (resHealth.ok) {
                    const health = await resHealth.json();
                    
                    // Render health badge
                    const badgeSlot = document.getElementById('health-badge-slot');
                    const cardContainer = document.getElementById('health-card-container');
                    
                    // Reset container classes
                    cardContainer.className = 'card health-card';
                    cardContainer.classList.add(health.health_state.toLowerCase());
                    
                    badgeSlot.innerHTML = `<span class="health-status-badge badge-${health.health_state.toLowerCase()}">${health.health_state}</span>`;
                    
                    // Render reasons
                    const list = document.getElementById('health-reasons-list');
                    list.innerHTML = '';
                    health.reasons.forEach(reason => {
                        const li = document.createElement('li');
                        li.textContent = reason;
                        list.appendChild(li);
                    });
                    
                    // Render Anomaly counters
                    updateAnomalyCounterUI('cnt-law', health.counters.hard_law_violation_count);
                    updateAnomalyCounterUI('cnt-stuck', health.counters.navigation_stuck_count);
                    updateAnomalyCounterUI('cnt-degraded', health.counters.governor_degraded_ticks);
                    updateAnomalyCounterUI('cnt-dropped', health.counters.dropped_event_count);
                    updateAnomalyCounterUI('cnt-error', health.counters.error_event_count);
                    updateAnomalyCounterUI('cnt-critical', health.counters.critical_event_count);
                }
            } catch (err) {
                console.error("Error polling telemetry and health:", err);
            }
        }
        
        function updateAnomalyCounterUI(elementId, count) {
            const el = document.getElementById(elementId);
            if (el) {
                el.textContent = count;
                if (count > 0) {
                    el.className = 'anomaly-count has-count';
                } else {
                    el.className = 'anomaly-count zero';
                }
            }
        }
        
        async function performEntityInspection() {
            const input = document.getElementById('inspector-input');
            const entityId = parseInt(input.value);
            if (isNaN(entityId)) {
                return;
            }
            
            const container = document.getElementById('inspector-results-container');
            container.innerHTML = '<div style="text-align: center; padding: 1rem;"><span style="color: #60A5FA;">Inspecting entity...</span></div>';
            
            try {
                const res = await fetch(`/api/v1/observability/live/entities/${entityId}`);
                if (!res.ok) {
                    container.innerHTML = `<div class="inspector-empty" style="color: #EF4444;">Entity ${entityId} not found or engine idle</div>`;
                    return;
                }
                
                const data = await res.json();
                
                let detailsHTML = `
                    <div style="font-weight: 600; color: #60A5FA; border-bottom: 1px solid rgba(255,255,255,0.05); padding-bottom: 0.25rem;">
                        Entity ${data.entity_id} (${data.type.toUpperCase()})
                    </div>
                    <div class="inspector-grid">
                        <div>Position: <span class="inspector-val">(${data.x.toFixed(1)}, ${data.y.toFixed(1)})</span></div>
                        <div>Region ID: <span class="inspector-val">${data.region_id || 'Global'}</span></div>
                    </div>
                    <div class="inspector-grid" style="border-bottom: 1px solid rgba(255,255,255,0.05); padding-bottom: 0.5rem; margin-bottom: 0.5rem;">
                        <div>Goal: <span class="inspector-val" style="color: #FBBF24;">${data.current_goal || 'None'}</span></div>
                        <div>Inventory: <span class="inspector-val">${data.inventory_weight}/${data.inventory_capacity} kg</span></div>
                    </div>
                `;
                
                // Add timeline events
                if (data.timeline && data.timeline.length > 0) {
                    detailsHTML += `<div style="font-weight: 600; font-size: 0.75rem; color: #9CA3AF; margin-bottom: 0.25rem;">RECENT TIMELINE EVENTS:</div>`;
                    data.timeline.forEach(item => {
                        detailsHTML += `
                            <div class="timeline-item-ui">
                                [TICK ${item.tick}] ${item.event_type.toUpperCase()}: ${item.message}
                            </div>
                        `;
                    });
                } else {
                    detailsHTML += `<div style="color: #9CA3AF; font-style: italic; font-size: 0.75rem;">No recent timeline events found.</div>`;
                }
                
                container.innerHTML = detailsHTML;
            } catch (err) {
                console.error("Error inspecting entity:", err);
                container.innerHTML = '<div class="inspector-empty" style="color: #EF4444;">Failed to retrieve inspector details.</div>';
            }
        }
        
        async function triggerSimControl(action) {
            try {
                await fetch(`/api/v1/control/${action}`, { method: 'POST' });
                pollTelemetryAndHealth();
            } catch (e) {
                console.error(`Failed to trigger control action ${action}:`, e);
            }
        }
        
        // Tab switching function
        function switchTab(tabName) {
            currentTab = tabName;
            
            document.querySelectorAll('.nav-tab').forEach(btn => btn.classList.remove('active'));
            const clickedTab = document.getElementById(`tab-btn-${tabName}`);
            if (clickedTab) clickedTab.classList.add('active');
            
            document.querySelectorAll('.view-container').forEach(view => view.classList.remove('active'));
            
            const activeView = document.getElementById(`view-${tabName}`);
            if (activeView) activeView.classList.add('active');
            
            if (tabName === 'runs') {
                loadRunsList();
            } else if (tabName === 'sweeps') {
                loadSweepsList();
            }
        }
        
        // Subtab switching inside completed run view
        function switchSubTab(subTabName) {
            document.querySelectorAll('.details-subtab').forEach(btn => btn.classList.remove('active'));
            const clickedSubTab = document.getElementById(`subtab-btn-${subTabName}`);
            if (clickedSubTab) clickedSubTab.classList.add('active');
            
            document.querySelectorAll('.details-subview-panel').forEach(panel => panel.classList.remove('active'));
            const activePanel = document.getElementById(`subview-${subTabName}`);
            if (activePanel) activePanel.classList.add('active');
        }
        
        function toggleDetails(elementId) {
            const el = document.getElementById(elementId);
            if (el) {
                el.style.display = (el.style.display === 'none') ? 'block' : 'none';
            }
        }
        
        function prefillSearch(runId) {
            document.getElementById('search-run-id').value = runId;
            document.getElementById('timeline-run-id').value = runId;
            switchTab('search');
            performHistoricalSearch();
        }
        
        // Tab 2: Completed Runs list & details
        async function loadRunsList(scenarioName = '', status = '') {
            const runsListContainer = document.getElementById('runs-list-container');
            runsListContainer.innerHTML = '<div class="loader">Loading completed runs...</div>';
            
            try {
                let url = '/api/v1/observability/search/runs?limit=50';
                if (scenarioName) url += `&scenario_name=${encodeURIComponent(scenarioName)}`;
                if (status) url += `&status=${encodeURIComponent(status)}`;
                
                let res = await fetch(url);
                if (!res.ok) {
                    res = await fetch('/api/v1/observability/history/runs?limit=50');
                }
                
                if (!res.ok) throw new Error("Failed to load runs");
                
                const runs = await res.json();
                if (runs.length === 0) {
                    runsListContainer.innerHTML = '<div class="empty-state">No completed runs found.</div>';
                    return;
                }
                
                runsListContainer.innerHTML = '';
                runs.forEach(run => {
                    const card = document.createElement('div');
                    card.className = 'run-card-item';
                    card.id = `run-card-${run.run_id}`;
                    card.onclick = () => selectRun(run.run_id);
                    
                    const healthScore = run.health_score !== undefined ? run.health_score : 100;
                    const healthClass = healthScore >= 90 ? 'healthy' : (healthScore >= 70 ? 'warning' : 'critical');
                    
                    card.innerHTML = `
                        <div class="run-card-header">
                            <span class="run-card-id">${run.run_id.substring(0, 16)}...</span>
                            <span class="run-card-badge badge-${healthClass}">${healthScore.toFixed(0)}%</span>
                        </div>
                        <div class="run-card-detail">Scenario: <strong>${run.scenario_name}</strong></div>
                        <div class="run-card-footer">
                            <span>Ticks: ${run.ticks_completed}</span>
                            <span class="run-card-status status-${run.status.toLowerCase()}">${run.status}</span>
                        </div>
                    `;
                    runsListContainer.appendChild(card);
                });
            } catch (err) {
                runsListContainer.innerHTML = `<div class="error-state">Failed to load completed runs: ${err.message}</div>`;
            }
        }
        
        async function selectRun(runId) {
            document.querySelectorAll('#runs-list-container .run-card-item').forEach(c => c.classList.remove('active'));
            const activeCard = document.getElementById(`run-card-${runId}`);
            if (activeCard) activeCard.classList.add('active');
            
            selectedRunId = runId;
            
            const detailsContainer = document.getElementById('run-details-pane');
            detailsContainer.innerHTML = '<div class="loader">Loading run details...</div>';
            
            try {
                const res = await fetch(`/api/v1/observability/history/runs/${runId}`);
                if (!res.ok) throw new Error("Failed to load run manifest");
                const manifest = await res.json();
                
                const anomaliesRes = await fetch(`/api/v1/observability/search/anomalies?run_id=${runId}`);
                const anomalies = anomaliesRes.ok ? await anomaliesRes.json() : [];
                
                const eventsRes = await fetch(`/api/v1/observability/search/events?run_id=${runId}&severity=CRITICAL&limit=100`);
                const events = eventsRes.ok ? await eventsRes.json() : [];
                
                const reportRes = await fetch(`/api/v1/observability/history/runs/${runId}/report`);
                const reportMd = reportRes.ok ? await reportRes.text() : 'No report available.';
                
                const scorecardRes = await fetch(`/api/v1/behavior/runs/${runId}/scorecard`);
                const scorecard = scorecardRes.ok ? await scorecardRes.json() : {};
                
                const insightsRes = await fetch(`/api/v1/behavior/runs/${runId}/insights`);
                const insights = insightsRes.ok ? await insightsRes.json() : [];
                
                let insightsHTML = '';
                if (!insights || insights.length === 0) {
                    insightsHTML = '<div class="inspector-empty">No behavior insights found.</div>';
                } else {
                    insights.forEach(ins => {
                        insightsHTML += `
                            <div style="background: rgba(31, 41, 55, 0.4); padding: 0.75rem; border-radius: 6px; border-left: 3px solid #3B82F6; margin-bottom: 0.5rem;">
                                <div style="font-weight: 600; font-size: 0.85rem; color: #F3F4F6; margin-bottom: 0.25rem;">${ins.title}</div>
                                <div style="font-size: 0.775rem; color: #9CA3AF; margin-bottom: 0.4rem;">${ins.recommendation}</div>
                                <span class="badge-${ins.severity ? ins.severity.toLowerCase() : 'unknown'}" style="font-size: 0.65rem; padding: 0.1rem 0.3rem; border-radius: 3px;">${ins.severity || 'INFO'}</span>
                            </div>
                        `;
                    });
                }
                
                let reportHTML = reportMd;
                if (window.marked && window.marked.parse) {
                    reportHTML = window.marked.parse(reportMd);
                } else {
                    reportHTML = `<pre class="raw-markdown" style="white-space: pre-wrap; font-family: inherit;">${reportMd}</pre>`;
                }
                
                const endedDate = manifest.ended_at ? new Date(manifest.ended_at).toLocaleString() : 'N/A';
                const startedDate = manifest.started_at ? new Date(manifest.started_at).toLocaleString() : 'N/A';
                
                let anomaliesRows = '';
                if (anomalies.length === 0) {
                    anomaliesRows = '<tr><td colspan="4" class="text-center">No anomalies reported for this run.</td></tr>';
                } else {
                    anomalies.forEach(an => {
                        anomaliesRows += `
                            <tr>
                                <td><strong>${an.rule_id}</strong></td>
                                <td><span class="badge-${an.severity.toLowerCase()}">${an.severity}</span></td>
                                <td>Ticks ${an.tick_start}-${an.tick_end}</td>
                                <td>${an.message}</td>
                            </tr>
                        `;
                    });
                }
                
                let violationsRows = '';
                if (events.length === 0) {
                    violationsRows = '<tr><td colspan="4" class="text-center">No hard law violations or critical events recorded.</td></tr>';
                } else {
                    events.forEach((ev, i) => {
                        const rowDetailsId = `row-details-${i}`;
                        violationsRows += `
                            <tr>
                                <td>Tick ${ev.tick}</td>
                                <td><span class="badge-critical">${ev.event_type}</span></td>
                                <td>${ev.message}</td>
                                <td>
                                    <button class="btn-xs" onclick="toggleDetails('${rowDetailsId}')">Payload</button>
                                    <div id="${rowDetailsId}" class="detail-json-drawer" style="display:none; margin-top:0.25rem;">
                                        <pre>${JSON.stringify(ev, null, 2)}</pre>
                                    </div>
                                </td>
                            </tr>
                        `;
                    });
                }
                
                detailsContainer.innerHTML = `
                    <div class="run-header">
                        <h2>Run ID: ${manifest.run_id}</h2>
                        <button class="btn-blue" onclick="prefillSearch('${manifest.run_id}')">Use in Search</button>
                    </div>
                    
                    <div class="run-meta-grid">
                        <div class="run-meta-item"><strong>Scenario Name:</strong> ${manifest.scenario_name}</div>
                        <div class="run-meta-item"><strong>Scenario Type:</strong> ${manifest.scenario_type}</div>
                        <div class="run-meta-item"><strong>Seed:</strong> ${manifest.seed}</div>
                        <div class="run-meta-item"><strong>Ticks Completed:</strong> ${manifest.ticks_completed} / ${manifest.ticks_requested}</div>
                        <div class="run-meta-item"><strong>Started At:</strong> ${startedDate}</div>
                        <div class="run-meta-item"><strong>Ended At:</strong> ${endedDate}</div>
                    </div>
                    
                    <div class="details-tab-header">
                        <button class="details-subtab active" id="subtab-btn-manifest" onclick="switchSubTab('manifest')">Manifest JSON</button>
                        <button class="details-subtab" id="subtab-btn-anomalies" onclick="switchSubTab('anomalies')">Anomalies (${anomalies.length})</button>
                        <button class="details-subtab" id="subtab-btn-violations" onclick="switchSubTab('violations')">Hard Violations (${events.length})</button>
                        <button class="details-subtab" id="subtab-btn-report" onclick="switchSubTab('report')">Executive Report</button>
                        <button class="details-subtab" id="subtab-btn-behavior" onclick="switchSubTab('behavior')">Behavior Scorecard</button>
                    </div>
                    
                    <div id="subview-manifest" class="details-subview-panel active">
                        <pre class="json-pre">${JSON.stringify(manifest, null, 2)}</pre>
                    </div>
                    
                    <div id="subview-anomalies" class="details-subview-panel">
                        <table class="data-table">
                            <thead>
                                <tr>
                                    <th>Rule ID</th>
                                    <th>Severity</th>
                                    <th>Tick Range</th>
                                    <th>Message</th>
                                </tr>
                            </thead>
                            <tbody>
                                ${anomaliesRows}
                            </tbody>
                        </table>
                    </div>
                    
                    <div id="subview-violations" class="details-subview-panel">
                        <table class="data-table">
                            <thead>
                                <tr>
                                    <th style="width: 100px;">Tick</th>
                                    <th style="width: 150px;">Type</th>
                                    <th>Message</th>
                                    <th style="width: 80px;">Action</th>
                                </tr>
                            </thead>
                            <tbody>
                                ${violationsRows}
                            </tbody>
                        </table>
                    </div>
                    
                    <div id="subview-report" class="details-subview-panel report-markdown-body">
                        ${reportHTML}
                    </div>
                    
                    <div id="subview-behavior" class="details-subview-panel">
                        <div class="stats-grid">
                            <div class="stat-box">
                                <div class="stat-label">Total Events</div>
                                <div class="stat-value">${scorecard.total_events || 0}</div>
                            </div>
                            <div class="stat-box">
                                <div class="stat-label">Total Episodes</div>
                                <div class="stat-value">${scorecard.total_episodes || 0}</div>
                            </div>
                            <div class="stat-box">
                                <div class="stat-label">Total Failures</div>
                                <div class="stat-value">${scorecard.total_failures || 0}</div>
                            </div>
                            <div class="stat-box">
                                <div class="stat-label">Total Adaptations</div>
                                <div class="stat-value">${scorecard.total_adaptations || 0}</div>
                            </div>
                        </div>
                        
                        <div class="card" style="margin-top: 1rem;">
                            <div class="card-title">Top Behavior Insights</div>
                            <div id="insights-list" style="display: flex; flex-direction: column; gap: 0.5rem; margin-top: 0.5rem;">
                                ${insightsHTML}
                            </div>
                        </div>
                    </div>
                `;
            } catch (err) {
                detailsContainer.innerHTML = `<div class="error-state">Failed to load run details: ${err.message}</div>`;
            }
        }
        
        // Tab 3: Historical Sweeps list & details
        async function loadSweepsList() {
            const sweepsListContainer = document.getElementById('sweeps-list-container');
            sweepsListContainer.innerHTML = '<div class="loader">Loading sweeps...</div>';
            
            try {
                const res = await fetch('/api/v1/observability/history/sweeps?limit=50');
                if (!res.ok) throw new Error("Failed to load sweeps");
                const sweeps = await res.json();
                
                if (sweeps.length === 0) {
                    sweepsListContainer.innerHTML = '<div class="empty-state">No historical sweeps found.</div>';
                    return;
                }
                
                sweepsListContainer.innerHTML = '';
                sweeps.forEach(sw => {
                    const card = document.createElement('div');
                    card.className = 'run-card-item';
                    card.id = `sweep-card-${sw.sweep_id}`;
                    card.onclick = () => selectSweep(sw.sweep_id);
                    
                    card.innerHTML = `
                        <div class="run-card-header">
                            <span class="run-card-id">${sw.sweep_id}</span>
                        </div>
                        <div class="run-card-detail">Scenario: <strong>${sw.scenario_name || 'unknown'}</strong></div>
                        <div class="run-card-footer">
                            <span>Runs: ${sw.total_runs || 0}</span>
                            <span>Type: ${sw.scenario_type || 'default'}</span>
                        </div>
                    `;
                    sweepsListContainer.appendChild(card);
                });
            } catch (err) {
                sweepsListContainer.innerHTML = `<div class="error-state">Failed to load sweeps: ${err.message}</div>`;
            }
        }
        
        async function selectSweep(sweepId) {
            document.querySelectorAll('#sweeps-list-container .run-card-item').forEach(c => c.classList.remove('active'));
            const activeCard = document.getElementById(`sweep-card-${sweepId}`);
            if (activeCard) activeCard.classList.add('active');
            
            const detailsContainer = document.getElementById('sweep-details-pane');
            detailsContainer.innerHTML = '<div class="loader">Loading sweep summary...</div>';
            
            try {
                const res = await fetch(`/api/v1/observability/history/sweeps/${sweepId}`);
                if (!res.ok) throw new Error("Failed to load sweep summary");
                const summary = await res.json();
                
                let worstSeedsRows = '';
                if (summary.worst_run_id) {
                    worstSeedsRows = `
                        <tr>
                            <td>Worst Run ID</td>
                            <td><span class="badge-critical">${summary.worst_run_id}</span></td>
                        </tr>
                    `;
                }
                if (summary.best_run_id) {
                    worstSeedsRows += `
                        <tr>
                            <td>Best Run ID</td>
                            <td><span class="badge-healthy">${summary.best_run_id}</span></td>
                        </tr>
                    `;
                }
                
                let anomaliesRows = '';
                const rules = summary.most_common_anomaly_rule_ids || {};
                const rulesList = Object.entries(rules);
                if (rulesList.length === 0) {
                    anomaliesRows = '<tr><td colspan="2" class="text-center">No anomalies reported in this sweep.</td></tr>';
                } else {
                    rulesList.forEach(([ruleId, count]) => {
                        anomaliesRows += `
                            <tr>
                                <td><strong>${ruleId}</strong></td>
                                <td><span class="anomaly-count has-count" style="font-size:0.85rem; color:#EF4444;">${count} times</span></td>
                            </tr>
                        `;
                    });
                }
                
                detailsContainer.innerHTML = `
                    <h2>Sweep Summary: ${summary.sweep_id}</h2>
                    <div class="run-meta-grid">
                        <div class="run-meta-item"><strong>Scenario Name:</strong> ${summary.scenario_name}</div>
                        <div class="run-meta-item"><strong>Scenario Type:</strong> ${summary.scenario_type}</div>
                        <div class="run-meta-item"><strong>Total Runs:</strong> ${summary.total_runs}</div>
                        <div class="run-meta-item"><strong>Completed Runs:</strong> ${summary.completed_runs}</div>
                        <div class="run-meta-item"><strong>Failed Runs:</strong> ${summary.failed_runs}</div>
                        <div class="run-meta-item"><strong>Average Health Score:</strong> <span class="badge-healthy">${(summary.average_health_score || 100.0).toFixed(1)}%</span></div>
                    </div>
                    
                    <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 1.5rem; margin-top: 1rem;">
                        <div class="card">
                            <div class="card-title">Run Performance Extremes</div>
                            <table class="data-table">
                                <thead>
                                    <tr>
                                        <th>Category</th>
                                        <th>Run ID</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    ${worstSeedsRows || '<tr><td colspan="2" class="text-center">No extremes available</td></tr>'}
                                </tbody>
                            </table>
                        </div>
                        
                        <div class="card">
                            <div class="card-title">Most Common Anomaly Rules</div>
                            <table class="data-table">
                                <thead>
                                    <tr>
                                        <th>Rule ID</th>
                                        <th>Occurrence Frequency</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    ${anomaliesRows}
                                </tbody>
                            </table>
                        </div>
                    </div>
                    
                    <div class="card" style="margin-top: 1rem;">
                        <div class="card-title">Sweep Manifest Raw JSON Summary</div>
                        <pre class="json-pre">${JSON.stringify(summary, null, 2)}</pre>
                    </div>
                `;
            } catch (err) {
                detailsContainer.innerHTML = `<div class="error-state">Failed to load sweep summary: ${err.message}</div>`;
            }
        }
        
        // Tab 4: Historical Event Search
        async function performHistoricalSearch(resetOffset = true) {
            if (resetOffset) searchOffset = 0;
            
            const runId = document.getElementById('search-run-id').value.trim();
            if (!runId) {
                alert("Please enter or prefill a Run ID.");
                return;
            }
            
            const entityId = document.getElementById('search-entity-id').value.trim();
            const tickStart = document.getElementById('search-tick-start').value;
            const tickEnd = document.getElementById('search-tick-end').value;
            const severity = document.getElementById('search-severity').value;
            
            const resultsContainer = document.getElementById('search-results-table-body');
            resultsContainer.innerHTML = '<tr><td colspan="5" class="text-center"><span class="loader">Querying warehouse...</span></td></tr>';
            
            try {
                let url = `/api/v1/observability/search/events?run_id=${encodeURIComponent(runId)}&limit=${searchLimit}&offset=${searchOffset}`;
                if (entityId) url += `&entity_id=${encodeURIComponent(entityId)}`;
                if (tickStart) url += `&tick_start=${tickStart}`;
                if (tickEnd) url += `&tick_end=${tickEnd}`;
                if (severity && severity !== 'ALL') url += `&severity=${severity}`;
                
                const res = await fetch(url);
                if (!res.ok) throw new Error("Search query failed");
                
                const events = await res.json();
                
                if (events.length === 0) {
                    resultsContainer.innerHTML = '<tr><td colspan="5" class="text-center empty-state">No matching events found in warehouse.</td></tr>';
                    document.getElementById('search-prev-btn').disabled = true;
                    document.getElementById('search-next-btn').disabled = true;
                    return;
                }
                
                resultsContainer.innerHTML = '';
                events.forEach((ev, idx) => {
                    const rowId = `search-row-${idx}`;
                    const detailRowId = `search-detail-row-${idx}`;
                    
                    const tr = document.createElement('tr');
                    tr.className = `event-row-clickable severity-${ev.severity.toLowerCase()}`;
                    tr.onclick = () => toggleDetails(detailRowId);
                    
                    tr.innerHTML = `
                        <td>Tick ${ev.tick}</td>
                        <td><span class="cat-pill cat-${ev.event_category || 'other'}">${ev.event_category || 'other'}</span></td>
                        <td><span class="badge-${ev.severity.toLowerCase()}">${ev.severity}</span></td>
                        <td>${ev.message}</td>
                        <td><button class="btn-xs">Payload</button></td>
                    `;
                    resultsContainer.appendChild(tr);
                    
                    const detailTr = document.createElement('tr');
                    detailTr.id = detailRowId;
                    detailTr.className = 'detail-drawer-row';
                    detailTr.style.display = 'none';
                    detailTr.innerHTML = `
                        <td colspan="5">
                            <pre class="json-pre">${JSON.stringify(ev, null, 2)}</pre>
                        </td>
                    `;
                    resultsContainer.appendChild(detailTr);
                });
                
                document.getElementById('search-prev-btn').disabled = searchOffset === 0;
                document.getElementById('search-next-btn').disabled = events.length < searchLimit;
                document.getElementById('search-page-indicator').textContent = `Showing offset ${searchOffset}`;
            } catch (err) {
                resultsContainer.innerHTML = `<tr><td colspan="5" class="text-center error-state">Search failed: ${err.message}</td></tr>`;
            }
        }
        
        function searchNavigate(direction) {
            if (direction === 'prev' && searchOffset >= searchLimit) {
                searchOffset -= searchLimit;
            } else if (direction === 'next') {
                searchOffset += searchLimit;
            }
            performHistoricalSearch(false);
        }
        
        // Tab 5: Entity Timeline
        async function loadEntityTimeline() {
            const runId = document.getElementById('timeline-run-id').value.trim();
            const entityId = document.getElementById('timeline-entity-id').value.trim();
            
            if (!runId || !entityId) {
                alert("Please enter both a Run ID and Entity ID.");
                return;
            }
            
            const timelineBody = document.getElementById('timeline-vertical-flow');
            timelineBody.innerHTML = '<div class="loader">Aggregating timeline from warehouse...</div>';
            
            try {
                const res = await fetch(`/api/v1/observability/search/entity-timeline?run_id=${encodeURIComponent(runId)}&entity_id=${encodeURIComponent(entityId)}`);
                if (!res.ok) throw new Error("Entity timeline request failed");
                
                const timeline = await res.json();
                
                if (timeline.length === 0) {
                    timelineBody.innerHTML = '<div class="empty-state">No timeline events or anomalies found for this entity in the selected run.</div>';
                    return;
                }
                
                timelineBody.innerHTML = '';
                timeline.forEach((item, idx) => {
                    const itemEl = document.createElement('div');
                    itemEl.className = `timeline-node-item timeline-type-${item.type}`;
                    
                    const isAnomaly = item.type === 'anomaly';
                    const nodeBadge = isAnomaly ? '⚠️' : '⚓';
                    const badgeClass = isAnomaly ? 'node-anomaly' : 'node-event';
                    const dateStr = item.timestamp ? new Date(item.timestamp).toLocaleTimeString() : 'TICK BOUNDS';
                    
                    const detailId = `timeline-detail-${idx}`;
                    
                    itemEl.innerHTML = `
                        <div class="timeline-left">
                            <span class="timeline-tick">TICK ${item.tick}</span>
                            <span class="timeline-date">${dateStr}</span>
                        </div>
                        <div class="timeline-center">
                            <div class="timeline-bullet ${badgeClass}">${nodeBadge}</div>
                        </div>
                        <div class="timeline-right">
                            <div class="timeline-card-content">
                                <div class="timeline-card-header">
                                    <span class="timeline-item-title">${isAnomaly ? item.rule_id : item.event_type}</span>
                                    <span class="badge-${item.severity.toLowerCase()}">${item.severity}</span>
                                </div>
                                <p class="timeline-item-msg">${item.message}</p>
                                <button class="btn-xs" style="margin-top: 0.5rem;" onclick="toggleDetails('${detailId}')">View Details JSON</button>
                                <div id="${detailId}" class="detail-json-drawer" style="display:none; margin-top: 0.5rem;">
                                    <pre>${JSON.stringify(item.details || {}, null, 2)}</pre>
                                </div>
                            </div>
                        </div>
                    `;
                    timelineBody.appendChild(itemEl);
                });
            } catch (err) {
                timelineBody.innerHTML = `<div class="error-state">Failed to aggregate entity timeline: ${err.message}</div>`;
            }
        }
    </script>
</body>
</html>
"""
        return HTMLResponse(content=html_content, status_code=200)

    @app.get("/observability/ui")
    async def redirect_ui():
        return RedirectResponse(url="/api/v1/observability/ui")

    @app.get("/api/v1/observability/live/ui")
    async def redirect_live_ui():
        return RedirectResponse(url="/api/v1/observability/ui")

    return app
