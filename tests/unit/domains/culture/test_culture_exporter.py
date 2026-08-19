"""Tests for CultureDriftExporter and CultureDriftImporter (E62B)."""

from unittest.mock import MagicMock, patch

from src.domains.campaigns.state import CampaignState, NarrativeLedgerEntry
from src.domains.chronicle.grouper import ChronicleGrouper
from src.domains.culture.exporter import CultureDriftExporter, CultureDriftImporter
from src.domains.culture.model import CultureState


def _make_state(campaign_id: str = "test") -> CampaignState:
    return CampaignState(campaign_id=campaign_id, episode_index=0)


def _hierarchy(entries: list[NarrativeLedgerEntry]):
    return ChronicleGrouper().group(entries)


def _calamity_entry(region_id: str = "r1", sig: float = 0.85, tick: int = 1):
    return NarrativeLedgerEntry(
        episode=0, tick=tick,
        event_type="calamity",
        subject_id="world",
        payload={"region_id": region_id},
        significance=sig,
        entry_id=f"0:{tick}:calamity:world:{region_id}",
    )


def test_exporter_populates_region_cultures():
    state = _make_state()
    h = _hierarchy([_calamity_entry("r1")])
    CultureDriftExporter.export(state, h, episode_index=0)
    assert "r1" in state.region_cultures
    ccf = state.region_cultures["r1"]
    assert ccf.culture.fatalism > 0.0
    assert ccf.derived_episode == 0


def test_exporter_overwrites_on_later_episode():
    state = _make_state()
    # Episode 0: calamity
    h0 = _hierarchy([_calamity_entry("r1", sig=0.5)])
    CultureDriftExporter.export(state, h0, episode_index=0)
    first_val = state.region_cultures["r1"].culture.fatalism

    # Episode 1: stronger calamity for same region
    h1 = _hierarchy([_calamity_entry("r1", sig=0.9)])
    CultureDriftExporter.export(state, h1, episode_index=1)
    second_val = state.region_cultures["r1"].culture.fatalism
    assert second_val != first_val
    assert state.region_cultures["r1"].derived_episode == 1


def test_exporter_empty_hierarchy_no_error():
    state = _make_state()
    h = _hierarchy([])
    CultureDriftExporter.export(state, h, episode_index=0)
    assert state.region_cultures == {}


def test_importer_returns_none_for_unknown_region():
    state = _make_state()
    result = CultureDriftImporter.get_culture(state, "nonexistent_region")
    assert result is None


def test_importer_returns_culture_for_known_region():
    state = _make_state()
    h = _hierarchy([_calamity_entry("r1")])
    CultureDriftExporter.export(state, h, episode_index=0)
    culture = CultureDriftImporter.get_culture(state, "r1")
    assert isinstance(culture, CultureState)
    assert culture.fatalism > 0.0


def test_exporter_round_trips_through_campaign_state_serialization():
    state = _make_state()
    h = _hierarchy([_calamity_entry("r1"), _calamity_entry("r2")])
    CultureDriftExporter.export(state, h, episode_index=2)
    d = state.to_dict()
    restored = CampaignState.from_dict(d)
    assert "r1" in restored.region_cultures
    assert "r2" in restored.region_cultures
    assert restored.region_cultures["r1"].derived_episode == 2
