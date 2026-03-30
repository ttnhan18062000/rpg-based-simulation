"""GET /api/v1/state — dynamic entity & event data (polled by UI)."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query

from src.api.dependencies import get_engine_manager
from src.api.engine_manager import EngineManager
from src.api.schemas import (
    AttributeCapSchema,
    AttributeSchema,
    BuildingSchema,
    BuildingStateSchema,
    EffectSchema,
    EntitySchema,
    EntitySlimSchema,
    EventSchema,
    GroundItemSchema,
    LocationSchema,
    QuestSchema,
    RegionSchema,
    ResourceNodeSchema,
    ResourceNodeStateSchema,
    SimulationStats,
    SkillSchema,
    StaticDataResponse,
    TreasureChestSchema,
    TreasureChestStateSchema,
    WorldStateResponse,
    EntityInspectionSchema,
    SchedulerTimelineItemSchema
)

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

    loot_dur = manager.config.loot_duration
    slim_entities: list[EntitySlimSchema] = []
    selected_entity: EntitySchema | None = None

    from src.api.presenters.entity_presenter import EntityPresenter
    for e in snapshot.entities.values():
        if not e.combat.alive:
            continue
        
        # Standardized serialization (AOA Presentation Layer)
        slim_entities.append(EntityPresenter.to_slim_schema(e, loot_duration=loot_dur))
        
        if e.id == selected:
            selected_entity = EntityPresenter.to_full_schema(e, loot_duration=loot_dur)
            
    events = [
        EventSchema(tick=ev.tick, category=ev.category, message=ev.message,
                    entity_ids=list(ev.entity_ids), metadata=ev.metadata)
        for ev in manager.event_log.since_tick(since_tick)
    ]

    ground_items = [
        GroundItemSchema(x=x, y=y, items=list(items))
        for (x, y), items in snapshot.ground_items.items()
        if items
    ]

    # Dynamic world objects (Audit Point 3)
    res_nodes: list[ResourceNodeStateSchema] = [
        ResourceNodeStateSchema(node_id=n.node_id, remaining=n.remaining, is_available=n.is_available)
        for n in snapshot.resource_nodes
    ]
    chests: list[TreasureChestStateSchema] = []
    if hasattr(snapshot, 'treasure_chests'):
        chests = [
            TreasureChestStateSchema(chest_id=c.chest_id, looted=c.looted, guard_entity_id=c.guard_entity_id)
            for c in snapshot.treasure_chests
        ]
    
    building_states: list[BuildingStateSchema] = []
    for b in snapshot.buildings:
        if b.building_type == "hero_house":
            try:
                owner_id = int(b.building_id.split("_")[-1])
                owner = snapshot.entities.get(owner_id)
                if owner and owner.inventory and owner.inventory.home_storage:
                    hs = owner.inventory.home_storage
                    building_states.append(BuildingStateSchema(
                        building_id=b.building_id,
                        storage_items=list(hs.items),
                        storage_used=hs.used_slots,
                        storage_max=hs.max_slots,
                        storage_level=hs.level,
                    ))
            except (ValueError, IndexError):
                pass

    return WorldStateResponse(
        tick=snapshot.tick,
        alive_count=len(slim_entities),
        entities=slim_entities,
        selected_entity=selected_entity,
        events=events,
        ground_items=ground_items,
        resource_nodes=res_nodes,
        treasure_chests=chests,
        buildings=building_states,
        war_status={str(k): v for k, v in snapshot.war_status.items()},
        faction_aggression={str(k): v for k, v in snapshot.faction_aggression.items()},
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
    return EntityPresenter.to_inspection_schema(entity, manager.config.loot_duration)

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
    snapshot = manager.get_snapshot()
    if snapshot is None:
        raise HTTPException(status_code=503, detail="No snapshot available yet.")

    buildings = [
        BuildingSchema(
            building_id=b.building_id, name=b.name,
            x=b.pos.x, y=b.pos.y, building_type=b.building_type,
            owner_entity_id=int(b.building_id.split("_")[-1]) if b.building_type == "hero_house" else None
        )
        for b in snapshot.buildings
    ]

    resource_nodes = [
        ResourceNodeSchema(
            node_id=n.node_id, resource_type=n.resource_type, name=n.name,
            x=n.pos.x, y=n.pos.y, terrain=int(n.terrain),
            yields_item=n.yields_item,
            max_harvests=n.max_harvests,
            respawn_cooldown=n.respawn_cooldown,
            harvest_ticks=n.harvest_ticks,
        )
        for n in snapshot.resource_nodes
    ]

    treasure_chests = []
    if hasattr(snapshot, 'treasure_chests'):
        treasure_chests = [
            TreasureChestSchema(
                chest_id=c.chest_id, x=c.pos.x, y=c.pos.y,
                tier=c.tier,
            )
            for c in snapshot.treasure_chests
        ]

    regions = []
    if hasattr(snapshot, 'regions'):
        regions = [
            RegionSchema(
                region_id=r.region_id, name=r.name, terrain=int(r.terrain),
                center_x=r.center.x, center_y=r.center.y, radius=r.radius,
                difficulty=r.difficulty,
                owner_faction=r.owner_faction.name.lower() if r.owner_faction else None,
                influence=snapshot.region_control.get(r.region_id, 0.0),
                locations=[
                    LocationSchema(
                        location_id=loc.location_id, name=loc.name,
                        location_type=loc.location_type, x=loc.pos.x, y=loc.pos.y,
                        region_id=loc.region_id
                    ) for loc in r.locations
                ]
            )
            for r in snapshot.regions
        ]

    return StaticDataResponse(
        buildings=buildings,
        resource_nodes=resource_nodes,
        treasure_chests=treasure_chests,
        regions=regions,
    )
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
