"""
tests/api/test_campaign_history_api.py
────────────────────────────────────────────────────────────────────────────────
Tests for GET /api/v1/campaigns/{id}/history endpoint.

Implemented for E32E (TCK-20260619-E32E-REST-HISTORY).

Test strategy:
  - Call the route handler directly (no HTTP layer needed for unit tests).
  - Inject CampaignState via register_campaign() / _clear_registry().
  - Assert shaped responses (presenter dicts), not raw domain objects.
  - anyio marker required for async route handlers.
"""
from __future__ import annotations

import pytest
from fastapi import HTTPException

from src.api.routes.campaigns import (
    _clear_registry,
    get_campaign_history,
    register_campaign,
)
from src.domains.campaigns.state import CampaignState, NarrativeLedgerEntry


# ── Fixtures ───────────────────────────────────────────────────────────────────


def _make_entry(
    episode: int = 0,
    tick: int = 10,
    event_type: str = "entity_death",
    subject_id: str = "goblin_1",
    payload: dict | None = None,
    significance: float = 0.5,
) -> NarrativeLedgerEntry:
    """Helper to construct a NarrativeLedgerEntry for testing."""
    entry_id = f"{episode}:{tick}:{event_type}:{subject_id}"
    return NarrativeLedgerEntry(
        episode=episode,
        tick=tick,
        event_type=event_type,
        subject_id=subject_id,
        payload=payload or {},
        significance=significance,
        entry_id=entry_id,
    )


@pytest.fixture(autouse=True)
def clear_registry():
    """Ensure the campaign registry is clean before and after each test."""
    _clear_registry()
    yield
    _clear_registry()


def _make_state(campaign_id: str, entries: list) -> CampaignState:
    """Construct a minimal CampaignState with the given narrative ledger entries."""
    state = CampaignState(campaign_id=campaign_id, episode_index=0)
    state.narrative_ledger.extend(entries)
    return state


# ── TC-1: test_campaign_history_endpoint_returns_narrative_ledger ──────────────


@pytest.mark.anyio
async def test_campaign_history_endpoint_returns_narrative_ledger():
    """AC-required: endpoint returns structured NarrativeLedger as JSON."""
    entries = [
        _make_entry(episode=0, tick=5, event_type="entity_death", subject_id="troll_1", significance=0.5),
        _make_entry(episode=0, tick=12, event_type="quest_completed", subject_id="q_1", significance=0.7),
        _make_entry(episode=1, tick=3, event_type="faction_shift", subject_id="faction_0", significance=0.9),
    ]
    state = _make_state("camp_abc", entries)
    register_campaign("camp_abc", state)

    response = await get_campaign_history(
        campaign_id="camp_abc",
        event_type=None,
        min_significance=0.0,
        episode=None,
    )

    assert response.campaign_id == "camp_abc"
    assert response.entry_count == 3
    assert len(response.entries) == 3

    # Verify entries are shaped presenter objects — not raw domain objects
    first = response.entries[0]
    assert hasattr(first, "episode")
    assert hasattr(first, "tick")
    assert hasattr(first, "event_type")
    assert hasattr(first, "subject_id")
    assert hasattr(first, "payload")
    assert hasattr(first, "significance")
    assert hasattr(first, "entry_id")

    # Verify NarrativeLedgerEntry domain type is NOT leaked (is Pydantic, not dataclass)
    from src.api.presenters.campaigns import NarrativeLedgerEntryPresenter
    assert isinstance(first, NarrativeLedgerEntryPresenter)

    # Spot-check values
    assert first.event_type == "entity_death"
    assert first.significance == 0.5
    assert first.entry_id == "0:5:entity_death:troll_1"


# ── TC-2: test_campaign_history_404_unknown_campaign ──────────────────────────


@pytest.mark.anyio
async def test_campaign_history_404_unknown_campaign():
    """Requesting a non-existent campaign returns HTTP 404."""
    with pytest.raises(HTTPException) as exc_info:
        await get_campaign_history(campaign_id="nonexistent")

    assert exc_info.value.status_code == 404
    assert "nonexistent" in exc_info.value.detail


# ── TC-3: test_campaign_history_filter_by_event_type ─────────────────────────


