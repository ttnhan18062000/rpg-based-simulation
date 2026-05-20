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

    @app.get("/api/v1/observability/ui", response_class=HTMLResponse)
    async def get_observability_ui():
        html_content = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>V2 Simulation Live Observatory</title>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap" rel="stylesheet">
    <style>
        * {
            box-sizing: border-box;
            margin: 0;
            padding: 0;
        }
        body {
            background: linear-gradient(135deg, #090D16 0%, #111827 100%);
            color: #F3F4F6;
            font-family: 'Outfit', sans-serif;
            min-height: 100vh;
            overflow-x: hidden;
            display: flex;
            flex-direction: column;
        }
        
        /* Glassmorphism Header */
        header {
            background: rgba(17, 24, 39, 0.7);
            backdrop-filter: blur(12px);
            -webkit-backdrop-filter: blur(12px);
            border-bottom: 1px solid rgba(255, 255, 255, 0.08);
            padding: 1.25rem 2rem;
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
            font-size: 1.25rem;
            font-weight: 700;
            letter-spacing: 0.1em;
            background: linear-gradient(to right, #3B82F6, #10B981);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }
        .logo-text p {
            font-size: 0.75rem;
            color: #9CA3AF;
            letter-spacing: 0.05em;
        }
        
        /* Main Layout Grid */
        .container {
            flex: 1;
            display: grid;
            grid-template-columns: 450px 1fr;
            gap: 1.5rem;
            padding: 1.5rem;
            max-width: 1800px;
            margin: 0 auto;
            width: 100%;
        }
        
        /* Glassmorphic card styling */
        .card {
            background: rgba(17, 24, 39, 0.65);
            backdrop-filter: blur(8px);
            -webkit-backdrop-filter: blur(8px);
            border: 1px solid rgba(255, 255, 255, 0.06);
            border-radius: 12px;
            padding: 1.5rem;
            box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.3);
            display: flex;
            flex-direction: column;
            gap: 1.25rem;
            transition: transform 0.2s ease, border-color 0.2s ease;
        }
        .card:hover {
            border-color: rgba(59, 130, 246, 0.2);
        }
        .card-title {
            font-size: 1rem;
            font-weight: 600;
            color: #E5E7EB;
            display: flex;
            align-items: center;
            justify-content: space-between;
            border-bottom: 1px solid rgba(255, 255, 255, 0.05);
            padding-bottom: 0.75rem;
        }
        .card-title-icon {
            color: #3B82F6;
        }
        
        /* Stats dashboard section */
        .stats-grid {
            display: grid;
            grid-template-columns: repeat(2, 1fr);
            gap: 0.75rem;
        }
        .stat-box {
            background: rgba(31, 41, 55, 0.4);
            border: 1px solid rgba(255, 255, 255, 0.04);
            border-radius: 8px;
            padding: 0.75rem 1rem;
            text-align: left;
        }
        .stat-label {
            font-size: 0.75rem;
            color: #9CA3AF;
            margin-bottom: 0.25rem;
        }
        .stat-value {
            font-size: 1.15rem;
            font-weight: 700;
            font-family: 'JetBrains Mono', monospace;
            color: #F9FAFB;
        }
        
        /* Health Status box */
        .health-card {
            background: linear-gradient(135deg, rgba(16, 185, 129, 0.05) 0%, rgba(17, 24, 39, 0.65) 100%);
            border-left: 4px solid #10B981;
        }
        .health-card.warning {
            background: linear-gradient(135deg, rgba(245, 158, 11, 0.05) 0%, rgba(17, 24, 39, 0.65) 100%);
            border-left: 4px solid #F59E0B;
        }
        .health-card.degraded {
            background: linear-gradient(135deg, rgba(239, 68, 68, 0.05) 0%, rgba(17, 24, 39, 0.65) 100%);
            border-left: 4px solid #EF4444;
        }
        .health-card.critical {
            background: linear-gradient(135deg, rgba(220, 38, 38, 0.05) 0%, rgba(17, 24, 39, 0.65) 100%);
            border-left: 4px solid #DC2626;
        }
        .health-status-badge {
            display: inline-flex;
            align-items: center;
            gap: 0.5rem;
            padding: 0.35rem 0.75rem;
            border-radius: 9999px;
            font-size: 0.75rem;
            font-weight: 700;
            letter-spacing: 0.05em;
        }
        .badge-healthy { background: rgba(16, 185, 129, 0.15); color: #34D399; border: 1px solid rgba(16, 185, 129, 0.25); }
        .badge-warning { background: rgba(245, 158, 11, 0.15); color: #FBBF24; border: 1px solid rgba(245, 158, 11, 0.25); }
        .badge-degraded { background: rgba(239, 68, 68, 0.15); color: #FCA5A5; border: 1px solid rgba(239, 68, 68, 0.25); }
        .badge-critical { background: rgba(220, 38, 38, 0.15); color: #F87171; border: 1px solid rgba(220, 38, 38, 0.25); }
        .badge-unknown { background: rgba(107, 114, 128, 0.15); color: #D1D5DB; border: 1px solid rgba(107, 114, 128, 0.25); }
        
        .health-reasons {
            font-size: 0.8rem;
            color: #D1D5DB;
            padding-left: 1.25rem;
            line-height: 1.4;
        }
        .health-reasons li {
            margin-bottom: 0.35rem;
        }
        
        /* Anomaly list grid */
        .anomalies-list {
            display: grid;
            grid-template-columns: repeat(2, 1fr);
            gap: 0.75rem;
        }
        .anomaly-item {
            background: rgba(31, 41, 55, 0.3);
            border: 1px solid rgba(255, 255, 255, 0.03);
            border-radius: 8px;
            padding: 0.75rem;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        .anomaly-label {
            font-size: 0.75rem;
            color: #9CA3AF;
        }
        .anomaly-count {
            font-size: 1.1rem;
            font-weight: 700;
            font-family: 'JetBrains Mono', monospace;
        }
        .anomaly-count.has-count {
            color: #EF4444;
            text-shadow: 0 0 8px rgba(239, 68, 68, 0.3);
        }
        .anomaly-count.zero {
            color: #9CA3AF;
        }
        
        /* Entity Inspector Styles */
        .inspector-search {
            display: flex;
            gap: 0.5rem;
        }
        .input-dark {
            background: rgba(17, 24, 39, 0.8);
            border: 1px solid rgba(255, 255, 255, 0.1);
            border-radius: 6px;
            padding: 0.5rem 0.75rem;
            color: #F9FAFB;
            font-family: inherit;
            font-size: 0.875rem;
            flex: 1;
            transition: border-color 0.15s ease;
        }
        .input-dark:focus {
            outline: none;
            border-color: #3B82F6;
            box-shadow: 0 0 0 2px rgba(59, 130, 246, 0.15);
        }
        .btn-blue {
            background: #2563EB;
            color: white;
            border: none;
            border-radius: 6px;
            padding: 0.5rem 1rem;
            font-weight: 600;
            font-size: 0.875rem;
            cursor: pointer;
            transition: background 0.15s ease;
        }
        .btn-blue:hover {
            background: #1D4ED8;
        }
        .inspector-results {
            background: rgba(31, 41, 55, 0.2);
            border: 1px solid rgba(255, 255, 255, 0.04);
            border-radius: 8px;
            padding: 1rem;
            min-height: 100px;
            font-size: 0.85rem;
            display: flex;
            flex-direction: column;
            gap: 0.75rem;
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
            padding: 1.5rem 0;
            font-style: italic;
        }
        .timeline-item-ui {
            padding: 0.35rem 0.5rem;
            background: rgba(255, 255, 255, 0.02);
            border-left: 2px solid #3B82F6;
            margin-bottom: 0.25rem;
            font-family: 'JetBrains Mono', monospace;
            font-size: 0.75rem;
        }
        
        /* Right Panel: Live Event Stream */
        .event-stream-container {
            display: flex;
            flex-direction: column;
            gap: 1rem;
            height: calc(100vh - 120px);
        }
        .filter-bar {
            background: rgba(17, 24, 39, 0.5);
            border: 1px solid rgba(255, 255, 255, 0.05);
            border-radius: 8px;
            padding: 0.75rem 1rem;
            display: flex;
            justify-content: space-between;
            align-items: center;
            gap: 1rem;
            flex-wrap: wrap;
        }
        .filter-group {
            display: flex;
            align-items: center;
            gap: 0.5rem;
        }
        .filter-label {
            font-size: 0.75rem;
            color: #9CA3AF;
            text-transform: uppercase;
            letter-spacing: 0.05em;
        }
        .filter-pill {
            background: rgba(31, 41, 55, 0.6);
            border: 1px solid rgba(255, 255, 255, 0.08);
            color: #9CA3AF;
            padding: 0.25rem 0.65rem;
            border-radius: 9999px;
            font-size: 0.75rem;
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
        
        /* Event Stream Terminal */
        .terminal {
            background: #060913;
            border: 1px solid rgba(255, 255, 255, 0.05);
            border-radius: 10px;
            flex: 1;
            display: flex;
            flex-direction: column;
            overflow: hidden;
            box-shadow: inset 0 2px 8px rgba(0,0,0,0.8);
        }
        .terminal-header {
            background: rgba(17, 24, 39, 0.8);
            border-bottom: 1px solid rgba(255, 255, 255, 0.05);
            padding: 0.5rem 1rem;
            display: flex;
            justify-content: space-between;
            align-items: center;
            font-size: 0.75rem;
            color: #9CA3AF;
        }
        .terminal-body {
            flex: 1;
            padding: 1rem;
            overflow-y: auto;
            font-family: 'JetBrains Mono', monospace;
            font-size: 0.825rem;
            display: flex;
            flex-direction: column;
            gap: 0.4rem;
        }
        .event-line {
            display: flex;
            align-items: flex-start;
            gap: 0.75rem;
            padding: 0.35rem 0.5rem;
            border-radius: 4px;
            transition: background 0.1s ease;
            cursor: pointer;
            line-height: 1.4;
        }
        .event-line:hover {
            background: rgba(255, 255, 255, 0.03);
        }
        .event-time {
            color: #4B5563;
            font-size: 0.75rem;
            flex-shrink: 0;
            width: 80px;
        }
        .event-tick-badge {
            color: #3B82F6;
            background: rgba(59, 130, 246, 0.08);
            border: 1px solid rgba(59, 130, 246, 0.15);
            padding: 0.05rem 0.25rem;
            border-radius: 3px;
            font-size: 0.7rem;
            flex-shrink: 0;
        }
        .event-cat-badge {
            padding: 0.05rem 0.35rem;
            border-radius: 3px;
            font-size: 0.7rem;
            font-weight: 600;
            text-transform: uppercase;
            flex-shrink: 0;
        }
        .cat-movement { background: rgba(59, 130, 246, 0.1); color: #60A5FA; border: 1px solid rgba(59, 130, 246, 0.2); }
        .cat-combat { background: rgba(239, 68, 68, 0.1); color: #FCA5A5; border: 1px solid rgba(239, 68, 68, 0.2); }
        .cat-resource { background: rgba(16, 185, 129, 0.1); color: #34D399; border: 1px solid rgba(16, 185, 129, 0.2); }
        .cat-economy { background: rgba(245, 158, 11, 0.1); color: #FBBF24; border: 1px solid rgba(245, 158, 11, 0.2); }
        .cat-hard_law { background: rgba(220, 38, 38, 0.15); color: #F87171; border: 1px solid rgba(220, 38, 38, 0.3); font-weight: 700; }
        .cat-anomaly { background: rgba(139, 92, 246, 0.15); color: #C084FC; border: 1px solid rgba(139, 92, 246, 0.3); font-weight: 700; }
        .cat-other { background: rgba(107, 114, 128, 0.1); color: #D1D5DB; border: 1px solid rgba(107, 114, 128, 0.2); }
        
        .event-msg {
            color: #E5E7EB;
            word-break: break-word;
        }
        .event-sev-err {
            border-left: 2px solid #EF4444;
            background: rgba(239, 68, 68, 0.03);
        }
        .event-sev-err .event-msg {
            color: #FCA5A5;
        }
        .event-sev-crit {
            border-left: 3px solid #DC2626;
            background: rgba(220, 38, 38, 0.06);
            font-weight: 500;
        }
        .event-sev-crit .event-msg {
            color: #FECACA;
        }
        .event-sev-warn {
            border-left: 2px solid #F59E0B;
        }
        .event-sev-warn .event-msg {
            color: #FDE68A;
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
    </style>
</head>
<body>
    <header>
        <div class="logo-container">
            <div class="logo-dot" id="header-pulse"></div>
            <div class="logo-text">
                <h1>V2 RPG ENGINE</h1>
                <p>LIVE DEVELOPER OBSERVATORY</p>
            </div>
        </div>
        <div class="connection-status">
            <div class="conn-dot" id="conn-indicator"></div>
            <span id="conn-text" style="color: #9CA3AF; font-weight: 500;">DISCONNECTED</span>
        </div>
    </header>
    
    <div class="container">
        <!-- Left Panel: Engine stats & Health status -->
        <div style="display: flex; flex-direction: column; gap: 1.5rem;">
            <!-- Running metrics card -->
            <div class="card">
                <div class="card-title">
                    <span>ENGINE TELEMETRY</span>
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
                </div>
                <div style="display: flex; gap: 0.5rem; margin-top: 0.25rem;">
                    <button class="btn-blue" style="flex: 1; background: #059669;" onclick="triggerSimControl('resume')">RESUME</button>
                    <button class="btn-blue" style="flex: 1; background: #D97706;" onclick="triggerSimControl('pause')">PAUSE</button>
                </div>
            </div>
            
            <!-- Health assessment card -->
            <div class="card health-card" id="health-card-container">
                <div class="card-title">
                    <span>HEALTH ASSESSMENT</span>
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
            
            <!-- Entity Inspector panel -->
            <div class="card">
                <div class="card-title">
                    <span>ENTITY INSPECTOR</span>
                    <span class="card-title-icon">🔍</span>
                </div>
                <div class="inspector-search">
                    <input type="number" id="inspector-input" class="input-dark" placeholder="Enter Entity ID..." min="0">
                    <button class="btn-blue" onclick="performEntityInspection()">INSPECT</button>
                </div>
                <div class="inspector-results" id="inspector-results-container">
                    <div class="inspector-empty">Enter an entity ID above to inspect goals, position, routine, and historical event timeline.</div>
                </div>
            </div>
        </div>
        
        <!-- Right Panel: WebSocket event logs -->
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
                    <span class="filter-label">Severity Min:</span>
                    <button class="filter-pill active" onclick="setSeverityFilter('DEBUG', this)">DEBUG</button>
                    <button class="filter-pill" onclick="setSeverityFilter('INFO', this)">INFO</button>
                    <button class="filter-pill" onclick="setSeverityFilter('WARNING', this)">WARNING</button>
                    <button class="filter-pill" onclick="setSeverityFilter('ERROR', this)">ERROR</button>
                </div>
            </div>
            
            <div class="terminal">
                <div class="terminal-header">
                    <span>LIVE EVENTS STREAM TICKER</span>
                    <div style="display: flex; gap: 1rem; align-items: center;">
                        <label style="cursor: pointer; display: flex; align-items: center; gap: 0.25rem;">
                            <input type="checkbox" id="autoscroll-chk" checked> Auto-Scroll
                        </label>
                        <span id="events-count" style="color: #60A5FA; font-weight: 600;">0 events</span>
                    </div>
                </div>
                <div class="terminal-body" id="event-ticker-body">
                    <!-- Events will dynamically append here -->
                </div>
            </div>
        </div>
    </div>
    
    <script>
        let wsClient = null;
        let activeCategory = '';
        let activeSeverity = 'DEBUG';
        let eventsArray = [];
        
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
                    
                    document.getElementById('val-tick').textContent = status.tick_count;
                    document.getElementById('val-compute').textContent = `${status.tick_compute_time_ms.toFixed(2)} ms`;
                    document.getElementById('val-memory').textContent = `${status.memory_rss_mb.toFixed(1)} MB`;
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
            el.textContent = count;
            if (count > 0) {
                el.className = 'anomaly-count has-count';
            } else {
                el.className = 'anomaly-count zero';
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
