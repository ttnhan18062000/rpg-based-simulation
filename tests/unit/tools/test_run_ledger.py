"""TCK-20261023-MEASURED-STEP-RUN-AND-RERUN-LEDGER: the run-ledger/v1 row, the append, the started/KILLED rule and the summary. Fakes only."""
from __future__ import annotations

import dataclasses
import datetime as dt
import json
import uuid
from pathlib import Path

import pytest

from tools.test_architecture import run_ledger as rl

RERUN = str(uuid.uuid4())
HOST = rl.Host("h", 4, 8000, "3.13.0", "Linux")


def _row(outcome="PASS", *, tool="paired", mode=None, step="hunger", rerun_of=None, runs=None, started_at="2026-10-26T10:00:00.000000Z", workers=2, invocation_id=None, detail=None):
    runs = [rl.RunEntry("base", "w", 1, 10.0, 100.0, False), rl.RunEntry("new", "w", 1, 12.5, 120.0, False)] if runs is None else runs
    ended = None if outcome is None else "2026-10-26T10:01:00.000000Z"
    return rl.RunLedgerRow(rl.SCHEMA, invocation_id or str(uuid.uuid4()), tool, step, mode or ("step" if tool == "paired" else "gate"), workers,
                           "abc" if tool == "paired" else None, "def", ("w",), (1,), 100, started_at, ended, outcome, detail, rerun_of, tuple(runs), HOST)


@pytest.mark.parametrize("outcome", [*rl.OUTCOMES, None])
def test_every_outcome_and_the_started_row_round_trip(outcome):
    row = _row(outcome)
    again = rl.RunLedgerRow.from_json(row.to_json())
    assert again == row and "\n" not in row.to_json()
    assert rl.RunLedgerRow.from_json(json.loads(row.to_json())) == row  # a dict is accepted too


@pytest.mark.parametrize("tool, mode", [("paired", "step"), ("paired", "neutral"), ("paired", "report_only"), ("gate", "gate")])
def test_the_modes_of_each_tool_round_trip(tool, mode):
    assert rl.RunLedgerRow.from_json(_row(tool=tool, mode=mode).to_json()).mode == mode


@pytest.mark.parametrize("tool, mode", [(t, m) for t in rl.TOOLS for m in ("step", "neutral", "report_only", "gate", "", None, "STEP") if m not in rl.MODES[t]])
def test_every_tool_mode_pair_outside_the_allowed_ones_is_rejected_naming_mode(tool, mode):
    data = _row(tool=tool).to_dict()
    data["mode"] = mode
    with pytest.raises(rl.LedgerRowError, match="^mode:"):
        rl.RunLedgerRow.from_json(data)


@pytest.mark.parametrize("workers", [0, -1, True, False, 2.0, "2", None])
def test_workers_must_be_a_strict_integer_at_least_one(workers):
    data = _row().to_dict()
    data["workers"] = workers
    with pytest.raises(rl.LedgerRowError, match="^workers:"):
        rl.RunLedgerRow.from_json(data)
    data["workers"] = 1
    assert rl.RunLedgerRow.from_json(data).workers == 1


def test_a_mode_of_the_other_tool_is_rejected_naming_the_field():
    with pytest.raises(rl.LedgerRowError, match="^mode:"):
        rl.RunLedgerRow.from_json(_row(tool="gate", mode="step").to_json())
    with pytest.raises(rl.LedgerRowError, match="^mode:"):
        rl.RunLedgerRow.from_json(_row(tool="paired", mode="gate").to_json())


@pytest.mark.parametrize("field", rl._FIELDS)
def test_a_missing_field_is_rejected_naming_it(field):
    data = _row().to_dict()
    del data[field]
    with pytest.raises(rl.LedgerRowError, match=f"^{field}: is required"):
        rl.RunLedgerRow.from_json(data)


def test_an_unknown_field_is_rejected_naming_it():
    data = {**_row().to_dict(), "extra": 1}
    with pytest.raises(rl.LedgerRowError, match="^extra: is not a field"):
        rl.RunLedgerRow.from_json(data)
    data = _row().to_dict()
    data["runs"][0]["colour"] = "red"
    with pytest.raises(rl.LedgerRowError, match=r"runs\[0\]\.colour"):
        rl.RunLedgerRow.from_json(data)
    data = _row().to_dict()
    del data["host"]["nproc"]
    with pytest.raises(rl.LedgerRowError, match=r"host\.nproc"):
        rl.RunLedgerRow.from_json(data)


