"""Tests for LoyaltyDriftService (TCK-20260905-DRIFTING-LOYALTY-SIGNAL, idea 56)."""

from __future__ import annotations

from src.domains.campaigns.state import CampaignState
from src.domains.culture.model import CultureCarryForward, CultureState
from src.systems.social_systems.loyalty_drift import LoyaltyDriftService


def _state_with_region(region_id: str, faction_conflict_exposure: float) -> CampaignState:
    state = CampaignState(campaign_id="test", episode_index=0)
    culture = CultureState(faction_conflict_exposure=faction_conflict_exposure)
    ccf = CultureCarryForward(region_id=region_id, culture=culture, derived_episode=0)
    state.region_cultures[region_id] = ccf
    return state


def test_compute_loyalty_pressure_returns_real_faction_conflict_exposure():
    state = _state_with_region("r1", faction_conflict_exposure=0.7)
    assert LoyaltyDriftService.compute_loyalty_pressure(state, "r1") == 0.7


def test_compute_loyalty_pressure_none_safe_for_unpopulated_region():
    state = CampaignState(campaign_id="test", episode_index=0)
    assert LoyaltyDriftService.compute_loyalty_pressure(state, "unknown_region") == 0.0


def test_compute_loyalty_pressure_none_safe_for_falsy_region_id():
    state = CampaignState(campaign_id="test", episode_index=0)
    assert LoyaltyDriftService.compute_loyalty_pressure(state, "") == 0.0
    assert LoyaltyDriftService.compute_loyalty_pressure(state, None) == 0.0


def test_compute_loyalty_pressure_is_deterministic():
    """Repeated calls with the same inputs return bit-identical output."""
    state = _state_with_region("r1", faction_conflict_exposure=0.42)
    results = {LoyaltyDriftService.compute_loyalty_pressure(state, "r1") for _ in range(5)}
    assert results == {0.42}


def test_compute_loyalty_pressure_does_not_mutate_campaign_state():
    state = _state_with_region("r1", faction_conflict_exposure=0.3)
    before = dict(state.region_cultures)
    LoyaltyDriftService.compute_loyalty_pressure(state, "r1")
    assert state.region_cultures == before
