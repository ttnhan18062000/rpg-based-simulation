"""
tests/unit/campaigns/test_narrative_ledger.py
────────────────────────────────────────────────────────────────────────────────
Unit tests for NarrativeLedger service and NarrativeLedgerEntry extraction.
(TCK-20260619-E32D-NARRATIVE-LEDGER)

Coverage:
  TC-D1  — record() appends entry
  TC-D2  — query(event_type=...) filters by event_type
  TC-D3  — query(episode=...) filters by episode
  TC-D4  — query(min_significance=...) filters by significance
  TC-D5  — query() with no filters returns all entries
  TC-D6  — query() combined filters
  TC-D7  — to_jsonl() writes valid JSONL
  TC-D8  — to_jsonl() round-trip entries parseable
  TC-D9  — NarrativeLedgerEntry is frozen
  TC-D10 — NarrativeLedgerEntry.to_dict()/from_dict() round-trip
  TC-D11 — NarrativeLedger constructed with initial entries
  TC-D12 — _extract_narrative_entries() maps WorldEvent correctly
  TC-D13 — _extract_narrative_entries() skips unsupported categories
  TC-D14 — CampaignState.narrative_ledger populated after _advance_state()
  TC-D15 — query() returns empty list when no matches
"""
from __future__ import annotations

import dataclasses
import json
from pathlib import Path
from typing import Any, Dict, List, Optional
from unittest.mock import MagicMock

import pytest

from src.domains.campaigns.narrative_ledger import NarrativeLedger
from src.domains.campaigns.state import NarrativeLedgerEntry


# ── Helpers ───────────────────────────────────────────────────────────────────


def _make_entry(
    episode: int = 0,
    tick: int = 10,
    event_type: str = "entity_death",
    subject_id: str = "entity_1",
    payload: Optional[Dict[str, Any]] = None,
    significance: float = 0.5,
    entry_id: str = "",
) -> NarrativeLedgerEntry:
    return NarrativeLedgerEntry(
        episode=episode,
        tick=tick,
        event_type=event_type,
        subject_id=subject_id,
        payload=payload or {},
        significance=significance,
        entry_id=entry_id or f"{episode}:{tick}:{event_type}:{subject_id}",
    )


def _make_world_event(
    category_value: str,
    tick: int = 5,
    subject: Optional[str] = None,
    payload: Optional[Dict[str, float]] = None,
    severity: float = 1.0,
):
    """Build a mock WorldEvent with the given category value."""
    category = MagicMock()
    category.value = category_value
    event = MagicMock()
    event.category = category
    event.tick = tick
    event.subject = subject
    event.payload = payload or {}
    event.severity = severity
    return event


def _make_final_state(world_events: list):
    """Build a mock AuthoritativeState with given recent_world_events."""
    state = MagicMock()
    state.recent_world_events = world_events
    state.entities = {}
    return state


# ── TC-D1: record() appends entry ─────────────────────────────────────────────


def test_narrative_ledger_record_appends():
    """TC-D1: record() grows the ledger by one."""
    ledger = NarrativeLedger()
    assert len(ledger) == 0
    ledger.record(_make_entry())
    assert len(ledger) == 1


# ── TC-D2: query(event_type=...) ──────────────────────────────────────────────


def test_narrative_ledger_query_by_event_type():
    """TC-D2: query(event_type='entity_death') returns only death entries."""
    ledger = NarrativeLedger(entries=[
        _make_entry(event_type="entity_death", subject_id="e1"),
        _make_entry(event_type="quest_completed", subject_id="q1"),
        _make_entry(event_type="entity_death", subject_id="e2"),
        _make_entry(event_type="faction_shift", subject_id="f1"),
    ])
    result = ledger.query(event_type="entity_death")
    assert len(result) == 2
    assert all(e.event_type == "entity_death" for e in result)
    subject_ids = {e.subject_id for e in result}
    assert subject_ids == {"e1", "e2"}


