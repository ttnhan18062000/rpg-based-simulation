# Compliance IDs: WORLD-GEN-006-TEST
"""
Unit tests for seed-based parameter sampling in ProceduralCompositionGenerator.

TCK-20260614-WORLDGEN-SEED-PARAMS acceptance criteria:
  - Same seed → identical ModuleRefSpec.parameters
  - Different seeds → different values for bounded params
  - Integer bounds respected (inclusive)
  - Float bounds respected
  - No-bounds params use declared default unchanged
  - allowed_values sampling always picks from declared values
"""
from __future__ import annotations

import yaml
import pytest
from pathlib import Path
from unittest.mock import MagicMock

from src.worldgeneration.generator import ProceduralCompositionGenerator
from src.worldgeneration.schema import GenerationIntentSpec
from src.worldmodules.schema import WorldModuleSpec, ModuleParameterSpec
from src.worldassembly.schema import WorldCompositionSpec


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_param(
    name: str,
    type: str = "integer",
    *,
    default=None,
    allowed_values=None,
    min_value=None,
    max_value=None,
    required: bool = False,
) -> ModuleParameterSpec:
    return ModuleParameterSpec(
        name=name,
        type=type,
        default=default,
        allowed_values=allowed_values,
        min_value=min_value,
        max_value=max_value,
        required=required,
    )


def _make_module(
    module_id: str,
    module_type: str = "terrain",
    parameters: list[ModuleParameterSpec] | None = None,
) -> WorldModuleSpec:
    return WorldModuleSpec(
        module_id=module_id,
        module_type=module_type,
        display_name=f"Module {module_id}",
        parameters=parameters or [],
    )


def _make_repo(modules: list[WorldModuleSpec]) -> MagicMock:
    repo = MagicMock()
    repo.list_modules.return_value = modules
    return repo


def _default_intent(**kwargs) -> GenerationIntentSpec:
    defaults = dict(
        generation_id="test_gen",
        seed=42,
        settlement_style="frontier",
        danger_level=3.0,
        terrain_style="temperate",
        resource_density=1.0,
        population_scale=1.0,
    )
    defaults.update(kwargs)
    return GenerationIntentSpec(**defaults)


def _generate_and_load(
    intent: GenerationIntentSpec,
    modules: list[WorldModuleSpec],
    tmp_path: Path,
    monkeypatch,
) -> WorldCompositionSpec:
    tmp_path.mkdir(parents=True, exist_ok=True)
    monkeypatch.chdir(tmp_path)
    repo = _make_repo(modules)
    gen = ProceduralCompositionGenerator()
    output_path = gen.generate(intent, repo)
    raw = yaml.safe_load(output_path.read_text())
    return WorldCompositionSpec.model_validate(raw)


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

class TestSameSeedDeterminism:
    """Same seed + same modules → identical parameter values on every call."""

    def test_identical_params_same_seed(self, tmp_path, monkeypatch):
        params = [
            _make_param("density", "integer", min_value=1, max_value=100),
            _make_param("scale", "float", min_value=0.1, max_value=5.0),
        ]
        modules = [_make_module("terrain_basic", "terrain", parameters=params)]
        intent = _default_intent(seed=42)

        # First call
        spec1 = _generate_and_load(intent, modules, tmp_path / "run1", monkeypatch)

        # Second call (fresh directory so file is re-created)
        spec2 = _generate_and_load(intent, modules, tmp_path / "run2", monkeypatch)

        params1 = {ref.module_id: ref.parameters for ref in spec1.module_refs}
        params2 = {ref.module_id: ref.parameters for ref in spec2.module_refs}

        assert params1 == params2, (
            "Same seed must produce identical parameter values across two generate() calls"
        )


class TestDifferentSeedsDiffer:
    """seed=42 vs seed=99 must produce different parameter values for bounded params."""

    def test_different_seeds_produce_different_params(self, tmp_path, monkeypatch):
        params = [
            _make_param("density", "integer", min_value=1, max_value=1000),
        ]
        modules = [_make_module("terrain_basic", "terrain", parameters=params)]

        spec42 = _generate_and_load(
            _default_intent(seed=42), modules, tmp_path / "run42", monkeypatch
        )
        spec99 = _generate_and_load(
            _default_intent(seed=99), modules, tmp_path / "run99", monkeypatch
        )

        params42 = spec42.module_refs[0].parameters
        params99 = spec99.module_refs[0].parameters

        # With a range of 1..1000, seed=42 and seed=99 are astronomically unlikely to collide
        assert params42 != params99, (
            "Different seeds must produce different parameter values for bounded params"
        )


class TestIntegerBounds:
    """Sampled integer values must be within [min_value, max_value] inclusive."""

    def test_sampled_int_within_bounds(self, tmp_path, monkeypatch):
        min_v, max_v = 10, 20
        params = [_make_param("count", "integer", min_value=min_v, max_value=max_v)]
        modules = [_make_module("terrain_basic", "terrain", parameters=params)]

        for seed in range(10):
            spec = _generate_and_load(
                _default_intent(seed=seed),
                modules,
                tmp_path / f"seed_{seed}",
                monkeypatch,
            )
            value = spec.module_refs[0].parameters["count"]
            assert isinstance(value, int), f"Expected int, got {type(value)}"
            assert min_v <= value <= max_v, (
                f"seed={seed}: sampled value {value} outside [{min_v}, {max_v}]"
            )


