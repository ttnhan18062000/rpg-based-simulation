"""Unit tests for E53Cc: territory transfer via siege_progress >= 1.0."""
from __future__ import annotations

from dataclasses import replace


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_faction(fid: str, territory=(), relations=None):
    from src.core.state import FactionState
    from src.core.enums import DiplomaticState
    return FactionState(
        faction_id=fid,
        territory=tuple(territory),
        diplomatic_relations={k: DiplomaticState(v) if isinstance(v, str) else v
                               for k, v in (relations or {}).items()},
    )


def _make_region(rid: str, bounds=(0, 0, 10, 10), siege_state=None, service_availability=1.0):
    from src.core.state import RegionState
    return RegionState(
        id=rid, name=rid, bounds=bounds,
        siege_state=siege_state, service_availability=service_availability,
    )


def _make_siege(attacker="fa", defender="fb", progress=1.0, tick=1):
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


# ---------------------------------------------------------------------------
# Territory transfer trigger
# ---------------------------------------------------------------------------

def test_transfer_triggers_when_siege_progress_is_1():
    """MilitaryConflictPhase emits siege_state_clear and territory events at progress >= 1.0."""
    from src.core.enums import DiplomaticState as DS
    from src.engine.military_conflict import MilitaryConflictPhase
    from src.domains.world_emergence.schema import WorldEventCategory

    ss = _make_siege(attacker="fa", defender="fb", progress=1.0, tick=1)
    factions = {
        "fa": _make_faction("fa", relations={"fb": DS.WAR}),
        "fb": _make_faction("fb", territory=["r_border"], relations={"fa": DS.WAR}),
    }
    regions = {"r_border": _make_region("r_border", siege_state=ss, service_availability=0.5)}
    state = _FakeState(factions=factions, regions=regions, tick=21)

    result = MilitaryConflictPhase.execute(state)

    # WorldUpdate should clear siege and restore service
    assert "r_border" in result.world_updates
    wu = result.world_updates["r_border"]
    assert wu.siege_state_clear is True
    assert wu.service_availability_delta > 0  # restoring

    # FactionUpdates: attacker gains, defender loses
    fu_by_fid = {fu.faction_id: fu for fu in result.faction_updates}
    assert "fa" in fu_by_fid
    assert "r_border" in fu_by_fid["fa"].territory_add
    assert "fb" in fu_by_fid
    assert "r_border" in fu_by_fid["fb"].territory_remove

    # WorldEvent emitted
    te_events = [e for e in result.world_events_add
                 if e.category == WorldEventCategory.TERRITORY_TRANSFERRED]
    assert len(te_events) == 1
    ev = te_events[0]
    assert "fa" in ev.subject
    assert "fb" in ev.subject
    assert "r_border" in ev.subject


def test_transfer_does_not_emit_degradation():
    """On the transfer tick, no siege_progress_delta or service_availability degradation is emitted."""
    from src.core.enums import DiplomaticState as DS
    from src.engine.military_conflict import MilitaryConflictPhase

    ss = _make_siege(progress=1.0)
    factions = {
        "fa": _make_faction("fa", relations={"fb": DS.WAR}),
        "fb": _make_faction("fb", territory=["r1"], relations={"fa": DS.WAR}),
    }
    regions = {"r1": _make_region("r1", siege_state=ss)}
    state = _FakeState(factions=factions, regions=regions, tick=21)

    result = MilitaryConflictPhase.execute(state)
    wu = result.world_updates.get("r1")
    assert wu is not None
    # No negative degradation this tick — this is the transfer tick
    assert wu.siege_progress_delta == 0.0
    assert wu.service_availability_delta > 0  # only positive restore


def test_no_transfer_when_progress_below_1():
    """siege_progress < 1.0 does not trigger territory transfer."""
    from src.core.enums import DiplomaticState as DS
    from src.engine.military_conflict import MilitaryConflictPhase
    from src.domains.world_emergence.schema import WorldEventCategory

    ss = _make_siege(progress=0.95)
    factions = {
        "fa": _make_faction("fa", relations={"fb": DS.WAR}),
        "fb": _make_faction("fb", territory=["r1"], relations={"fa": DS.WAR}),
    }
    regions = {"r1": _make_region("r1", siege_state=ss)}
    state = _FakeState(factions=factions, regions=regions, tick=20)

    result = MilitaryConflictPhase.execute(state)

    # No TERRITORY_TRANSFERRED event
    te_events = [e for e in result.world_events_add
                 if e.category == WorldEventCategory.TERRITORY_TRANSFERRED]
    assert len(te_events) == 0

    # No siege_state_clear
    wu = result.world_updates.get("r1")
    assert wu is None or not wu.siege_state_clear

    # No faction territory changes (drain FactionUpdates are OK — check no territory mutations)
    for fu in result.faction_updates:
        assert not fu.territory_add, f"Unexpected territory_add in {fu}"
        assert not fu.territory_remove, f"Unexpected territory_remove in {fu}"


def test_transfer_world_event_subject_format():
    """TERRITORY_TRANSFERRED subject encodes attacker:defender:region_id."""
    from src.core.enums import DiplomaticState as DS
    from src.engine.military_conflict import MilitaryConflictPhase
    from src.domains.world_emergence.schema import WorldEventCategory

    ss = _make_siege(attacker="alpha", defender="beta", progress=1.0)
    factions = {
        "alpha": _make_faction("alpha", relations={"beta": DS.WAR}),
        "beta": _make_faction("beta", territory=["border"], relations={"alpha": DS.WAR}),
    }
    regions = {"border": _make_region("border", siege_state=ss)}
    state = _FakeState(factions=factions, regions=regions, tick=21)

    result = MilitaryConflictPhase.execute(state)
    ev = next(e for e in result.world_events_add
              if e.category == WorldEventCategory.TERRITORY_TRANSFERRED)
    assert ev.subject == "alpha:beta:border"
    assert ev.tick == 21


def test_transfer_service_availability_restored():
    """Transfer WorldUpdate includes service_availability_delta=+1.0 to restore region service."""
    from src.core.enums import DiplomaticState as DS
    from src.engine.military_conflict import MilitaryConflictPhase

    ss = _make_siege(progress=1.0)
    factions = {
        "fa": _make_faction("fa", relations={"fb": DS.WAR}),
        "fb": _make_faction("fb", territory=["r1"], relations={"fa": DS.WAR}),
    }
    regions = {"r1": _make_region("r1", siege_state=ss, service_availability=0.3)}
    state = _FakeState(factions=factions, regions=regions, tick=21)

    result = MilitaryConflictPhase.execute(state)
    wu = result.world_updates["r1"]
    # +1.0 restore; apply_plan clamps to 1.0 regardless of current value
    assert wu.service_availability_delta == 1.0


def test_territory_transferred_category_exists():
    """WorldEventCategory.TERRITORY_TRANSFERRED exists and has correct value."""
    from src.domains.world_emergence.schema import WorldEventCategory
    assert WorldEventCategory.TERRITORY_TRANSFERRED == "TERRITORY_TRANSFERRED"


def test_territory_transferred_significance_in_map():
    """TERRITORY_TRANSFERRED is in the orchestrator significance map at 0.85."""
    from src.domains.campaigns.orchestrator import _SIGNIFICANCE_MAP
    assert "TERRITORY_TRANSFERRED" in _SIGNIFICANCE_MAP
    event_type, sig = _SIGNIFICANCE_MAP["TERRITORY_TRANSFERRED"]
    assert event_type == "territory_transferred"
    assert sig == 0.85
