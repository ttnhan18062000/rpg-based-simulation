import hashlib
import pytest
import asyncio
import json
import subprocess
import time
import websockets
import msgpack
import os

_TEST_CLIENT_ID = "ws-protocol-test-client"
_TEST_RAW_KEY = "ws-protocol-test-key"
_TEST_KEY_HASH = hashlib.sha256(_TEST_RAW_KEY.encode("utf-8")).hexdigest()

@pytest.mark.anyio
async def test_ws_json_handshake():
    """Verify WebSocket handshake and streaming in JSON mode."""
    port = 8004
    cmd = ["python3", "-m", "src", "serve", "--port", str(port), "--log-level", "ERROR"]
    env = {**os.environ, "RPG_API_KEY_HASHES": f"{_TEST_CLIENT_ID}:{_TEST_KEY_HASH}"}
    server = subprocess.Popen(cmd, env=env)
    time.sleep(3)

    try:
        async with websockets.connect(
            f"ws://127.0.0.1:{port}/api/v1/ws", additional_headers={"X-API-Key": _TEST_RAW_KEY}
        ) as ws:
            # 1. Handshake
            await ws.send(json.dumps({"type": "handshake", "format": "json"}))
            
            # 2. Receive initial state
            resp = await ws.recv()
            data = json.loads(resp)
            assert "tick" in data
            assert data["seed"] == 42
            
            # 3. Receive next tick (might take a bit depending on tick_rate)
            resp = await asyncio.wait_for(ws.recv(), timeout=5.0)
            data = json.loads(resp)
            assert "tick" in data
            
    finally:
        server.terminate()
        server.wait()

@pytest.mark.anyio
async def test_ws_msgpack_handshake():
    """Verify WebSocket handshake and streaming in MessagePack mode."""
    port = 8005
    cmd = ["python3", "-m", "src", "serve", "--port", str(port), "--log-level", "ERROR"]
    env = {**os.environ, "RPG_API_KEY_HASHES": f"{_TEST_CLIENT_ID}:{_TEST_KEY_HASH}"}
    server = subprocess.Popen(cmd, env=env)
    time.sleep(3)

    try:
        async with websockets.connect(
            f"ws://127.0.0.1:{port}/api/v1/ws", additional_headers={"X-API-Key": _TEST_RAW_KEY}
        ) as ws:
            # 1. Handshake
            await ws.send(json.dumps({"type": "handshake", "format": "msgpack"}))
            
            # 2. Receive initial state (bytes)
            resp = await ws.recv()
            assert isinstance(resp, bytes)
            data = msgpack.unpackb(resp)
            assert data["tick"] >= 0
            
    finally:
        server.terminate()
        server.wait()

@pytest.mark.anyio
async def test_ws_msgpack_delta_payload_shape():
    """Verify the per-tick entity-delta broadcast round-trips over msgpack with the expected
    changed/removed/tick/snapshot_as_of_tick shape (TCK-20260821-WS-ENTITY-DELTA-BROADCAST)."""
    port = 8006
    cmd = ["python3", "-m", "src", "serve", "--port", str(port), "--log-level", "ERROR"]
    env = {**os.environ, "RPG_API_KEY_HASHES": f"{_TEST_CLIENT_ID}:{_TEST_KEY_HASH}"}
    server = subprocess.Popen(cmd, env=env)
    time.sleep(3)

    try:
        async with websockets.connect(
            f"ws://127.0.0.1:{port}/api/v1/ws", additional_headers={"X-API-Key": _TEST_RAW_KEY}
        ) as ws:
            await ws.send(json.dumps({"type": "handshake", "format": "msgpack"}))

            # Initial connect-time minimal-summary payload -- unchanged shape, not the delta.
            resp = await ws.recv()
            assert isinstance(resp, bytes)
            initial = msgpack.unpackb(resp)
            assert "tick" in initial

            # First real per-tick delta message.
            resp = await asyncio.wait_for(ws.recv(), timeout=5.0)
            assert isinstance(resp, bytes)
            data = msgpack.unpackb(resp)

            assert "changed" in data
            assert "removed" in data
            assert "tick" in data
            assert "snapshot_as_of_tick" in data
            assert isinstance(data["changed"], list)
            assert isinstance(data["removed"], list)
            assert data["snapshot_as_of_tick"] == initial["tick"]

    finally:
        server.terminate()
        server.wait()


if __name__ == "__main__":
    asyncio.run(test_ws_json_handshake())
    asyncio.run(test_ws_msgpack_handshake())
    print("WS Tests Passed!")
