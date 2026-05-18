import pytest
import asyncio
import json
import subprocess
import time
import websockets
import msgpack
import os

@pytest.mark.asyncio
async def test_ws_json_handshake():
    """Verify WebSocket handshake and streaming in JSON mode."""
    port = 8004
    cmd = ["python3", "-m", "src", "serve", "--port", str(port), "--log-level", "ERROR"]
    server = subprocess.Popen(cmd)
    time.sleep(3)
    
    try:
        async with websockets.connect(f"ws://127.0.0.1:{port}/api/v1/ws") as ws:
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

@pytest.mark.asyncio
async def test_ws_msgpack_handshake():
    """Verify WebSocket handshake and streaming in MessagePack mode."""
    port = 8005
    cmd = ["python3", "-m", "src", "serve", "--port", str(port), "--log-level", "ERROR"]
    server = subprocess.Popen(cmd)
    time.sleep(3)
    
    try:
        async with websockets.connect(f"ws://127.0.0.1:{port}/api/v1/ws") as ws:
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

if __name__ == "__main__":
    asyncio.run(test_ws_json_handshake())
    asyncio.run(test_ws_msgpack_handshake())
    print("WS Tests Passed!")
