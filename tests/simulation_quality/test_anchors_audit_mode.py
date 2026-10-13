"""TCK-20261011-SIMQ-GRADE-ANCHORS-RUN-UNDER-AUDIT-MODE (AC1): every anchor is measured under audit_mode; every other caller of the calibration runner is unchanged.

Outside audit_mode the kernel's wall-clock watchdog and throttle make a run depend on host speed, so the grade anchors are produced with ``audit_mode`` on.
``audit_mode`` is a Kernel constructor flag, so ``_run_engine`` takes an explicit parameter (``extra_flags`` only carries state feature flags).
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

import pytest

import tools.calibrate_simq as cal_mod
import tools.evaluate_simq as ev_mod

ANCHORS = Path(__file__).parent / "fixtures" / "grade_anchors.json"
CORPUS_TEST = Path(__file__).resolve().parents[1] / "unit" / "worldassembly" / "test_corpus_diversity.py"


class _Stop(Exception):
    """Raised by the capturing Kernel so a test reads the flags without running a world."""


def _capture_kernel_flags(monkeypatch) -> dict:
    import src.engine.kernel as kernel_mod

    seen: dict = {}

    class _Capturing:
        def __init__(self, *args, **kwargs):
            seen["flags"] = dict(kwargs.get("flags") or {})
            raise _Stop

    monkeypatch.setattr(kernel_mod, "Kernel", _Capturing)
    return seen


def test_run_engine_builds_the_kernel_with_audit_mode_only_when_asked(monkeypatch, tmp_path):
    for requested, expected in ((True, True), (False, False)):
        seen = _capture_kernel_flags(monkeypatch)
        with pytest.raises(_Stop):
            cal_mod._run_engine("generic", seed=1, ticks=1, entity_count=2, cal_dir=str(tmp_path), audit_mode=requested)
        assert seen["flags"].get("audit_mode", False) is expected and seen["flags"]["no_frame_pacing"] is True
    seen = _capture_kernel_flags(monkeypatch)
    with pytest.raises(_Stop):
        cal_mod._run_engine("generic", seed=1, ticks=1, entity_count=2, cal_dir=str(tmp_path))
    assert "audit_mode" not in seen["flags"]  # the default for every other caller is unchanged


def test_the_calibration_cli_flag_reaches_run_engine_and_defaults_off(monkeypatch, tmp_path):
    calls = []
    monkeypatch.setattr(cal_mod, "_run_engine", lambda *a, **kw: calls.append(kw) or (_ for _ in ()).throw(_Stop()))
    for argv, expected in ((["--audit-mode"], True), ([], False)):
        monkeypatch.setattr(sys, "argv", ["calibrate_simq", "--name", "generic", "--ticks", "1", "--output", str(tmp_path / "o"), *argv])
        with pytest.raises(_Stop):
            cal_mod.main()
        assert calls[-1]["audit_mode"] is expected


def test_evaluate_simq_passes_audit_mode_for_every_run_key_it_builds(monkeypatch, capsys):
    anchors = [k for k in json.loads(ANCHORS.read_text()) if not k.startswith("_")]
    argvs: dict[str, list[str]] = {}
    current: list[str] = []

    def fake_main():
        argvs[current[0]] = list(sys.argv)

    monkeypatch.setattr(cal_mod, "main", fake_main)
    monkeypatch.setattr(ev_mod, "_load_calibration_report", lambda key: None)
    real = ev_mod._run_calibration
    monkeypatch.setattr(ev_mod, "_run_calibration", lambda world, profile, seed, ticks, run_key: (current.__setitem__(slice(None), [run_key]), real(world, profile, seed, ticks, run_key))[1])
    monkeypatch.setattr(sys, "argv", ["evaluate_simq", "--include-slow"])
    with pytest.raises(SystemExit):
        ev_mod.main()
    assert set(argvs) == set(anchors) and len(anchors) > 50  # every anchor was built, none skipped
    assert all("--audit-mode" in argv for argv in argvs.values()), [k for k, v in argvs.items() if "--audit-mode" not in v]


def test_every_grade_stability_test_runs_its_engine_under_audit_mode():
    # A line-based guard: a call split over several lines would get past it, so keep each `_run_engine(...)` call on one line.
    lines = [ln for ln in CORPUS_TEST.read_text(encoding="utf-8").splitlines() if re.search(r"\b_run_engine\(\w", ln) and not ln.lstrip().startswith(("#", '"', "`"))]
    assert len(lines) >= 13 and all("audit_mode=True" in ln for ln in lines), [ln for ln in lines if "audit_mode=True" not in ln]


def test_two_same_seed_runs_in_one_second_get_distinct_run_dirs(monkeypatch, tmp_path):
    """The Kernel's default run id is ``run_<unix second>_<seeded suffix>``; two same-seed runs started within one second would share a directory and double each
    other's events (found in the stage-1 proof). ``_run_engine`` passes a unique id, so a frozen clock still gives two directories."""
    import time

    monkeypatch.setattr(time, "time", lambda: 1_800_000_000.0)
    dirs = []
    for index in range(2):
        cal = tmp_path / f"cal{index}"
        cal.mkdir()
        run_dir, _elapsed, run_id = cal_mod._run_engine("generic", seed=42, ticks=2, entity_count=4, cal_dir=str(cal))
        dirs.append((run_dir, run_id))
    try:
        assert dirs[0][0] != dirs[1][0] and dirs[0][1] != dirs[1][1]
        assert all(Path(d).name == rid for d, rid in dirs)
    finally:
        import shutil

        for run_dir, _ in dirs:
            if Path(run_dir).parent.name == "runs":
                shutil.rmtree(run_dir, ignore_errors=True)  # exactly the directories this test created
