"""Unit tests for BETRAYAL WorldEvent emission and NarrativeLedger wiring (E53Db).

Covers:
- events_from_transitions emits BETRAYAL when betrayal_updates contain ALLIED→HOSTILE
- No BETRAYAL when prior relation was not ALLIED
- Deduplication across mirror (A→B, B→A) betrayal updates
- CampaignOrchestrator._extract_narrative_entries converts BETRAYAL correctly
- List-filtered narrative_ledger returns correct entry
"""
from __future__ import annotations

from unittest.mock import MagicMock


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_faction_state(fid: str, relations: dict):
    from src.core.state import FactionState
    from src.core.enums import DiplomaticState
    return FactionState(
        faction_id=fid,
        diplomatic_relations={
            k: DiplomaticState(v) if isinstance(v, str) else v
            for k, v in relations.items()
        },
    )


def _make_faction_update(faction_id: str, relations_set: dict):
    from src.core.enums import DiplomaticState
    from src.core.updates import FactionUpdate
    return FactionUpdate(
        faction_id=faction_id,
        diplomatic_relations_set={
            k: DiplomaticState(v) if isinstance(v, str) else v
            for k, v in relations_set.items()
        },
    )


def _make_world_event(category_value: str, subject: str, tick: int = 1):
    from src.domains.world_emergence.schema import WorldEvent, WorldEventCategory
    return WorldEvent(
        category=WorldEventCategory(category_value),
        tick=tick,
        subject=subject,
    )


def _make_orchestrator():
    from src.domains.campaigns.orchestrator import CampaignManifest, CampaignOrchestrator
    manifest = CampaignManifest(id="test", episodes=[MagicMock()], base_seed=0)
    return CampaignOrchestrator(manifest)


# ---------------------------------------------------------------------------
# BETRAYAL emission via events_from_transitions
# ---------------------------------------------------------------------------

def test_betrayal_emitted_when_allied_faction_transitions_hostile():
    """events_from_transitions emits BETRAYAL when betrayal_updates show ALLIED→HOSTILE."""
    from src.core.enums import DiplomaticState as DS
    from src.domains.faction.diplomatic_state_machine import events_from_transitions
    from src.domains.world_emergence.schema import WorldEventCategory

    prior_factions = {
        "fa": _make_faction_state("fa", {"fb": DS.ALLIED}),
        "fb": _make_faction_state("fb", {"fa": DS.ALLIED}),
    }
    betrayal_upd = [_make_faction_update("fa", {"fb": DS.HOSTILE})]

    events = events_from_transitions(
        transition_updates=[],
        alliance_updates=[],
        prior_factions=prior_factions,
        tick=10,
        betrayal_updates=betrayal_upd,
    )

    betrayal_events = [e for e in events if e.category == WorldEventCategory.BETRAYAL]
    assert len(betrayal_events) == 1
    ev = betrayal_events[0]
    assert ev.tick == 10
    # subject is sorted pair
    assert ev.subject in ("fa:fb", "fb:fa")
    parts = ev.subject.split(":")
    assert sorted(parts) == ["fa", "fb"]


def test_betrayal_not_emitted_when_prior_not_allied():
    """No BETRAYAL event when prior diplomatic state was not ALLIED (e.g. NEUTRAL→HOSTILE)."""
    from src.core.enums import DiplomaticState as DS
    from src.domains.faction.diplomatic_state_machine import events_from_transitions
    from src.domains.world_emergence.schema import WorldEventCategory

    prior_factions = {
        "fa": _make_faction_state("fa", {"fb": DS.NEUTRAL}),
        "fb": _make_faction_state("fb", {"fa": DS.NEUTRAL}),
    }
    betrayal_upd = [_make_faction_update("fa", {"fb": DS.HOSTILE})]

    events = events_from_transitions(
        transition_updates=[],
        alliance_updates=[],
        prior_factions=prior_factions,
        tick=5,
        betrayal_updates=betrayal_upd,
    )

    betrayal_events = [e for e in events if e.category == WorldEventCategory.BETRAYAL]
    assert len(betrayal_events) == 0


