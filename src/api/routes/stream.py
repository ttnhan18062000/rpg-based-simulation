"""GET /api/v1/stream — Server-Sent Events (SSE) state streaming."""

from __future__ import annotations

import asyncio
import json
import logging
from typing import AsyncGenerator

from fastapi import APIRouter, Depends, HTTPException, Request
from sse_starlette.sse import EventSourceResponse

from src.api.dependencies import get_engine_manager
from src.api.engine_manager import EngineManager
from src.api.schemas import EntitySlimSchema, EventSchema
from src.api.routes.state import _get_weapon_range
from src.core.snapshot import Snapshot
from src.utils.event_log import SimEvent

router = APIRouter()
logger = logging.getLogger(__name__)


def _snapshot_to_slim_dict(snapshot: Snapshot, loot_duration: int) -> dict[int, EntitySlimSchema]:
    """Convert snapshot entities to a dict of fast serializable SlimSchemas."""
    res = {}
    for eid, e in snapshot.entities.items():
        if not e.alive:
            continue
        res[eid] = EntitySlimSchema(
            id=e.id,
            kind=e.kind,
            x=e.pos.x,
            y=e.pos.y,
            hp=e.stats.hp,
            max_hp=e.stats.max_hp,
            state=e.ai_state.name,
            level=e.stats.level,
            tier=e.tier,
            faction=e.faction.name.lower(),
            weapon_range=_get_weapon_range(e),
            combat_target_id=e.combat_target_id,
            loot_progress=e.loot_progress,
            loot_duration=loot_duration,
        )
    return res


def compute_delta(
    old_slim: dict[int, EntitySlimSchema],
    new_slim: dict[int, EntitySlimSchema],
    tick: int,
    events: list[SimEvent],
) -> str | None:
    """Compute diff between two snapshots. Returns JSON string of delta, or None if empty."""
    changed = []
    removed = []

    # Find changed & new
    for eid, e in new_slim.items():
        old_e = old_slim.get(eid)
        if old_e is None or old_e != e:
            changed.append(e.model_dump())

    # Find removed (died)
    for eid in old_slim:
        if eid not in new_slim:
            removed.append(eid)

    # Convert events
    serialized_events = [
        EventSchema(tick=ev.tick, category=ev.category, message=ev.message,
                    entity_ids=list(ev.entity_ids), metadata=ev.metadata).model_dump()
        for ev in events
    ]

    # Don't send empty updates to save bandwidth (unless tick is divisible by 20 to heartbeat)
    if not changed and not removed and not serialized_events and tick % 20 != 0:
        return None

    delta = {
        "tick": tick,
        "changed": changed,
        "removed": removed,
        "events": serialized_events,
    }
    
    # We output strict JSON to encode properly in Server-Sent Events
    return json.dumps(delta)


async def _stream_generator(request: Request, manager: EngineManager) -> AsyncGenerator[dict, None]:
    """Yields SSE events from the Redis stream."""
    import time
    from src.api.redis_client import get_async_redis

    # Start by capturing the initial state and dropping a full dump
    initial_snap = manager.get_snapshot()
    if not initial_snap:
        yield {"data": json.dumps({"error": "Engine not ready"})}
        return
        
    loot_duration = manager.config.loot_duration
    prev_slim = _snapshot_to_slim_dict(initial_snap, loot_duration)

    # We send the very first full snapshot so the frontend can populate its maps initially
    initial_delta = {
        "tick": initial_snap.tick,
        "changed": [e.model_dump() for e in prev_slim.values()],
        "removed": [],
        "events": [],
    }
    yield {"data": json.dumps(initial_delta)}

    r = get_async_redis()
    # We want to start reading from the exact moment we grabbed the snapshot.
    # "$" means "only messages appended to the stream from now on"
    last_id = "$"

    while True:
        if await request.is_disconnected():
            break

        try:
            # Block and wait for a single new tick to hit the stream
            # The structure returned by xread is:
            # [[stream_name, [(msg_id, {field: value}), ...]], ...]
            response = await r.xread({"sim:stream": last_id}, count=1, block=1000)
            
            if response:
                stream_name, messages = response[0]
                msg_id, msg_data = messages[0]
                
                # Advance the pointer
                last_id = msg_id
                
                # Extract the pre-computed JSON delta from EngineManager
                payload_json = msg_data.get("payload")
                
                if payload_json:
                    yield {"data": payload_json}
        
        except asyncio.CancelledError:
            break
        except Exception as e:
            logger.error(f"Stream generation error: {e}")
            await asyncio.sleep(1)


@router.get("", response_class=EventSourceResponse)
async def stream_state(
    request: Request,
    manager: EngineManager = Depends(get_engine_manager)
) -> EventSourceResponse:
    """Connect to a Server-Sent Events stream for realtime entity deltas."""
    if manager.get_snapshot() is None:
        raise HTTPException(status_code=503, detail="No snapshot available yet.")
        
    return EventSourceResponse(_stream_generator(request, manager))
