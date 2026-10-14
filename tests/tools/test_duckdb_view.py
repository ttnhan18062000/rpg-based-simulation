"""tools/agent-monitoring/duckdb_view.py: in-memory views over the monitoring shards (TCK-20261013-MONITORING-DUCKDB-VIEW)."""

from __future__ import annotations

import hashlib
import importlib.util
import io
import json
import sys
import types
from pathlib import Path

import pytest

_REPO_ROOT = Path(__file__).resolve().parents[2]
_TOOLS = _REPO_ROOT / "tools" / "agent-monitoring"
for p in (str(_REPO_ROOT), str(_TOOLS)):
    if p not in sys.path:
        sys.path.insert(0, p)


def _load() -> types.ModuleType:
    spec = importlib.util.spec_from_file_location("duckdb_view", _TOOLS / "duckdb_view.py")
    mod = importlib.util.module_from_spec(spec)  # type: ignore[arg-type]
    spec.loader.exec_module(mod)  # type: ignore[union-attr]
    return mod


dv = _load()
from generate_retro import _resolve_status  # noqa: E402
from validate import load_data_glob  # noqa: E402


def _write(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(json.dumps(r) + "\n" for r in rows), encoding="utf-8")


@pytest.fixture()
def data_root(tmp_path: Path) -> Path:
    root = tmp_path / "data"
    # week 1: bare canonical file plus one per-batch file; legacy run uses `status`, current uses `final_status`
    _write(root / "2026-W41" / "runs.jsonl", [
        {"run_id": "TCK-A", "ticket_id": "TCK-A", "workflow": "implement-ticket", "tier": "standard", "final_status": "DONE", "duration_s": 10, "session_role": "x"},
        {"run_id": "TCK-OLD", "status": "success", "start_ts": "2026-10-01T00:00:00Z"},
    ])
    _write(root / "2026-W41" / "batch-a.runs.jsonl", [
        {"run_id": "TCK-A-2", "ticket_id": "TCK-A", "final_status": "DONE", "session_role": "x"},
    ])
    # week 2, second batch
    _write(root / "2026-W42" / "batch-b.runs.jsonl", [
        {"run_id": "EPIC-1", "final_status": "FAILED", "tier": "epic"},
        {"run_id": "TCK-B", "ticket_id": "TCK-B", "final_status": "", "status": "DONE"},
    ])
    _write(root / "2026-W42" / "batch-b.events.jsonl", [
        {"run_id": "TCK-B", "seq": 1, "phase": "Scope", "agent": "a", "status": "ok"},
        {"run_id": "TCK-OLD", "seq": 1, "event": "legacy free text"},
    ])
    _write(root / "2026-W42" / "batch-b.tools.jsonl", [
        {"run_id": "TCK-B", "seq": 1, "tool": "Bash"}, {"run_id": None, "seq": None, "tool": "Read"},
    ])
    _write(root / "2026-W42" / "batch-b.gate_verdicts.jsonl", [
        {"gate_verdict_id": "gv-1", "gate_id": "g1", "verdict": "PASS", "blocking": False},
        {"gate_verdict_id": "gv-2", "gate_id": "g1", "verdict": "FAIL", "blocking": True},
        {"gate_verdict_id": "gv-2", "row_kind": "outcome", "outcome": "fixed_and_rerun"},
    ])
    return root


def _count(con, view: str) -> int:
    return con.execute(f"SELECT count(*) FROM {view}").fetchone()[0]


def test_row_counts_match_the_shard_aware_loaders(data_root):
    pytest.importorskip("duckdb")
    con = dv.connect(data_root)
    for kind in ("runs", "events", "tools"):
        assert _count(con, kind) == len(load_data_glob(data_root, kind))
    assert _count(con, "gate_verdicts") == 3


