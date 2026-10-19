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


# TCK-20261014-SIMQ-COMPARE-TOOLS-REFUSE-RUNS-NOT-RECORDED-HOST-INDEPENDENT: calibrate_simq records the run's host-independence beside the report it writes, and the
# comparison tools refuse a calibration directory that does not carry it.
def _calibrate(tmp_path, *flags):
    import os

    from tools.gate_checks.done_checker_static import delete_data_run_paths

    out = tmp_path / "cal"
    old_argv = sys.argv[:]
    sys.argv = ["calibrate_simq", "--name", "generic", "--ticks", "5", "--entities", "4", "--output", str(out), *flags]
    try:
        cal_mod.main()
    finally:
        sys.argv = old_argv
    from tools.test_architecture.simq_run_record import load_sidecar

    record = load_sidecar(out)
    assert (out / "quality_report.json").exists()
    if record and record.get("run_id") and os.path.isdir(os.path.join("data", "runs", record["run_id"])):
        delete_data_run_paths([record["run_id"]])  # this test's own run, by exact id
    return record


def test_calibrate_simq_writes_the_run_record_beside_the_report_from_the_runs_own_manifest(tmp_path):
    record = _calibrate(tmp_path, "--audit-mode")
    assert record["audit_mode"] is True and record["signals_zeroed"] is True and record["run_id"]


def test_calibrate_simq_without_audit_mode_records_it_as_not_audit_mode(tmp_path):
    record = _calibrate(tmp_path)
    assert record["audit_mode"] is False and record["signals_zeroed"] is not True


def _evaluate_dry_run(monkeypatch, tmp_path, sidecar):
    import json

    from tools.test_architecture.simq_run_record import SIDECAR_NAME

    run_key = "sandbox_world_seed42_5t"
    cal = tmp_path / "calibration" / run_key
    cal.mkdir(parents=True)
    (cal / "quality_report.json").write_text(json.dumps({"pillars": {"COMBAT": {"grade": "B", "normalized_score": 0.0, "event_count": 9}}}))
    if sidecar is not None:
        (cal / SIDECAR_NAME).write_text(json.dumps(sidecar))
    anchors = tmp_path / "anchors.json"
    anchors.write_text(json.dumps({run_key: {"COMBAT": {"grade": "B", "score": 0.0}}}))
    monkeypatch.setattr(ev_mod, "CALIBRATION_ROOT", tmp_path / "calibration")
    monkeypatch.setattr(sys, "argv", ["evaluate_simq", "--dry-run", "--scenario", run_key, "--anchors", str(anchors)])
    with pytest.raises(SystemExit) as caught:
        ev_mod.main()
    return caught.value.code


def test_evaluate_simq_compares_a_calibration_dir_recorded_host_independent(monkeypatch, tmp_path):
    assert _evaluate_dry_run(monkeypatch, tmp_path, {"run_id": "r", "audit_mode": True, "signals_zeroed": True}) == 0


@pytest.mark.parametrize(
    "sidecar", [None, {"run_id": "r", "audit_mode": None, "signals_zeroed": None}, {"run_id": "r", "audit_mode": False, "signals_zeroed": False}],
    ids=["no sidecar (a stale directory)", "nulls", "a live run"],
)
def test_evaluate_simq_refuses_a_calibration_dir_not_recorded_host_independent(monkeypatch, tmp_path, capsys, sidecar):
    assert _evaluate_dry_run(monkeypatch, tmp_path, sidecar) == 2
    assert "not recorded as host-independent" in capsys.readouterr().err
