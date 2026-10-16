"""TCK-20261015-WEEK-CLOSE-ALL-SHARD-KINDS-AND-VOID-ROW: the week close also folds gate_verdicts shards (readers see the
same ledger before and after), and a pending working_log row of a dropped ticket can be voided, recorded, never
silently deleted. Fixtures live in tmp_path."""
import json
import sys
from datetime import date
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
for sub in ("tools", "tools/agent-monitoring"):
    sys.path.insert(0, str(REPO_ROOT / sub))

import gate_ledger  # noqa: E402
import week_close as wc  # noqa: E402
import working_log_parser as wlp  # noqa: E402
import working_log_writer as wlw  # noqa: E402

WEEK, AFTER = "2026-W41", date(2026, 10, 12)
HEADER = "timestamp,ticket_id,title,status,summary,artifacts_path\n"


def _w(path, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(json.dumps(r, sort_keys=True) + "\n" for r in rows), encoding="utf-8")


def _verdict(vid, ts, blocking, ticket="TCK-1"):
    return {"ts": ts, "gate_verdict_id": vid, "execution_mode": "hand", "ticket_id": ticket, "gate_id": "cli:g",
            "gate_type": "static_check", "verdict": "FAIL" if blocking else "PASS", "blocking": blocking,
            "inputs_ref": {"cmd_sha": "a"}}


def _ledger(root):
    rows = gate_ledger.load_rows(root)
    view = gate_ledger.resolved_view(rows)
    return sorted(v["gate_verdict_id"] for v in gate_ledger.unresolved(view)), len(rows)


def test_gate_verdict_shards_fold_to_one_canonical_file_with_equal_counts_and_the_same_ledger(tmp_path):
    data = tmp_path / "data"
    wk = data / WEEK
    _w(wk / "a.gate_verdicts.jsonl", [_verdict("v1", "2026-10-06T01:00:00Z", True), _verdict("v2", "2026-10-06T02:00:00Z", False)])
    _w(wk / "b.gate_verdicts.jsonl", [_verdict("v3", "2026-10-07T01:00:00Z", True, "TCK-2"),
                                      {"ts": "2026-10-07T02:00:00Z", "row_kind": "adjudication", "gate_verdict_id": "v3",
                                       "adjudication": "false_block", "adjudicated_by": "t", "reason": "r"}])
    before = _ledger(data)
    result = wc.close_week(WEEK, data_dir=data, today=AFTER)
    r = result["gate_verdicts"]
    assert r["shard_files"] == 2 and r["lines_in"] == 4 and r["lines_out"] == 4 and r["duplicates_dropped"] == 0
    assert sorted(p.name for p in wk.glob("*gate_verdicts*")) == ["gate_verdicts.jsonl"]
    assert len((wk / "gate_verdicts.jsonl").read_text().splitlines()) == 4
    assert _ledger(data) == before  # gate_ledger readers see the same unresolved ids and row count


def test_a_week_with_no_gate_shards_is_left_alone(tmp_path):
    data = tmp_path / "data"
    _w(data / WEEK / "runs.jsonl", [{"run_id": "A", "start_ts": "2026-10-06T00:00:00Z"}])
    result = wc.close_week(WEEK, data_dir=data, today=AFTER)
    assert result["gate_verdicts"]["shard_files"] == 0 and not (data / WEEK / "gate_verdicts.jsonl").exists()


def test_bare_manual_actions_and_role_boundary_files_are_untouched(tmp_path):
    data = tmp_path / "data"
    _w(data / WEEK / "manual_actions.jsonl", [{"x": 1}])
    _w(data / WEEK / "role_boundary.jsonl", [{"y": 2}])
    wc.close_week(WEEK, data_dir=data, today=AFTER)
    assert (data / WEEK / "manual_actions.jsonl").exists() and (data / WEEK / "role_boundary.jsonl").exists()


# --- the void row -------------------------------------------------------------------------------------------------

def _row(ticket, ts="2026-10-14T10:00:00Z"):
    return {"timestamp": ts, "ticket_id": ticket, "title": "t", "status": "DONE", "summary": "s", "artifacts_path": ""}


def _void(ticket, ts="2026-10-15T10:00:00Z"):
    return {"row_kind": "void", "timestamp": ts, "ticket_id": ticket, "reason": "ticket dropped", "voided_by": "impl"}


def test_apply_voids_removes_earlier_rows_only_and_reports_unmatched():
    rows = [_row("A"), _row("B"), _row("A", "2026-10-16T00:00:00Z"), _void("A"), _void("NOPE")]
    kept, applied = wlp.apply_voids(rows)
    assert [(r["ticket_id"], r["timestamp"][:10]) for r in kept] == [("B", "2026-10-14"), ("A", "2026-10-16")]
    assert [(v["ticket_id"], voided is not None) for v, voided in applied] == [("A", True), ("NOPE", False)]


def test_a_voided_pending_row_never_reaches_the_csv_and_is_recorded(tmp_path):
    data, csv_path = tmp_path / "data", tmp_path / "working_log.csv"
    csv_path.write_text(HEADER)
    wk = data / "2026-W42"
    _w(wk / "platform.working_log.jsonl", [_row("TCK-DROPPED"), _row("TCK-REAL")])
    _w(wk / "impl.working_log.jsonl", [_void("TCK-DROPPED")])
    pending = wlp.parse_pending_working_log_shards(data)
    assert [r["ticket_id"] for r in pending] == ["TCK-REAL"]  # readers of pending rows see it already void
    result = wlw.consolidate_pending_rows(data_root=data, csv_path=csv_path, week="2026-W42")
    assert result["consolidated_rows"] == 1 and result["voided_rows"] == 1
    text = csv_path.read_text()
    assert "TCK-REAL" in text and "TCK-DROPPED" not in text
    record = [json.loads(x) for x in (wk / "working_log_voids.jsonl").read_text().splitlines()]
    assert record[0]["matched"] is True and record[0]["voided_row"]["ticket_id"] == "TCK-DROPPED"
    assert record[0]["void"]["reason"] == "ticket dropped"
    assert not list(wk.glob("*.working_log.jsonl"))  # shards consumed as before


def test_a_week_close_dry_run_of_the_dropped_ticket_writes_no_csv_row(tmp_path):
    data, csv_path = tmp_path / "data", tmp_path / "working_log.csv"
    csv_path.write_text(HEADER)
    _w(data / "2026-W42" / "platform.working_log.jsonl", [_row("TCK-DROPPED")])
    _w(data / "2026-W42" / "impl.working_log.jsonl", [_void("TCK-DROPPED")])
    wlw.consolidate_pending_rows(data_root=data, csv_path=csv_path, week="2026-W42")
    assert csv_path.read_text() == HEADER


def test_append_void_row_stages_a_typed_row_and_refuses_an_empty_reason(tmp_path, monkeypatch):
    import pytest

    target = tmp_path / "shard.working_log.jsonl"
    monkeypatch.setattr(wlw, "resolve_write_target", lambda kind: target)
    wlw.append_void_row("TCK-X", "dropped", "impl", timestamp="2026-10-15T00:00:00Z")
    assert json.loads(target.read_text()) == {"row_kind": "void", "timestamp": "2026-10-15T00:00:00Z",
                                              "ticket_id": "TCK-X", "reason": "dropped", "voided_by": "impl"}
    with pytest.raises(ValueError):
        wlw.append_void_row("TCK-X", "", "impl")