@pytest.mark.parametrize("field, value", [
    ("schema", "run-ledger/v2"), ("invocation_id", "not-a-uuid"), ("tool", "other"), ("step", ""), ("workers", 0), ("workers", True), ("worlds", []),
    ("seeds", ["1"]), ("ticks", 0), ("started_at", "2026-10-26T10:00:00"), ("started_at", "yesterday"), ("outcome", "WIN"), ("rerun_of", "x"),
    ("base_sha", ""), ("runs", "none"),
])
def test_a_wrongly_typed_field_is_rejected_naming_it(field, value):
    data = _row().to_dict()
    data[field] = value
    with pytest.raises(rl.LedgerRowError, match=f"^{field}:"):
        rl.RunLedgerRow.from_json(data)


def test_a_run_entry_is_checked_field_by_field():
    for key, value in (("arm", "other"), ("seed", "1"), ("wall_seconds", -1), ("peak_rss_mb", "big"), ("cached", 1)):
        data = _row().to_dict()
        data["runs"][0][key] = value
        with pytest.raises(rl.LedgerRowError, match=rf"runs\[0\]\.{key}"):
            rl.RunLedgerRow.from_json(data)
    data = _row().to_dict()
    data["runs"][0]["peak_rss_mb"] = None  # not measured is allowed
    assert rl.RunLedgerRow.from_json(data).runs[0].peak_rss_mb is None


def test_a_started_row_has_no_end_and_an_end_row_has_both():
    data = _row(None).to_dict()
    assert data["outcome"] is None and data["ended_at"] is None
    data["outcome"] = "PASS"
    with pytest.raises(rl.LedgerRowError, match="^ended_at:"):
        rl.RunLedgerRow.from_json(data)
    data = _row("PASS").to_dict()
    data["ended_at"] = None
    with pytest.raises(rl.LedgerRowError, match="^ended_at:"):
        rl.RunLedgerRow.from_json(data)


def test_a_rerun_names_an_earlier_invocation_not_itself():
    row = _row(rerun_of=RERUN)
    assert rl.RunLedgerRow.from_json(row.to_json()).rerun_of == RERUN
    with pytest.raises(rl.LedgerRowError, match="^rerun_of:"):
        rl.RunLedgerRow.from_json(dataclasses.replace(row, rerun_of=row.invocation_id).to_json())


# ---- append and path

def test_append_writes_one_line_per_row_and_creates_the_directory(tmp_path):
    path = tmp_path / "deep" / "ledger.jsonl"
    assert rl.append_row(path, _row()) and rl.append_row(path, _row("STOP"))
    assert len(path.read_text().splitlines()) == 2
    rows, bad = rl.read_rows(path)
    assert [r.outcome for r in rows] == ["PASS", "STOP"] and bad == 0


def test_the_default_path_is_data_ledgers_and_the_environment_overrides_it(tmp_path, monkeypatch):
    monkeypatch.delenv(rl.ENV_PATH, raising=False)
    assert rl.ledger_path().parts[-3:] == ("data", "ledgers", "run_ledger.jsonl")
    monkeypatch.setenv(rl.ENV_PATH, str(tmp_path / "x.jsonl"))
    assert rl.ledger_path() == tmp_path / "x.jsonl"
    assert rl.append_row(None, _row()) and (tmp_path / "x.jsonl").is_file()


def test_a_write_failure_warns_and_never_raises(tmp_path, capsys):
    blocker = tmp_path / "file"
    blocker.write_text("not a directory")
    assert rl.append_row(blocker / "ledger.jsonl", _row()) is False
    assert "run ledger not written" in capsys.readouterr().err


def test_a_torn_or_foreign_line_is_counted_not_fatal(tmp_path):
    path = tmp_path / "l.jsonl"
    rl.append_row(path, _row())
    with open(path, "a") as fh:
        fh.write('{"schema": "run-ledger/v1"\n\nnot json\n')
    rows, bad = rl.read_rows(path)
    assert len(rows) == 1 and bad == 2
    assert rl.read_rows(tmp_path / "missing.jsonl") == ([], 0)


def test_begin_and_finish_write_a_started_row_then_an_end_row_with_one_id(tmp_path):
    path = tmp_path / "l.jsonl"
    started = rl.begin(tool="gate", step="M0", mode="gate", workers=3, base_sha=None, new_sha="abc", worlds=["w"], seeds=[1, 2], ticks=10, path=path)
    assert started is not None and started.is_started_row
    rl.finish(started, "ERROR", detail="boom", runs=[rl.RunEntry("gate", "w", 1, 1.0, None, False)], path=path)
    rows, _ = rl.read_rows(path)
    assert [r.outcome for r in rows] == [None, "ERROR"] and rows[0].invocation_id == rows[1].invocation_id
    assert rows[1].runs[0].arm == "gate" and rows[1].outcome_detail == "boom"


def test_begin_with_a_bad_value_warns_and_the_invocation_goes_on(tmp_path, capsys):
    assert rl.begin(tool="gate", step="", mode="gate", workers=1, base_sha=None, new_sha="a", worlds=["w"], seeds=[1], ticks=1, path=tmp_path / "l") is None
    assert "step:" in capsys.readouterr().err
    rl.finish(None, "PASS", path=tmp_path / "l")  # a no-op
    assert not (tmp_path / "l").exists()


