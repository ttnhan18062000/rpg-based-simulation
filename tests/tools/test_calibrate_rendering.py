"""Unit/integration tests for tools/calibrate_rendering.py.

Mirrors tools/calibrate_simq.py's own test file's discipline (tests/simulation_quality/
test_calibrate_simq.py): tests the script's own logic and guard behavior, never asserts
against a specific calibrated numeric healthy-band value -- those are empirical outputs
of running real worlds, not a regression anchor (see
staging_artifacts/TCK-20260821-VISUAL-QUALITY-CALIBRATION/test_plan.md).

All written artifacts use tmp_path -- never the real data/calibration/rendering/ tree.
"""
from __future__ import annotations

import ast
import glob
import json
import os
import sys
from pathlib import Path

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../.."))

import pytest

import tools.calibrate_rendering as cal_mod
from src.worldbuilding.compiler import WorldCompiler

_CAL_MODULE_PATH = Path(cal_mod.__file__)


class _Args:
    """Plain namespace mirroring argparse.Namespace's attribute-access shape."""

    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)


def test_cli_runs_all_four_families_for_one_world_seed_pair():
    state, compile_report = cal_mod._load_and_compile("dungeon_crawl", seed=42)
    artifact = cal_mod._build_run_artifact("dungeon_crawl", 42, state, compile_report)
    payload = artifact.to_dict()

    assert payload["world_id"] == "dungeon_crawl"
    assert payload["seed"] == 42
    assert payload["connectivity"]
    assert payload["density"]
    assert payload["shape"]["components"]
    assert payload["variants"]["terrain_histogram_normalized"]


def test_output_artifact_written_to_correct_location_atomically(tmp_path):
    cal_dir = str(tmp_path / "dungeon_crawl_seed42")
    args = _Args(world="dungeon_crawl", seed=42, output=cal_dir)
    cal_mod._run_one(args)

    output_path = os.path.join(cal_dir, "quality_report.json")
    assert os.path.isfile(output_path)
    assert not os.path.isfile(output_path + ".tmp")

    with open(output_path, "r", encoding="utf-8") as fh:
        payload = json.load(fh)
    assert payload["world_id"] == "dungeon_crawl"
    assert payload["seed"] == 42


def test_seed_flag_is_singular_per_invocation():
    parser = cal_mod._build_parser()
    args = parser.parse_args(["run", "--world", "dungeon_crawl", "--seed", "42"])
    assert args.seed == 42
    assert isinstance(args.seed, int)

    with pytest.raises(SystemExit):
        parser.parse_args(["run", "--world", "dungeon_crawl", "--seed", "42", "137"])


def test_calibration_run_integrity_guard_fails_loud_on_corrupted_compile(monkeypatch, tmp_path):
    def _fake_compile(spec, seed, output_report_path=None, context=None):
        state, report = _real_compile(spec, seed=seed)
        report = dict(report)
        report["warnings"] = ["synthetic warning injected by test"]
        return state, report

    _real_compile = WorldCompiler.compile
    monkeypatch.setattr(WorldCompiler, "compile", staticmethod(_fake_compile))

    cal_dir = str(tmp_path / "corrupted_run")
    args = _Args(world="dungeon_crawl", seed=42, output=cal_dir)

    with pytest.raises(cal_mod.CalibrationIntegrityError):
        cal_mod._run_one(args)

    sidecar_path = os.path.join(cal_dir, "compile_health.json")
    assert os.path.isfile(sidecar_path), "compile_health.json sidecar must be written even on guard failure"
    with open(sidecar_path, "r", encoding="utf-8") as fh:
        sidecar = json.load(fh)
    assert sidecar["guard_passed"] is False

    assert not os.path.isfile(os.path.join(cal_dir, "quality_report.json")), (
        "a failed run must never produce a quality_report.json"
    )


def test_calibration_run_succeeds_normally_on_clean_compile(tmp_path):
    cal_dir = str(tmp_path / "clean_run")
    args = _Args(world="dungeon_crawl", seed=42, output=cal_dir)
    cal_mod._run_one(args)

    sidecar_path = os.path.join(cal_dir, "compile_health.json")
    assert os.path.isfile(sidecar_path)
    with open(sidecar_path, "r", encoding="utf-8") as fh:
        sidecar = json.load(fh)
    assert sidecar["guard_passed"] is True

    assert os.path.isfile(os.path.join(cal_dir, "quality_report.json"))


