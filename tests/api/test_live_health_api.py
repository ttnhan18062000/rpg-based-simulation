import hashlib
import pytest
import subprocess
import time
import os
import requests

_TEST_CLIENT_ID = "live-health-api-test-client"
_TEST_RAW_KEY = "live-health-api-test-key"
_TEST_KEY_HASH = hashlib.sha256(_TEST_RAW_KEY.encode("utf-8")).hexdigest()

@pytest.mark.anyio
async def test_live_health_api_suite():
    """Exhaustively verify Live Health, Observatory UI, and redirection endpoints."""
    port = 8021
    env = os.environ.copy()
    env["SIM_OBS_MODE"] = "DEBUG"
    env["RPG_API_KEY_HASHES"] = f"{_TEST_CLIENT_ID}:{_TEST_KEY_HASH}"
    headers = {"X-API-Key": _TEST_RAW_KEY}

    log_file = open("uvicorn_health_obs.log", "w")

    # Start the V2 API server uvicorn subprocess
    cmd = ["python3", "-m", "src", "serve", "--port", str(port), "--log-level", "INFO"]
    server = subprocess.Popen(cmd, env=env, stdout=log_file, stderr=log_file)
    time.sleep(4.0)  # Wait for uvicorn server to initialize completely

    try:
        # 1. Test GET /api/v1/observability/live/health default response
        url_health = f"http://127.0.0.1:{port}/api/v1/observability/live/health"
        resp = requests.get(url_health, headers=headers)
        assert resp.status_code == 200
        data = resp.json()
        assert "health_state" in data
        assert "counters" in data
        assert "reasons" in data

        # Initially, since engine is initializing: health should be UNKNOWN, HEALTHY, or DEGRADED depending on status
        assert data["health_state"] in ("UNKNOWN", "HEALTHY", "DEGRADED")

        # 2. Test GET /api/v1/observability/ui serves the HTML dashboard
        url_ui = f"http://127.0.0.1:{port}/api/v1/observability/ui"
        resp_ui = requests.get(url_ui, headers=headers)
        assert resp_ui.status_code == 200
        assert "text/html" in resp_ui.headers.get("content-type", "")
        assert "V2 Simulation Live Observatory" in resp_ui.text
        assert "LIVE DEVELOPER OBSERVATORY" in resp_ui.text

        # 3. Test Redirects
        # 3a. /observability/ui redirect
        url_redirect1 = f"http://127.0.0.1:{port}/observability/ui"
        resp_red1 = requests.get(url_redirect1, headers=headers, allow_redirects=False)
        assert resp_red1.status_code in (302, 307)
        assert resp_red1.headers.get("location") == "/api/v1/observability/ui"

        # 3b. /api/v1/observability/live/ui redirect
        url_redirect2 = f"http://127.0.0.1:{port}/api/v1/observability/live/ui"
        resp_red2 = requests.get(url_redirect2, headers=headers, allow_redirects=False)
        assert resp_red2.status_code in (302, 307)
        assert resp_red2.headers.get("location") == "/api/v1/observability/ui"

        # 4. Trigger anomalies and check live health counter updates
        url_publish = f"http://127.0.0.1:{port}/api/v1/test/publish_event"

        # Publish navigation stuck anomaly
        payload_stuck = {
            "event_type": "NavigationStuck",
            "event_category": "anomaly",
            "severity": "WARNING",
            "message": "Actor stuck in rock"
        }
        res_pub1 = requests.post(url_publish, json=payload_stuck, headers=headers)
        assert res_pub1.status_code == 200

        # Publish hard law violation anomaly
        payload_law = {
            "event_type": "InvariantViolation",
            "event_category": "hard_law",
            "severity": "ERROR",
            "message": "Hard law constraint broken!"
        }
        res_pub2 = requests.post(url_publish, json=payload_law, headers=headers)
        assert res_pub2.status_code == 200

        # Re-fetch health and confirm counters updated and health transitioned to CRITICAL
        resp_health_after = requests.get(url_health, headers=headers)
        assert resp_health_after.status_code == 200
        health_data = resp_health_after.json()
        
        assert health_data["counters"]["navigation_stuck_count"] == 1
        assert health_data["counters"]["hard_law_violation_count"] == 1
        assert health_data["health_state"] == "CRITICAL"
        assert "Critical hard law violation" in "".join(health_data["reasons"])

    finally:
        server.kill()
        server.wait()
        log_file.close()
        # Clean up uvicorn log
        if os.path.exists("uvicorn_health_obs.log"):
            os.remove("uvicorn_health_obs.log")
