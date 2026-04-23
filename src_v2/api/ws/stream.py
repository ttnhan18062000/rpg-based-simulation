from __future__ import annotations
import asyncio
import logging
import json
import msgpack
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends
from fastapi.encoders import jsonable_encoder

from src_v2.api.dependencies import get_engine_manager
from src_v2.api.engine_manager import V2EngineManager
from src_v2.core.state import AuthoritativeState

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

    def on_tick(state: AuthoritativeState):
        # This runs in the engine thread, so we use call_soon_threadsafe
        payload = {
            "tick": state.tick,
            "entities_count": len(state.entities),
            "seed": state.seed
        }
        loop.call_soon_threadsafe(queue.put_nowait, payload)

    manager.add_tick_listener(on_tick)

    try:
        # Send initial state
        initial_state = manager.get_state()
        if initial_state:
            initial_payload = {
                "tick": initial_state.tick,
                "entities_count": len(initial_state.entities),
                "seed": initial_state.seed
            }
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
