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


# ---------------------------------------------------------------------------
# EXPAND_TERRITORY (TCK-20260904-FACTION-EXPAND-DIRECTIVE, ideas 51+52)
# ---------------------------------------------------------------------------

def _pressured_region(region_id: str, owner_faction_id=None) -> "RegionState":
    """A region with zero resource nodes -> compute_regional_scarcity() == 1.0 (max scarcity)."""
    from src.core.state import RegionState

    return RegionState(id=region_id, name=region_id, bounds=(0, 0, 10, 10), owner_faction_id=owner_faction_id)


def test_faction_decision_phase_expand_territory_emitted_under_population_pressure():
    from src.engine.faction_decision import FactionDecisionPhase
    from src.core.state import FactionState, AuthoritativeState, RegionState

    fs = FactionState(faction_id="faction_e", tension_level=0.1, military_strength=0.1, territory=("region_home",))
    home = _pressured_region("region_home", owner_faction_id=1)
    free = RegionState(id="region_free", name="region_free", bounds=(20, 20, 30, 30), owner_faction_id=None)
    state = AuthoritativeState(tick=0, seed=0, factions={"faction_e": fs}, regions={"region_home": home, "region_free": free})

    directives = FactionDecisionPhase.execute(state, policy=None)

    expand = [d for d in directives if d.faction_id == "faction_e" and d.directive_kind == "EXPAND_TERRITORY"]
    assert len(expand) == 1
    assert expand[0].target_region == "region_free"


def test_faction_decision_phase_expand_territory_not_emitted_without_pressure():
    from src.engine.faction_decision import FactionDecisionPhase
    from src.core.state import FactionState, AuthoritativeState, RegionState, ResourceNodeState

    fs = FactionState(faction_id="faction_f", tension_level=0.1, military_strength=0.1, territory=("region_home",))
    home = RegionState(id="region_home", name="region_home", bounds=(0, 0, 10, 10), owner_faction_id=1)
    free = RegionState(id="region_free", name="region_free", bounds=(20, 20, 30, 30), owner_faction_id=None)
    # A fully-stocked resource node inside region_home's bounds -> scarcity == 0.0, well below the 0.7 gate.
    node = ResourceNodeState(
        id=1, kind="ORE", position=(5.0, 5.0), yields_item="iron_ore",
        remaining_charges=100, max_charges=100, required_ticks=10,
    )
    state = AuthoritativeState(
        tick=0, seed=0, factions={"faction_f": fs},
        regions={"region_home": home, "region_free": free},
        resource_nodes={1: node},
    )

    directives = FactionDecisionPhase.execute(state, policy=None)

    kinds = {d.directive_kind for d in directives if d.faction_id == "faction_f"}
    assert "EXPAND_TERRITORY" not in kinds


def test_faction_decision_phase_expand_territory_not_emitted_without_target():
    from src.engine.faction_decision import FactionDecisionPhase
    from src.core.state import FactionState, AuthoritativeState

    fs = FactionState(faction_id="faction_g", tension_level=0.1, military_strength=0.1, territory=("region_home",))
    home = _pressured_region("region_home", owner_faction_id=1)
    # No other regions exist -> no faction-less target available.
    state = AuthoritativeState(tick=0, seed=0, factions={"faction_g": fs}, regions={"region_home": home})

    directives = FactionDecisionPhase.execute(state, policy=None)

    kinds = {d.directive_kind for d in directives if d.faction_id == "faction_g"}
    assert "EXPAND_TERRITORY" not in kinds


def test_faction_decision_phase_expand_territory_target_resolution_deterministic():
    from src.engine.faction_decision import FactionDecisionPhase
    from src.core.state import FactionState, AuthoritativeState, RegionState

    fs = FactionState(faction_id="faction_h", tension_level=0.1, military_strength=0.1, territory=("region_home",))
    home = _pressured_region("region_home", owner_faction_id=1)
    # Two faction-less regions; ids chosen so unsorted dict-iteration order would be observable.
    region_zeta = RegionState(id="region_zeta", name="region_zeta", bounds=(20, 20, 30, 30), owner_faction_id=None)
    region_alpha = RegionState(id="region_alpha", name="region_alpha", bounds=(40, 40, 50, 50), owner_faction_id=None)
    state = AuthoritativeState(
        tick=0, seed=0, factions={"faction_h": fs},
        regions={"region_zeta": region_zeta, "region_home": home, "region_alpha": region_alpha},
    )

    first = FactionDecisionPhase.execute(state, policy=None)
    second = FactionDecisionPhase.execute(state, policy=None)

    expand_first = [d for d in first if d.faction_id == "faction_h" and d.directive_kind == "EXPAND_TERRITORY"]
    expand_second = [d for d in second if d.faction_id == "faction_h" and d.directive_kind == "EXPAND_TERRITORY"]
    assert len(expand_first) == 1 and len(expand_second) == 1
    assert expand_first[0].target_region == "region_alpha"  # lowest sorted id
    assert expand_first[0].target_region == expand_second[0].target_region


