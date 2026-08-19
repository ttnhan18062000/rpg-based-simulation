"""Unit tests for FactionDecisionPhase and FactionDirective (TCK-20260619-E53Ab-DECISION-PHASE).

8 tests:
  1. test_faction_decision_phase_produces_defend_border
  2. test_faction_decision_phase_no_factions_returns_empty
  3. test_faction_directive_frozen
  4. test_faction_decision_phase_trade_route
  5. test_faction_decision_phase_commission_quest
  6. test_faction_directive_directive_kind_is_string
  7. test_faction_decision_phase_high_tension_emits_defend_and_commission
  8. test_faction_decision_phase_cadence_field_exists

Anti-drift guards woven into the above (no pipeline imports in this file):
  - FactionDirective is NOT in StateUpdate
  - execute() returns list, not StateUpdate
  - FactionDirective uses __slots__
"""
import pytest


# ---------------------------------------------------------------------------
# 1. DEFEND_BORDER emitted for high-tension faction with territory
# ---------------------------------------------------------------------------
def test_faction_decision_phase_produces_defend_border():
    from src.engine.faction_decision import FactionDecisionPhase
    from src.core.state import FactionState, AuthoritativeState

    fs = FactionState(faction_id="faction_a", tension_level=0.7, territory=("region_01",), military_strength=1.0)
    state = AuthoritativeState(tick=0, seed=0, factions={"faction_a": fs})

    directives = FactionDecisionPhase.execute(state, policy=None)

    kinds = {d.directive_kind for d in directives if d.faction_id == "faction_a"}
    assert "DEFEND_BORDER" in kinds


# ---------------------------------------------------------------------------
# 2. Empty factions dict → empty list, no exception
# ---------------------------------------------------------------------------
def test_faction_decision_phase_no_factions_returns_empty():
    from src.engine.faction_decision import FactionDecisionPhase
    from src.core.state import AuthoritativeState

    state = AuthoritativeState(tick=0, seed=0)
    assert state.factions == {}

    result = FactionDecisionPhase.execute(state, policy=None)
    assert result == []


# ---------------------------------------------------------------------------
# 3. FactionDirective is frozen — attribute assignment raises FrozenInstanceError
# ---------------------------------------------------------------------------
def test_faction_directive_frozen():
    from dataclasses import FrozenInstanceError
    from src.engine.faction_decision import FactionDirective

    d = FactionDirective(faction_id="faction_a", directive_kind="DEFEND_BORDER", created_tick=5)
    with pytest.raises(FrozenInstanceError):
        d.faction_id = "other"  # type: ignore[misc]


# ---------------------------------------------------------------------------
# 4. TRADE_ROUTE emitted for high-military, low-tension faction
# ---------------------------------------------------------------------------
def test_faction_decision_phase_trade_route():
    from src.engine.faction_decision import FactionDecisionPhase
    from src.core.state import FactionState, AuthoritativeState

    fs = FactionState(faction_id="faction_b", military_strength=0.8, tension_level=0.2, territory=())
    state = AuthoritativeState(tick=10, seed=0, factions={"faction_b": fs})

    directives = FactionDecisionPhase.execute(state, policy=None)

    kinds = {d.directive_kind for d in directives if d.faction_id == "faction_b"}
    assert "TRADE_ROUTE" in kinds
    assert "DEFEND_BORDER" not in kinds


# ---------------------------------------------------------------------------
# 5. COMMISSION_QUEST emitted with priority == tension_level (no DEFEND_BORDER)
# ---------------------------------------------------------------------------
def test_faction_decision_phase_commission_quest():
    from src.engine.faction_decision import FactionDecisionPhase
    from src.core.state import FactionState, AuthoritativeState

    # tension_level=0.4 is below the DEFEND_BORDER threshold (> 0.5), isolating COMMISSION_QUEST
    fs = FactionState(faction_id="faction_c", territory=("region_02",), tension_level=0.4, military_strength=0.5)
    state = AuthoritativeState(tick=5, seed=0, factions={"faction_c": fs})

    directives = FactionDecisionPhase.execute(state, policy=None)

    quest_directives = [d for d in directives if d.faction_id == "faction_c" and d.directive_kind == "COMMISSION_QUEST"]
    assert len(quest_directives) >= 1
    assert quest_directives[0].priority == pytest.approx(0.4)
    defend_directives = [d for d in directives if d.faction_id == "faction_c" and d.directive_kind == "DEFEND_BORDER"]
    assert defend_directives == []


# ---------------------------------------------------------------------------
# 6. directive_kind is a plain str, not IntEnum
# ---------------------------------------------------------------------------
def test_faction_directive_directive_kind_is_string():
    from src.engine.faction_decision import FactionDirective, DEFEND_BORDER

    d = FactionDirective(faction_id="faction_a", directive_kind=DEFEND_BORDER)
    assert isinstance(d.directive_kind, str)
    assert type(d.directive_kind) is str  # not a subclass (IntEnum, StrEnum, etc.)


# ---------------------------------------------------------------------------
# 7. High-tension faction with territory → both DEFEND_BORDER and COMMISSION_QUEST
# ---------------------------------------------------------------------------
def test_faction_decision_phase_high_tension_emits_defend_and_commission():
    from src.engine.faction_decision import FactionDecisionPhase
    from src.core.state import FactionState, AuthoritativeState

    fs = FactionState(faction_id="faction_d", tension_level=0.7, territory=("region_03",), military_strength=1.0)
    state = AuthoritativeState(tick=0, seed=0, factions={"faction_d": fs})

    directives = FactionDecisionPhase.execute(state, policy=None)

    kinds = {d.directive_kind for d in directives if d.faction_id == "faction_d"}
    assert "DEFEND_BORDER" in kinds
    assert "COMMISSION_QUEST" in kinds


# ---------------------------------------------------------------------------
# 8. SystemCadence has faction_decision field defaulting to 10
# ---------------------------------------------------------------------------
def test_faction_decision_phase_cadence_field_exists():
    from src.engine.cadence import SystemCadence

    assert SystemCadence().faction_decision == 10


# ---------------------------------------------------------------------------
# Anti-drift guard A: FactionDirective NOT in StateUpdate
# ---------------------------------------------------------------------------
def test_faction_directive_not_in_state_update():
    from src.core.updates import StateUpdate

    assert not hasattr(StateUpdate, "faction_directives"), (
        "FactionDirective must never be added to StateUpdate — directives are transient"
    )


# ---------------------------------------------------------------------------
# Anti-drift guard B: execute() returns list, not StateUpdate
# ---------------------------------------------------------------------------
def test_faction_decision_phase_returns_list_not_state_update():
    from src.engine.faction_decision import FactionDecisionPhase
    from src.core.state import AuthoritativeState
    from src.core.updates import StateUpdate

    state = AuthoritativeState(tick=0, seed=0)
    result = FactionDecisionPhase.execute(state, policy=None)
    assert isinstance(result, list), "FactionDecisionPhase.execute() must return list[FactionDirective], not StateUpdate"
    assert not isinstance(result, StateUpdate)


# ---------------------------------------------------------------------------
# Anti-drift guard C: FactionDirective uses __slots__
# ---------------------------------------------------------------------------
def test_faction_directive_has_slots():
    from src.engine.faction_decision import FactionDirective

    assert hasattr(FactionDirective, "__slots__"), "FactionDirective must use slots=True for memory efficiency"
