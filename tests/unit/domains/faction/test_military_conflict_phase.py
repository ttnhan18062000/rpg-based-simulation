"""Unit tests for MilitaryConflictPhase (E53Ca)."""
from dataclasses import dataclass, field
from typing import Dict


def _make_faction(fid: str, relations: dict = None):
    from src.core.state import FactionState
    from src.core.enums import DiplomaticState
    return FactionState(
        faction_id=fid,
        diplomatic_relations={k: DiplomaticState(v) if isinstance(v, str) else v
                               for k, v in (relations or {}).items()},
    )


def _make_state(factions: dict):
    """Build a minimal AuthoritativeState-like object with factions, regions, entities, tick."""
    class FakeState:
        def __init__(self, factions, tick=1):
            self.factions = factions
            self.regions = {}
            self.entities = {}
            self.tick = tick
    return FakeState(factions)


def test_military_conflict_phase_noop_empty_factions():
    """Empty factions → execute returns StateUpdate without raising."""
    from src.engine.military_conflict import MilitaryConflictPhase
    from src.core.updates import StateUpdate

    state = _make_state({})
    result = MilitaryConflictPhase.execute(state)
    assert isinstance(result, StateUpdate)


def test_military_conflict_phase_noop_on_peace():
    """No WAR pairs → execute returns empty StateUpdate."""
    from src.core.enums import DiplomaticState as DS
    from src.engine.military_conflict import MilitaryConflictPhase
    from src.core.updates import StateUpdate

    factions = {
        "fa": _make_faction("fa", relations={"fb": DS.NEUTRAL}),
        "fb": _make_faction("fb", relations={"fa": DS.NEUTRAL}),
    }
    state = _make_state(factions)
    result = MilitaryConflictPhase.execute(state)
    assert isinstance(result, StateUpdate)
    assert result.is_noop()


def test_military_conflict_phase_detects_war_pairs():
    """Two factions in WAR → execute returns StateUpdate without raising."""
    from src.core.enums import DiplomaticState as DS
    from src.engine.military_conflict import MilitaryConflictPhase
    from src.core.updates import StateUpdate

    factions = {
        "fa": _make_faction("fa", relations={"fb": DS.WAR}),
        "fb": _make_faction("fb", relations={"fa": DS.WAR}),
    }
    state = _make_state(factions)
    result = MilitaryConflictPhase.execute(state)
    assert isinstance(result, StateUpdate)


def test_military_conflict_phase_get_war_pairs_dedup():
    """get_war_pairs returns one pair per WAR dyad in lexicographic order."""
    from src.core.enums import DiplomaticState as DS
    from src.engine.military_conflict import MilitaryConflictPhase

    factions = {
        "gamma": _make_faction("gamma", relations={"alpha": DS.WAR}),
        "alpha": _make_faction("alpha", relations={"gamma": DS.WAR}),
    }
    state = _make_state(factions)
    pairs = MilitaryConflictPhase.get_war_pairs(state)
    assert pairs == [("alpha", "gamma")]


def test_military_conflict_phase_ignores_non_war_pairs():
    """HOSTILE and TENSE pairs are not treated as WAR."""
    from src.core.enums import DiplomaticState as DS
    from src.engine.military_conflict import MilitaryConflictPhase

    factions = {
        "fa": _make_faction("fa", relations={"fb": DS.HOSTILE, "fc": DS.TENSE}),
        "fb": _make_faction("fb", relations={"fa": DS.HOSTILE}),
        "fc": _make_faction("fc", relations={"fa": DS.TENSE}),
    }
    state = _make_state(factions)
    pairs = MilitaryConflictPhase.get_war_pairs(state)
    assert pairs == []


def test_military_conflict_phase_returns_state_update_not_list():
    """Anti-drift guard: execute() returns StateUpdate, not a list."""
    from src.engine.military_conflict import MilitaryConflictPhase
    from src.core.updates import StateUpdate

    state = _make_state({})
    result = MilitaryConflictPhase.execute(state)
    assert isinstance(result, StateUpdate)
    assert not isinstance(result, list)