def test_betrayal_deduped_across_mirror_updates():
    """Mirror updates (A→B and B→A) produce only one BETRAYAL event."""
    from src.core.enums import DiplomaticState as DS
    from src.domains.faction.diplomatic_state_machine import events_from_transitions
    from src.domains.world_emergence.schema import WorldEventCategory

    prior_factions = {
        "fa": _make_faction_state("fa", {"fb": DS.ALLIED}),
        "fb": _make_faction_state("fb", {"fa": DS.ALLIED}),
    }
    betrayal_upd = [
        _make_faction_update("fa", {"fb": DS.HOSTILE}),
        _make_faction_update("fb", {"fa": DS.HOSTILE}),
    ]

    events = events_from_transitions(
        transition_updates=[],
        alliance_updates=[],
        prior_factions=prior_factions,
        tick=8,
        betrayal_updates=betrayal_upd,
    )

    betrayal_events = [e for e in events if e.category == WorldEventCategory.BETRAYAL]
    assert len(betrayal_events) == 1


def test_betrayal_subject_is_sorted_pair():
    """BETRAYAL WorldEvent.subject is alphabetically sorted faction pair (consistent dedup key)."""
    from src.core.enums import DiplomaticState as DS
    from src.domains.faction.diplomatic_state_machine import events_from_transitions
    from src.domains.world_emergence.schema import WorldEventCategory

    prior_factions = {
        "zion": _make_faction_state("zion", {"alpha": DS.ALLIED}),
        "alpha": _make_faction_state("alpha", {"zion": DS.ALLIED}),
    }
    betrayal_upd = [_make_faction_update("zion", {"alpha": DS.HOSTILE})]

    events = events_from_transitions(
        transition_updates=[],
        alliance_updates=[],
        prior_factions=prior_factions,
        tick=1,
        betrayal_updates=betrayal_upd,
    )

    betrayal_events = [e for e in events if e.category == WorldEventCategory.BETRAYAL]
    assert len(betrayal_events) == 1
    assert betrayal_events[0].subject == "alpha:zion"


def test_betrayal_none_updates_backward_compat():
    """events_from_transitions with no betrayal_updates (default None) still works correctly."""
    from src.core.enums import DiplomaticState as DS
    from src.domains.faction.diplomatic_state_machine import events_from_transitions

    prior_factions = {
        "fa": _make_faction_state("fa", {"fb": DS.NEUTRAL}),
        "fb": _make_faction_state("fb", {"fa": DS.NEUTRAL}),
    }

    # Must not raise — backward-compatible with existing pipeline.py call
    events = events_from_transitions(
        transition_updates=[],
        alliance_updates=[],
        prior_factions=prior_factions,
        tick=1,
    )
    assert isinstance(events, list)


# ---------------------------------------------------------------------------
# Orchestrator harvesting: BETRAYAL → NarrativeLedgerEntry
# ---------------------------------------------------------------------------

def test_orchestrator_converts_betrayal_to_ledger_entry():
    """_extract_narrative_entries converts BETRAYAL WorldEvent → entry with correct fields."""
    from src.domains.campaigns.state import NarrativeLedgerEntry

    orch = _make_orchestrator()
    mock_state = MagicMock()
    mock_state.recent_world_events = [
        _make_world_event("BETRAYAL", subject="fa:fb", tick=12)
    ]

    entries = orch._extract_narrative_entries(mock_state, episode_index=1)

    assert len(entries) == 1
    e = entries[0]
    assert isinstance(e, NarrativeLedgerEntry)
    assert e.event_type == "betrayal"
    assert e.significance == 0.85
    assert e.subject_id == "fa:fb"
    assert e.tick == 12
    assert e.episode == 1


def test_betrayal_entry_id_is_deterministic():
    """NarrativeLedgerEntry.entry_id for betrayal follows {episode}:{tick}:{type}:{subject} pattern."""
    orch = _make_orchestrator()
    mock_state = MagicMock()
    mock_state.recent_world_events = [
        _make_world_event("BETRAYAL", subject="alpha:zion", tick=9)
    ]

    entries = orch._extract_narrative_entries(mock_state, episode_index=0)

    assert entries[0].entry_id == "0:9:betrayal:alpha:zion"


def test_narrative_ledger_query_by_betrayal():
    """narrative_ledger filtered by event_type=='betrayal' returns the correct entry."""
    from src.domains.campaigns.state import CampaignState, NarrativeLedgerEntry

    entry = NarrativeLedgerEntry(
        episode=2,
        tick=15,
        event_type="betrayal",
        subject_id="iron_throne:thornwood",
        payload={},
        significance=0.85,
        entry_id="2:15:betrayal:iron_throne:thornwood",
    )
    state = CampaignState(campaign_id="c", episode_index=0, narrative_ledger=[entry])

    results = [e for e in state.narrative_ledger if e.event_type == "betrayal"]

    assert len(results) == 1
    assert results[0].subject_id == "iron_throne:thornwood"
    assert results[0].significance == 0.85
