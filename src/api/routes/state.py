"""GET /api/v1/state — dynamic entity & event data (polled by UI)."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query

from src.api.dependencies import get_engine_manager
from src.api.engine_manager import EngineManager
from src.api.schemas import (
    StaticDataResponse,
    WorldStateResponse,
    EntityInspectionSchema,
    SchedulerTimelineItemSchema,
    SimulationStats
)
from src.api.presenters.world_presenter import WorldPresenter


router = APIRouter()



# --- Standardized serialization logic moved to src.core.models.Entity (epic-05) ---




@router.get("/state", response_model=WorldStateResponse)
def get_state(
    since_tick: int = Query(0, ge=0, description="Only return events since this tick"),
    selected: int = Query(-1, description="Entity ID to get full details for (-1 = none)"),
    manager: EngineManager = Depends(get_engine_manager),
) -> WorldStateResponse:
    snapshot = manager.get_snapshot()
    if snapshot is None:
        raise HTTPException(status_code=503, detail="No snapshot available yet.")

    # 1. Fetch relevant events
    events = manager.event_log.since_tick(since_tick)

    # 2. Present World State (Unified Presentation Layer)
    return WorldPresenter.to_world_state_response(
        snapshot, 
        events, 
        selected_id=selected if selected != -1 else None,
        loot_duration=manager.config.loot_duration
    )


@router.get("/inspect/{entity_id}", response_model=EntityInspectionSchema)
def inspect_entity(
    entity_id: int,
    manager: EngineManager = Depends(get_engine_manager),
) -> EntityInspectionSchema:
    snapshot = manager.get_snapshot()
    if snapshot is None:
        raise HTTPException(status_code=503, detail="No snapshot available yet.")
    
    entity = snapshot.entities.get(entity_id)
    if not entity:
        raise HTTPException(status_code=404, detail=f"Entity {entity_id} not found.")
        
    from src.api.presenters.entity_presenter import EntityPresenter
    registry = getattr(snapshot, "social_registry", None)
    return EntityPresenter.to_inspection_schema(entity, manager.config.loot_duration, registry, snapshot)

@router.get("/timeline", response_model=list[SchedulerTimelineItemSchema])
def get_timeline(
    limit: int = Query(20, ge=1, le=100),
    manager: EngineManager = Depends(get_engine_manager),
) -> list[SchedulerTimelineItemSchema]:
    snapshot = manager.get_snapshot()
    if snapshot is None:
        return []
        
    from src.api.presenters.scheduler_presenter import SchedulerPresenter
    return SchedulerPresenter.get_timeline(snapshot, limit)

@router.get("/static", response_model=StaticDataResponse)
def get_static(
    manager: EngineManager = Depends(get_engine_manager),
) -> StaticDataResponse:
    """Static world data — buildings, resource nodes, regions, chests. Fetch once."""
    static_data = manager.get_static_data()
    if static_data is None:
        raise HTTPException(status_code=503, detail="Static data not generated yet.")
    return static_data

@router.post("/clear_events")
def clear_events(
    manager: EngineManager = Depends(get_engine_manager),
) -> dict:
    """Clear all stored events."""
    manager.event_log.clear()
    return {"status": "ok"}


@router.get("/stats", response_model=SimulationStats)
def get_stats(
    manager: EngineManager = Depends(get_engine_manager),
) -> SimulationStats:
    snapshot = manager.get_snapshot()
    tick = snapshot.tick if snapshot else 0
    alive = sum(1 for e in snapshot.entities.values() if e.combat.alive) if snapshot else 0

    return SimulationStats(
        tick=tick,
        world_day=tick // 100,
        alive_count=alive,
        total_spawned=manager.total_spawned,
        total_deaths=manager.total_deaths,
        running=manager.running,
        paused=manager.paused,
    )
