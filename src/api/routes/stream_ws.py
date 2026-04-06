"""WebSocket streaming — High-performance binary state synchronization."""

from __future__ import annotations

import asyncio
import logging
from typing import Any

from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect
from src.api.dependencies import get_engine_manager
from src.api.engine_manager import EngineManager
from src.api.presenters.world_presenter import WorldPresenter
from src.api.redis_client import get_async_redis
from src.core.models.snapshot import Snapshot
import msgpack
import json
from fastapi.encoders import jsonable_encoder

router = APIRouter()
logger = logging.getLogger(__name__)

@router.websocket("/ws")
async def stream_ws(
    websocket: WebSocket,
    manager: EngineManager = Depends(get_engine_manager)
):
    """
    WebSocket endpoint for real-time world state.
    Supports JSON and MessagePack (BWS protocol).
    """
    await websocket.accept()
    
    # 1. Protocol Negotiation (Handshake)
    try:
        # Expected: {"type": "handshake", "format": "json" | "msgpack"}
        handshake = await websocket.receive_json()
        if handshake.get("type") != "handshake":
            await websocket.close(code=1003, reason="Missing handshake")
            return
            
        fmt = handshake.get("format", "json")
        mode = "compact" if fmt == "msgpack" else "rich"
        logger.info(f"WebSocket client connected (format={fmt}, mode={mode})")
        
    except Exception as e:
        logger.error(f"WebSocket handshake failed: {e}")
        await websocket.close(code=1003)
        return

    # 2. Redis Subscription Loop
    r = get_async_redis()
    # "$" means "only messages started after this moment"
    # However, for a fresh connection, we might want the CURRENT state first.
    last_id = "$"
    
    # Send initial full state (Rich/Compact based on mode)
    initial_snap = manager.get_snapshot()
    if initial_snap:
        # We don't have events for the initial dump, or we could fetch them.
        # For simplicity, just send the entities.
        initial_payload = WorldPresenter.to_compact_tick(initial_snap, [], mode=mode)
        if fmt == "msgpack":
            serialized = msgpack.packb(jsonable_encoder(initial_payload), use_bin_type=True)
            await websocket.send_bytes(serialized)
        else:
            serialized = json.dumps(jsonable_encoder(initial_payload))
            await websocket.send_text(serialized)

    try:
        while True:
            # Block wait for new tick in Redis
            response = await r.xread({"sim:stream": last_id}, count=1, block=1000)
            
            if response:
                stream_name, messages = response[0]
                msg_id, msg_data = messages[0]
                last_id = msg_id
                
                # Canonicalization: Consume pre-computed payloads from Redis (Pillar 5)
                # These are produced by the engine's PersistencePhase.
                raw_payload = msg_data.get(mode)
                
                if raw_payload:
                    # Redis fields are strings, but we need to (re)encode for BWS/JSON
                    # In a true high-perf scenario, we'd store pre-baked msgpack in Redis.
                    # For now, we take the JSON dict and encode.
                    payload = json.loads(raw_payload)
                    
                    if fmt == "msgpack":
                        serialized = msgpack.packb(jsonable_encoder(payload), use_bin_type=True)
                        await websocket.send_bytes(serialized)
                    else:
                        # Optimization: since it's already JSON from Redis, just send it!
                        await websocket.send_text(raw_payload)
                        
    except WebSocketDisconnect:
        logger.info("WebSocket client disconnected")
    except Exception as e:
        logger.error(f"WebSocket stream error: {e}")
        await websocket.close(code=1011)