def test_shape_zero_cross_seed_variance_is_recorded_as_expected_not_flagged(tmp_path):
    input_dir = tmp_path / "input"
    for seed in (42, 137):
        args = _Args(world="dungeon_crawl", seed=seed, output=str(input_dir / f"dungeon_crawl_seed{seed}"))
        cal_mod._run_one(args)

    output_path = str(tmp_path / "aggregate_report.json")
    agg_args = _Args(input_dir=str(input_dir), output=output_path)
    cal_mod._aggregate(agg_args)

    with open(output_path, "r", encoding="utf-8") as fh:
        report = json.load(fh)

    assert report["observed"]["shape"]["same_world_cross_seed_variance"]["dungeon_crawl"] == "none (expected)"
    assert report["observed"]["variants"]["same_world_cross_seed_tvd"]["dungeon_crawl"] == "none (expected)"


def test_density_and_connectivity_show_real_cross_seed_variance_in_output(tmp_path):
    input_dir = tmp_path / "input"
    for seed in (42, 137):
        args = _Args(world="sandbox_world", seed=seed, output=str(input_dir / f"sandbox_world_seed{seed}"))
        cal_mod._run_one(args)

    output_path = str(tmp_path / "aggregate_report.json")
    agg_args = _Args(input_dir=str(input_dir), output=output_path)
    cal_mod._aggregate(agg_args)

    with open(output_path, "r", encoding="utf-8") as fh:
        report = json.load(fh)

    density_stats = report["observed"]["density"]["cv"]
    assert density_stats["n"] == 2
    assert density_stats["min"] != density_stats["max"], (
        "density cv must show real cross-seed variance for sandbox_world, not a collapsed single value"
    )


def test_output_config_header_matches_grade_thresholds_yaml_field_set(tmp_path):
    input_dir = tmp_path / "input"
    args = _Args(world="dungeon_crawl", seed=42, output=str(input_dir / "dungeon_crawl_seed42"))
    cal_mod._run_one(args)

    output_path = str(tmp_path / "aggregate_report.json")
    agg_args = _Args(input_dir=str(input_dir), output=output_path)
    cal_mod._aggregate(agg_args)

    with open(output_path, "r", encoding="utf-8") as fh:
        report = json.load(fh)

    provenance = report["provenance"]
    for field in ("calibration", "worlds", "seeds", "ticks", "scope_note"):
        assert field in provenance, f"provenance object missing required field {field!r}"
    assert "TCK-20260821-VISUAL-QUALITY-CALIBRATION" in provenance["calibration"]
    assert provenance["worlds"] == ["dungeon_crawl"]
    assert provenance["seeds"] == [42]
    assert "validation_summary" in report


def test_no_pytest_or_ci_gate_asserts_against_calibrated_threshold_values():
    """AC #4: no test file anywhere in tests/ (other than this script-logic file itself)
    imports/opens the calibration report path and asserts a specific numeric value from it."""
    repo_root = _CAL_MODULE_PATH.parent.parent
    tests_dir = repo_root / "tests"
    this_file = Path(__file__).resolve()

    offenders = []
    for path_str in glob.glob(str(tests_dir / "**" / "*.py"), recursive=True):
        path = Path(path_str).resolve()
        if path == this_file:
            continue
        text = path.read_text(encoding="utf-8")
        if "calibration_report_TCK-20260821-VISUAL-QUALITY-CALIBRATION" in text or (
            "calibrate_rendering" in text and "quality_report.json" in text
        ):
            offenders.append(str(path))

    assert not offenders, (
        f"no test outside this file may consume calibrate_rendering's output as a "
        f"CI-gated threshold value: {offenders}"
    )


def test_calibration_script_module_does_not_import_simulation_quality_or_observability_events():
    tree = ast.parse(_CAL_MODULE_PATH.read_text())

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            names = [alias.name for alias in node.names]
        elif isinstance(node, ast.ImportFrom):
            names = [node.module or ""]
        else:
            continue
        for name in names:
            assert "simulation_quality" not in name, f"calibrate_rendering.py must not import {name}"
            assert "observability.events" not in name, f"calibrate_rendering.py must not import {name}"


def test_calibration_run_does_not_mutate_any_resolved_world_cache_on_disk(tmp_path):
    repo_root = _CAL_MODULE_PATH.parent.parent
    resolved_dir = repo_root / "data" / "worlds" / "dungeon_crawl" / "resolved"
    resolved_files = sorted(resolved_dir.glob("*"))
    assert resolved_files, "expected real resolved/ files to exist for dungeon_crawl"

    mtimes_before = {p: p.stat().st_mtime for p in resolved_files}

    cal_dir = str(tmp_path / "mutation_check_run")
    args = _Args(world="dungeon_crawl", seed=42, output=cal_dir)
    cal_mod._run_one(args)

    mtimes_after = {p: p.stat().st_mtime for p in resolved_files}
    assert mtimes_before == mtimes_after, "calibration run must not mutate any resolved/ cache file"