# ── TC-D3: query(episode=...) ─────────────────────────────────────────────────


def test_narrative_ledger_query_by_episode():
    """TC-D3: query(episode=1) returns only episode-1 entries."""
    ledger = NarrativeLedger(entries=[
        _make_entry(episode=0, subject_id="a"),
        _make_entry(episode=1, subject_id="b"),
        _make_entry(episode=0, subject_id="c"),
        _make_entry(episode=1, subject_id="d"),
    ])
    result = ledger.query(episode=1)
    assert len(result) == 2
    assert all(e.episode == 1 for e in result)
    subject_ids = {e.subject_id for e in result}
    assert subject_ids == {"b", "d"}


# ── TC-D4: query(min_significance=...) ───────────────────────────────────────


def test_narrative_ledger_query_by_significance():
    """TC-D4: query(min_significance=0.6) returns only high-significance entries."""
    ledger = NarrativeLedger(entries=[
        _make_entry(significance=0.3, subject_id="low"),
        _make_entry(significance=0.5, subject_id="mid"),
        _make_entry(significance=0.9, subject_id="high"),
        _make_entry(significance=0.7, subject_id="med_high"),
    ])
    result = ledger.query(min_significance=0.6)
    assert len(result) == 2
    subject_ids = {e.subject_id for e in result}
    assert subject_ids == {"high", "med_high"}


# ── TC-D5: query() no filters returns all ─────────────────────────────────────


def test_narrative_ledger_query_no_filters_returns_all():
    """TC-D5: query() with no arguments returns all entries."""
    entries = [_make_entry(subject_id=f"s{i}") for i in range(5)]
    ledger = NarrativeLedger(entries=entries)
    result = ledger.query()
    assert len(result) == 5


# ── TC-D6: query() combined filters ───────────────────────────────────────────


def test_narrative_ledger_query_combined_filters():
    """TC-D6: Combined event_type + episode filters return correct subset."""
    ledger = NarrativeLedger(entries=[
        _make_entry(episode=0, event_type="quest_completed", subject_id="q0"),
        _make_entry(episode=0, event_type="entity_death",    subject_id="e0"),
        _make_entry(episode=1, event_type="quest_completed", subject_id="q1"),
        _make_entry(episode=1, event_type="entity_death",    subject_id="e1"),
    ])
    result = ledger.query(event_type="quest_completed", episode=0)
    assert len(result) == 1
    assert result[0].subject_id == "q0"


# ── TC-D7: to_jsonl() writes valid JSONL ──────────────────────────────────────


def test_narrative_ledger_to_jsonl_writes_valid_lines(tmp_path):
    """TC-D7: to_jsonl() writes one valid JSON object per line."""
    entries = [
        _make_entry(episode=0, tick=10, event_type="entity_death",    subject_id="e1"),
        _make_entry(episode=0, tick=20, event_type="quest_completed",  subject_id="q1"),
        _make_entry(episode=1, tick=5,  event_type="faction_shift",    subject_id="f1"),
    ]
    ledger = NarrativeLedger(entries=entries)
    out = tmp_path / "ledger.jsonl"
    ledger.to_jsonl(str(out))

    lines = out.read_text(encoding="utf-8").strip().split("\n")
    assert len(lines) == 3
    for line in lines:
        obj = json.loads(line)
        assert "episode" in obj
        assert "tick" in obj
        assert "event_type" in obj
        assert "subject_id" in obj
        assert "payload" in obj
        assert "significance" in obj


# ── TC-D8: to_jsonl() round-trip parseable ────────────────────────────────────


def test_narrative_ledger_to_jsonl_round_trip(tmp_path):
    """TC-D8: Each JSONL line deserializes to a dict matching entry.to_dict()."""
    entries = [_make_entry(significance=0.7, payload={"xp": 100.0})]
    ledger = NarrativeLedger(entries=entries)
    out = tmp_path / "rt.jsonl"
    ledger.to_jsonl(str(out))

    lines = out.read_text(encoding="utf-8").strip().split("\n")
    assert len(lines) == 1
    parsed = json.loads(lines[0])
    assert parsed == entries[0].to_dict()
    assert parsed["significance"] == pytest.approx(0.7)
    assert parsed["payload"] == {"xp": 100.0}


