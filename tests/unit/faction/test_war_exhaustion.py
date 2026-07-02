"""Unit tests for E53Cd: military_strength drain, WAR_ENDED_EXHAUSTION, orphan siege cleanup."""
from __future__ import annotations


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_faction(fid: str, territory=(), relations=None, military_strength=1.0):
    from src.core.state import FactionState
    from src.core.enums import DiplomaticState
    return FactionState(
        faction_id=fid,
        military_strength=military_strength,
        territory=tuple(territory),
        diplomatic_relations={k: DiplomaticState(v) if isinstance(v, str) else v
                               for k, v in (relations or {}).items()},
    )


def _make_region(rid: str, bounds=(0, 0, 10, 10), siege_state=None, service_availability=1.0):
    from src.core.state import RegionState
    return RegionState(id=rid, name=rid, bounds=bounds,
                       siege_state=siege_state, service_availability=service_availability)


def _make_siege(attacker="fa", defender="fb", progress=0.0, tick=1):
    from src.core.state import SiegeState
    return SiegeState(attacker_faction_id=attacker, defender_faction_id=defender,
                      siege_progress=progress, started_tick=tick)


class _FakeState:
    def __init__(self, factions=None, regions=None, entities=None, tick=1):
        self.factions = factions or {}
        self.regions = regions or {}
        self.entities = entities or {}
        self.tick = tick


# ---------------------------------------------------------------------------
# AC1: military_strength drains by 0.001/tick per WAR faction
# ---------------------------------------------------------------------------

def test_exhaustion_drain_emits_military_strength_set():
    """execute() emits FactionUpdate with military_strength_set reduced by 0.001."""
    from src.core.enums import DiplomaticState as DS
    from src.engine.military_conflict import MilitaryConflictPhase

    factions = {
        "fa": _make_faction("fa", military_strength=0.5, relations={"fb": DS.WAR}),
        "fb": _make_faction("fb", military_strength=0.5, relations={"fa": DS.WAR}),
    }
    state = _FakeState(factions=factions, regions={}, tick=1)
    result = MilitaryConflictPhase.execute(state)

    fu_by_fid = {fu.faction_id: fu for fu in result.faction_updates
                 if fu.military_strength_set is not None}
    assert "fa" in fu_by_fid
    assert "fb" in fu_by_fid
    import math
    assert math.isclose(fu_by_fid["fa"].military_strength_set, 0.499, abs_tol=1e-9)
    assert math.isclose(fu_by_fid["fb"].military_strength_set, 0.499, abs_tol=1e-9)


def test_exhaustion_drain_clamped_to_zero():
    """military_strength never drains below 0.0."""
    from src.core.enums import DiplomaticState as DS
    from src.engine.military_conflict import MilitaryConflictPhase

    factions = {
        "fa": _make_faction("fa", military_strength=0.0, relations={"fb": DS.WAR}),
        "fb": _make_faction("fb", military_strength=0.0, relations={"fa": DS.WAR}),
    }
    state = _FakeState(factions=factions, regions={}, tick=1)
    result = MilitaryConflictPhase.execute(state)

    fu_by_fid = {fu.faction_id: fu for fu in result.faction_updates
                 if fu.military_strength_set is not None}
    assert fu_by_fid["fa"].military_strength_set == 0.0
    assert fu_by_fid["fb"].military_strength_set == 0.0


def test_exhaustion_drain_deduplicated_per_faction():
    """A faction in multiple WAR pairs is drained only once."""
    from src.core.enums import DiplomaticState as DS
    from src.engine.military_conflict import MilitaryConflictPhase

    factions = {
        "fa": _make_faction("fa", military_strength=0.5,
                            relations={"fb": DS.WAR, "fc": DS.WAR}),
        "fb": _make_faction("fb", military_strength=0.5, relations={"fa": DS.WAR}),
        "fc": _make_faction("fc", military_strength=0.5, relations={"fa": DS.WAR}),
    }
    state = _FakeState(factions=factions, regions={}, tick=1)
    result = MilitaryConflictPhase.execute(state)

    # "fa" should appear exactly once in drain updates
    fa_drain_updates = [fu for fu in result.faction_updates
                        if fu.faction_id == "fa" and fu.military_strength_set is not None]
    assert len(fa_drain_updates) == 1
    import math
    assert math.isclose(fa_drain_updates[0].military_strength_set, 0.499, abs_tol=1e-9)


def test_no_drain_when_not_at_war():
    """Factions not at WAR do not receive military_strength drain."""
    from src.core.enums import DiplomaticState as DS
    from src.engine.military_conflict import MilitaryConflictPhase

    factions = {
        "fa": _make_faction("fa", military_strength=0.5, relations={"fb": DS.HOSTILE}),
        "fb": _make_faction("fb", military_strength=0.5, relations={"fa": DS.HOSTILE}),
    }
    state = _FakeState(factions=factions, regions={}, tick=1)
    result = MilitaryConflictPhase.execute(state)

    drain_updates = [fu for fu in result.faction_updates if fu.military_strength_set is not None]
    assert len(drain_updates) == 0


# ---------------------------------------------------------------------------
# AC2: WAR_ENDED_EXHAUSTION event when faction crosses peace threshold
# ---------------------------------------------------------------------------

