"""
tests/api/test_chronicle_api.py
────────────────────────────────────────────────────────────────────────────────
Tests for chronicle REST endpoints:
  GET /api/v1/chronicle/{campaign_id}
  GET /api/v1/chronicle/{campaign_id}/eras/{era_id}/summary

Implemented for E51E (TCK-20260619-E51E-REST-API).

Test strategy:
  - Call the route handlers directly (no HTTP layer for unit tests).
  - Inject chronicle data via register_chronicle() / _clear_registry().
  - Assert shaped responses (presenter models), not raw dicts.
  - anyio marker required for async route handlers.
"""
from __future__ import annotations

import pytest
from fastapi import HTTPException

from src.api.routes.chronicle import (
    _clear_registry,
    get_chronicle,
    get_era_summary,
    register_chronicle,
)
from src.api.presenters.chronicle import (
    ChronicleEraPresenter,
    ChronicleEpisodePresenter,
    ChronicleMilestonePresenter,
    ChronicleResponse,
    ErasSummaryResponse,
)


# ── Fixtures ───────────────────────────────────────────────────────────────────


def _make_chronicle(
    campaign_id: str = "camp_test",
    with_eras: bool = True,
) -> dict:
    """Build a minimal chronicle.json dict for testing."""
    if not with_eras:
        return {
            "campaign_id": campaign_id,
            "eras": [],
            "episodes": [],
            "named_milestones": [],
        }

    return {
        "campaign_id": campaign_id,
        "eras": [
            {
                "id": "era:0",
                "ordinal": 0,
                "name": "Age of Conflict",
                "significance": 0.9,
                "episode_ids": ["episode:0", "episode:1", "episode:2"],
            },
            {
                "id": "era:1",
                "ordinal": 1,
                "name": "Age of Quests",
                "significance": 0.7,
                "episode_ids": ["episode:3", "episode:4", "episode:5"],
            },
        ],
        "episodes": [
            {"id": "episode:0", "index": 0, "significance": 0.8, "incident_ids": ["ep0:t5-55"]},
            {"id": "episode:1", "index": 1, "significance": 0.6, "incident_ids": []},
            {"id": "episode:2", "index": 2, "significance": 0.9, "incident_ids": ["ep2:t10-10"]},
            {"id": "episode:3", "index": 3, "significance": 0.7, "incident_ids": []},
            {"id": "episode:4", "index": 4, "significance": 0.5, "incident_ids": []},
            {"id": "episode:5", "index": 5, "significance": 0.6, "incident_ids": []},
        ],
        "named_milestones": [
            {
                "name": "Death of Goblin King",
                "tick": 5,
                "episode": 0,
                "event_type": "entity_death",
                "significance": 0.8,
                "entry_id": "0:5:entity_death:goblin_king",
            },
            {
                "name": "Battle at the Iron Gate",
                "tick": 55,
                "episode": 0,
                "event_type": "entity_death",
                "significance": 0.9,
                "entry_id": "0:55:entity_death:iron_guard",
            },
            {
                "name": "Siege of the Ancient Tower",
                "tick": 10,
                "episode": 2,
                "event_type": "faction_shift",
                "significance": 0.9,
                "entry_id": "2:10:faction_shift:tower_faction",
            },
            {
                "name": "Quest for the Lost Relic",
                "tick": 20,
                "episode": 3,
                "event_type": "quest_completed",
                "significance": 0.7,
                "entry_id": "3:20:quest_completed:relic_q",
            },
        ],
    }


@pytest.fixture(autouse=True)
def clear_registry():
    """Ensure the chronicle registry is clean before and after each test."""
    _clear_registry()
    yield
    _clear_registry()


# ── TC-1: test_chronicle_rest_endpoint_returns_structured_json (AC-1) ─────────