@pytest.mark.anyio
async def test_campaign_history_filter_by_event_type():
    """event_type filter returns only entries with the matching type."""
    entries = [
        _make_entry(episode=0, tick=1, event_type="entity_death", subject_id="e1", significance=0.5),
        _make_entry(episode=0, tick=2, event_type="entity_death", subject_id="e2", significance=0.5),
        _make_entry(episode=0, tick=3, event_type="quest_completed", subject_id="q1", significance=0.7),
    ]
    state = _make_state("camp_filter_type", entries)
    register_campaign("camp_filter_type", state)

    response = await get_campaign_history(
        campaign_id="camp_filter_type",
        event_type="entity_death",
        min_significance=0.0,
        episode=None,
    )

    assert response.entry_count == 2
    assert all(e.event_type == "entity_death" for e in response.entries)


# ── TC-4: test_campaign_history_filter_by_min_significance ───────────────────


@pytest.mark.anyio
async def test_campaign_history_filter_by_min_significance():
    """min_significance filter returns only entries at or above the threshold."""
    entries = [
        _make_entry(episode=0, tick=1, event_type="entity_death", subject_id="e1", significance=0.4),
        _make_entry(episode=0, tick=2, event_type="entity_death", subject_id="e2", significance=0.5),
        _make_entry(episode=0, tick=3, event_type="faction_shift", subject_id="f1", significance=0.9),
    ]
    state = _make_state("camp_filter_sig", entries)
    register_campaign("camp_filter_sig", state)

    response = await get_campaign_history(
        campaign_id="camp_filter_sig",
        event_type=None,
        min_significance=0.5,
        episode=None,
    )

    # significance=0.4 excluded; 0.5 and 0.9 included
    assert response.entry_count == 2
    assert all(e.significance >= 0.5 for e in response.entries)


# ── TC-5: test_campaign_history_filter_by_episode ────────────────────────────


@pytest.mark.anyio
async def test_campaign_history_filter_by_episode():
    """episode filter returns only entries from the specified episode."""
    entries = [
        _make_entry(episode=0, tick=5, event_type="entity_death", subject_id="e1", significance=0.5),
        _make_entry(episode=0, tick=10, event_type="quest_completed", subject_id="q1", significance=0.7),
        _make_entry(episode=1, tick=3, event_type="faction_shift", subject_id="f1", significance=0.9),
        _make_entry(episode=1, tick=8, event_type="entity_death", subject_id="e2", significance=0.5),
    ]
    state = _make_state("camp_filter_ep", entries)
    register_campaign("camp_filter_ep", state)

    response = await get_campaign_history(
        campaign_id="camp_filter_ep",
        event_type=None,
        min_significance=0.0,
        episode=1,
    )

    assert response.entry_count == 2
    assert all(e.episode == 1 for e in response.entries)


# ── TC-6: test_campaign_history_empty_ledger ─────────────────────────────────


@pytest.mark.anyio
async def test_campaign_history_empty_ledger():
    """A campaign with no ledger entries returns entry_count=0 and empty list."""
    state = _make_state("camp_empty", [])
    register_campaign("camp_empty", state)

    response = await get_campaign_history(
        campaign_id="camp_empty",
        event_type=None,
        min_significance=0.0,
        episode=None,
    )

    assert response.campaign_id == "camp_empty"
    assert response.entry_count == 0
    assert response.entries == []


# ── TC-7: test_campaign_history_combined_filters ─────────────────────────────


@pytest.mark.anyio
async def test_campaign_history_combined_filters():
    """All three filters can be combined; only entries matching all criteria returned."""
    entries = [
        # Episode 0 — various
        _make_entry(episode=0, tick=1, event_type="entity_death", subject_id="e1", significance=0.5),
        _make_entry(episode=0, tick=2, event_type="quest_completed", subject_id="q1", significance=0.7),
        _make_entry(episode=0, tick=3, event_type="entity_death", subject_id="e2", significance=0.3),
        # Episode 1 — entity_death with varying significance
        _make_entry(episode=1, tick=4, event_type="entity_death", subject_id="e3", significance=0.6),
        _make_entry(episode=1, tick=5, event_type="entity_death", subject_id="e4", significance=0.4),
        _make_entry(episode=1, tick=6, event_type="faction_shift", subject_id="f1", significance=0.9),
    ]
    state = _make_state("camp_combined", entries)
    register_campaign("camp_combined", state)

    # Only: episode=1, event_type="entity_death", significance >= 0.5
    # Matches: e3 (sig=0.6) only — e4 (sig=0.4) excluded
    response = await get_campaign_history(
        campaign_id="camp_combined",
        event_type="entity_death",
        min_significance=0.5,
        episode=1,
    )

    assert response.entry_count == 1
    assert response.entries[0].subject_id == "e3"
    assert response.entries[0].significance == 0.6
    assert response.entries[0].episode == 1
