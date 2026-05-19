from __future__ import annotations
import asyncio
import logging
import json
import msgpack
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends
from fastapi.encoders import jsonable_encoder

from src.api.dependencies import get_engine_manager
from src.api.engine_manager import V2EngineManager
from src.core.state import AuthoritativeState

router = APIRouter()
logger = logging.getLogger(__name__)

@router.websocket("/ws")
async def stream_ws(
    websocket: WebSocket,
    manager: V2EngineManager = Depends(get_engine_manager)
):
    """
    V2 WebSocket endpoint for real-time state streaming.
    Matches legacy BWS protocol.
    """
    await websocket.accept()
    
    # 1. Protocol Negotiation
    try:
        handshake = await websocket.receive_json()
        if handshake.get("type") != "handshake":
            await websocket.close(code=1003, reason="Missing handshake")
            return
            
        fmt = handshake.get("format", "json")
        logger.info(f"V2 WebSocket client connected (format={fmt})")
    except Exception as e:
        logger.error(f"V2 WebSocket handshake failed: {e}")
        await websocket.close(code=1003)
        return

    queue = asyncio.Queue(maxsize=10)
    loop = asyncio.get_event_loop()

    from src.api.presenters.state_presenter import StatePresenter

    def on_tick(snapshot: Dict[str, Any]):
        # This runs in the engine thread, so we use call_soon_threadsafe
        loop.call_soon_threadsafe(queue.put_nowait, snapshot)

    manager.add_tick_listener(on_tick)

    try:
        # Send initial state
        initial_payload = manager.get_state()
        if initial_payload:
            if fmt == "msgpack":
                await websocket.send_bytes(msgpack.packb(jsonable_encoder(initial_payload)))
            else:
                await websocket.send_json(jsonable_encoder(initial_payload))

        while True:
            # Wait for next tick from queue
            payload = await queue.get()
            
            if fmt == "msgpack":
                await websocket.send_bytes(msgpack.packb(jsonable_encoder(payload)))
            else:
                await websocket.send_json(jsonable_encoder(payload))
                
    except WebSocketDisconnect:
        logger.info("V2 WebSocket client disconnected")
    except Exception as e:
        logger.error(f"V2 WebSocket error: {e}")
        await websocket.close(code=1011)
    finally:
        manager.remove_tick_listener(on_tick)


@router.websocket("/ws/observe")
async def stream_observe_ws(
    websocket: WebSocket,
    entity_id: int = None,
    manager: V2EngineManager = Depends(get_engine_manager)
):
    """
    WebSocket endpoint for real-time SimulationEvent streaming.
    Supports filtering by a specific entity_id and retrieves its initial timeline buffer.
    """
    await websocket.accept()
    
    # 1. Protocol Negotiation (Handshake)
    try:
        handshake = await websocket.receive_json()
        if handshake.get("type") != "handshake":
            await websocket.close(code=1003, reason="Missing handshake")
            return
        logger.info(f"SimulationEvent WebSocket client connected (entity_id={entity_id})")
    except Exception as e:
        logger.error(f"SimulationEvent WebSocket handshake failed: {e}")
        await websocket.close(code=1003)
        return

    from typing import List, Any
    queue = asyncio.Queue(maxsize=200)
    loop = asyncio.get_event_loop()

    def on_events(events: List[Any]):
        filtered = []
        for ev in events:
            if entity_id is None or ev.entity_id == entity_id:
                filtered.append(ev.model_dump())
        
        if filtered:
            try:
                loop.call_soon_threadsafe(queue.put_nowait, filtered)
            except asyncio.QueueFull:
                pass

    manager.add_event_listener(on_events)

    try:
        # Send initial event log if requested
        if entity_id is not None:
            initial_events = []
            state = manager._latest_state
            if state and entity_id in state.entities:
                entity = state.entities[entity_id]
                if hasattr(entity, "timeline") and entity.timeline:
                    initial_events = [ev.model_dump() for ev in entity.timeline]
            await websocket.send_json(jsonable_encoder(initial_events))

        while True:
            events_batch = await queue.get()
            await websocket.send_json(jsonable_encoder(events_batch))
            # Paced stream updates
            await asyncio.sleep(1 / 60)
            
    except WebSocketDisconnect:
        logger.info(f"SimulationEvent WebSocket client disconnected (entity_id={entity_id})")
    except Exception as e:
        logger.error(f"SimulationEvent WebSocket error: {e}")
        await websocket.close(code=1011)
    finally:
        manager.remove_event_listener(on_events)

