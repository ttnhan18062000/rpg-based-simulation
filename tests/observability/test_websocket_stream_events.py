import pytest
import asyncio
import json
import subprocess
import time
import websockets
import os

@pytest.mark.anyio
async def test_ws_events_stream():
    """Verify WebSocket connection, handshake, and receipt of initial timeline buffer."""
    port = 8009
    env = os.environ.copy()
    env["OBSERVABILITY_MODE"] = "LIGHT"
    
    log_file = open("uvicorn.log", "w")
    
    # Run uvicorn server in a subprocess
    cmd = ["python3", "-m", "src", "serve", "--port", str(port), "--log-level", "INFO"]
    server = subprocess.Popen(cmd, env=env, stdout=log_file, stderr=log_file)
    time.sleep(4.0)  # Wait for uvicorn to fully boot
    
    try:
        # Connect to entity_id=0 (Hero) to get their initial timeline log
        async with websockets.connect(f"ws://127.0.0.1:{port}/api/v1/ws/observe?entity_id=0") as ws:
            # 1. Handshake
            await ws.send(json.dumps({"type": "handshake"}))
            
            # 2. Wait for initial timeline payload (an empty list since no events have occurred yet)
            resp = await asyncio.wait_for(ws.recv(), timeout=3.0)
            initial_timeline = json.loads(resp)
            
            assert isinstance(initial_timeline, list)
            print(f"Received initial timeline: {initial_timeline}")
            
    finally:
        server.kill()
        server.wait()
        log_file.close()

if __name__ == "__main__":
    asyncio.run(test_ws_events_stream())
    print("WS Events Stream Test Passed!")
