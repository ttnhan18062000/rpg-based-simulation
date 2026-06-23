"""5-episode Culture Drift acceptance test (E62D / WORLD-CULT-003).

Proves that two regions with different narrative histories produce measurably
different CultureState values and entity motivation deltas.

  calamity_region — 3 calamity events (significance=0.85 each)
  hero_region     — 3 entity_death HERO events (significance=0.8 each)

No engine is started. Derivation uses synthetic NarrativeLedgerEntry objects
grouped by ChronicleGrouper and derived by CultureDeriver.
"""

import pytest

from src.domains.campaigns.state import NarrativeLedgerEntry
from src.domains.chronicle.grouper import ChronicleGrouper
from src.domains.culture.applicator import CulturalBiasApplicator
from src.domains.culture.deriver import CultureDeriver


def _ledger_entry(
    event_type: str,
    significance: float,
    region_id: str,
    episode: int,
    tick: int,
    subject_id: str = "1",
    payload_extra: dict | None = None,
) -> NarrativeLedgerEntry:
    payload = {"region_id": region_id}
    if payload_extra:
        payload.update(payload_extra)
    return NarrativeLedgerEntry(
        episode=episode,
        tick=tick,
        event_type=event_type,
        subject_id=subject_id,
        payload=payload,
        significance=significance,
        entry_id=f"{episode}:{tick}:{event_type}:{subject_id}:{region_id}",
    )


def _build_synthetic_ledger() -> list[NarrativeLedgerEntry]:
    """5 episodes: 3 calamity events in calamity_region, 3 HERO deaths in hero_region."""
    entries = []
    for episode in range(3):
        entries.append(_ledger_entry(
            event_type="calamity",
            significance=0.85,
            region_id="calamity_region",
            episode=episode,
            tick=50,
        ))
        entries.append(_ledger_entry(
            event_type="entity_death",
            significance=0.8,
            region_id="hero_region",
            episode=episode,
            tick=80,
            subject_id=str(episode + 10),
            payload_extra={"entity_role": "HERO"},
        ))
    return entries


@pytest.mark.integration
def test_two_regions_diverge_after_5_episodes():
    """Calamity region develops higher fatalism; hero region develops higher hero_veneration."""
    entries = _build_synthetic_ledger()
    hierarchy = ChronicleGrouper().group(entries)
    cultures = CultureDeriver.derive(hierarchy)

    assert "calamity_region" in cultures, "calamity_region must be in derived cultures"
    assert "hero_region" in cultures, "hero_region must be in derived cultures"

    calamity_cs = cultures["calamity_region"]
    hero_cs = cultures["hero_region"]

    # AC: calamity region has substantially higher fatalism
    assert calamity_cs.fatalism > hero_cs.fatalism + 0.3, (
        f"Expected calamity_region.fatalism ({calamity_cs.fatalism:.3f}) > "
        f"hero_region.fatalism ({hero_cs.fatalism:.3f}) + 0.3"
    )

    # AC: hero region has substantially higher hero_veneration
    assert hero_cs.hero_veneration > calamity_cs.hero_veneration + 0.3, (
        f"Expected hero_region.hero_veneration ({hero_cs.hero_veneration:.3f}) > "
        f"calamity_region.hero_veneration ({calamity_cs.hero_veneration:.3f}) + 0.3"
    )


@pytest.mark.integration
def test_calamity_region_higher_caution_delta_than_hero_region():
    """Caution-tag motivation delta is measurably higher in the calamity region."""
    entries = _build_synthetic_ledger()
    hierarchy = ChronicleGrouper().group(entries)
    cultures = CultureDeriver.derive(hierarchy)

    calamity_delta = CulturalBiasApplicator.compute_culture_delta(
        cultures["calamity_region"], ["caution"]
    )
    hero_delta = CulturalBiasApplicator.compute_culture_delta(
        cultures["hero_region"], ["caution"]
    )

    assert calamity_delta > hero_delta + 0.1, (
        f"Expected calamity_region caution delta ({calamity_delta:.3f}) > "
        f"hero_region caution delta ({hero_delta:.3f}) + 0.1"
    )