def test_resolved_status_is_the_retro_helpers_value_for_every_run(data_root):
    pytest.importorskip("duckdb")
    con = dv.connect(data_root)
    got = dict(con.execute("SELECT run_id, resolved_status FROM runs").fetchall())
    want = {r["run_id"]: _resolve_status(r) for r in load_data_glob(data_root, "runs")}
    assert got == want
    assert got["TCK-OLD"] == "success"  # legacy spelling is kept literally
    assert got["TCK-B"] == "DONE"  # empty final_status falls back to status


def test_week_comes_from_the_shard_directory(data_root):
    pytest.importorskip("duckdb")
    con = dv.connect(data_root)
    assert dict(con.execute("SELECT week, count(*) FROM runs GROUP BY 1").fetchall()) == {"2026-W41": 3, "2026-W42": 2}


def test_named_queries_run_and_give_the_expected_numbers(data_root):
    pytest.importorskip("duckdb")
    con = dv.connect(data_root)
    for sql in dv.NAMED_QUERIES.values():
        con.execute(sql).fetchall()
    gate = con.execute(dv.NAMED_QUERIES["gate_pass_rate_per_gate"]).fetchall()
    assert gate == [("g1", 2, 1, 50.0)]  # the outcome row is not a verdict
    rework = dict((r[0], r[1:]) for r in con.execute(dv.NAMED_QUERIES["rework_rate_per_agent"]).fetchall())
    assert rework["x"] == (1, 1, 100.0)  # TCK-A has two runs


def test_an_empty_data_root_gives_empty_views(tmp_path):
    pytest.importorskip("duckdb")
    con = dv.connect(tmp_path / "nothing")
    assert [_count(con, v) for v in ("runs", "events", "tools", "gate_verdicts")] == [0, 0, 0, 0]


def _tree_digest(root: Path) -> dict[str, str]:
    return {str(p.relative_to(root)): hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(root.rglob("*")) if p.is_file()}


def test_views_and_queries_never_write_to_the_data_root(data_root):
    pytest.importorskip("duckdb")
    before = _tree_digest(data_root)
    con = dv.connect(data_root)
    for sql in dv.NAMED_QUERIES.values():
        con.execute(sql).fetchall()
    assert dv.main(["--data-root", str(data_root), "query", "SELECT count(*) FROM runs"], out=io.StringIO(), err=io.StringIO()) == 0
    assert _tree_digest(data_root) == before


@pytest.mark.parametrize("sql", [
    "COPY runs TO '/tmp/x.csv'", "CREATE TABLE t AS SELECT 1", "DROP VIEW runs", "SELECT 1; DROP VIEW runs",
    "ATTACH 'x.db'", "INSERT INTO runs VALUES (1)",
])
def test_query_refuses_anything_but_one_read_statement(data_root, sql):
    pytest.importorskip("duckdb")
    err = io.StringIO()
    assert dv.main(["--data-root", str(data_root), "query", sql], out=io.StringIO(), err=err) == 2
    assert "only a single read statement" in err.getvalue()


def test_explain_prints_an_analyzed_plan(data_root):
    pytest.importorskip("duckdb")
    out = io.StringIO()
    assert dv.main(["--data-root", str(data_root), "explain", "runs_per_week_by_status"], out=out, err=io.StringIO()) == 0
    assert "Total Time" in out.getvalue()


def test_a_missing_duckdb_prints_one_line_and_exits_zero(data_root, monkeypatch):
    monkeypatch.setitem(sys.modules, "duckdb", None)  # `import duckdb` now raises ImportError
    out, err = io.StringIO(), io.StringIO()
    assert dv.main(["--data-root", str(data_root), "query", "SELECT 1"], out=out, err=err) == 0
    assert "duckdb is not importable" in err.getvalue()
    assert out.getvalue() == ""


def test_list_works_without_duckdb(monkeypatch):
    monkeypatch.setitem(sys.modules, "duckdb", None)
    out = io.StringIO()
    assert dv.main(["list"], out=out, err=io.StringIO()) == 0
    assert "runs_per_week_by_status" in out.getvalue()
