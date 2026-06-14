"""Tests for scripts/profile_memory.py (TCK-20260614-CERT-MEMRAY-BUDGET).

Covers:
  TC-1  Script exits cleanly with error message when memray is absent
  TC-2  --save-baseline writes baseline.json with expected schema
  TC-3  Baseline comparison prints delta on subsequent run
  TC-4  --suite certification selects correct test path
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

# Import the module under test
import importlib.util
import types

_SCRIPT = Path(__file__).parent.parent.parent.parent / "scripts" / "profile_memory.py"


def _load_script() -> types.ModuleType:
    spec = importlib.util.spec_from_file_location("profile_memory", _SCRIPT)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


# ---------------------------------------------------------------------------
# TC-1: exits cleanly when memray absent
# ---------------------------------------------------------------------------

def test_script_exits_cleanly_on_missing_memray(tmp_path, capsys):
    mod = _load_script()

    with patch.object(mod, "check_memray", return_value=False):
        ret = mod.run_suite("certification", use_memray=True, save_baseline=False)

    assert ret == 1
    captured = capsys.readouterr()
    assert "memray" in captured.err.lower() or "Memray" in captured.err


# ---------------------------------------------------------------------------
# TC-2: --save-baseline writes baseline.json with expected schema
# ---------------------------------------------------------------------------

def test_baseline_write_creates_json_file(tmp_path, capsys):
    mod = _load_script()

    # Patch REPORTS_DIR to tmp_path, subprocess.run to succeed, and RSS to a fixed value
    with (
        patch.object(mod, "REPORTS_DIR", tmp_path),
        patch.object(mod, "_get_peak_rss_mb", return_value=123.4),
        patch("subprocess.run", return_value=MagicMock(returncode=0)),
    ):
        ret = mod.run_suite("certification", use_memray=False, save_baseline=True)

    assert ret == 0
    baseline = json.loads((tmp_path / "baseline.json").read_text())
    assert baseline["suite"] == "certification"
    assert baseline["peak_rss_mb"] == pytest.approx(123.4)
    assert "timestamp" in baseline


# ---------------------------------------------------------------------------
# TC-3: baseline comparison prints delta when baseline exists
# ---------------------------------------------------------------------------

def test_baseline_comparison_prints_delta(tmp_path, capsys):
    mod = _load_script()

    # Write an existing baseline
    baseline_data = {"suite": "certification", "peak_rss_mb": 100.0, "timestamp": "20260101T000000"}
    (tmp_path / "baseline.json").write_text(json.dumps(baseline_data))

    with (
        patch.object(mod, "REPORTS_DIR", tmp_path),
        patch.object(mod, "_get_peak_rss_mb", return_value=110.0),
        patch("subprocess.run", return_value=MagicMock(returncode=0)),
    ):
        ret = mod.run_suite("certification", use_memray=False, save_baseline=False)

    assert ret == 0
    captured = capsys.readouterr()
    assert "10.0" in captured.out  # delta printed
    assert "10.0%" in captured.out or "10%" in captured.out


# ---------------------------------------------------------------------------
# TC-4: --suite certification selects correct test path
# ---------------------------------------------------------------------------

def test_suite_certification_selects_correct_test_paths(tmp_path):
    mod = _load_script()

    captured_cmd: list = []

    def fake_run(cmd, **kwargs):
        captured_cmd.extend(cmd)
        return MagicMock(returncode=0)

    with (
        patch.object(mod, "REPORTS_DIR", tmp_path),
        patch.object(mod, "_get_peak_rss_mb", return_value=50.0),
        patch("subprocess.run", side_effect=fake_run),
    ):
        mod.run_suite("certification", use_memray=False, save_baseline=False)

    assert "tests/certification/" in captured_cmd
    assert "--resource-budget" in captured_cmd
    assert "off" in captured_cmd
