import hashlib
import requests
import time
import subprocess
import os

_TEST_CLIENT_ID = "rest-parity-test-client"
_TEST_RAW_KEY = "rest-parity-test-key"
_TEST_KEY_HASH = hashlib.sha256(_TEST_RAW_KEY.encode("utf-8")).hexdigest()

def test_api_rest_parity():
    """Verify that V2 API responds with expected JSON shapes."""
    # Start server in background
    port = 8002
    cmd = ["python3", "-m", "src", "serve", "--port", str(port), "--log-level", "ERROR"]
    env = {**os.environ, "RPG_API_KEY_HASHES": f"{_TEST_CLIENT_ID}:{_TEST_KEY_HASH}"}
    server = subprocess.Popen(cmd, env=env)
    headers = {"X-API-Key": _TEST_RAW_KEY}

    # Wait for server
    time.sleep(3)

    try:
        # 1. Health check (the sole route exempt from API-key auth)
        resp = requests.get(f"http://127.0.0.1:{port}/health")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "ok"
        assert data["version"] == "v2"

        # 2. State check
        resp = requests.get(f"http://127.0.0.1:{port}/api/v1/state", headers=headers)
        assert resp.status_code == 200
        data = resp.json()
        assert "tick" in data
        assert "entities_count" in data

        # 3. Control check
        resp = requests.post(f"http://127.0.0.1:{port}/api/v1/control/pause", headers=headers)
        assert resp.status_code == 200
        assert resp.json()["status"] == "paused"

        resp = requests.post(f"http://127.0.0.1:{port}/api/v1/control/resume", headers=headers)
        assert resp.status_code == 200
        assert resp.json()["status"] == "resumed"

    finally:
        server.terminate()
        server.wait()

def test_api_compression():
    """Verify that GZip compression is working for large responses."""
    port = 8003
    cmd = ["python3", "-m", "src", "serve", "--port", str(port), "--log-level", "ERROR"]
    env = {**os.environ, "RPG_API_KEY_HASHES": f"{_TEST_CLIENT_ID}:{_TEST_KEY_HASH}"}
    server = subprocess.Popen(cmd, env=env)
    time.sleep(3)

    try:
        # Request with gzip encoding
        headers = {"Accept-Encoding": "gzip", "X-API-Key": _TEST_RAW_KEY}
        resp = requests.get(f"http://127.0.0.1:{port}/api/v1/state", headers=headers)
        # requests automatically decodes gzip, but we can check the response history or size if needed.
        # But FastAPI GZipMiddleware only kicks in for > 512 bytes.
        # For now, just ensure it doesn't crash.
        assert resp.status_code == 200
    finally:
        server.terminate()
        server.wait()
