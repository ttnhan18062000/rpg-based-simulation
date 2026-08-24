from __future__ import annotations
import asyncio
import logging
import json
import msgpack
import threading
import time
import traceback
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends
from fastapi.encoders import jsonable_encoder

from src.api.dependencies import get_engine_manager
from src.api.engine_manager import V2EngineManager

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

        snapshot_as_of_tick = initial_payload.get("tick", 0) if initial_payload else 0

        while True:
            # Wait for next tick from queue
            payload = await queue.get()

            # payload is the same dict object handed to every registered listener
            # (_notify_listeners fans it out by reference) -- copy before mutating so
            # concurrent connections don't race on snapshot_as_of_tick.
            out_payload = dict(payload)
            out_payload["snapshot_as_of_tick"] = snapshot_as_of_tick

            if fmt == "msgpack":
                await websocket.send_bytes(msgpack.packb(jsonable_encoder(out_payload)))
            else:
                await websocket.send_json(jsonable_encoder(out_payload))
                
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
            initial_events = manager.get_entity_timeline_events(entity_id)
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


active_websocket_subscribers = 0
active_subscribers_lock = threading.Lock()

@router.websocket("/ws/observability/events")
async def stream_live_events_ws(
    websocket: WebSocket,
    manager: V2EngineManager = Depends(get_engine_manager)
):
    """
    WebSocket endpoint for real-time live event streaming with granular query-parameter filtering.
    """
    global active_websocket_subscribers
    
    # 1. Cap active connections
    with active_subscribers_lock:
        logger.info(f"New connection request. Active subscribers count: {active_websocket_subscribers}")
        if active_websocket_subscribers >= 10:
            await websocket.accept()
            await websocket.send_json({"type": "error", "message": "Max subscribers capacity reached"})
            await websocket.close(code=1008)
            return
        active_websocket_subscribers += 1
        logger.info(f"Connection accepted. Active subscribers count incremented to: {active_websocket_subscribers}")

    # 2. Parse and validate query filters
    errors = []
    severity_min = None
    entity_id = None
    event_category = None
    event_type = None
    region_id = None
    quest_id = None

    allowed_keys = {"severity_min", "entity_id", "category", "event_category", "event_type", "region_id", "quest_id"}
    for key in websocket.query_params.keys():
        if key not in allowed_keys:
            errors.append(f"Unsupported query parameter: {key}")

    if "severity_min" in websocket.query_params:
        sev = websocket.query_params["severity_min"].upper()
        if sev not in {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}:
            errors.append(f"Invalid severity_min: {sev}")
        else:
            severity_min = sev

    cat_val = websocket.query_params.get("category") or websocket.query_params.get("event_category")
    if cat_val:
        cat = cat_val.lower()
        valid_categories = {
            "movement", "combat", "resource", "economy", "inventory",
            "quest", "strategy", "social", "lifecycle", "region",
            "infrastructure", "hard_law", "anomaly"
        }
        if cat not in valid_categories:
            errors.append(f"Invalid category: {cat_val}")
        else:
            event_category = cat

    if "entity_id" in websocket.query_params:
        ent_str = websocket.query_params["entity_id"]
        try:
            entity_id = int(ent_str)
        except ValueError:
            errors.append(f"Invalid entity_id format: {ent_str}")

    if "event_type" in websocket.query_params:
        event_type = websocket.query_params["event_type"]

    if "region_id" in websocket.query_params:
        region_id = websocket.query_params["region_id"]

    if "quest_id" in websocket.query_params:
        quest_id = websocket.query_params["quest_id"]

    if errors:
        await websocket.accept()
        await websocket.send_json({"type": "error", "message": "; ".join(errors)})
        await websocket.close(code=1003)
        with active_subscribers_lock:
            active_websocket_subscribers = max(0, active_websocket_subscribers - 1)
            logger.info(f"Connection rejected/failed validation. Active subscribers count decremented to: {active_websocket_subscribers}")
        return

    # Accept connection and register subscription
    await websocket.accept()
    
    send_lock = asyncio.Lock()

    async def safe_send_json(data):
        async with send_lock:
            await websocket.send_json(data)
    
    from src.observability.live.event_publisher import SubscriptionFilter, LiveEventSubscriber, LiveEventPublisher

    filter_obj = SubscriptionFilter(
        event_type=event_type,
        event_category=event_category,
        severity_min=severity_min,
        entity_id=entity_id,
        region_id=region_id,
        quest_id=quest_id
    )
    subscriber = LiveEventSubscriber(filter_obj=filter_obj, capacity=500)
    publisher = LiveEventPublisher.get_instance()
    publisher.register(subscriber)

    logger.info(f"WebSocket live events subscriber connected with filter: {filter_obj}")

    # Send subscription_ack
    resolved_filters = {k: v for k, v in filter_obj.model_dump().items() if v is not None}
    await safe_send_json({
        "type": "subscription_ack",
        "filters": resolved_filters
    })

    # Spin up concurrent heartbeat task
    async def heartbeat_loop():
        try:
            while True:
                await asyncio.sleep(5.0)
                await safe_send_json({
                    "type": "heartbeat",
                    "timestamp": time.time()
                })
        except (asyncio.CancelledError, WebSocketDisconnect):
            pass
        except Exception as e:
            logger.error(f"Error in WebSocket heartbeat task: {traceback.format_exc()}")

    # Spin up concurrent receive task to instantly detect client-initiated disconnects
    async def receive_loop():
        try:
            while True:
                await websocket.receive_text()
        except WebSocketDisconnect:
            pass
        except Exception:
            pass

    receive_task = asyncio.create_task(receive_loop())
    heartbeat_task = asyncio.create_task(heartbeat_loop())
    last_dropped_count = 0

    try:
        while True:
            # Check if client disconnected via the receive task
            if receive_task.done():
                raise WebSocketDisconnect()
            # Check for backpressure threshold disconnection
            if subscriber.disconnect_flag:
                logger.warning("Subscriber disconnected due to backpressure threshold")
                await safe_send_json({"type": "error", "message": "Connection closed due to slow consumer backpressure"})
                await websocket.close(code=1008)
                break

            # Send dropped event notice if count increases
            current_drops = subscriber.dropped_count
            if current_drops > last_dropped_count:
                await safe_send_json({
                    "type": "dropped_event_notice",
                    "dropped_count": current_drops
                })
                last_dropped_count = current_drops

            # Broadcast matching events
            events = subscriber.get_events()
            for event in events:
                payload = {
                    "type": "event",
                    "run_id": getattr(event, "run_id", None),
                    "event": event.model_dump()
                }
                await safe_send_json(jsonable_encoder(payload))

            # Paced execution check
            await asyncio.sleep(0.05)

    except WebSocketDisconnect:
        logger.info("WebSocket live events client disconnected")
    except Exception as e:
        logger.error(f"WebSocket live events error: {traceback.format_exc()}")
        try:
            await websocket.close(code=1011)
        except Exception:
            pass
    finally:
        # Cancel receive task
        receive_task.cancel()
        # Cancel keep-alive heartbeat
        heartbeat_task.cancel()
        # Unregister subscriber
        publisher.unregister(subscriber)
        # Decrement active subscribers count
        with active_subscribers_lock:
            active_websocket_subscribers = max(0, active_websocket_subscribers - 1)
            logger.info(f"Connection closed. Active subscribers count decremented to: {active_websocket_subscribers}")