def test_faction_decision_phase_expand_territory_transient_not_persisted():
    from src.engine.faction_decision import FactionDecisionPhase
    from src.core.state import FactionState, AuthoritativeState, RegionState
    from src.core.updates import StateUpdate

    assert not hasattr(StateUpdate, "faction_directives")
    field_names = getattr(StateUpdate, "__dataclass_fields__", {}).keys()
    assert not any("expand" in f.lower() or "territory" in f.lower() for f in field_names)

    fs = FactionState(faction_id="faction_i", tension_level=0.1, military_strength=0.1, territory=("region_home",))
    home = _pressured_region("region_home", owner_faction_id=1)
    free = RegionState(id="region_free", name="region_free", bounds=(20, 20, 30, 30), owner_faction_id=None)
    state = AuthoritativeState(tick=0, seed=0, factions={"faction_i": fs}, regions={"region_home": home, "region_free": free})

    result = FactionDecisionPhase.execute(state, policy=None)
    assert isinstance(result, list)
    assert not isinstance(result, StateUpdate)
    assert any(d.directive_kind == "EXPAND_TERRITORY" for d in result)


def test_faction_constants_expand_territory_value():
    from src.engine.faction_constants import EXPAND_TERRITORY as const_expand
    from src.engine.faction_decision import EXPAND_TERRITORY as decision_expand

    assert const_expand == "EXPAND_TERRITORY"
    assert decision_expand == "EXPAND_TERRITORY"


# ---------------------------------------------------------------------------
# Anti-drift guard D: EXPAND_TERRITORY does not suppress or duplicate DEFEND_BORDER
# ---------------------------------------------------------------------------
def test_faction_decision_phase_expand_territory_coexists_with_defend_border():
    from src.engine.faction_decision import FactionDecisionPhase
    from src.core.state import FactionState, AuthoritativeState, RegionState

    fs = FactionState(faction_id="faction_j", tension_level=0.7, military_strength=1.0, territory=("region_home",))
    home = _pressured_region("region_home", owner_faction_id=1)
    free = RegionState(id="region_free", name="region_free", bounds=(20, 20, 30, 30), owner_faction_id=None)
    state = AuthoritativeState(tick=0, seed=0, factions={"faction_j": fs}, regions={"region_home": home, "region_free": free})

    directives = FactionDecisionPhase.execute(state, policy=None)

    kinds = {d.directive_kind for d in directives if d.faction_id == "faction_j"}
    assert "DEFEND_BORDER" in kinds
    assert "EXPAND_TERRITORY" in kinds
    assert "COMMISSION_QUEST" in kinds


# ---------------------------------------------------------------------------
# Anti-drift guard E: no Camp/Nest or City-ownership-aware logic in target resolution
# ---------------------------------------------------------------------------
def test_faction_decision_phase_expand_territory_target_resolution_ignores_camps_and_places():
    import inspect
    from src.engine.faction_decision import FactionDecisionPhase

    sig = inspect.signature(FactionDecisionPhase._resolve_expand_territory_target)
    params = set(sig.parameters.keys())
    assert params == {"state", "fs"}, (
        "_resolve_expand_territory_target must only read state.regions/fs.territory "
        "(RegionState.owner_faction_id) -- no camps/places/city-ownership parameter"
    )


# ---------------------------------------------------------------------------
# Anti-drift guard F: recipe_materials() is never a hard gate for EXPAND_TERRITORY
# ---------------------------------------------------------------------------
def test_faction_decision_phase_expand_territory_not_gated_on_recipe_materials():
    from src.domains.progression.material_predicate import recipe_materials
    from src.engine.faction_decision import FactionDecisionPhase
    from src.core.state import FactionState, AuthoritativeState, RegionState

    # Confirmed real-world case: known_recipes are craft_*-prefixed and share no ids with
    # recipes.py's 3-entry catalog, so recipe_materials() returns () for any real crafted recipe.
    assert recipe_materials("craft_steel_sword") == ()

    fs = FactionState(faction_id="faction_k", tension_level=0.1, military_strength=0.1, territory=("region_home",))
    home = _pressured_region("region_home", owner_faction_id=1)
    free = RegionState(id="region_free", name="region_free", bounds=(20, 20, 30, 30), owner_faction_id=None)
    state = AuthoritativeState(tick=0, seed=0, factions={"faction_k": fs}, regions={"region_home": home, "region_free": free})

    directives = FactionDecisionPhase.execute(state, policy=None)

    assert any(d.directive_kind == "EXPAND_TERRITORY" for d in directives if d.faction_id == "faction_k")
