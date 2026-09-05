"""Tests for FidelityExporter and FidelityImporter (idea 62).

Mirrors tests/unit/domains/culture/test_culture_exporter.py's structure.
"""

from src.domains.campaigns.state import CampaignState, NarrativeLedgerEntry
from src.domains.chronicle.grouper import ChronicleGrouper
from src.domains.fidelity.exporter import FidelityExporter, FidelityImporter
from src.domains.fidelity.model import FidelityState


def _make_state(campaign_id: str = "test") -> CampaignState:
    return CampaignState(campaign_id=campaign_id, episode_index=0)


def _hierarchy(entries: list[NarrativeLedgerEntry]):
    return ChronicleGrouper().group(entries)


def _calamity_entry(episode: int = 0, tick: int = 1, subject_id: str = "world"):
    return NarrativeLedgerEntry(
        episode=episode,
        tick=tick,
        event_type="calamity",
        subject_id=subject_id,
        payload={},
        significance=0.85,
        entry_id=f"{episode}:{tick}:calamity:{subject_id}",
    )


def test_exporter_populates_historical_drift():
    state = _make_state()
    h = _hierarchy([_calamity_entry()])
    FidelityExporter.export(state, h, episode_index=0)
    key = "0:1:calamity:world"
    assert key in state.historical_drift
    cf = state.historical_drift[key]
    assert cf.fidelity.fidelity == 1.0
    assert cf.derived_episode == 0


def test_exporter_empty_hierarchy_no_error():
    state = _make_state()
    h = _hierarchy([])
    FidelityExporter.export(state, h, episode_index=0)
    assert state.historical_drift == {}


def test_importer_returns_none_for_unknown_entry():
    state = _make_state()
    result = FidelityImporter.get_fidelity(state, "nonexistent")
    assert result is None


def test_importer_returns_fidelity_for_known_entry():
    state = _make_state()
    h = _hierarchy([_calamity_entry()])
    FidelityExporter.export(state, h, episode_index=0)
    fidelity = FidelityImporter.get_fidelity(state, "0:1:calamity:world")
    assert isinstance(fidelity, FidelityState)
    assert fidelity.fidelity == 1.0


def test_fidelity_carry_forward_round_trips_through_campaign_state_serialization():
    state = _make_state()
    entries = [_calamity_entry(episode=ep) for ep in range(6)]
    h = _hierarchy(entries)
    FidelityExporter.export(state, h, episode_index=5)

    d = state.to_dict()
    restored = CampaignState.from_dict(d)

    key = "0:1:calamity:world"
    assert key in restored.historical_drift
    assert restored.historical_drift[key].derived_episode == 5
    assert restored.historical_drift[key].fidelity.fidelity == state.historical_drift[key].fidelity.fidelity