@pytest.mark.anyio
async def test_chronicle_rest_endpoint_returns_structured_json():
    """AC-required: endpoint returns full structured chronicle as shaped JSON."""
    data = _make_chronicle("camp_alpha")
    register_chronicle("camp_alpha", data)

    response = await get_chronicle(campaign_id="camp_alpha")

    # Response type check
    assert isinstance(response, ChronicleResponse)
    assert response.campaign_id == "camp_alpha"

    # Eras are shaped presenter objects
    assert len(response.eras) == 2
    assert isinstance(response.eras[0], ChronicleEraPresenter)
    assert response.eras[0].id == "era:0"
    assert response.eras[0].name == "Age of Conflict"
    assert response.eras[0].ordinal == 0
    assert response.eras[0].significance == 0.9
    assert "episode:0" in response.eras[0].episode_ids

    # Episodes are shaped
    assert len(response.episodes) == 6
    assert isinstance(response.episodes[0], ChronicleEpisodePresenter)
    assert response.episodes[0].id == "episode:0"
    assert response.episodes[0].index == 0

    # Named milestones are shaped
    assert len(response.named_milestones) == 4
    assert isinstance(response.named_milestones[0], ChronicleMilestonePresenter)
    assert response.named_milestones[0].name == "Death of Goblin King"
    assert response.named_milestones[0].tick == 5
    assert response.named_milestones[0].event_type == "entity_death"
    assert response.named_milestones[0].entry_id == "0:5:entity_death:goblin_king"

    # Verify raw dicts are NOT leaked
    assert not isinstance(response.eras[0], dict)
    assert not isinstance(response.named_milestones[0], dict)


# ── TC-2: test_era_summary_endpoint_returns_milestone_names (AC-2) ────────────


@pytest.mark.anyio
async def test_era_summary_endpoint_returns_milestone_names():
    """AC-required: era summary endpoint returns era name and milestone name list."""
    data = _make_chronicle("camp_beta")
    register_chronicle("camp_beta", data)

    response = await get_era_summary(campaign_id="camp_beta", era_id="era:0")

    assert isinstance(response, ErasSummaryResponse)
    assert response.era_id == "era:0"
    assert response.name == "Age of Conflict"

    # era:0 covers episodes 0, 1, 2 — milestones in episodes 0 and 2
    assert response.milestone_count == 3
    assert isinstance(response.named_milestones, list)
    assert all(isinstance(n, str) for n in response.named_milestones)
    assert "Death of Goblin King" in response.named_milestones
    assert "Battle at the Iron Gate" in response.named_milestones
    assert "Siege of the Ancient Tower" in response.named_milestones

    # era:1 milestones (episode 3) should NOT appear
    assert "Quest for the Lost Relic" not in response.named_milestones


@pytest.mark.anyio
async def test_era_summary_second_era_returns_correct_milestones():
    """Era summary for era:1 returns only milestones from its episodes."""
    data = _make_chronicle("camp_gamma")
    register_chronicle("camp_gamma", data)

    response = await get_era_summary(campaign_id="camp_gamma", era_id="era:1")

    assert response.era_id == "era:1"
    assert response.name == "Age of Quests"
    # era:1 covers episodes 3, 4, 5 — milestone in episode 3 only
    assert response.milestone_count == 1
    assert response.named_milestones == ["Quest for the Lost Relic"]


# ── TC-3: test_chronicle_404_unknown_campaign ──────────────────────────────────


@pytest.mark.anyio
async def test_chronicle_404_unknown_campaign():
    """Requesting a chronicle for non-existent campaign returns HTTP 404."""
    with pytest.raises(HTTPException) as exc_info:
        await get_chronicle(campaign_id="nonexistent")

    assert exc_info.value.status_code == 404
    assert "nonexistent" in exc_info.value.detail


# ── TC-4: test_era_summary_404_unknown_era ────────────────────────────────────


@pytest.mark.anyio
async def test_era_summary_404_unknown_era():
    """Requesting summary for a non-existent era_id returns HTTP 404."""
    data = _make_chronicle("camp_delta")
    register_chronicle("camp_delta", data)

    with pytest.raises(HTTPException) as exc_info:
        await get_era_summary(campaign_id="camp_delta", era_id="era:99")

    assert exc_info.value.status_code == 404
    assert "era:99" in exc_info.value.detail


@pytest.mark.anyio
async def test_era_summary_404_unknown_campaign():
    """Requesting era summary for a non-existent campaign returns HTTP 404."""
    with pytest.raises(HTTPException) as exc_info:
        await get_era_summary(campaign_id="no_campaign", era_id="era:0")

    assert exc_info.value.status_code == 404
    assert "no_campaign" in exc_info.value.detail


# ── TC-5: test_chronicle_empty_eras ──────────────────────────────────────────


@pytest.mark.anyio
async def test_chronicle_empty_eras():
    """A chronicle with no eras/episodes/milestones returns empty lists."""
    data = _make_chronicle("camp_empty", with_eras=False)
    register_chronicle("camp_empty", data)

    response = await get_chronicle(campaign_id="camp_empty")

    assert response.campaign_id == "camp_empty"
    assert response.eras == []
    assert response.episodes == []
    assert response.named_milestones == []
