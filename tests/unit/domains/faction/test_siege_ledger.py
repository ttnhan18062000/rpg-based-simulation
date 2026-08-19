"""Unit tests for SIEGE_BEGINS WorldEvent emission and NarrativeLedger wiring (E53Db).

Covers:
- MilitaryConflictPhase emits SIEGE_BEGINS on first siege tick
- No duplicate SIEGE_BEGINS when siege already active
- CampaignOrchestrator._extract_narrative_entries converts SIEGE_BEGINS correctly
- List-filtered narrative_ledger returns correct entry
"""
from __future__ import annotations

from unittest.mock import MagicMock


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_faction(fid: str, territory=(), relations=None):
    from src.core.state import FactionState
    from src.core.enums import DiplomaticState
    return FactionState(
        faction_id=fid,
        territory=tuple(territory),
        diplomatic_relations={
            k: DiplomaticState(v) if isinstance(v, str) else v
            for k, v in (relations or {}).items()
        },
    )


def _make_region(rid: str, siege_state=None, service_availability=1.0):
    from src.core.state import RegionState
    return RegionState(
        id=rid, name=rid, bounds=(0, 0, 10, 10),
        siege_state=siege_state,
        service_availability=service_availability,
    )


def _make_siege(attacker="fa", defender="fb", progress=0.0, tick=1):
    from src.core.state import SiegeState
    return SiegeState(
        attacker_faction_id=attacker,
        defender_faction_id=defender,
        siege_progress=progress,
        started_tick=tick,
    )


class _FakeState:
    def __init__(self, factions=None, regions=None, entities=None, tick=1):
        self.factions = factions or {}
        self.regions = regions or {}
        self.entities = entities or {}
        self.tick = tick


def _make_world_event(category_value: str, subject: str, tick: int = 1):
    from src.domains.world_emergence.schema import WorldEvent, WorldEventCategory
    return WorldEvent(
        category=WorldEventCategory(category_value),
        tick=tick,
        subject=subject,
    )


def _make_orchestrator():
    from unittest.mock import MagicMock
    from src.domains.campaigns.orchestrator import CampaignManifest, CampaignOrchestrator
    manifest = CampaignManifest(id="test", episodes=[MagicMock()], base_seed=0)
    return CampaignOrchestrator(manifest)


# ---------------------------------------------------------------------------
# SIEGE_BEGINS emission
# ---------------------------------------------------------------------------

def test_siege_begins_emitted_on_first_siege_tick():
    """MilitaryConflictPhase emits SIEGE_BEGINS WorldEvent when siege initiates (no prior siege_state)."""
    from src.core.enums import DiplomaticState as DS
    from src.engine.military_conflict import MilitaryConflictPhase
    from src.domains.world_emergence.schema import WorldEventCategory

    factions = {
        "fa": _make_faction("fa", territory=["r1"], relations={"fb": DS.WAR}),
        "fb": _make_faction("fb", territory=["r1"], relations={"fa": DS.WAR}),
    }
    regions = {"r1": _make_region("r1", siege_state=None)}
    state = _FakeState(factions=factions, regions=regions, tick=5)

    result = MilitaryConflictPhase.execute(state)

    siege_events = [
        e for e in result.world_events_add
        if e.category == WorldEventCategory.SIEGE_BEGINS
    ]
    assert len(siege_events) == 1
    ev = siege_events[0]
    assert ev.subject == "r1"
    assert ev.tick == 5


def test_siege_begins_not_emitted_when_siege_already_active():
    """No SIEGE_BEGINS WorldEvent when siege is already in progress (second tick+)."""
    from src.core.enums import DiplomaticState as DS
    from src.engine.military_conflict import MilitaryConflictPhase
    from src.domains.world_emergence.schema import WorldEventCategory

    existing_siege = _make_siege(attacker="fa", defender="fb", progress=0.3, tick=2)
    factions = {
        "fa": _make_faction("fa", territory=["r1"], relations={"fb": DS.WAR}),
        "fb": _make_faction("fb", territory=["r1"], relations={"fa": DS.WAR}),
    }
    regions = {"r1": _make_region("r1", siege_state=existing_siege)}
    state = _FakeState(factions=factions, regions=regions, tick=6)

    result = MilitaryConflictPhase.execute(state)

    siege_events = [
        e for e in result.world_events_add
        if e.category == WorldEventCategory.SIEGE_BEGINS
    ]
    assert len(siege_events) == 0


def test_siege_begins_subject_is_region_id():
    """SIEGE_BEGINS WorldEvent.subject is the region_id (for ChronicleNamer region template)."""
    from src.core.enums import DiplomaticState as DS
    from src.engine.military_conflict import MilitaryConflictPhase
    from src.domains.world_emergence.schema import WorldEventCategory

    factions = {
        "alpha": _make_faction("alpha", territory=["fortress_north"], relations={"beta": DS.WAR}),
        "beta": _make_faction("beta", territory=["fortress_north"], relations={"alpha": DS.WAR}),
    }
    regions = {"fortress_north": _make_region("fortress_north", siege_state=None)}
    state = _FakeState(factions=factions, regions=regions, tick=10)

    result = MilitaryConflictPhase.execute(state)

    siege_events = [
        e for e in result.world_events_add
        if e.category == WorldEventCategory.SIEGE_BEGINS
    ]
    assert len(siege_events) == 1
    assert siege_events[0].subject == "fortress_north"


# ---------------------------------------------------------------------------
# Orchestrator harvesting: SIEGE_BEGINS → NarrativeLedgerEntry
# ---------------------------------------------------------------------------

def test_orchestrator_converts_siege_begins_to_ledger_entry():
    """_extract_narrative_entries converts SIEGE_BEGINS WorldEvent → entry with correct fields."""
    from src.domains.campaigns.state import NarrativeLedgerEntry

    orch = _make_orchestrator()
    mock_state = MagicMock()
    mock_state.recent_world_events = [
        _make_world_event("SIEGE_BEGINS", subject="border_keep", tick=7)
    ]

    entries = orch._extract_narrative_entries(mock_state, episode_index=2)

    assert len(entries) == 1
    e = entries[0]
    assert isinstance(e, NarrativeLedgerEntry)
    assert e.event_type == "siege_begins"
    assert e.significance == 0.80
    assert e.subject_id == "border_keep"
    assert e.tick == 7
    assert e.episode == 2


def test_siege_begins_entry_id_is_deterministic():
    """NarrativeLedgerEntry.entry_id for siege_begins follows {episode}:{tick}:{type}:{subject} pattern."""
    orch = _make_orchestrator()
    mock_state = MagicMock()
    mock_state.recent_world_events = [
        _make_world_event("SIEGE_BEGINS", subject="northern_pass", tick=3)
    ]

    entries = orch._extract_narrative_entries(mock_state, episode_index=1)

    assert entries[0].entry_id == "1:3:siege_begins:northern_pass"


def test_narrative_ledger_query_by_siege_begins():
    """narrative_ledger filtered by event_type=='siege_begins' returns the correct entry."""
    from src.domains.campaigns.state import CampaignState, NarrativeLedgerEntry

    entry = NarrativeLedgerEntry(
        episode=0,
        tick=4,
        event_type="siege_begins",
        subject_id="city_walls",
        payload={},
        significance=0.80,
        entry_id="0:4:siege_begins:city_walls",
    )
    state = CampaignState(campaign_id="c", episode_index=0, narrative_ledger=[entry])

    results = [e for e in state.narrative_ledger if e.event_type == "siege_begins"]

    assert len(results) == 1
    assert results[0].subject_id == "city_walls"
    assert results[0].significance == 0.80
