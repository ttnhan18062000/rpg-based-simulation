"""The real API app records request durations by route template on the registry the API's /metrics route serves (issue #622, R2)."""
from __future__ import annotations

import hashlib

from fastapi.testclient import TestClient
from prometheus_client import generate_latest

from src.api.dependencies import get_engine_manager
from src.api.http_metrics import METRIC_NAME, UNMATCHED_ROUTE
from src.api.server import create_v2_app
from src.config.profiles import PROD_SMALL

KEY = "request-duration-probe"


def test_the_metrics_registry_shows_template_labels_and_never_a_raw_path():
    profile = PROD_SMALL.model_copy(update={"api_key_hashes": "probe:" + hashlib.sha256(KEY.encode()).hexdigest()})
    app = create_v2_app(profile, seed=42, world_id="sandbox_world")
    with TestClient(app, headers={"X-API-Key": KEY}) as client:
        client.get("/health")
        for entity_id in (1, 2, 987654):
            client.get(f"/api/v1/entities/{entity_id}")
        client.get("/definitely/not/a/route/12345")
        text = generate_latest(get_engine_manager().metrics_registry).decode()
    series = [line for line in text.splitlines() if line.startswith(f"{METRIC_NAME}_count")]
    assert any('route="/health"' in line for line in series)
    assert any('route="/api/v1/entities/{entity_id}"' in line for line in series)
    assert any(f'route="{UNMATCHED_ROUTE}"' in line for line in series)
    assert not any(raw in line for line in series for raw in ("987654", "12345")), series
