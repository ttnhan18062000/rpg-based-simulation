"""Tests for FidelityDeriver — Era-distance fidelity derivation (idea 62).

Mirrors tests/unit/domains/culture/test_culture_deriver.py's _hierarchy()/_entry()
helper pattern.
"""

from src.domains.campaigns.state import NarrativeLedgerEntry
from src.domains.chronicle.grouper import ChronicleGrouper
from src.domains.fidelity.deriver import FIDELITY_DECAY_PER_ERA, FidelityDeriver


def _hierarchy(entries: list[NarrativeLedgerEntry]):
    """Produce a ChronicleHierarchy from raw entries via ChronicleGrouper."""
    return ChronicleGrouper().group(entries)


def _entry(
    episode: int,
    event_type: str = "calamity",
    significance: float = 0.85,
    tick: int = 1,
    subject_id: str = "world",
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


def _six_episode_two_era_entries() -> list[NarrativeLedgerEntry]:
    # ERA_EPISODE_MIN=3, so 6 distinct episodes (each with >=1 chronicle-worthy
    # event) force two real Era objects: era 0 = episodes [0,1,2], era 1 =
    # episodes [3,4,5].
    return [_entry(episode=ep) for ep in range(6)]


def test_deriver_empty_hierarchy_returns_empty_dict():
    h = _hierarchy([])
    result = FidelityDeriver.derive(h)
    assert result == {}


def test_fidelity_lowers_with_era_distance():
    entries = _six_episode_two_era_entries()
    h = _hierarchy(entries)
    result = FidelityDeriver.derive(h)

    oldest_key = "0:1:calamity:world"
    newest_key = "5:1:calamity:world"
    assert oldest_key in result
    assert newest_key in result
    assert result[oldest_key].fidelity < result[newest_key].fidelity


def test_fidelity_same_era_event_is_1_0():
    entries = _six_episode_two_era_entries()
    h = _hierarchy(entries)
    result = FidelityDeriver.derive(h)

    current_era_key = "5:1:calamity:world"
    assert result[current_era_key].fidelity == 1.0


def test_fidelity_older_era_decays_by_decay_constant():
    entries = _six_episode_two_era_entries()
    h = _hierarchy(entries)
    result = FidelityDeriver.derive(h)

    older_era_key = "0:1:calamity:world"
    # era_distance = 1 (era 0 vs current era 1) -> fidelity = 1.0 - 0.2 = 0.8
    assert result[older_era_key].fidelity == 1.0 - FIDELITY_DECAY_PER_ERA


def test_fidelity_clamped_at_0_0_floor():
    # Force a large era-distance by adding many episodes; fidelity must never
    # go negative regardless of how far back the event is.
    entries = [_entry(episode=ep) for ep in range(30)]
    h = _hierarchy(entries)
    result = FidelityDeriver.derive(h)

    oldest_key = "0:1:calamity:world"
    assert result[oldest_key].fidelity == 0.0


def test_fidelity_legacy_empty_entry_id_reconstructs_deterministic_key():
    e = NarrativeLedgerEntry(
        episode=0,
        tick=1,
        event_type="calamity",
        subject_id="world",
        payload={},
        significance=0.85,
        entry_id="",
    )
    h = _hierarchy([e])
    result = FidelityDeriver.derive(h)
    assert "0:1:calamity:world" in result


def test_fidelity_derive_is_deterministic_byte_identical():
    entries = _six_episode_two_era_entries()
    h = _hierarchy(entries)

    result_a = FidelityDeriver.derive(h)
    result_b = FidelityDeriver.derive(h)

    dict_a = {k: v.to_dict() for k, v in result_a.items()}
    dict_b = {k: v.to_dict() for k, v in result_b.items()}
    assert repr(sorted(dict_a.items())) == repr(sorted(dict_b.items()))
