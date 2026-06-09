import pytest

from src.scenarios.resolver import StateSetupModifier
from src.scenarios.modifier_applicator import (
    ModifierApplicator,
    ScenarioSetupContext,
    UnsupportedModifierError,
)


APPLICATOR = ModifierApplicator()


def _mod(modifier_type: str, value) -> StateSetupModifier:
    return StateSetupModifier(modifier_type=modifier_type, parameters={"value": value})


# ---------------------------------------------------------------------------
# Region pressure
# ---------------------------------------------------------------------------

def test_region_pressure_sets_global_override():
    ctx = APPLICATOR.apply([_mod("region_pressure", 0.8)])
    assert ctx.region_pressure_overrides == {"global": 0.8}


# ---------------------------------------------------------------------------
# Faction activity
# ---------------------------------------------------------------------------

def test_faction_activity_sets_all_alertness_level():
    ctx = APPLICATOR.apply([_mod("faction_activity", "high")])
    assert ctx.faction_alertness_levels == {"all": "high"}


def test_faction_activity_numeric_value_stored_as_string():
    ctx = APPLICATOR.apply([_mod("faction_activity", 2)])
    assert ctx.faction_alertness_levels["all"] == "2"


# ---------------------------------------------------------------------------
# Resource scarcity
# ---------------------------------------------------------------------------

def test_resource_scarcity_sets_all_factor():
    ctx = APPLICATOR.apply([_mod("resource_scarcity", 0.3)])
    assert ctx.resource_scarcity_factors == {"all": 0.3}


# ---------------------------------------------------------------------------
# Population alertness
# ---------------------------------------------------------------------------

def test_population_alertness_sets_all_readiness_hint():
    ctx = APPLICATOR.apply([_mod("population_alertness", 75.0)])
    assert ctx.population_readiness_hints == {"all": 75.0}


# ---------------------------------------------------------------------------
# Territorial intrusion
# ---------------------------------------------------------------------------

def test_territorial_intrusion_adds_claim():
    ctx = APPLICATOR.apply([_mod("territorial_intrusion", "monster_horde")])
    assert len(ctx.territorial_intrusion_claims) == 1
    assert ctx.territorial_intrusion_claims[0]["claim"] == "monster_horde"


def test_multiple_territorial_intrusion_modifiers_accumulate():
    ctx = APPLICATOR.apply([
        _mod("territorial_intrusion", "monster_horde"),
        _mod("territorial_intrusion", "goblin_warband"),
    ])
    assert len(ctx.territorial_intrusion_claims) == 2


# ---------------------------------------------------------------------------
# Trade route risk
# ---------------------------------------------------------------------------

def test_trade_route_risk_sets_level():
    ctx = APPLICATOR.apply([_mod("trade_route_risk", 0.6)])
    assert ctx.trade_route_risk_level == pytest.approx(0.6)


# ---------------------------------------------------------------------------
# Danger level override
# ---------------------------------------------------------------------------

def test_danger_level_override_sets_value():
    ctx = APPLICATOR.apply([_mod("danger_level_override", 0.9)])
    assert ctx.danger_level_override == pytest.approx(0.9)


# ---------------------------------------------------------------------------
# Spawn bias
# ---------------------------------------------------------------------------

def test_spawn_bias_stores_config():
    ctx = APPLICATOR.apply([_mod("spawn_bias", {"role": "monster", "factor": 2})])
    assert ctx.spawn_bias_config == {"role": "monster", "factor": 2}


# ---------------------------------------------------------------------------
# Empty list
# ---------------------------------------------------------------------------

def test_empty_modifier_list_produces_empty_context():
    ctx = APPLICATOR.apply([])
    assert ctx.region_pressure_overrides == {}
    assert ctx.faction_alertness_levels == {}
    assert ctx.resource_scarcity_factors == {}
    assert ctx.population_readiness_hints == {}
    assert ctx.territorial_intrusion_claims == []
    assert ctx.trade_route_risk_level is None
    assert ctx.danger_level_override is None
    assert ctx.spawn_bias_config is None


# ---------------------------------------------------------------------------
# Unsupported modifier type
# ---------------------------------------------------------------------------

def test_unsupported_modifier_type_raises_error():
    with pytest.raises(UnsupportedModifierError, match="unknown_modifier"):
        APPLICATOR.apply([_mod("unknown_modifier", 1.0)])


def test_unsupported_modifier_fails_not_silently_skips():
    # Must raise, not return partial context
    with pytest.raises(UnsupportedModifierError):
        APPLICATOR.apply([
            _mod("region_pressure", 0.5),
            _mod("not_a_real_type", "x"),
        ])


# ---------------------------------------------------------------------------
# Determinism
# ---------------------------------------------------------------------------

def test_same_modifiers_same_context():
    mods = [
        _mod("region_pressure", 0.7),
        _mod("faction_activity", "medium"),
        _mod("spawn_bias", 3),
    ]
    ctx_a = APPLICATOR.apply(mods)
    ctx_b = APPLICATOR.apply(mods)
    assert ctx_a == ctx_b


def test_context_is_frozen():
    ctx = APPLICATOR.apply([_mod("region_pressure", 0.5)])
    with pytest.raises(Exception):
        ctx.danger_level_override = 1.0  # type: ignore[misc]


# ---------------------------------------------------------------------------
# No tick required: applicator is self-contained
# ---------------------------------------------------------------------------

def test_applicator_does_not_require_catalog_or_repo():
    """Applicator needs no catalog or module repo — pure data transformation."""
    import inspect
    import ast
    import src.scenarios.modifier_applicator as mod

    source = inspect.getsource(mod)
    tree = ast.parse(source)
    for node in ast.walk(tree):
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            module = getattr(node, "module", "") or ""
            for alias in getattr(node, "names", []):
                name = alias.name or ""
                full = f"{module}.{name}".strip(".")
                assert "CatalogRepository" not in full
                assert "WorldModuleRepository" not in full
                assert "tick" not in full.lower()
