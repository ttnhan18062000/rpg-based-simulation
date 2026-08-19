"""Tests for CultureState and CultureCarryForward models (E62A)."""

from src.domains.campaigns.state import CampaignState
from src.domains.culture.model import CultureCarryForward, CultureState


def test_culture_state_default_axes():
    cs = CultureState()
    assert cs.fatalism == 0.0
    assert cs.hero_veneration == 0.0
    assert cs.resource_scarcity_memory == 0.0
    assert cs.faction_conflict_exposure == 0.0


def test_culture_state_round_trip():
    cs = CultureState(
        fatalism=0.4,
        hero_veneration=0.7,
        resource_scarcity_memory=0.2,
        faction_conflict_exposure=0.9,
    )
    restored = CultureState.from_dict(cs.to_dict())
    assert restored == cs


def test_culture_carry_forward_round_trip():
    ccf = CultureCarryForward(
        region_id="region_alpha",
        culture=CultureState(fatalism=0.5, hero_veneration=0.3),
        derived_episode=2,
    )
    restored = CultureCarryForward.from_dict(ccf.to_dict())
    assert restored == ccf
    assert restored.region_id == "region_alpha"
    assert restored.culture.fatalism == 0.5
    assert restored.derived_episode == 2


def test_campaign_state_region_cultures_serialization():
    state = CampaignState(campaign_id="test", episode_index=3)
    state.region_cultures["region_alpha"] = CultureCarryForward(
        region_id="region_alpha",
        culture=CultureState(fatalism=0.6, hero_veneration=0.2),
        derived_episode=2,
    )
    state.region_cultures["region_beta"] = CultureCarryForward(
        region_id="region_beta",
        culture=CultureState(resource_scarcity_memory=0.8, faction_conflict_exposure=0.4),
        derived_episode=2,
    )
    d = state.to_dict()
    assert "region_cultures" in d
    assert "region_alpha" in d["region_cultures"]
    assert "region_beta" in d["region_cultures"]

    restored = CampaignState.from_dict(d)
    assert len(restored.region_cultures) == 2
    alpha = restored.region_cultures["region_alpha"]
    assert alpha.culture.fatalism == 0.6
    assert alpha.culture.hero_veneration == 0.2
    beta = restored.region_cultures["region_beta"]
    assert beta.culture.resource_scarcity_memory == 0.8
    assert beta.culture.faction_conflict_exposure == 0.4


def test_campaign_state_backward_compat():
    d = {
        "campaign_id": "old_save",
        "episode_index": 0,
    }
    state = CampaignState.from_dict(d)
    assert state.region_cultures == {}
