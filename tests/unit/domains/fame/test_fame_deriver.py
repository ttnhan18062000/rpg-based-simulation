"""Tests for FameDeriver — Option B fame accumulation derivation (idea 57).

Mirrors tests/unit/domains/culture/test_culture_deriver.py's _hierarchy()/_entry()
helper pattern.
"""

from src.domains.campaigns.state import NarrativeLedgerEntry
from src.domains.chronicle.grouper import ChronicleGrouper
from src.domains.fame.deriver import NORMALISE_DENOMINATOR, FameDeriver


def _hierarchy(entries: list[NarrativeLedgerEntry]):
    """Produce a ChronicleHierarchy from raw entries via ChronicleGrouper."""
    return ChronicleGrouper().group(entries)


def _entry(
    episode: int = 0,
    event_type: str = "quest_completed",
    significance: float = 0.7,
    tick: int = 1,
    subject_id: str = "hero_1",
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


def test_fame_deriver_empty_hierarchy_returns_empty_dict():
    h = _hierarchy([])
    result = FameDeriver.derive(h)
    assert result == {}


def test_fame_deriver_attributes_two_subjects_distinctly():
    entries = [
        _entry(episode=0, event_type="quest_completed", significance=0.7, subject_id="hero_1"),
        _entry(
            episode=1,
            tick=2,
            event_type="entity_death",
            significance=0.5,
            subject_id="hero_2",
            payload={"entity_role": "HERO"},
        ),
    ]
    h = _hierarchy(entries)
    result = FameDeriver.derive(h)

    assert "hero_1" in result
    assert "hero_2" in result
    assert result["hero_1"].fame > 0.0
    assert result["hero_2"].fame > 0.0
    assert result["hero_1"].fame != result["hero_2"].fame


def test_fame_deriver_only_option_b_events_contribute():
    entries = [
        # quest_completed -- contributes.
        _entry(episode=0, event_type="quest_completed", significance=0.7, subject_id="hero_1"),
        # entity_death without HERO role -- chronicle-worthy but must not contribute.
        _entry(
            episode=1,
            tick=2,
            event_type="entity_death",
            significance=0.5,
            subject_id="commoner_1",
            payload={},
        ),
        # calamity -- chronicle-worthy but not an Option B event type.
        _entry(episode=2, tick=3, event_type="calamity", significance=0.85, subject_id="hero_1"),
    ]
    h = _hierarchy(entries)
    result = FameDeriver.derive(h)

    assert "commoner_1" not in result
    # hero_1's fame is only from the quest_completed entry, not the calamity entry.
    assert result["hero_1"].fame == FameDeriver._normalise(0.7)


def test_fame_deriver_normalises_like_culture_deriver():
    entries = [
        _entry(episode=0, event_type="quest_completed", significance=0.7, subject_id="hero_1"),
        _entry(episode=1, tick=2, event_type="quest_completed", significance=0.7, subject_id="hero_1"),
        _entry(episode=2, tick=3, event_type="quest_completed", significance=0.7, subject_id="hero_1"),
    ]
    h = _hierarchy(entries)
    result = FameDeriver.derive(h)

    raw = 0.7 * 3
    assert result["hero_1"].fame == min(1.0, raw / NORMALISE_DENOMINATOR)


def test_fame_deriver_empty_subject_id_does_not_accumulate():
    entries = [
        _entry(episode=0, event_type="quest_completed", significance=0.7, subject_id=""),
    ]
    h = _hierarchy(entries)
    result = FameDeriver.derive(h)
    assert result == {}


def test_fame_deriver_is_deterministic_byte_identical():
    entries = [
        _entry(episode=0, event_type="quest_completed", significance=0.7, subject_id="hero_1"),
        _entry(
            episode=1,
            tick=2,
            event_type="entity_death",
            significance=0.5,
            subject_id="hero_2",
            payload={"entity_role": "HERO"},
        ),
    ]
    h = _hierarchy(entries)

    result_a = FameDeriver.derive(h)
    result_b = FameDeriver.derive(h)

    dict_a = {k: v.to_dict() for k, v in result_a.items()}
    dict_b = {k: v.to_dict() for k, v in result_b.items()}
    assert repr(sorted(dict_a.items())) == repr(sorted(dict_b.items()))