# ---- KILLED and the summary

def test_a_started_row_with_no_end_row_is_read_as_killed():
    started, done = _row(None, step="s"), _row("PASS", step="s")
    summary = rl.summarize([started, done])
    assert summary["steps"]["s"]["outcomes"] == {"KILLED": 1, "PASS": 1}
    ended = dataclasses.replace(started, outcome="STOP", ended_at="2026-10-26T10:02:00.000000Z")
    assert rl.summarize([started, ended])["steps"]["s"]["outcomes"] == {"STOP": 1}  # an end row with the same id wins, in either order
    assert rl.summarize([ended, started])["steps"]["s"]["outcomes"] == {"STOP": 1}


def _fixture_rows():
    first = _row("STOP", step="hunger", started_at="2026-10-25T09:00:00.000000Z", mode="step",
                 runs=[rl.RunEntry("base", "w", 1, 100.0, 500.0, False), rl.RunEntry("new", "w", 1, 120.0, 650.0, False)])
    rerun = _row("PASS", step="hunger", started_at="2026-10-26T09:00:00.000000Z", mode="report_only", rerun_of=first.invocation_id,
                 runs=[rl.RunEntry("base", "w", 1, 0.0, None, True), rl.RunEntry("new", "w", 1, 110.0, 700.0, False)])
    other = _row("REFUSED", step="thirst", started_at="2026-10-26T11:00:00.000000Z", runs=[], detail="NonAuditRunError: x")
    gate = _row("PASS", tool="gate", step="M0", started_at="2026-10-26T12:00:00.000000Z", runs=[rl.RunEntry("gate", "w", 1, 30.0, 400.0, False)])
    return [first, rerun, other, gate, _row(None, step="thirst", started_at="2026-10-26T13:00:00.000000Z", runs=[])]


def test_the_summary_reports_runs_reruns_and_wall_time_per_step():
    steps = rl.summarize(_fixture_rows())["steps"]
    assert steps["hunger"] == {
        "invocations": 2, "runs_executed": 3, "runs_cached": 1, "reruns": 1, "wall_seconds_total": 330.0,
        "wall_seconds_by_arm": {"base": 100.0, "new": 230.0}, "max_peak_rss_mb": 700.0,
        "outcomes": {"PASS": 1, "STOP": 1}, "modes": {"report_only": 1, "step": 1},
    }
    assert steps["thirst"]["outcomes"] == {"KILLED": 1, "REFUSED": 1} and steps["thirst"]["max_peak_rss_mb"] is None
    assert steps["M0"]["wall_seconds_by_arm"] == {"gate": 30.0}


def test_the_summary_filters_by_step_and_since():
    rows = _fixture_rows()
    assert list(rl.summarize(rows, step="hunger")["steps"]) == ["hunger"]
    since = rl.summarize(rows, since=dt.date(2026, 10, 26))["steps"]
    assert since["hunger"]["invocations"] == 1 and since["hunger"]["reruns"] == 1
    assert rl.summarize(rows, since=dt.date(2026, 11, 1))["steps"] == {}


def test_the_json_output_is_pinned(tmp_path, capsys):
    path = tmp_path / "l.jsonl"
    for row in _fixture_rows():
        rl.append_row(path, row)
    with open(path, "a") as fh:
        fh.write("garbage\n")
    assert rl.main(["summary", "--path", str(path), "--step", "hunger", "--json"]) == 0
    assert json.loads(capsys.readouterr().out) == {
        "schema": "run-ledger-summary/v1", "invalid_lines": 1,
        "steps": {"hunger": {
            "invocations": 2, "runs_executed": 3, "runs_cached": 1, "reruns": 1, "wall_seconds_total": 330.0,
            "wall_seconds_by_arm": {"base": 100.0, "new": 230.0}, "max_peak_rss_mb": 700.0,
            "outcomes": {"PASS": 1, "STOP": 1}, "modes": {"report_only": 1, "step": 1}}},
    }


def test_the_text_output_names_runs_reruns_and_wall_time(tmp_path, capsys):
    path = tmp_path / "l.jsonl"
    for row in _fixture_rows():
        rl.append_row(path, row)
    assert rl.main(["summary", "--path", str(path), "--step", "hunger"]) == 0
    out = capsys.readouterr().out
    assert out == ("hunger: 2 invocation(s), 1 rerun(s); runs 3 executed, 1 cached; wall 330s (base 100s, new 230s); max peak RSS 700 MB; "
                   "outcomes: PASS 1, STOP 1; modes: report_only 1, step 1\n")
    assert rl.main(["summary", "--path", str(tmp_path / "none.jsonl")]) == 0 and capsys.readouterr().out == "no ledger rows\n"