def test_war_ended_exhaustion_event_emitted_at_threshold():
    """WAR_ENDED_EXHAUSTION is emitted when drain pushes a faction below 0.3."""
    from src.core.enums import DiplomaticState as DS
    from src.engine.military_conflict import MilitaryConflictPhase
    from src.domains.world_emergence.schema import WorldEventCategory

    # 0.300 - 0.001 = 0.299 < 0.3
    factions = {
        "fa": _make_faction("fa", military_strength=0.300, relations={"fb": DS.WAR}),
        "fb": _make_faction("fb", military_strength=0.300, relations={"fa": DS.WAR}),
    }
    state = _FakeState(factions=factions, regions={}, tick=100)
    result = MilitaryConflictPhase.execute(state)

    exhaustion_events = [e for e in result.world_events_add
                         if e.category == WorldEventCategory.WAR_ENDED_EXHAUSTION]
    assert len(exhaustion_events) == 1
    ev = exhaustion_events[0]
    assert "fa" in ev.subject
    assert "fb" in ev.subject
    assert ev.tick == 100


def test_war_ended_exhaustion_not_emitted_above_threshold():
    """WAR_ENDED_EXHAUSTION is NOT emitted when drain keeps ms above 0.3."""
    from src.core.enums import DiplomaticState as DS
    from src.engine.military_conflict import MilitaryConflictPhase
    from src.domains.world_emergence.schema import WorldEventCategory

    factions = {
        "fa": _make_faction("fa", military_strength=0.5, relations={"fb": DS.WAR}),
        "fb": _make_faction("fb", military_strength=0.5, relations={"fa": DS.WAR}),
    }
    state = _FakeState(factions=factions, regions={}, tick=1)
    result = MilitaryConflictPhase.execute(state)

    exhaustion_events = [e for e in result.world_events_add
                         if e.category == WorldEventCategory.WAR_ENDED_EXHAUSTION]
    assert len(exhaustion_events) == 0


def test_war_ended_exhaustion_fires_once_at_crossing():
    """WAR_ENDED_EXHAUSTION fires at the crossing tick, not on every tick below threshold."""
    from src.core.enums import DiplomaticState as DS
    from src.engine.military_conflict import MilitaryConflictPhase
    from src.domains.world_emergence.schema import WorldEventCategory

    # Already below threshold: ms=0.15, drain to 0.149 — both already below so no CROSSING event
    factions = {
        "fa": _make_faction("fa", military_strength=0.15, relations={"fb": DS.WAR}),
        "fb": _make_faction("fb", military_strength=0.15, relations={"fa": DS.WAR}),
    }
    state = _FakeState(factions=factions, regions={}, tick=200)
    result = MilitaryConflictPhase.execute(state)

    exhaustion_events = [e for e in result.world_events_add
                         if e.category == WorldEventCategory.WAR_ENDED_EXHAUSTION]
    # Should NOT emit: both were already below threshold before this tick
    assert len(exhaustion_events) == 0


# ---------------------------------------------------------------------------
# AC3: Orphaned siege cleanup when factions are no longer at WAR
# ---------------------------------------------------------------------------

def test_orphan_siege_cleared_when_peace():
    """execute() clears siege_state on regions where the WAR pair returned to NEUTRAL."""
    from src.core.enums import DiplomaticState as DS
    from src.engine.military_conflict import MilitaryConflictPhase

    ss = _make_siege(attacker="fa", defender="fb", progress=0.5)
    factions = {
        "fa": _make_faction("fa", relations={"fb": DS.NEUTRAL}),  # peace declared
        "fb": _make_faction("fb", relations={"fa": DS.NEUTRAL}),
    }
    regions = {"r1": _make_region("r1", siege_state=ss)}
    state = _FakeState(factions=factions, regions=regions, tick=50)

    result = MilitaryConflictPhase.execute(state)

    wu = result.world_updates.get("r1")
    assert wu is not None
    assert wu.siege_state_clear is True
    assert wu.service_availability_delta == 1.0  # restore


def test_orphan_siege_not_cleared_during_active_war():
    """execute() does NOT clear siege when factions are still at WAR."""
    from src.core.enums import DiplomaticState as DS
    from src.engine.military_conflict import MilitaryConflictPhase

    ss = _make_siege(attacker="fa", defender="fb", progress=0.5)
    factions = {
        "fa": _make_faction("fa", relations={"fb": DS.WAR}),
        "fb": _make_faction("fb", territory=["r1"], relations={"fa": DS.WAR}),
    }
    regions = {"r1": _make_region("r1", siege_state=ss)}
    state = _FakeState(factions=factions, regions=regions, tick=10)

    result = MilitaryConflictPhase.execute(state)

    wu = result.world_updates.get("r1")
    # If wu exists, siege_state_clear must be False (continuation, not cleanup)
    assert wu is None or not wu.siege_state_clear


# ---------------------------------------------------------------------------
# AC4: WAR_ENDED_EXHAUSTION in significance map
# ---------------------------------------------------------------------------

def test_war_ended_exhaustion_category_exists():
    """WorldEventCategory.WAR_ENDED_EXHAUSTION exists with correct value."""
    from src.domains.world_emergence.schema import WorldEventCategory
    assert WorldEventCategory.WAR_ENDED_EXHAUSTION == "WAR_ENDED_EXHAUSTION"


def test_war_ended_exhaustion_significance():
    """WAR_ENDED_EXHAUSTION is in the orchestrator significance map at 0.80."""
    from src.domains.campaigns.orchestrator import _SIGNIFICANCE_MAP
    assert "WAR_ENDED_EXHAUSTION" in _SIGNIFICANCE_MAP
    event_type, sig = _SIGNIFICANCE_MAP["WAR_ENDED_EXHAUSTION"]
    assert event_type == "war_ended_exhaustion"
    assert sig == 0.80
