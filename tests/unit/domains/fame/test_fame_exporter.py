"""Tests for FameExporter and FameImporter (idea 57).

Mirrors tests/unit/domains/culture/test_culture_exporter.py's structure.
"""

from src.domains.campaigns.state import CampaignState, NarrativeLedgerEntry
from src.domains.chronicle.grouper import ChronicleGrouper
from src.domains.fame.exporter import FameExporter, FameImporter
from src.domains.fame.model import FameState


def _make_state(campaign_id: str = "test") -> CampaignState:
    return CampaignState(campaign_id=campaign_id, episode_index=0)


def _hierarchy(entries: list[NarrativeLedgerEntry]):
    return ChronicleGrouper().group(entries)


def _quest_entry(episode: int = 0, tick: int = 1, subject_id: str = "hero_1"):
    return NarrativeLedgerEntry(
        episode=episode,
        tick=tick,
        event_type="quest_completed",
        subject_id=subject_id,
        payload={},
        significance=0.7,
        entry_id=f"{episode}:{tick}:quest_completed:{subject_id}",
    )


def test_fame_exporter_populates_entity_fame():
    state = _make_state()
    h = _hierarchy([_quest_entry()])
    FameExporter.export(state, h, episode_index=0)

    assert "hero_1" in state.entity_fame
    cf = state.entity_fame["hero_1"]
    assert cf.fame.fame > 0.0
    assert cf.derived_episode == 0


def test_fame_exporter_empty_hierarchy_no_error():
    state = _make_state()
    h = _hierarchy([])
    FameExporter.export(state, h, episode_index=0)
    assert state.entity_fame == {}


def test_fame_exporter_preserves_untouched_entity_across_zero_event_episode():
    state = _make_state()
    h1 = _hierarchy([_quest_entry(episode=0, subject_id="hero_1")])
    FameExporter.export(state, h1, episode_index=0)
    original = state.entity_fame["hero_1"]

    # A later episode with an event for a *different* subject only.
    h2 = _hierarchy([_quest_entry(episode=1, tick=2, subject_id="hero_2")])
    FameExporter.export(state, h2, episode_index=1)

    assert state.entity_fame["hero_1"] is original
    assert "hero_2" in state.entity_fame


def test_importer_returns_none_for_unknown_subject():
    state = _make_state()
    result = FameImporter.get_fame(state, "nonexistent")
    assert result is None


def test_importer_returns_fame_for_known_subject():
    state = _make_state()
    h = _hierarchy([_quest_entry()])
    FameExporter.export(state, h, episode_index=0)
    fame = FameImporter.get_fame(state, "hero_1")
    assert isinstance(fame, FameState)
    assert fame.fame > 0.0


def test_fame_carry_forward_round_trips_through_campaign_state_serialization():
    state = _make_state()
    h = _hierarchy([_quest_entry()])
    FameExporter.export(state, h, episode_index=5)

    d = state.to_dict()
    restored = CampaignState.from_dict(d)

    assert "hero_1" in restored.entity_fame
    assert restored.entity_fame["hero_1"].derived_episode == 5
    assert restored.entity_fame["hero_1"].fame.fame == state.entity_fame["hero_1"].fame.fame
