"""
tests/unit/chronicle/test_chronicle_compiler.py
────────────────────────────────────────────────────────────────────────────────
Unit tests for EventSignificanceScorer (E51A — TCK-20260619-E51A-SIGNIFICANCE).

Covers:
  - TC-1: death ranks above unknown/harvesting event type
  - TC-2: hero death scores >= 0.8
  - TC-3: is_chronicle_worthy filters below CHRONICLE_THRESHOLD
  - TC-4: all known BASE_SIGNIFICANCE types score correctly
  - TC-5: score is capped at 1.0
  - TC-6: unknown event type defaults to 0.1
"""
import pytest

from src.domains.campaigns.state import NarrativeLedgerEntry
from src.domains.chronicle.significance import (
    BASE_SIGNIFICANCE,
    CHRONICLE_THRESHOLD,
    EventSignificanceScorer,
)


# ── helpers ───────────────────────────────────────────────────────────────────

def _make_entry(event_type: str, payload: dict | None = None) -> NarrativeLedgerEntry:
    return NarrativeLedgerEntry(
        episode=0,
        tick=1,
        event_type=event_type,
        subject_id="test-subject",
        payload=payload or {},
        significance=0.0,  # raw ledger significance — scorer re-derives independently
        entry_id=f"0:1:{event_type}:test-subject",
    )


# ── TC-1 ──────────────────────────────────────────────────────────────────────

def test_significance_scoring_ranks_death_above_harvesting():
    """TC-1: entity_death (0.5) scores higher than harvesting (unknown → 0.1)."""
    death_entry = _make_entry("entity_death")
    harvest_entry = _make_entry("harvesting")

    death_score = EventSignificanceScorer.score(death_entry)
    harvest_score = EventSignificanceScorer.score(harvest_entry)

    assert death_score == pytest.approx(0.5)
    assert harvest_score == pytest.approx(0.1)
    assert death_score > harvest_score


# ── TC-2 ──────────────────────────────────────────────────────────────────────

def test_hero_death_scores_higher_than_commoner_death():
    """TC-2: entity_death with entity_role=HERO scores 0.8 (>= 0.8 per AC)."""
    hero_entry = _make_entry("entity_death", payload={"entity_role": "HERO"})
    commoner_entry = _make_entry("entity_death", payload={})

    hero_score = EventSignificanceScorer.score(hero_entry)
    commoner_score = EventSignificanceScorer.score(commoner_entry)

    assert hero_score == pytest.approx(0.8)
    assert hero_score >= 0.8
    assert hero_score > commoner_score


# ── TC-3 ──────────────────────────────────────────────────────────────────────

def test_is_chronicle_worthy_filters_below_threshold():
    """TC-3: is_chronicle_worthy uses CHRONICLE_THRESHOLD=0.5 correctly."""
    # exactly at threshold — worthy
    death_entry = _make_entry("entity_death")  # score = 0.5
    assert EventSignificanceScorer.is_chronicle_worthy(death_entry) is True

    # above threshold — worthy
    quest_entry = _make_entry("quest_completed")  # score = 0.7
    assert EventSignificanceScorer.is_chronicle_worthy(quest_entry) is True

    # below threshold — not worthy
    harvest_entry = _make_entry("harvesting")  # score = 0.1
    assert EventSignificanceScorer.is_chronicle_worthy(harvest_entry) is False

    # threshold constant value is correct
    assert CHRONICLE_THRESHOLD == pytest.approx(0.5)


# ── TC-4 ──────────────────────────────────────────────────────────────────────

def test_known_event_types_score_correctly():
    """TC-4: Each key in BASE_SIGNIFICANCE maps to its declared value."""
    for event_type, expected_score in BASE_SIGNIFICANCE.items():
        entry = _make_entry(event_type)
        assert EventSignificanceScorer.score(entry) == pytest.approx(expected_score), (
            f"event_type={event_type!r}: expected {expected_score}, "
            f"got {EventSignificanceScorer.score(entry)}"
        )


# ── TC-5 ──────────────────────────────────────────────────────────────────────

def test_score_capped_at_1_0():
    """TC-5: base + hero_bonus > 1.0 is capped at 1.0."""
    # faction_destroyed = 0.9 + hero_bonus 0.3 = 1.2 → capped at 1.0
    entry = _make_entry("faction_destroyed", payload={"entity_role": "HERO"})
    assert EventSignificanceScorer.score(entry) == pytest.approx(1.0)

    # calamity = 0.85 + hero_bonus 0.3 = 1.15 → capped at 1.0
    calamity_entry = _make_entry("calamity", payload={"entity_role": "HERO"})
    assert EventSignificanceScorer.score(calamity_entry) == pytest.approx(1.0)


# ── TC-6 ──────────────────────────────────────────────────────────────────────

def test_unknown_event_type_scores_default():
    """TC-6: Unrecognised event types fall back to 0.1."""
    for unknown_type in ["harvesting", "idle", "gossip", "trade", "rest", ""]:
        entry = _make_entry(unknown_type)
        assert EventSignificanceScorer.score(entry) == pytest.approx(0.1), (
            f"event_type={unknown_type!r} should score 0.1 (default)"
        )
