from typing import TYPE_CHECKING, List, Dict, Any
if TYPE_CHECKING:
    from src.core.models.world_state import WorldState
    from src.api.schemas import WorldStateResponse, StaticDataResponse, EventSchema

class WorldPresenter:
    """Presenter to unify the world state API response."""

    @staticmethod
    def to_world_state_response(
        world: "WorldState", 
        events: List[Any], 
        selected_id: int | None = None,
        loot_duration: int = 3
    ) -> "WorldStateResponse":
        from src.api.schemas import (
            WorldStateResponse, 
            GroundItemSchema, 
            ResourceNodeStateSchema, 
            TreasureChestStateSchema, 
            BuildingStateSchema
        )
        from src.api.presenters.entity_presenter import EntityPresenter
        from src.api.presenters.event_presenter import EventPresenter

        # 1. Base Stats
        alive = [e for e in world.entities.values() if e.combat.alive]
        
        # 2. Map Ground Items
        ground = [
            GroundItemSchema(x=pos[0], y=pos[1], items=list(items))
            for pos, items in world.ground_items.items()
        ]

        # 3. Present Entities (Slim for all, Full for selected)
        entities_slim = [
            EntityPresenter.to_slim_schema(e, loot_duration)
            for e in alive
        ]
        
        selected_full = None
        if selected_id:
            sel_entity = world.entities.get(selected_id)
            if sel_entity:
                registry = getattr(world, "social_registry", None)
                selected_full = EntityPresenter.to_full_schema(sel_entity, loot_duration, registry)

        # 4. Filter and Present Events
        presented_events = [
            EventPresenter.to_schema(ev)
            for ev in events
        ]

        # 5. Object States (Dynamic)
        resources = [
            ResourceNodeStateSchema(
                node_id=id(node), # Internal ID or actual ID if exists
                remaining=node.remaining_harvests,
                is_available=node.is_available
            )
            for node in world.resources.values()
        ]
        
        chests = [
            TreasureChestStateSchema(
                chest_id=id(chest),
                looted=chest.looted,
                guard_entity_id=chest.guard_id
            )
            for chest in world.treasure_chests.values()
        ]
        
        # Buildings might not have state yet in all phases, but we map them uniformly
        buildings = [
            BuildingStateSchema(
                building_id=id(b),
                storage_used=0, # Simplified for now, or map building data if exists
                storage_max=b.storage_capacity if hasattr(b, "storage_capacity") else 0
            )
            for b in world.buildings.values()
        ]

        return WorldStateResponse(
            tick=world.tick,
            alive_count=len(alive),
            entities=entities_slim,
            selected_entity=selected_full,
            events=presented_events,
            ground_items=ground,
            resource_nodes=resources,
            treasure_chests=chests,
            buildings=buildings
        )

    @staticmethod
    def to_static_data_response(world: "WorldState") -> "StaticDataResponse":
        from src.api.schemas import (
            StaticDataResponse, 
            BuildingSchema, 
            ResourceNodeSchema, 
            TreasureChestSchema
        )
        
        # Note: id(obj) is a temporary surrogate for real persistent IDs if they are missing
        
        return StaticDataResponse(
            buildings=[
                BuildingSchema(
                    building_id=str(id(b)),
                    name=b.name,
                    x=b.pos.x,
                    y=b.pos.y,
                    building_type=b.kind,
                    owner_entity_id=b.owner_id
                )
                for b in world.buildings.values()
            ],
            resource_nodes=[
                ResourceNodeSchema(
                    node_id=id(n),
                    resource_type=n.kind,
                    name=n.name,
                    x=n.pos.x,
                    y=n.pos.y,
                    terrain=0, # Default terrain
                    yields_item=n.yield_item_id,
                    max_harvests=n.max_harvests,
                    respawn_cooldown=n.respawn_ticks,
                    harvest_ticks=n.harvest_ticks
                )
                for n in world.resources.values()
            ],
            treasure_chests=[
                TreasureChestSchema(
                    chest_id=id(c),
                    x=c.pos.x,
                    y=c.pos.y,
                    tier=c.tier
                )
                for c in world.treasure_chests.values()
            ],
            regions=[] # Add regions if WorldState has them
        )

    @staticmethod
    def to_compact_tick(world: "WorldState", events: List[Any], mode: str = "compact") -> Any:
        """
        Unifies tick encoding for WebSocket. 
        Matches WorldStateEncoder.encode_tick logic.
        """
        from src.api.presenters.entity_presenter import EntityPresenter
        from src.api.presenters.event_presenter import EventPresenter
        
        entities = [
            EntityPresenter.to_compact_list(e) if mode == "compact" else EntityPresenter.to_slim_schema(e)
            for e in world.entities.values()
            if e.combat.alive
        ]
        
        encoded_events = [
            EventPresenter.to_compact_list(ev) if mode == "compact" else EventPresenter.to_schema(ev)
            for ev in events
        ]
        
        if mode == "compact":
            # [tick, entities, events]
            return [world.tick, entities, encoded_events]
        else:
            # Rich dict mode (not Schema-bound, but consistent with legacy rich mode)
            return {
                "tick": world.tick,
                "entities": entities,
                "events": encoded_events,
                "alive_count": len(entities)
            }
