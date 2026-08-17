import pytest
import asyncio
import json
import subprocess
import time
import websockets
import os
import requests

@pytest.mark.anyio
async def test_observability_websocket_suite():
    """Exhaustively verify WebSocket live events API handshake, filtering, heartbeats, and limits."""
    port = 8019
    env = os.environ.copy()
    env["SIM_OBS_MODE"] = "DEBUG"
    
    log_file = open("uvicorn_ws_obs.log", "w")
    
    # Start the V2 API server uvicorn subprocess
    cmd = ["python3", "-m", "src", "serve", "--port", str(port), "--log-level", "INFO"]
    server = subprocess.Popen(cmd, env=env, stdout=log_file, stderr=log_file)
    time.sleep(4.0)  # Wait for uvicorn server to initialize completely
    
    try:
        base_url = f"ws://127.0.0.1:{port}/api/v1/ws/observability/events"

        # 1. Test Valid Handshake, Ack, and Heartbeat
        async with websockets.connect(base_url) as ws:
            # Check subscription_ack message
            resp = await asyncio.wait_for(ws.recv(), timeout=3.0)
            data = json.loads(resp)
            assert data["type"] == "subscription_ack"
            assert data["filters"] == {}

            # Wait for a heartbeat. The default server runs a live, continuously-ticking
            # simulation broadcasting real domain events (combat/economy/etc.) much faster
            # than the 5s heartbeat interval -- a small fixed read count can exhaust itself
            # entirely on real events still ahead of the heartbeat in the FIFO queue. Drain
            # on an overall wall-clock deadline instead of a message count, so several
            # heartbeat intervals are guaranteed to elapse regardless of event volume.
            has_heartbeat = False
            deadline = asyncio.get_event_loop().time() + 20.0
            while asyncio.get_event_loop().time() < deadline:
                resp = await asyncio.wait_for(ws.recv(), timeout=6.0)
                data = json.loads(resp)
                if data["type"] == "heartbeat":
                    assert "timestamp" in data
                    has_heartbeat = True
                    break
            assert has_heartbeat, "Did not receive keep-alive heartbeat message"

        # 2. Test Parameter Validation & Reject Unknown Parameters
        async with websockets.connect(f"{base_url}?unknown_param=hello") as ws:
            resp = await asyncio.wait_for(ws.recv(), timeout=3.0)
            data = json.loads(resp)
            assert data["type"] == "error"
            assert "Unsupported query parameter" in data["message"]
            with pytest.raises(websockets.exceptions.ConnectionClosed) as exc_info:
                await ws.recv()
            assert exc_info.value.code == 1003

        # 3. Test Parameter Validation & Reject Invalid Severity
        async with websockets.connect(f"{base_url}?severity_min=DUMMY") as ws:
            resp = await asyncio.wait_for(ws.recv(), timeout=3.0)
            data = json.loads(resp)
            assert data["type"] == "error"
            assert "Invalid severity_min" in data["message"]
            with pytest.raises(websockets.exceptions.ConnectionClosed) as exc_info:
                await ws.recv()
            assert exc_info.value.code == 1003

        # 4. Test Parameter Validation & Reject Invalid Entity ID Format
        async with websockets.connect(f"{base_url}?entity_id=abc") as ws:
            resp = await asyncio.wait_for(ws.recv(), timeout=3.0)
            data = json.loads(resp)
            assert data["type"] == "error"
            assert "Invalid entity_id format" in data["message"]
            with pytest.raises(websockets.exceptions.ConnectionClosed) as exc_info:
                await ws.recv()
            assert exc_info.value.code == 1003

        # 5. Test Live Event Delivery and Filtering
        async with websockets.connect(f"{base_url}?severity_min=INFO&category=movement") as ws:
            # Check subscription_ack
            resp = await asyncio.wait_for(ws.recv(), timeout=3.0)
            data = json.loads(resp)
            assert data["type"] == "subscription_ack"
            assert data["filters"]["event_category"] == "movement"
            assert data["filters"]["severity_min"] == "INFO"

            # Trigger a test movement event via the server HTTP endpoint
            ev_payload = {
                "event_type": "walk",
                "event_category": "movement",
                "tick": 10,
                "severity": "INFO",
                "source_system": "navigation",
                "message": "Hero moves to new location"
            }
            resp_post = requests.post(f"http://127.0.0.1:{port}/api/v1/test/publish_event", json=ev_payload)
            assert resp_post.status_code == 200

            # Check that we receive the movement category event
            event_received = False
            for _ in range(10):
                try:
                    resp = await asyncio.wait_for(ws.recv(), timeout=2.0)
                    data = json.loads(resp)
                    if data["type"] == "event":
                        assert data["event"]["event_category"] == "movement"
                        assert data["event"]["event_type"] == "walk"
                        event_received = True
                        break
                except asyncio.TimeoutError:
                    continue
            assert event_received, "Failed to receive movement event from stream"
            # If no lifecycle events occurred, that's fine, we verified the filter structure.

        # Wait for previous connections to fully close and clean up active subscribers count
        await asyncio.sleep(0.5)

        # 6. Test Max Subscribers Safety Limit (Max 10)
        clients = []
        try:
            # Open 10 valid connections
            for i in range(10):
                ws_client = await websockets.connect(base_url)
                # Read the initial subscription_ack to complete the connection process
                resp = await asyncio.wait_for(ws_client.recv(), timeout=3.0)
                data = json.loads(resp)
                assert data["type"] == "subscription_ack"
                clients.append(ws_client)

            # Try to connect the 11th subscriber
            async with websockets.connect(base_url) as ws11:
                resp = await asyncio.wait_for(ws11.recv(), timeout=3.0)
                data = json.loads(resp)
                assert data["type"] == "error"
                assert "Max subscribers capacity reached" in data["message"]
                with pytest.raises(websockets.exceptions.ConnectionClosed) as exc_info:
                    await ws11.recv()
                assert exc_info.value.code == 1008

        finally:
            # Safely close all concurrent connections
            for client in clients:
                await client.close()

    finally:
        server.kill()
        server.wait()
        log_file.close()
        # Clean up uvicorn log
        if os.path.exists("uvicorn_ws_obs.log"):
            os.remove("uvicorn_ws_obs.log")