# ── TC-D9: NarrativeLedgerEntry is frozen ─────────────────────────────────────


def test_narrative_ledger_entry_is_frozen():
    """TC-D9: NarrativeLedgerEntry is immutable (frozen dataclass)."""
    entry = _make_entry()
    with pytest.raises((dataclasses.FrozenInstanceError, AttributeError)):
        entry.significance = 0.99  # type: ignore[misc]


# ── TC-D10: to_dict()/from_dict() round-trip ──────────────────────────────────


def test_narrative_ledger_entry_to_dict_from_dict_round_trip():
    """TC-D10: Full field round-trip through to_dict()/from_dict()."""
    original = NarrativeLedgerEntry(
        episode=2,
        tick=300,
        event_type="faction_shift",
        subject_id="faction_5",
        payload={"tension_delta": 0.3},
        significance=0.9,
        entry_id="2:300:faction_shift:faction_5",
    )
    restored = NarrativeLedgerEntry.from_dict(original.to_dict())
    assert restored == original
    assert restored.episode == 2
    assert restored.event_type == "faction_shift"
    assert restored.significance == pytest.approx(0.9)
    assert restored.payload == {"tension_delta": 0.3}
    assert restored.entry_id == "2:300:faction_shift:faction_5"


# ── TC-D11: Construction with initial entries ─────────────────────────────────


def test_narrative_ledger_constructed_with_entries():
    """TC-D11: NarrativeLedger(entries=[...]) accepts existing entries."""
    entries = [_make_entry(subject_id=f"s{i}") for i in range(3)]
    ledger = NarrativeLedger(entries=entries)
    result = ledger.query()
    assert len(result) == 3
    assert {e.subject_id for e in result} == {"s0", "s1", "s2"}


# ── TC-D12: _extract_narrative_entries() maps WorldEvent correctly ─────────────


def test_extract_narrative_entries_maps_entity_death():
    """TC-D12: ENTITY_DEATH WorldEvent maps to entity_death entry with significance 0.5."""
    from src.domains.campaigns.orchestrator import CampaignManifest, CampaignOrchestrator

    manifest = CampaignManifest(id="test", episodes=[], base_seed=0)
    orch = CampaignOrchestrator(manifest)

    world_events = [
        _make_world_event("ENTITY_DEATH", tick=7, subject="entity_42", payload={"hp": 0.0}),
        _make_world_event("QUEST_COMPLETED", tick=9, subject="quest_01"),
    ]
    final_state = _make_final_state(world_events)

    entries = orch._extract_narrative_entries(final_state, episode_index=0)

    assert len(entries) == 2

    death_entry = next(e for e in entries if e.event_type == "entity_death")
    assert death_entry.episode == 0
    assert death_entry.tick == 7
    assert death_entry.subject_id == "entity_42"
    assert death_entry.significance == pytest.approx(0.5)
    assert death_entry.payload == {"hp": 0.0}
    assert death_entry.entry_id == "0:7:entity_death:entity_42"

    quest_entry = next(e for e in entries if e.event_type == "quest_completed")
    assert quest_entry.significance == pytest.approx(0.7)
    assert quest_entry.subject_id == "quest_01"


def test_extract_narrative_entries_camp_cleared_is_faction_shift():
    """TC-D12b: CAMP_CLEARED maps to faction_shift with significance 0.9."""
    from src.domains.campaigns.orchestrator import CampaignManifest, CampaignOrchestrator

    manifest = CampaignManifest(id="test", episodes=[], base_seed=0)
    orch = CampaignOrchestrator(manifest)

    world_events = [_make_world_event("CAMP_CLEARED", tick=15, subject="camp_north")]
    final_state = _make_final_state(world_events)

    entries = orch._extract_narrative_entries(final_state, episode_index=1)
    assert len(entries) == 1
    assert entries[0].event_type == "faction_shift"
    assert entries[0].significance == pytest.approx(0.9)
    assert entries[0].episode == 1


