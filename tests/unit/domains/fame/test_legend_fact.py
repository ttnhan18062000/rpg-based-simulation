"""Tests for LegendFact / LegendFactService (idea 57).

LegendFact is a lazily-computed, non-durable read-model over FameCarryForward --
constructed only once fame crosses FAME_THRESHOLD, never persisted on
CampaignState itself.
"""

from src.domains.campaigns.state import CampaignState, NarrativeLedgerEntry
from src.domains.chronicle.grouper import ChronicleGrouper
from src.domains.fame.exporter import FameExporter
from src.domains.fame.legend import FAME_THRESHOLD, LegendFact, LegendFactService
from src.domains.perception.salience import WorldSignal


def _make_state() -> CampaignState:
    return CampaignState(campaign_id="test", episode_index=0)


def _hierarchy(entries):
    return ChronicleGrouper().group(entries)


def _quest_entry(episode: int, tick: int, subject_id: str):
    return NarrativeLedgerEntry(
        episode=episode,
        tick=tick,
        event_type="quest_completed",
        subject_id=subject_id,
        payload={},
        significance=0.7,
        entry_id=f"{episode}:{tick}:quest_completed:{subject_id}",
    )


def test_legend_fact_constructed_only_above_threshold():
    state = _make_state()
    # Three quest_completed entries -> raw 2.1 / 3.0 = 0.7 >= FAME_THRESHOLD (0.5).
    entries = [_quest_entry(ep, ep + 1, "hero_1") for ep in range(3)]
    h = _hierarchy(entries)
    FameExporter.export(state, h, episode_index=2)

    fact = LegendFactService.for_entity(state, "hero_1")
    assert fact is not None
    assert isinstance(fact, LegendFact)
    assert fact.subject_id == "hero_1"
    assert fact.fame >= FAME_THRESHOLD


def test_legend_fact_not_constructed_below_threshold():
    state = _make_state()
    # A single quest_completed entry -> raw 0.7 / 3.0 ≈ 0.233 < FAME_THRESHOLD (0.5).
    h = _hierarchy([_quest_entry(0, 1, "hero_1")])
    FameExporter.export(state, h, episode_index=0)

    fact = LegendFactService.for_entity(state, "hero_1")
    assert fact is None


def test_legend_fact_not_constructed_for_unknown_subject():
    state = _make_state()
    fact = LegendFactService.for_entity(state, "nonexistent")
    assert fact is None


def test_legend_fact_to_world_signal_shape():
    fact = LegendFact(subject_id="hero_1", fame=0.7, entity_name="Aldric")
    signal = LegendFactService.to_world_signal(fact)

    assert isinstance(signal, WorldSignal)
    assert signal.signal_id == "legend:hero_1"
    assert signal.kind == "legend_fact"
    assert signal.base_relevance == 0.7
    assert signal.danger_level == 0.0
    assert signal.is_novel is False
    assert signal.position == (0.0, 0.0)
