"""Unit tests for EventSignificanceScorer faction event types (E53Da).

Tickets: TCK-20260619-E53Da-SIGNIFICANCE-NAMING
AC: faction events score above CHRONICLE_THRESHOLD; specific values per type.
"""
from __future__ import annotations

import pytest

from src.domains.campaigns.state import NarrativeLedgerEntry
from src.domains.chronicle.significance import (
    BASE_SIGNIFICANCE,
    CHRONICLE_THRESHOLD,
    EventSignificanceScorer,
)


def _make_entry(event_type: str, payload: dict | None = None) -> NarrativeLedgerEntry:
    return NarrativeLedgerEntry(
        episode=0,
        tick=1,
        event_type=event_type,
        subject_id="test",
        payload=payload or {},
        significance=0.0,
        entry_id=f"0:1:{event_type}:test",
    )


# ---------------------------------------------------------------------------
# Faction event significance values
# ---------------------------------------------------------------------------

def test_war_declared_scores_0_95():
    """war_declared scores 0.95 — above CHRONICLE_THRESHOLD."""
    entry = _make_entry("war_declared")
    assert EventSignificanceScorer.score(entry) == pytest.approx(0.95)
    assert EventSignificanceScorer.is_chronicle_worthy(entry)


def test_siege_begins_scores_0_80():
    """siege_begins scores 0.80."""
    entry = _make_entry("siege_begins")
    assert EventSignificanceScorer.score(entry) == pytest.approx(0.80)
    assert EventSignificanceScorer.is_chronicle_worthy(entry)


def test_territory_transferred_scores_0_85():
    """territory_transferred scores 0.85."""
    entry = _make_entry("territory_transferred")
    assert EventSignificanceScorer.score(entry) == pytest.approx(0.85)
    assert EventSignificanceScorer.is_chronicle_worthy(entry)


def test_alliance_formed_scores_0_80():
    """alliance_formed scores 0.80."""
    entry = _make_entry("alliance_formed")
    assert EventSignificanceScorer.score(entry) == pytest.approx(0.80)
    assert EventSignificanceScorer.is_chronicle_worthy(entry)


def test_peace_treaty_scores_0_75():
    """peace_treaty scores 0.75."""
    entry = _make_entry("peace_treaty")
    assert EventSignificanceScorer.score(entry) == pytest.approx(0.75)
    assert EventSignificanceScorer.is_chronicle_worthy(entry)


def test_betrayal_scores_0_85():
    """betrayal scores 0.85."""
    entry = _make_entry("betrayal")
    assert EventSignificanceScorer.score(entry) == pytest.approx(0.85)
    assert EventSignificanceScorer.is_chronicle_worthy(entry)


# ---------------------------------------------------------------------------
# E53D acceptance criterion
# ---------------------------------------------------------------------------

def test_faction_war_declared_event_in_narrative_ledger():
    """E53D AC: war_declared scores >= 0.9, passing CHRONICLE_THRESHOLD."""
    entry = _make_entry("war_declared")
    score = EventSignificanceScorer.score(entry)
    assert score >= 0.9, f"war_declared should score >= 0.9, got {score}"
    assert EventSignificanceScorer.is_chronicle_worthy(entry)


# ---------------------------------------------------------------------------
# Hero bonus still works on faction events
# ---------------------------------------------------------------------------

def test_hero_bonus_applies_to_faction_events_capped_at_1():
    """Hero bonus on already-high faction events is capped at 1.0."""
    entry = _make_entry("war_declared", payload={"entity_role": "HERO"})
    score = EventSignificanceScorer.score(entry)
    # 0.95 + 0.3 = 1.25 → capped at 1.0
    assert score == pytest.approx(1.0)


# ---------------------------------------------------------------------------
# Faction keys exist in BASE_SIGNIFICANCE
# ---------------------------------------------------------------------------

def test_faction_keys_present_in_base_significance():
    """All 6 faction event types are registered in BASE_SIGNIFICANCE."""
    expected_keys = {
        "war_declared", "siege_begins", "territory_transferred",
        "alliance_formed", "peace_treaty", "betrayal",
    }
    missing = expected_keys - set(BASE_SIGNIFICANCE.keys())
    assert not missing, f"Missing keys in BASE_SIGNIFICANCE: {missing}"
