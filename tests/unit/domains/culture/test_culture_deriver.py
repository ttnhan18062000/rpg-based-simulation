"""Tests for CultureDeriver — axis derivation rules (E62B)."""

from src.domains.campaigns.state import NarrativeLedgerEntry
from src.domains.chronicle.grouper import ChronicleGrouper
from src.domains.culture.deriver import CultureDeriver


def _hierarchy(entries: list[NarrativeLedgerEntry]):
    """Produce a ChronicleHierarchy from raw entries via ChronicleGrouper."""
    return ChronicleGrouper().group(entries)


def _entry(
    event_type: str,
    significance: float,
    episode: int = 0,
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


def test_deriver_empty_hierarchy_returns_zero_culture():
    h = _hierarchy([])
    result = CultureDeriver.derive(h)
    assert result == {}


def test_deriver_calamity_raises_fatalism():
    e = _entry("calamity", significance=0.85, payload={"region_id": "r1"})
    h = _hierarchy([e])
    result = CultureDeriver.derive(h)
    assert "r1" in result
    cs = result["r1"]
    assert cs.fatalism > 0.0
    assert cs.hero_veneration == 0.0
    assert cs.resource_scarcity_memory == 0.0
    assert cs.faction_conflict_exposure == 0.0


def test_deriver_hero_death_raises_hero_veneration():
    e = _entry(
        "entity_death",
        significance=0.9,
        payload={"region_id": "r1", "entity_role": "HERO"},
    )
    h = _hierarchy([e])
    result = CultureDeriver.derive(h)
    cs = result["r1"]
    assert cs.hero_veneration > 0.0
    assert cs.fatalism == 0.0


def test_deriver_entity_death_calamity_cause_raises_fatalism():
    e = _entry(
        "entity_death",
        significance=0.6,
        payload={"region_id": "r1", "cause": "calamity"},
    )
    h = _hierarchy([e])
    result = CultureDeriver.derive(h)
    cs = result["r1"]
    assert cs.fatalism > 0.0


def test_deriver_inflation_raises_scarcity_memory():
    e = _entry("INFLATION_SPIRAL", significance=0.7, payload={"region_id": "r1"})
    h = _hierarchy([e])
    result = CultureDeriver.derive(h)
    cs = result["r1"]
    assert cs.resource_scarcity_memory > 0.0
    assert cs.faction_conflict_exposure == 0.0


def test_deriver_war_events_raise_conflict_exposure():
    entries = [
        _entry("war_declared", significance=0.9, tick=1, payload={"region_id": "r1"}),
        _entry("territory_transferred", significance=0.9, tick=2, payload={"region_id": "r1"}),
        _entry("faction_destroyed", significance=0.9, tick=3, payload={"region_id": "r1"}),
    ]
    h = _hierarchy(entries)
    result = CultureDeriver.derive(h)
    cs = result["r1"]
    assert cs.faction_conflict_exposure >= 0.9


def test_deriver_saturation_clamps_at_1_0():
    # 10 high-significance calamities → raw sum 8.5, normalised = min(1.0, 8.5/3.0) = 1.0
    entries = [
        _entry("calamity", significance=0.85, tick=i + 1, payload={"region_id": "r1"})
        for i in range(10)
    ]
    h = _hierarchy(entries)
    result = CultureDeriver.derive(h)
    cs = result["r1"]
    assert cs.fatalism == 1.0


def test_deriver_unknown_event_type_no_effect():
    e = _entry("some_unknown_event", significance=0.9, payload={"region_id": "r1"})
    h = _hierarchy([e])
    result = CultureDeriver.derive(h)
    # No axis affected → region not in result
    assert "r1" not in result


def test_deriver_global_fallback_when_no_region_in_payload():
    e = _entry("calamity", significance=0.85, payload={})
    h = _hierarchy([e])
    result = CultureDeriver.derive(h)
    assert "__global__" in result
    assert result["__global__"].fatalism > 0.0