# ── TC-D13: _extract_narrative_entries() skips unsupported categories ──────────


def test_extract_narrative_entries_skips_unsupported_categories():
    """TC-D13: Categories not in _SIGNIFICANCE_MAP are ignored."""
    from src.domains.campaigns.orchestrator import CampaignManifest, CampaignOrchestrator

    manifest = CampaignManifest(id="test", episodes=[], base_seed=0)
    orch = CampaignOrchestrator(manifest)

    world_events = [
        _make_world_event("REGION_ENTERED", tick=3, subject="region_forest"),
        _make_world_event("RESOURCE_HARVESTED", tick=4, subject="node_01"),
        _make_world_event("NEAR_DEATH", tick=5, subject="entity_7"),
        _make_world_event("ENTITY_DEATH", tick=6, subject="entity_8"),  # supported
    ]
    final_state = _make_final_state(world_events)

    entries = orch._extract_narrative_entries(final_state, episode_index=0)
    assert len(entries) == 1
    assert entries[0].event_type == "entity_death"


# ── TC-D14: narrative_ledger populated after _advance_state() ─────────────────


def test_campaign_orchestrator_advance_state_populates_narrative_ledger():
    """TC-D14: After _advance_state(), CampaignState.narrative_ledger has entries."""
    from src.domains.campaigns.orchestrator import CampaignManifest, CampaignOrchestrator
    from src.domains.campaigns.state import EpisodeSummary

    manifest = CampaignManifest(id="test", episodes=[], base_seed=0)
    orch = CampaignOrchestrator(manifest)

    world_events = [
        _make_world_event("ENTITY_DEATH",    tick=3, subject="entity_1"),
        _make_world_event("QUEST_COMPLETED", tick=5, subject="quest_main"),
        _make_world_event("CAMP_CLEARED",    tick=8, subject="camp_east"),
    ]
    final_state = _make_final_state(world_events)

    summary = EpisodeSummary(episode_index=0, completed_tick=10)
    orch._advance_state(final_state, summary)

    assert len(orch.state.narrative_ledger) == 3
    event_types = {e.event_type for e in orch.state.narrative_ledger}
    assert "entity_death" in event_types
    assert "quest_completed" in event_types
    assert "faction_shift" in event_types
    assert all(e.episode == 0 for e in orch.state.narrative_ledger)

    # Second episode — entries accumulate
    summary1 = EpisodeSummary(episode_index=1, completed_tick=20)
    world_events_ep1 = [_make_world_event("ENTITY_DEATH", tick=12, subject="entity_2")]
    final_state1 = _make_final_state(world_events_ep1)
    orch._advance_state(final_state1, summary1)

    assert len(orch.state.narrative_ledger) == 4
    ep1_entries = [e for e in orch.state.narrative_ledger if e.episode == 1]
    assert len(ep1_entries) == 1


# ── TC-D15: query() returns empty list when no matches ────────────────────────


def test_narrative_ledger_query_empty_ledger():
    """TC-D15: query() on empty ledger returns []."""
    ledger = NarrativeLedger()
    assert ledger.query() == []
    assert ledger.query(event_type="entity_death") == []
    assert ledger.query(episode=0) == []
    assert ledger.query(min_significance=0.5) == []


def test_narrative_ledger_query_no_match():
    """TC-D15b: query() with filters returns [] when no entry matches."""
    ledger = NarrativeLedger(entries=[_make_entry(event_type="entity_death", episode=0)])
    assert ledger.query(event_type="quest_completed") == []
    assert ledger.query(episode=5) == []
    assert ledger.query(min_significance=1.0) == []
