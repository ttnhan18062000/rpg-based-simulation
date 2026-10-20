"""GET /api/v1/entities/{id}/quests: the paged quest history (TCK-20261020-ENTITY-LIST-RETURNS-A-BOUNDED-SUMMARY-NOT-THE-FULL-DETAIL)."""
from __future__ import annotations

import hashlib

from fastapi.testclient import TestClient

from src.api.server import create_v2_app
from src.config.profiles import PROD_SMALL

KEY = "entity-quests-route-key"
SEED = 42


def _client():
    profile = PROD_SMALL.model_copy(update={"api_key_hashes": "probe:" + hashlib.sha256(KEY.encode()).hexdigest()})
    return TestClient(create_v2_app(profile, seed=SEED, world_id="sandbox_world"), headers={"X-API-Key": KEY})


def test_the_quest_history_route_pages_one_entitys_quests_and_rejects_what_it_cannot_serve():
    with _client() as client:
        listing = client.get("/api/v1/entities", params={"limit": 5}).json()
        assert listing["entities"], "the authored world presents entities"
        entity_id = listing["entities"][0]["id"]
        page = client.get(f"/api/v1/entities/{entity_id}/quests", params={"status": "all", "offset": 0, "limit": 10}).json()
        assert page["entity_id"] == entity_id and page["status"] == "all" and page["offset"] == 0 and page["limit"] == 10
        assert isinstance(page["quests"], list) and page["total"] >= len(page["quests"])
        assert client.get(f"/api/v1/entities/{entity_id}/quests", params={"status": "nonsense"}).status_code == 422  # live | terminal | all only
        assert "not found" in client.get("/api/v1/entities/987654/quests").json()["error"]
        # the list is a summary and the detail carries the totals the history pages through
        detail = client.get(f"/api/v1/entities/{entity_id}").json()
        assert detail["quests_total"] == client.get(f"/api/v1/entities/{entity_id}/quests").json()["total"]
        assert "counts" in listing["entities"][0] and "quests" not in listing["entities"][0]
