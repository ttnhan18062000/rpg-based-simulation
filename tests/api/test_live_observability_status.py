from __future__ import annotations
import hashlib
import os
import subprocess
import sys
import requests
import time
import pytest

_TEST_CLIENT_ID = "live-observability-status-test-client"
_TEST_RAW_KEY = "live-observability-status-test-key"
_TEST_KEY_HASH = hashlib.sha256(_TEST_RAW_KEY.encode("utf-8")).hexdigest()

def test_live_observability_endpoints():
    """Verify live status and snapshot endpoints under running server."""
    port = 8011
    cmd = [sys.executable, "-m", "src", "serve", "--port", str(port), "--log-level", "ERROR"]
    env = {**os.environ, "RPG_API_KEY_HASHES": f"{_TEST_CLIENT_ID}:{_TEST_KEY_HASH}"}
    server = subprocess.Popen(cmd, env=env)
    headers = {"X-API-Key": _TEST_RAW_KEY}

    # Wait for server to boot
    time.sleep(3)

    try:
        # 1. Verify status endpoint returns RUNNING or PAUSED and the correct health status
        resp = requests.get(f"http://127.0.0.1:{port}/api/v1/observability/live/status", headers=headers)
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] in ("RUNNING", "PAUSED")
        assert "current_tick" in data
        assert "observability_mode" in data
        assert data["governor_mode"] in ("NORMAL", "CONSTRAINED", "DEGRADED", "CRITICAL")
        assert data["health_state"] in ("HEALTHY", "WARNING", "DEGRADED", "CRITICAL")

        # 2. Verify snapshot endpoint returns the correct categories
        resp = requests.get(f"http://127.0.0.1:{port}/api/v1/observability/live/snapshot", headers=headers)
        assert resp.status_code == 200
        snapshot_data = resp.json()
        assert "run_status" in snapshot_data
        assert "latest_world_metrics" in snapshot_data
        assert "latest_runtime_status" in snapshot_data

        # 3. Verify pause control transitions status to PAUSED
        resp = requests.post(f"http://127.0.0.1:{port}/api/v1/control/pause", headers=headers)
        assert resp.status_code == 200
        time.sleep(0.5)

        resp = requests.get(f"http://127.0.0.1:{port}/api/v1/observability/live/status", headers=headers)
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "PAUSED"

        # 4. Verify resume control transitions status back to RUNNING
        resp = requests.post(f"http://127.0.0.1:{port}/api/v1/control/resume", headers=headers)
        assert resp.status_code == 200
        time.sleep(0.5)

        resp = requests.get(f"http://127.0.0.1:{port}/api/v1/observability/live/status", headers=headers)
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "RUNNING"

    finally:
        server.terminate()
        server.wait()

def test_live_observability_endpoints_idle():
    """Verify live status and snapshot endpoints when manager is uninitialized."""
    from src.observability.live.snapshot_provider import LiveSnapshotProvider
    
    # Test provider directly when engine manager is not active/None
    status = LiveSnapshotProvider.get_status(None)
    assert status.status == "IDLE"
    assert status.health_state == "UNKNOWN"
    
    snapshot = LiveSnapshotProvider.get_snapshot(None)
    assert snapshot.run_status.status == "IDLE"
    assert len(snapshot.latest_world_metrics) == 0
