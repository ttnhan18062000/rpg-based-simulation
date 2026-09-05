"""Tests for BeliefInstitutionDeriver (idea 63, AC3/AC4 + determinism + safety).

Mirrors tests/unit/domains/fame/test_fame_deriver.py's _hierarchy()/_entry() helper
pattern.
"""

from src.core.state import ClanState
from src.domains.campaigns.state import CampaignState, NarrativeLedgerEntry
from src.domains.chronicle.grouper import ChronicleGrouper
from src.domains.belief_institution.deriver import OUT_GROUP_DAMPENING, BeliefInstitutionDeriver
from src.domains.fame.exporter import FameExporter


def _hierarchy(entries: list[NarrativeLedgerEntry]):
    return ChronicleGrouper().group(entries)


def _entry(
    episode: int = 0,
    event_type: str = "quest_completed",
    significance: float = 0.7,
    tick: int = 1,
    subject_id: str = "1",
    payload: dict | None = None,
) -> NarrativeLedgerEntry:
    return NarrativeLedgerEntry(
        episode=episode,
        tick=tick,
        event_type=event_type,
        subject_id=subject_id,
        payload=payload or {},
        significance=significance,
        entry_id=f"{episode}:{tick}:{event_type}:{subject_id}",
    )


def _legendary_entries(subject_id: str = "1") -> list[NarrativeLedgerEntry]:
    """3 quest_completed entries at significance 0.7 -> raw=2.1 -> fame=min(1.0, 0.7)=0.7,
    comfortably above FAME_THRESHOLD (0.5)."""
    return [
        _entry(episode=0, tick=1, significance=0.7, subject_id=subject_id),
        _entry(episode=0, tick=2, significance=0.7, subject_id=subject_id),
        _entry(episode=0, tick=3, significance=0.7, subject_id=subject_id),
    ]


def _campaign_state_with_fame(entries: list[NarrativeLedgerEntry]) -> tuple[CampaignState, "object"]:
    cs = CampaignState(campaign_id="test", episode_index=0)
    hierarchy = _hierarchy(entries)
    FameExporter.export(cs, hierarchy, episode_index=0)
    return cs, hierarchy


def test_no_belief_institution_without_qualifying_legend_fact():
    # A single quest_completed (fame=0.7/3.0=0.233) never crosses FAME_THRESHOLD=0.5.
    entries = [_entry(episode=0, tick=1, significance=0.7, subject_id="1")]
    cs, hierarchy = _campaign_state_with_fame(entries)
    clans = {"clan_a": ClanState(clan_id="clan_a", member_entity_ids=(1,))}

    result = BeliefInstitutionDeriver.derive(hierarchy, cs, clans)
    assert result == {}


def test_two_clans_form_different_belief_strength_for_same_origin_event():
    entries = _legendary_entries(subject_id="1")
    cs, hierarchy = _campaign_state_with_fame(entries)
    clans = {
        "clan_in": ClanState(clan_id="clan_in", member_entity_ids=(1, 2)),
        "clan_out": ClanState(clan_id="clan_out", member_entity_ids=(3, 4)),
    }

    result = BeliefInstitutionDeriver.derive(hierarchy, cs, clans)

    in_group = [v for v in result.values() if v.clan_id == "clan_in"]
    out_group = [v for v in result.values() if v.clan_id == "clan_out"]
    assert len(in_group) == 1
    assert len(out_group) == 1
    assert in_group[0].belief_strength > out_group[0].belief_strength
    assert out_group[0].belief_strength == in_group[0].belief_strength * OUT_GROUP_DAMPENING
    # Same origin event referenced by both.
    assert in_group[0].origin_event_id == out_group[0].origin_event_id


def test_belief_institution_derivation_is_deterministic():
    entries = _legendary_entries(subject_id="1")
    cs, hierarchy = _campaign_state_with_fame(entries)
    clans = {"clan_a": ClanState(clan_id="clan_a", member_entity_ids=(1,))}

    result_1 = BeliefInstitutionDeriver.derive(hierarchy, cs, clans)
    result_2 = BeliefInstitutionDeriver.derive(hierarchy, cs, clans)
    assert result_1 == result_2


def test_belief_institution_skips_non_numeric_subject_id_safely():
    # subject_id "faction_north" is not int-castable -- must not crash, treated as
    # out-group for every clan (never a member match).
    entries = _legendary_entries(subject_id="faction_north")
    cs, hierarchy = _campaign_state_with_fame(entries)
    clans = {"clan_a": ClanState(clan_id="clan_a", member_entity_ids=(1, 2))}

    result = BeliefInstitutionDeriver.derive(hierarchy, cs, clans)
    assert len(result) == 1
    inst = next(iter(result.values()))
    # Cannot be in-group since subject_id isn't int-castable -- always out-group.
    fame = cs.entity_fame["faction_north"].fame.fame
    assert inst.belief_strength == min(1.0, fame * OUT_GROUP_DAMPENING)


def test_belief_institution_origin_event_prefers_posthumous_hero_death():
    entries = [
        _entry(episode=0, tick=1, event_type="quest_completed", significance=0.7, subject_id="1"),
        _entry(episode=0, tick=2, event_type="quest_completed", significance=0.7, subject_id="1"),
        _entry(
            episode=0,
            tick=3,
            event_type="entity_death",
            significance=0.5,
            subject_id="1",
            payload={"entity_role": "HERO"},
        ),
    ]
    cs, hierarchy = _campaign_state_with_fame(entries)
    clans = {"clan_a": ClanState(clan_id="clan_a", member_entity_ids=(1,))}

    result = BeliefInstitutionDeriver.derive(hierarchy, cs, clans)
    inst = next(iter(result.values()))
    assert inst.origin_event_id == "0:3:entity_death:1"


def test_belief_institution_adherent_entity_ids_is_clan_snapshot():
    entries = _legendary_entries(subject_id="1")
    cs, hierarchy = _campaign_state_with_fame(entries)
    clans = {"clan_a": ClanState(clan_id="clan_a", member_entity_ids=(1, 2, 3))}

    result = BeliefInstitutionDeriver.derive(hierarchy, cs, clans)
    inst = next(iter(result.values()))
    assert inst.adherent_entity_ids == (1, 2, 3)
