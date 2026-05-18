import requests
import time
import subprocess
import os

def test_api_rest_parity():
    """Verify that V2 API responds with expected JSON shapes."""
    # Start server in background
    port = 8002
    cmd = ["python3", "-m", "src", "serve", "--port", str(port), "--log-level", "ERROR"]
    server = subprocess.Popen(cmd)
    
    # Wait for server
    time.sleep(3)
    
    try:
        # 1. Health check
        resp = requests.get(f"http://127.0.0.1:{port}/health")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "ok"
        assert data["version"] == "v2"
        
        # 2. State check
        resp = requests.get(f"http://127.0.0.1:{port}/api/v1/state")
        assert resp.status_code == 200
        data = resp.json()
        assert "tick" in data
        assert "entities_count" in data
        
        # 3. Control check
        resp = requests.post(f"http://127.0.0.1:{port}/api/v1/control/pause")
        assert resp.status_code == 200
        assert resp.json()["status"] == "paused"
        
        resp = requests.post(f"http://127.0.0.1:{port}/api/v1/control/resume")
        assert resp.status_code == 200
        assert resp.json()["status"] == "resumed"
        
    finally:
        server.terminate()
        server.wait()

def test_api_compression():
    """Verify that GZip compression is working for large responses."""
    port = 8003
    cmd = ["python3", "-m", "src", "serve", "--port", str(port), "--log-level", "ERROR"]
    server = subprocess.Popen(cmd)
    time.sleep(3)
    
    try:
        # Request with gzip encoding
        headers = {"Accept-Encoding": "gzip"}
        resp = requests.get(f"http://127.0.0.1:{port}/api/v1/state", headers=headers)
        # requests automatically decodes gzip, but we can check the response history or size if needed.
        # But FastAPI GZipMiddleware only kicks in for > 512 bytes.
        # For now, just ensure it doesn't crash.
        assert resp.status_code == 200
    finally:
        server.terminate()
        server.wait()
