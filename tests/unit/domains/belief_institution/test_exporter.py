"""Tests for BeliefInstitutionExporter/Importer (idea 63)."""

from src.core.state import ClanState
from src.domains.campaigns.state import CampaignState, NarrativeLedgerEntry
from src.domains.chronicle.grouper import ChronicleGrouper
from src.domains.belief_institution.exporter import BeliefInstitutionExporter, BeliefInstitutionImporter
from src.domains.fame.exporter import FameExporter


def _hierarchy(entries):
    return ChronicleGrouper().group(entries)


def _entry(episode=0, event_type="quest_completed", significance=0.7, tick=1, subject_id="1", payload=None):
    return NarrativeLedgerEntry(
        episode=episode,
        tick=tick,
        event_type=event_type,
        subject_id=subject_id,
        payload=payload or {},
        significance=significance,
        entry_id=f"{episode}:{tick}:{event_type}:{subject_id}",
    )


def test_belief_institution_exporter_writes_and_importer_reads():
    entries = [
        _entry(tick=1, subject_id="1"),
        _entry(tick=2, subject_id="1"),
        _entry(tick=3, subject_id="1"),
    ]
    cs = CampaignState(campaign_id="test", episode_index=0)
    hierarchy = _hierarchy(entries)
    FameExporter.export(cs, hierarchy, episode_index=0)
    clans = {"clan_a": ClanState(clan_id="clan_a", member_entity_ids=(1,))}

    BeliefInstitutionExporter.export(cs, hierarchy, clans, episode_index=0)

    origin_event_id = "0:1:quest_completed:1"
    inst = BeliefInstitutionImporter.get_institution(cs, "clan_a", origin_event_id)
    assert inst is not None
    assert inst.clan_id == "clan_a"


def test_belief_institution_importer_returns_none_for_unknown_key():
    cs = CampaignState(campaign_id="test", episode_index=0)
    assert BeliefInstitutionImporter.get_institution(cs, "clan_x", "no_such_event") is None


def test_belief_institution_exporter_preserves_untouched_entries_across_episodes():
    entries = [_entry(tick=1, subject_id="1"), _entry(tick=2, subject_id="1"), _entry(tick=3, subject_id="1")]
    cs = CampaignState(campaign_id="test", episode_index=0)
    hierarchy = _hierarchy(entries)
    FameExporter.export(cs, hierarchy, episode_index=0)
    clans = {"clan_a": ClanState(clan_id="clan_a", member_entity_ids=(1,))}
    BeliefInstitutionExporter.export(cs, hierarchy, clans, episode_index=0)
    before = dict(cs.belief_institutions)

    # A later episode with no new events for subject "1" -- export again with an
    # empty-events hierarchy; prior entries must be preserved (untouched keys kept).
    empty_hierarchy = _hierarchy([])
    BeliefInstitutionExporter.export(cs, empty_hierarchy, clans, episode_index=1)

    for key, cf in before.items():
        assert cs.belief_institutions[key] == cf
