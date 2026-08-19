"""Integration tests for ChronicleCompiler faction event naming (E53Dc).

Verifies the full pipeline: NarrativeLedgerEntry → ChronicleGrouper → ChronicleRenderer
→ ChronicleNamer with faction_names/region_names resolution.

Tickets: TCK-20260619-E53Dc-COMPILER-INTEGRATION
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from src.domains.campaigns.state import CampaignState, NarrativeLedgerEntry
from src.domains.chronicle.compiler import ChronicleCompiler
from src.domains.chronicle.significance import EventSignificanceScorer


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_entry(
    event_type: str,
    subject_id: str,
    significance: float,
    tick: int = 5,
    episode: int = 0,
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


def _make_state(entries: list[NarrativeLedgerEntry]) -> CampaignState:
    return CampaignState(
        campaign_id="test_campaign",
        episode_index=len({e.episode for e in entries}),
        narrative_ledger=entries,
    )


# ---------------------------------------------------------------------------
# Test 1: significance scoring for war_declared
# ---------------------------------------------------------------------------

def test_faction_war_declared_event_in_narrative_ledger():
    """war_declared entry scores >= 0.9 and is_chronicle_worthy=True (E53D AC)."""
    entry = _make_entry(
        event_type="war_declared",
        subject_id="ALPHA:BETA",
        significance=0.95,
        tick=10,
        episode=0,
        payload={"from_faction": "ALPHA", "to_faction": "BETA"},
    )
    assert EventSignificanceScorer.score(entry) >= 0.9
    assert EventSignificanceScorer.is_chronicle_worthy(entry) is True


# ---------------------------------------------------------------------------
# Test 2: ChronicleCompiler names a war
# ---------------------------------------------------------------------------

def test_chronicle_names_the_war(tmp_path: Path):
    """Full compile() pipeline produces named milestone 'The Alpha Kingdom War against Beta Empire'."""
    entry = _make_entry(
        event_type="war_declared",
        subject_id="ALPHA:BETA",
        significance=0.95,
        tick=5,
        episode=0,
    )
    state = _make_state([entry])
    compiler = ChronicleCompiler()

    _, data = compiler.compile(
        state,
        output_dir=str(tmp_path),
        faction_names={"ALPHA": "Alpha Kingdom", "BETA": "Beta Empire"},
    )

    assert len(data["named_milestones"]) >= 1
    first = data["named_milestones"][0]
    assert first["name"] == "The Alpha Kingdom War against Beta Empire"
    assert first["event_type"] == "war_declared"
    assert first["significance"] == pytest.approx(0.95)


def test_chronicle_names_the_war_chronicle_json(tmp_path: Path):
    """compile() writes chronicle.json that contains the faction-named milestone."""
    entry = _make_entry(
        event_type="war_declared",
        subject_id="ALPHA:BETA",
        significance=0.95,
        tick=5,
        episode=0,
    )
    state = _make_state([entry])
    compiler = ChronicleCompiler()

    compiler.compile(
        state,
        output_dir=str(tmp_path),
        faction_names={"ALPHA": "Alpha Kingdom", "BETA": "Beta Empire"},
    )

    written = json.loads((tmp_path / "chronicle.json").read_text())
    names = [m["name"] for m in written["named_milestones"]]
    assert "The Alpha Kingdom War against Beta Empire" in names


# ---------------------------------------------------------------------------
# Test 3: territory_transferred with region_names
# ---------------------------------------------------------------------------

def test_chronicle_names_territory_transfer(tmp_path: Path):
    """Full compile() produces named milestone 'The Conquest of The Border Wastes'."""
    entry = _make_entry(
        event_type="territory_transferred",
        subject_id="border_region",
        significance=0.85,
        tick=20,
        episode=0,
    )
    state = _make_state([entry])
    compiler = ChronicleCompiler()

    _, data = compiler.compile(
        state,
        output_dir=str(tmp_path),
        region_names={"border_region": "The Border Wastes"},
    )

    assert len(data["named_milestones"]) >= 1
    first = data["named_milestones"][0]
    assert first["name"] == "The Conquest of The Border Wastes"
    assert first["event_type"] == "territory_transferred"


# ---------------------------------------------------------------------------
# Test 4: era naming for war-dominated eras
# ---------------------------------------------------------------------------

def test_chronicle_era_named_age_of_war(tmp_path: Path):
    """3 war_declared entries across 3 episodes → era named 'The Age of War'."""
    entries = [
        _make_entry("war_declared", "FA:FB", 0.95, tick=1, episode=0),
        _make_entry("war_declared", "FC:FD", 0.95, tick=2, episode=1),
        _make_entry("war_declared", "FE:FF", 0.95, tick=3, episode=2),
    ]
    state = _make_state(entries)
    compiler = ChronicleCompiler()

    _, data = compiler.compile(state, output_dir=str(tmp_path))

    era_names = [era["name"] for era in data["eras"]]
    assert any("Age of War" in name for name in era_names), (
        f"Expected 'Age of War' in era names, got: {era_names}"
    )
