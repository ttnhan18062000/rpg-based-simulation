# Tests for ModuleParameterEvaluator and AssemblyParameterError (WORLD-MOD-003)
import pytest

from src.worldmodules.evaluator import AssemblyParameterError, ModuleParameterEvaluator
from src.worldmodules.schema import ModuleParameterSpec


def _spec(name: str, type_: str = "integer", **kwargs) -> ModuleParameterSpec:
    return ModuleParameterSpec(name=name, type=type_, **kwargs)


# ---------------------------------------------------------------------------
# Group A — evaluate_field() arithmetic
# ---------------------------------------------------------------------------

def test_evaluate_field_integer_passthrough():
    assert ModuleParameterEvaluator.evaluate_field(9, {}) == 9


def test_evaluate_field_simple_substitution():
    assert ModuleParameterEvaluator.evaluate_field("{scale} * 3", {"scale": 3}) == 9


def test_evaluate_field_complex_expression():
    result = ModuleParameterEvaluator.evaluate_field("{base} + {scale} * 2", {"base": 1, "scale": 3})
    assert result == 7


def test_evaluate_field_division_truncates():
    result = ModuleParameterEvaluator.evaluate_field("{total} / {parts}", {"total": 7, "parts": 2})
    assert result == 3


def test_evaluate_field_float_param_in_arithmetic():
    result = ModuleParameterEvaluator.evaluate_field("{rate} * 4", {"rate": 2.5})
    assert result == 10


def test_evaluate_field_unary_minus():
    result = ModuleParameterEvaluator.evaluate_field("-{offset} + 5", {"offset": 2})
    assert result == 3


def test_evaluate_field_valid_parentheses():
    result = ModuleParameterEvaluator.evaluate_field("({scale} + 1) * 2", {"scale": 4})
    assert result == 10


# ---------------------------------------------------------------------------
# Group B — constraint validation raises AssemblyParameterError
# ---------------------------------------------------------------------------

def test_evaluate_raises_on_max_value_exceeded():
    specs = [_spec("scale", min_value=1, max_value=5)]
    ev = ModuleParameterEvaluator(specs, {"scale": 10}, module_id="mod_x")
    with pytest.raises(AssemblyParameterError) as exc_info:
        ev.evaluate()
    msg = str(exc_info.value)
    assert "mod_x" in msg
    assert "scale" in msg


def test_evaluate_raises_on_min_value_exceeded():
    specs = [_spec("scale", min_value=1, max_value=10)]
    ev = ModuleParameterEvaluator(specs, {"scale": 0}, module_id="mod_x")
    with pytest.raises(AssemblyParameterError) as exc_info:
        ev.evaluate()
    assert "scale" in str(exc_info.value)


def test_evaluate_raises_on_allowed_values_violation():
    specs = [_spec("tier", type_="enum", allowed_values=["low", "med", "high"])]
    ev = ModuleParameterEvaluator(specs, {"tier": "ultra"}, module_id="mod_y")
    with pytest.raises(AssemblyParameterError) as exc_info:
        ev.evaluate()
    assert "tier" in str(exc_info.value)


# ---------------------------------------------------------------------------
# Group C — required param enforcement
# ---------------------------------------------------------------------------

def test_evaluate_raises_required_param_missing():
    specs = [_spec("density", required=True)]
    ev = ModuleParameterEvaluator(specs, {}, module_id="mod_z")
    with pytest.raises(AssemblyParameterError) as exc_info:
        ev.evaluate()
    assert "density" in str(exc_info.value)


def test_evaluate_required_param_satisfied_by_default():
    specs = [_spec("scale", required=True, default=2)]
    ev = ModuleParameterEvaluator(specs, {}, module_id="mod_a")
    result = ev.evaluate()
    assert result["scale"] == 2


def test_evaluate_required_param_satisfied_by_injected():
    specs = [_spec("scale", required=True)]
    ev = ModuleParameterEvaluator(specs, {"scale": 4}, module_id="mod_b")
    result = ev.evaluate()
    assert result["scale"] == 4


# ---------------------------------------------------------------------------
# Group D — zero-param fast paths
# ---------------------------------------------------------------------------

def test_evaluate_no_params_returns_empty():
    ev = ModuleParameterEvaluator([], {}, module_id="mod_empty")
    assert ev.evaluate() == {}


def test_evaluate_field_int_no_params_fast_path():
    result = ModuleParameterEvaluator.evaluate_field(5, {})
    assert result == 5


# ---------------------------------------------------------------------------
# Group E — security / AST safety
# ---------------------------------------------------------------------------

def test_evaluate_field_rejects_function_call():
    with pytest.raises((ValueError, KeyError)):
        ModuleParameterEvaluator.evaluate_field("len('x')", {})


def test_evaluate_field_rejects_name_lookup():
    with pytest.raises((ValueError, KeyError)):
        ModuleParameterEvaluator.evaluate_field("os.getenv('SECRET')", {})


def test_evaluate_field_rejects_import():
    with pytest.raises(ValueError):
        ModuleParameterEvaluator.evaluate_field("__import__('os')", {})


def test_evaluate_field_rejects_attribute_access():
    with pytest.raises((ValueError, KeyError)):
        ModuleParameterEvaluator.evaluate_field("{a}.bit_length()", {"a": 1})


def test_evaluate_field_unresolved_key_raises():
    with pytest.raises((AssemblyParameterError, KeyError, ValueError)):
        ModuleParameterEvaluator.evaluate_field("{unknown_key} * 2", {})


# ---------------------------------------------------------------------------
# Group F — end-to-end AC scenarios
# ---------------------------------------------------------------------------

def test_evaluate_full_ac1_scenario():
    specs = [_spec("scale", min_value=1, max_value=5, default=1)]
    ev = ModuleParameterEvaluator(specs, {"scale": 3}, module_id="mod_ac1")
    resolved = ev.evaluate()
    result = ModuleParameterEvaluator.evaluate_field("{scale} * 3", resolved)
    assert result == 9


def test_evaluate_full_ac2_scenario():
    specs = [_spec("scale", min_value=1, max_value=5, default=1)]
    ev = ModuleParameterEvaluator(specs, {"scale": 10}, module_id="mod_ac2")
    with pytest.raises(AssemblyParameterError):
        ev.evaluate()


# ---------------------------------------------------------------------------
# Group G — scalable_bandit_camp acceptance criteria (TCK-20260614-WORLDDAT-NEWMODS)
# ---------------------------------------------------------------------------

def test_scalable_bandit_camp_danger_scale_4_produces_count_12():
    """AC: scalable_bandit_camp with danger_scale=4 → population count expression evaluates to 12."""
    specs = [_spec("danger_scale", min_value=1, max_value=5, default=2)]
    ev = ModuleParameterEvaluator(specs, {"danger_scale": 4}, module_id="scalable_bandit_camp")
    resolved = ev.evaluate()
    result = ModuleParameterEvaluator.evaluate_field("{danger_scale} * 3", resolved)
    assert result == 12


def test_scalable_bandit_camp_danger_scale_6_raises_parameter_error():
    """AC: scalable_bandit_camp with danger_scale=6 exceeds max_value=5 → AssemblyParameterError."""
    specs = [_spec("danger_scale", min_value=1, max_value=5, default=2)]
    ev = ModuleParameterEvaluator(specs, {"danger_scale": 6}, module_id="scalable_bandit_camp")
    with pytest.raises(AssemblyParameterError) as exc_info:
        ev.evaluate()
    assert "danger_scale" in str(exc_info.value)
    assert "scalable_bandit_camp" in str(exc_info.value)
