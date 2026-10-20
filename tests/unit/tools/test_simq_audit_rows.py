"""TCK-20261014-SIMQ-COMPARE-TOOLS-REFUSE-RUNS-NOT-RECORDED-HOST-INDEPENDENT (AC1): the rows producer copies the run manifest's host-independence record verbatim, and deletes only its own runs.

No test here runs a simulation: each uses a fake run directory (a manifest with both fields, with one field absent, with nulls, and no manifest).
"""
from __future__ import annotations

import json

import pytest

from tools.test_architecture import simq_audit_rows as rows
from tools.test_architecture.simq_run_record import SIDECAR_NAME, load_sidecar, read_run_determinism, write_sidecar

REPORT = {
    "overall_grade": "B", "overall_score": 1.5,
    "pillars": {
        "COMBAT": {"grade": "A", "normalized_score": 2.0, "raw_score": 4.0, "event_count": 30},
        "FACTION": {"status": "no-data", "grade": None, "normalized_score": None, "raw_score": None, "event_count": 1, "min_events": 3},
    },
}


def _run(runs, run_id, manifest):
    d = runs / run_id
    d.mkdir(parents=True)
    if manifest is not None:
        (d / "run_manifest.json").write_text(json.dumps(manifest))
    (d / "simulation_events.jsonl").write_text("{}\n")
    return d


def _finished(tmp_path, run_id, manifest, returncode=0):
    runs, out = tmp_path / "runs", tmp_path / "out"
    runs.mkdir(exist_ok=True)
    out.mkdir(exist_ok=True)
    _run(runs, run_id, manifest)
    (out / "quality_report.json").write_text(json.dumps(REPORT))
    stdout = f"[calibrate_simq] Engine done in 1s. JSONL at: data/runs/{run_id}\n"
    return rows.collect_row("k_seed1_200t", 1, returncode, stdout, 1.234, out, runs_dir=runs, proof_dir=tmp_path / "proof")


def test_the_row_shape_is_pinned_and_the_fields_are_copied_from_the_manifest(tmp_path):
    row = _finished(tmp_path, "r1", {"audit_mode": True, "signals_zeroed": True, "unrelated": 1})
    assert row == {
        "key": "k_seed1_200t", "rep": 1, "exit": 0, "wall_s": 1.2, "run_id": "r1", "audit_mode": True, "signals_zeroed": True,
        "pillars": {
            "COMBAT": {"grade": "A", "norm": 2.0, "raw": 4.0, "events": 30},
            "FACTION": {"grade": None, "norm": None, "raw": None, "events": 1, "status": "no-data", "min_events": 3},
        },
        "overall": ["B", 1.5],
    }


@pytest.mark.parametrize(
    "manifest, expected",
    [
        ({"audit_mode": False, "signals_zeroed": True}, (False, True)),  # a pinned-governor run is recorded as it is: not inferred from the producer's own flag
        ({"audit_mode": False, "signals_zeroed": False}, (False, False)),
        ({"signals_zeroed": True}, (None, True)),  # one field absent
        ({"audit_mode": None, "signals_zeroed": None}, (None, None)),
        ({"audit_mode": "yes", "signals_zeroed": 1}, (None, None)),  # not a boolean is not recorded
        ({}, (None, None)),
        (None, (None, None)),  # no manifest at all
    ],
)
def test_absent_or_non_boolean_fields_are_none_never_inferred(tmp_path, manifest, expected):
    row = _finished(tmp_path, "r2", manifest)
    assert (row["audit_mode"], row["signals_zeroed"]) == expected


def test_the_manifest_is_read_before_the_run_directory_is_deleted_and_only_that_run_is_deleted(tmp_path):
    runs = tmp_path / "runs"
    runs.mkdir()
    other = _run(runs, "someone_elses_run", {"audit_mode": True, "signals_zeroed": True})
    row = _finished(tmp_path, "mine", {"audit_mode": True, "signals_zeroed": True})
    assert row["audit_mode"] is True and not (runs / "mine").exists()
    assert other.exists()  # another session's run directory is untouched


def test_a_failed_run_keeps_empty_pillars_and_still_records_its_fields(tmp_path):
    row = _finished(tmp_path, "r3", {"audit_mode": True, "signals_zeroed": True}, returncode=3)
    assert row["exit"] == 3 and row["pillars"] == {} and row["overall"] is None and row["audit_mode"] is True


def test_no_run_id_in_stdout_gives_none_fields_and_deletes_nothing(tmp_path):
    runs, out = tmp_path / "runs", tmp_path / "out"
    runs.mkdir()
    out.mkdir()
    keep = _run(runs, "keep", {"audit_mode": True, "signals_zeroed": True})
    row = rows.collect_row("k_seed1_200t", 2, 1, "no run line\n", 0.1, out, runs_dir=runs, proof_dir=tmp_path / "proof")
    assert (row["run_id"], row["audit_mode"], row["signals_zeroed"]) == (None, None, None) and keep.exists()


def test_the_sidecar_carries_the_run_id_and_both_fields_verbatim(tmp_path):
    run_dir = _run(tmp_path / "runs", "run-9", {"audit_mode": True, "signals_zeroed": True})
    cal = tmp_path / "cal"
    cal.mkdir()
    assert write_sidecar(cal, run_dir) == {"run_id": "run-9", "audit_mode": True, "signals_zeroed": True}
    assert load_sidecar(cal) == {"run_id": "run-9", "audit_mode": True, "signals_zeroed": True}
    assert (cal / SIDECAR_NAME).name == "quality_report.run_determinism.json"


def test_a_missing_manifest_or_missing_sidecar_is_not_recorded(tmp_path):
    run_dir = _run(tmp_path / "runs", "bare", None)
    assert read_run_determinism(run_dir) == {"run_id": "bare", "audit_mode": None, "signals_zeroed": None}
    assert load_sidecar(tmp_path / "no_such_dir") is None
    (tmp_path / "bad").mkdir()
    (tmp_path / "bad" / SIDECAR_NAME).write_text("not json")
    assert load_sidecar(tmp_path / "bad") is None