class TestFloatBounds:
    """Sampled float values must be within [min_value, max_value]."""

    def test_sampled_float_within_bounds(self, tmp_path, monkeypatch):
        min_v, max_v = 0.5, 3.5
        params = [_make_param("intensity", "float", min_value=min_v, max_value=max_v)]
        modules = [_make_module("terrain_basic", "terrain", parameters=params)]

        for seed in range(10):
            spec = _generate_and_load(
                _default_intent(seed=seed),
                modules,
                tmp_path / f"seed_{seed}",
                monkeypatch,
            )
            value = spec.module_refs[0].parameters["intensity"]
            assert isinstance(value, float), f"Expected float, got {type(value)}"
            assert min_v <= value <= max_v, (
                f"seed={seed}: sampled value {value} outside [{min_v}, {max_v}]"
            )


class TestNoBoundsUsesDefault:
    """Parameters with no min/max and no allowed_values must use the declared default unchanged."""

    def test_no_bounds_uses_default(self, tmp_path, monkeypatch):
        params = [_make_param("label", "string", default="temperate")]
        modules = [_make_module("terrain_basic", "terrain", parameters=params)]
        intent = _default_intent(seed=42)

        spec = _generate_and_load(intent, modules, tmp_path, monkeypatch)
        value = spec.module_refs[0].parameters.get("label")
        assert value == "temperate", (
            f"Expected default value 'temperate', got {value!r}"
        )

    def test_no_bounds_no_default_leaves_absent(self, tmp_path, monkeypatch):
        """A required param with no default and no bounds must be absent from parameters dict."""
        params = [_make_param("external_id", "id_reference", required=True)]
        modules = [_make_module("terrain_basic", "terrain", parameters=params)]
        intent = _default_intent(seed=42)

        spec = _generate_and_load(intent, modules, tmp_path, monkeypatch)
        assert "external_id" not in spec.module_refs[0].parameters, (
            "Required param with no default and no bounds must be left absent"
        )


class TestAllowedValuesSampling:
    """allowed_values: result must always be one of the declared values."""

    def test_sampled_value_is_from_allowed_values(self, tmp_path, monkeypatch):
        allowed = ["flat", "hilly", "mountainous"]
        params = [_make_param("terrain_shape", "enum", allowed_values=allowed, default="flat")]
        modules = [_make_module("terrain_basic", "terrain", parameters=params)]

        for seed in range(15):
            spec = _generate_and_load(
                _default_intent(seed=seed),
                modules,
                tmp_path / f"s{seed}",
                monkeypatch,
            )
            value = spec.module_refs[0].parameters["terrain_shape"]
            assert value in allowed, (
                f"seed={seed}: sampled value {value!r} not in allowed_values {allowed}"
            )

    def test_allowed_values_takes_priority_over_bounds(self, tmp_path, monkeypatch):
        """When allowed_values is set, it takes priority — bounds are ignored."""
        allowed = [1, 5, 10]
        params = [
            _make_param(
                "tier", "integer",
                allowed_values=allowed,
                min_value=1,
                max_value=100,
            )
        ]
        modules = [_make_module("terrain_basic", "terrain", parameters=params)]

        for seed in range(10):
            spec = _generate_and_load(
                _default_intent(seed=seed),
                modules,
                tmp_path / f"s{seed}",
                monkeypatch,
            )
            value = spec.module_refs[0].parameters["tier"]
            assert value in allowed, (
                f"seed={seed}: expected value from {allowed}, got {value!r}"
            )


class TestModuleWithNoParameters:
    """Modules with empty parameters list must produce empty parameters dict and not crash."""

    def test_no_params_module_runs_cleanly(self, tmp_path, monkeypatch):
        modules = [_make_module("terrain_basic", "terrain", parameters=[])]
        intent = _default_intent(seed=42)

        spec = _generate_and_load(intent, modules, tmp_path, monkeypatch)
        assert spec.module_refs[0].parameters == {}, (
            "Module with no parameters must produce empty dict"
        )


class TestRNGCallOrder:
    """
    The RNG must be consumed in a fixed order (module rank × param declaration order)
    so that parameter values are stable across calls and independent of unrelated module changes.
    """

    def test_first_module_params_stable_when_second_module_added(
        self, tmp_path, monkeypatch
    ):
        """
        Adding a module that sorts AFTER terrain_basic must not change terrain_basic's params.
        terrain_basic (terrain type) is always selected first; a later module must not
        alter its RNG draw if it doesn't precede it in rank order.
        """
        param = _make_param("density", "integer", min_value=1, max_value=500)

        # Run with only terrain module
        modules_single = [_make_module("terrain_basic", "terrain", parameters=[param])]
        spec_single = _generate_and_load(
            _default_intent(seed=42),
            modules_single,
            tmp_path / "single",
            monkeypatch,
        )
        val_single = spec_single.module_refs[0].parameters["density"]

        # Run with terrain + a second module that has its own param
        second_param = _make_param("pop", "integer", min_value=1, max_value=100)
        modules_dual = [
            _make_module("terrain_basic", "terrain", parameters=[param]),
            _make_module("ecology_extra", "ecology", parameters=[second_param]),
        ]
        spec_dual = _generate_and_load(
            _default_intent(seed=42, settlement_style="none"),
            modules_dual,
            tmp_path / "dual",
            monkeypatch,
        )
        # terrain_basic is always first; find it by module_id
        terrain_ref = next(
            ref for ref in spec_dual.module_refs if ref.module_id == "terrain_basic"
        )
        val_dual = terrain_ref.parameters["density"]

        assert val_single == val_dual, (
            "terrain_basic parameter must be stable regardless of other modules appended after it"
        )
