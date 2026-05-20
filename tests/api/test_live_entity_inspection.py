from __future__ import annotations
import subprocess
import requests
import time
import pytest

def test_live_entity_inspection():
    """Verify live entity inspection endpoints under a running server."""
    port = 8012
    cmd = ["python3", "-m", "src", "serve", "--port", str(port), "--log-level", "ERROR"]
    server = subprocess.Popen(cmd)
    
    # Wait for server to boot
    time.sleep(3)
    
    try:
        # 1. Inspect a missing/invalid entity ID (should return 404)
        resp = requests.get(f"http://127.0.0.1:{port}/api/v1/observability/live/entities/9999")
        assert resp.status_code == 404
        
        # 2. Retrieve paged entities list to find an active entity
        resp = requests.get(f"http://127.0.0.1:{port}/api/v1/entities")
        assert resp.status_code == 200
        entities_data = resp.json()
        assert "entities" in entities_data
        
        # If active entities are present, inspect the first one
        if len(entities_data["entities"]) > 0:
            valid_id = entities_data["entities"][0]["id"]
            
            resp = requests.get(f"http://127.0.0.1:{port}/api/v1/observability/live/entities/{valid_id}")
            assert resp.status_code == 200
            snapshot = resp.json()
            assert snapshot["entity_id"] == valid_id
            assert snapshot["exists"]
            assert "alive" in snapshot
            assert "position" in snapshot
            assert "combat_summary" in snapshot
            assert "inventory_summary" in snapshot
            assert "quest_summary" in snapshot
            assert "strategic_summary" in snapshot
            assert "recent_timeline_events" in snapshot
            
            # 3. Test timeline limit query parameter
            resp_lim = requests.get(f"http://127.0.0.1:{port}/api/v1/observability/live/entities/{valid_id}?timeline_limit=1")
            assert resp_lim.status_code == 200
            snapshot_lim = resp_lim.json()
            assert len(snapshot_lim["recent_timeline_events"]) <= 1
            
    finally:
        server.terminate()
        server.wait()
