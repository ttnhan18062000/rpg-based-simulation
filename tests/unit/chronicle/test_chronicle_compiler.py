"""
tests/unit/chronicle/test_chronicle_compiler.py
────────────────────────────────────────────────────────────────────────────────
Unit tests for EventSignificanceScorer (E51A) and ChronicleGrouper (E51B).

Covers:
  E51A — EventSignificanceScorer:
  - TC-1: death ranks above unknown/harvesting event type
  - TC-2: hero death scores >= 0.8
  - TC-3: is_chronicle_worthy filters below CHRONICLE_THRESHOLD
  - TC-4: all known BASE_SIGNIFICANCE types score correctly
  - TC-5: score is capped at 1.0
  - TC-6: unknown event type defaults to 0.1

  E51B — ChronicleGrouper:
  - TC-7: grouping 15 events produces ≥2 incident clusters (AC-1)
  - TC-8: hierarchy contains all four levels — events, incidents, episodes, eras (AC-2)
  - TC-9: events >50 ticks apart in same episode → separate incidents
  - TC-10: below-threshold events are excluded from the hierarchy
  - TC-11: era boundary every ERA_EPISODE_MIN episodes
  - TC-12: empty input returns empty hierarchy
"""
import pytest

from src.domains.campaigns.state import NarrativeLedgerEntry
from src.domains.chronicle.grouper import ChronicleGrouper
from src.domains.chronicle.significance import (
    BASE_SIGNIFICANCE,
    CHRONICLE_THRESHOLD,
    EventSignificanceScorer,
)


# ── helpers ───────────────────────────────────────────────────────────────────

def _make_entry(
    event_type: str,
    payload: dict | None = None,
    episode: int = 0,
    tick: int = 1,
    subject_id: str = "test-subject",
) -> NarrativeLedgerEntry:
    return NarrativeLedgerEntry(
        episode=episode,
        tick=tick,
        event_type=event_type,
        subject_id=subject_id,
        payload=payload or {},
        significance=0.0,  # raw ledger significance — scorer re-derives independently
        entry_id=f"{episode}:{tick}:{event_type}:{subject_id}",
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


# ═══════════════════════════════════════════════════════════════════════════════
# E51B — ChronicleGrouper tests
# ═══════════════════════════════════════════════════════════════════════════════

# ── TC-7 ──────────────────────────────────────────────────────────────────────

def test_event_grouping_produces_incident_clusters():
    """TC-7 (AC-1): 15 worthy events in two separated tick clusters → ≥2 incidents.

    Structure:
      - Episode 0, ticks 10-50 → 8 quest_completed events (one cluster)
      - Episode 0, ticks 200-240 → 7 entity_death events (separated by >50 ticks)
    Expected: ≥2 incidents produced.
    """
    entries = []
    # cluster 1: 8 events within window
    for i in range(8):
        entries.append(_make_entry("quest_completed", episode=0, tick=10 + i * 5))
    # cluster 2: 7 events within window but >50 ticks from cluster 1
    for i in range(7):
        entries.append(_make_entry("entity_death", episode=0, tick=200 + i * 5))

    grouper = ChronicleGrouper()
    hierarchy = grouper.group(entries)

    assert len(hierarchy.events) == 15
    assert len(hierarchy.incidents) >= 2, (
        f"Expected ≥2 incidents, got {len(hierarchy.incidents)}"
    )


# ── TC-8 ──────────────────────────────────────────────────────────────────────

def test_chronicle_hierarchy_contains_all_four_levels():
    """TC-8 (AC-2): hierarchy exposes all four levels — events, incidents, episodes, eras."""
    entries = []
    # 3 episodes × 3 events each → 3 episodes → 1 era (ERA_EPISODE_MIN=3)
    for ep in range(3):
        for t in range(3):
            entries.append(_make_entry("calamity", episode=ep, tick=10 + t * 5))

    grouper = ChronicleGrouper()
    hierarchy = grouper.group(entries)

    assert len(hierarchy.events) > 0,    "events must not be empty"
    assert len(hierarchy.incidents) > 0, "incidents must not be empty"
    assert len(hierarchy.episodes) > 0,  "episodes must not be empty"
    assert len(hierarchy.eras) > 0,      "eras must not be empty"


# ── TC-9 ──────────────────────────────────────────────────────────────────────

def test_incident_groups_by_tick_window():
    """TC-9: Events within 50 ticks → same incident; >50 apart → separate incidents."""
    grouper = ChronicleGrouper()

    # two events exactly at the window boundary — should be same incident
    close = [
        _make_entry("quest_completed", episode=0, tick=100),
        _make_entry("quest_completed", episode=0, tick=150),  # gap = 50 (within)
    ]
    h_close = grouper.group(close)
    assert len(h_close.incidents) == 1, "gap == 50 should still be same incident"

    # two events just beyond the window — separate incidents
    far = [
        _make_entry("quest_completed", episode=0, tick=100),
        _make_entry("quest_completed", episode=0, tick=151),  # gap = 51 (beyond)
    ]
    h_far = grouper.group(far)
    assert len(h_far.incidents) == 2, "gap == 51 should split into two incidents"


# ── TC-10 ─────────────────────────────────────────────────────────────────────

def test_below_threshold_events_excluded():
    """TC-10: Non-worthy events (score < 0.5) are excluded from all hierarchy levels."""
    entries = [
        _make_entry("harvesting", episode=0, tick=10),   # score 0.1 — below threshold
        _make_entry("quest_completed", episode=0, tick=20),  # score 0.7 — worthy
        _make_entry("idle", episode=0, tick=30),         # score 0.1 — below threshold
    ]

    grouper = ChronicleGrouper()
    hierarchy = grouper.group(entries)

    assert len(hierarchy.events) == 1, "only the worthy event should be in hierarchy.events"
    assert all(
        EventSignificanceScorer.is_chronicle_worthy(e) for e in hierarchy.events
    ), "all events in hierarchy must be chronicle-worthy"
    assert len(hierarchy.incidents) == 1


# ── TC-11 ─────────────────────────────────────────────────────────────────────

def test_era_boundary_every_n_episodes():
    """TC-11: ERA_EPISODE_MIN=3 → episodes grouped into eras of ≤ERA_EPISODE_MIN."""
    grouper = ChronicleGrouper()

    # 6 episodes → exactly 2 eras
    entries = []
    for ep in range(6):
        entries.append(_make_entry("calamity", episode=ep, tick=10))

    hierarchy = grouper.group(entries)
    assert len(hierarchy.episodes) == 6
    assert len(hierarchy.eras) == 2, f"6 episodes / ERA_EPISODE_MIN=3 should give 2 eras"
    for era in hierarchy.eras:
        assert len(era.episodes) == 3

    # 7 episodes → 2 full eras + 1 partial era (3+3+1)
    entries2 = []
    for ep in range(7):
        entries2.append(_make_entry("calamity", episode=ep, tick=10))

    h2 = grouper.group(entries2)
    assert len(h2.eras) == 3, f"7 episodes should give 3 eras (3+3+1)"


# ── TC-12 ─────────────────────────────────────────────────────────────────────

def test_empty_input_returns_empty_hierarchy():
    """TC-12: Empty input list produces an empty ChronicleHierarchy."""
    grouper = ChronicleGrouper()
    hierarchy = grouper.group([])

    assert len(hierarchy.events) == 0
    assert len(hierarchy.incidents) == 0
    assert len(hierarchy.episodes) == 0
    assert len(hierarchy.eras) == 0
