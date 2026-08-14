"""
Tests for tools/agent-monitoring/query.py's SQLite-index-backed read path,
TCK-20260713-MONITORING-QUERY-INDEX-MIGRATE.

Groups:
  1. per-flag event filters
  2. per-flag / combined runs filters
  3. combined event filters
  4. missing-index error path (AC4)
  5. regression parity vs the frozen pre-migration in-memory-scan logic (AC2)
  6. architecture guards (AC3, ordering)

Fixture DBs are built with build_index.py's own _create_schema/_ingest_runs/
_ingest_events functions (imported, not reimplemented) so the schema under test
is guaranteed to match production, mirroring test_build_index.py's own pattern.
"""
import importlib.util
import json
import sqlite3
import sys
import types
from pathlib import Path

import pytest

_REPO_ROOT = Path(__file__).parent.parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

_QUERY_MODULE_PATH = _REPO_ROOT / "tools" / "agent-monitoring" / "query.py"
_BUILD_INDEX_MODULE_PATH = _REPO_ROOT / "tools" / "agent-monitoring" / "build_index.py"
_FIXTURES_DIR = _REPO_ROOT / "tests" / "fixtures" / "agent_monitoring"


def _load_module(name: str, path: Path) -> types.ModuleType:
    spec = importlib.util.spec_from_file_location(name, path)
    mod: types.ModuleType = importlib.util.module_from_spec(spec)  # type: ignore[arg-type]
    spec.loader.exec_module(mod)  # type: ignore[union-attr]
    return mod


query = _load_module("query", _QUERY_MODULE_PATH)
build_index = _load_module("build_index", _BUILD_INDEX_MODULE_PATH)


def _build_db(tmp_path: Path, runs=None, events=None) -> Path:
    db_path = tmp_path / "monitoring.db"
    conn = sqlite3.connect(str(db_path))
    build_index._create_schema(conn)
    build_index._ingest_runs(conn, runs or [])
    build_index._ingest_events(conn, events or [])
    conn.commit()
    conn.close()
    return db_path


def _args(argv):
    return query.build_parser().parse_args(argv)


def _load_events(tmp_path, events):
    db_path = _build_db(tmp_path, events=events)
    conn = sqlite3.connect(str(db_path))
    records = query.load_events_from_index(conn)
    conn.close()
    return records


def _load_runs(tmp_path, runs):
    db_path = _build_db(tmp_path, runs=runs)
    conn = sqlite3.connect(str(db_path))
    records = query.load_runs_from_index(conn)
    conn.close()
    return records


_RUNS = [
    {
        "run_id": "TCK-A", "start_ts": "2026-07-01T00:00:00Z", "tier": "standard",
        "final_status": "DONE", "agent_count": 3, "duration_s": 100,
    },
    {
        "run_id": "TCK-B", "start_ts": "2026-07-03T00:00:00Z", "tier": "standard",
        "final_status": "TESTS_FAILED", "agent_count": 2, "duration_s": 50,
    },
    # Legacy shape: only a bare `status` field, no `final_status` — resolved_status
    # falls back to `status` via generate_retro._resolve_status at ingest time.
    {"run_id": "TCK-C", "start_ts": "2026-06-01T00:00:00Z", "tier": "standard", "status": "DONE"},
]

_EVENTS = [
    {
        "run_id": "TCK-A", "seq": 1, "ts": "2026-07-01T00:00:00Z", "phase": "Scope",
        "agent": "ticket-scoper", "status": "ok", "summary": "Loaded ticket A",
    },
    {
        "run_id": "TCK-A", "seq": 2, "ts": "2026-07-02T00:00:00Z", "phase": "Implement",
        "agent": "implementer", "status": "ok", "summary": "Wrote code",
    },
    {
        "run_id": "TCK-B", "seq": 1, "ts": "2026-07-03T00:00:00Z", "phase": "Implement",
        "agent": "implementer", "status": "failed", "summary": "Hit a parity gap",
    },
    {
        "run_id": "TCK-B", "seq": 2, "ts": "2026-06-01T00:00:00Z", "phase": "Verify",
        "agent": "test-scoper", "status": "ok", "summary": "old event outside days window",
    },
]


# ---------------------------------------------------------------------------
# Group 1 — per-flag event filters
# ---------------------------------------------------------------------------

class TestEventFilters:

    def test_filter_by_agent(self, tmp_path):
        records = _load_events(tmp_path, _EVENTS)
        result = query.filter_events(records, _args(["--agent", "implementer"]))
        assert {(e["run_id"], e["seq"]) for e in result} == {("TCK-A", 2), ("TCK-B", 1)}

    def test_filter_by_status(self, tmp_path):
        records = _load_events(tmp_path, _EVENTS)
        result = query.filter_events(records, _args(["--status", "failed"]))
        assert [(e["run_id"], e["seq"]) for e in result] == [("TCK-B", 1)]

    def test_filter_by_phase(self, tmp_path):
        records = _load_events(tmp_path, _EVENTS)
        result = query.filter_events(records, _args(["--phase", "Verify"]))
        assert [(e["run_id"], e["seq"]) for e in result] == [("TCK-B", 2)]

    def test_filter_by_run_id(self, tmp_path):
        records = _load_events(tmp_path, _EVENTS)
        result = query.filter_events(records, _args(["--run-id", "TCK-A"]))
        assert {e["seq"] for e in result} == {1, 2}
        assert all(e["run_id"] == "TCK-A" for e in result)

    def test_filter_by_days(self, tmp_path, monkeypatch):
        monkeypatch.setattr(query, "cutoff_ts", lambda days: "2026-06-15T00:00:00Z")
        records = _load_events(tmp_path, _EVENTS)
        result = query.filter_events(records, _args(["--days", "1"]))
        assert {(e["run_id"], e["seq"]) for e in result} == {("TCK-A", 1), ("TCK-A", 2), ("TCK-B", 1)}
        assert ("TCK-B", 2) not in {(e["run_id"], e["seq"]) for e in result}

    def test_filter_by_summary_contains(self, tmp_path):
        records = _load_events(tmp_path, _EVENTS)
        result = query.filter_events(records, _args(["--summary-contains", "PARITY GAP"]))
        assert [(e["run_id"], e["seq"]) for e in result] == [("TCK-B", 1)]


# ---------------------------------------------------------------------------
# Group 2 — runs source + combined runs filters
# ---------------------------------------------------------------------------

class TestRunsFilters:

    def test_runs_flag_queries_runs_table(self, tmp_path, capsys):
        db_path = _build_db(tmp_path, runs=_RUNS, events=_EVENTS)

        query.main(["--runs", "--db-path", str(db_path)])
        runs_output = capsys.readouterr().out
        assert "tier" in runs_output
        assert "agents" in runs_output

        query.main(["--db-path", str(db_path)])
        events_output = capsys.readouterr().out
        assert "phase" in events_output
        assert "tier" not in events_output

    def test_combined_runs_status_and_days_filter(self, tmp_path, monkeypatch):
        """--runs --status --days together. This is the specific combination that
        exercises the intentional Step 2 bug fix: TCK-C only has a bare `status`
        field (no `final_status`), so pre-migration query.py's `final_status`-only
        check silently excluded it from `--status DONE` results. The migrated
        filter_runs() reads the SQL resolved_status column instead and correctly
        includes it. This divergence is deliberate — see filter_runs()'s inline
        comment — and is excluded from TestRegressionParity's strict comparisons."""
        monkeypatch.setattr(query, "cutoff_ts", lambda days: "2026-05-01T00:00:00Z")
        records = _load_runs(tmp_path, _RUNS)
        result = query.filter_runs(records, _args(["--runs", "--status", "DONE", "--days", "1"]))
        assert {r["run_id"] for r in result} == {"TCK-A", "TCK-C"}


# ---------------------------------------------------------------------------
# Group 3 — combined event filters
# ---------------------------------------------------------------------------

class TestCombinedEventFilters:

    def test_combined_agent_status_phase_filters_events(self, tmp_path):
        records = _load_events(tmp_path, _EVENTS)
        result = query.filter_events(
            records, _args(["--agent", "implementer", "--status", "ok", "--phase", "Implement"])
        )
        assert [(e["run_id"], e["seq"]) for e in result] == [("TCK-A", 2)]

    def test_combined_run_id_and_summary_contains(self, tmp_path):
        records = _load_events(tmp_path, _EVENTS)
        result = query.filter_events(
            records, _args(["--run-id", "TCK-B", "--summary-contains", "parity"])
        )
        assert [(e["run_id"], e["seq"]) for e in result] == [("TCK-B", 1)]


# ---------------------------------------------------------------------------
# Group 4 — missing-index error path (AC4)
# ---------------------------------------------------------------------------

class TestMissingIndex:

    def test_missing_index_raises_actionable_error(self, tmp_path, capsys):
        missing_db = tmp_path / "does-not-exist" / "monitoring.db"
        with pytest.raises(SystemExit):
            query.open_index(missing_db)
        captured = capsys.readouterr()
        assert "agent-monitoring-index" in captured.err
        assert "make agent-monitoring-index" in captured.err

    def test_missing_index_exits_nonzero(self, tmp_path):
        missing_db = tmp_path / "does-not-exist" / "monitoring.db"
        with pytest.raises(SystemExit) as exc_info:
            query.open_index(missing_db)
        assert exc_info.value.code != 0

    def test_main_exits_nonzero_when_index_missing(self, tmp_path):
        missing_db = tmp_path / "nope" / "monitoring.db"
        with pytest.raises(SystemExit) as exc_info:
            query.main(["--db-path", str(missing_db)])
        assert exc_info.value.code != 0

    def test_corrupt_db_does_not_print_missing_index_message(self, tmp_path, capsys):
        corrupt_db = tmp_path / "corrupt.db"
        corrupt_db.write_text("not a sqlite file", encoding="utf-8")

        conn = query.open_index(corrupt_db)
        with pytest.raises(sqlite3.DatabaseError):
            conn.execute("SELECT * FROM runs")

        captured = capsys.readouterr()
        assert "No agent-monitoring index found" not in captured.err


# ---------------------------------------------------------------------------
# Group 5 — regression parity vs the frozen pre-migration logic (AC2)
# ---------------------------------------------------------------------------

def _legacy_filter_runs(records, args):
    """Frozen copy of pre-migration query.py's runs-branch filter (main(), lines
    93-101 before this ticket's migration) — the AC2 parity oracle. Deliberately
    NOT updated to use resolved_status; that is the one intentional divergence
    (see filter_runs()'s inline comment), so this function must stay exactly as
    it was pre-migration, bugs and all."""
    cut = query.cutoff_ts(args.days)
    if args.run_id:
        records = [r for r in records if r.get("run_id") == args.run_id]
    if args.status:
        records = [r for r in records if r.get("final_status") == args.status]
    if cut:
        records = [r for r in records if (r.get("start_ts") or "") >= cut]
    return records


def _legacy_filter_events(records, args):
    """Frozen copy of pre-migration query.py's events-branch filter (main(), lines
    102-116 before this ticket's migration) — the AC2 parity oracle. Events-branch
    filtering is byte-for-byte unchanged by this migration, so this mirrors
    filter_events() exactly; kept as a separate frozen copy anyway so a future
    edit to filter_events() can't silently drift without this test noticing."""
    cut = query.cutoff_ts(args.days)
    if args.agent:
        records = [e for e in records if e.get("agent") == args.agent]
    if args.status:
        records = [e for e in records if e.get("status") == args.status]
    if args.phase:
        records = [e for e in records if e.get("phase") == args.phase]
    if args.run_id:
        records = [e for e in records if e.get("run_id") == args.run_id]
    if args.summary_contains:
        records = [e for e in records if args.summary_contains.lower() in e.get("summary", "").lower()]
    if cut:
        records = [e for e in records if (e.get("ts") or "") >= cut]
    return records


def _load_fixture_jsonl(name: str) -> list:
    path = _FIXTURES_DIR / name
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


_RUN_SHAPE_FILES = [
    "shape1_started_finished_notes.jsonl",
    "shape2_final_status_no_end_ts.jsonl",
    "shape3_ts_start_ts_end_result.jsonl",
    "shape4_completed_at_status.jsonl",
    "shape5_folder_epic_bare_status.jsonl",
    "shape6_type_checker_exception.jsonl",
]
_EVENT_SHAPE_FILES = [
    "events_jsonl_reason_code_null.jsonl",
    "events_jsonl_tool_call_count_absent.jsonl",
]

_PARITY_RUNS = [record for name in _RUN_SHAPE_FILES for record in _load_fixture_jsonl(name)]
_PARITY_EVENTS = [record for name in _EVENT_SHAPE_FILES for record in _load_fixture_jsonl(name)]


class TestRegressionParity:
    """AC2 — pre-migration in-memory-scan output vs post-migration SQLite-index-
    backed output must be field-for-field identical on the existing legacy-shape
    fixtures, with exactly one documented exception: `--runs --status`, which
    now reads resolved_status (test_combined_runs_status_and_days_filter above).
    That case is never included in the argv lists compared here."""

    def test_pre_and_post_migration_output_field_for_field_identical_events(self, tmp_path, capsys):
        migrated_records = _load_events(tmp_path, _PARITY_EVENTS)
        for argv in (
            ["--agent", "ticket-scoper"],
            ["--phase", "Scope"],
            ["--run-id", "TCK-20260607-PATH-DRIFT-SRC"],
            ["--summary-contains", "hardcoded"],
            ["--status", "ok"],
            ["--agent", "ticket-scoper", "--phase", "Scope"],
            ["--run-id", "TCK-20260607-PATH-DRIFT-SRC", "--summary-contains", "hardcoded"],
        ):
            args = _args(argv)

            query.print_events(_legacy_filter_events(_PARITY_EVENTS, args))
            legacy_output = capsys.readouterr().out

            query.print_events(query.filter_events(migrated_records, args))
            migrated_output = capsys.readouterr().out

            assert legacy_output == migrated_output, f"parity mismatch for argv={argv}"

    def test_pre_and_post_migration_output_field_for_field_identical_runs(self, tmp_path, capsys):
        # No `--status` in any of these argv lists — see class docstring.
        migrated_records = _load_runs(tmp_path, _PARITY_RUNS)
        for argv in (
            [],
            ["--run-id", "TCK-20260613-DOC-DOMAIN-CONTRACTS"],
            ["--run-id", "TCK-20260623-TYPE-CHECKER"],
        ):
            args = _args(["--runs"] + argv)

            query.print_runs(_legacy_filter_runs(_PARITY_RUNS, args))
            legacy_output = capsys.readouterr().out

            query.print_runs(query.filter_runs(migrated_records, args))
            migrated_output = capsys.readouterr().out

            assert legacy_output == migrated_output, f"parity mismatch for argv={argv}"

    def test_pre_and_post_migration_output_field_for_field_identical_runs_with_days(
        self, tmp_path, capsys, monkeypatch
    ):
        monkeypatch.setattr(query, "cutoff_ts", lambda days: "2026-06-12T00:00:00Z")
        migrated_records = _load_runs(tmp_path, _PARITY_RUNS)
        args = _args(["--runs", "--days", "1"])

        query.print_runs(_legacy_filter_runs(_PARITY_RUNS, args))
        legacy_output = capsys.readouterr().out

        query.print_runs(query.filter_runs(migrated_records, args))
        migrated_output = capsys.readouterr().out

        assert legacy_output == migrated_output

    def test_pre_and_post_migration_parity_includes_type_checker_legacy_shape(self, tmp_path, capsys):
        """shape6: TCK-20260623-TYPE-CHECKER has neither final_status nor status —
        resolved_status is legitimately NULL (permanently-accepted exception, per
        docs/agent-monitoring/schema.md's Known Limitations). Confirms the migrated
        path doesn't crash and matches the frozen reference for this record."""
        migrated_records = _load_runs(tmp_path, _PARITY_RUNS)
        args = _args(["--runs", "--run-id", "TCK-20260623-TYPE-CHECKER"])

        query.print_runs(_legacy_filter_runs(_PARITY_RUNS, args))
        legacy_output = capsys.readouterr().out

        query.print_runs(query.filter_runs(migrated_records, args))
        migrated_output = capsys.readouterr().out

        assert legacy_output == migrated_output
        assert "TCK-20260623-TYPE-CHECKER" in migrated_output


# ---------------------------------------------------------------------------
# Group 6 — architecture guards (AC3, ordering)
# ---------------------------------------------------------------------------

class TestArchitectureGuards:

    def test_query_py_has_no_direct_jsonl_reads(self):
        source = _QUERY_MODULE_PATH.read_text(encoding="utf-8")
        for forbidden in ("RUNS_FILE", "EVENTS_FILE", "load_jsonl"):
            assert forbidden not in source, f"query.py must not reference {forbidden!r}"

    def test_query_py_uses_order_by_id_in_index_queries(self):
        source = _QUERY_MODULE_PATH.read_text(encoding="utf-8")
        assert "ORDER BY id" in source

    def test_query_py_output_ordering_matches_source_order(self, tmp_path):
        events = [
            {"run_id": "TCK-Z", "seq": 3, "ts": "t3", "phase": "P", "agent": "a", "status": "ok", "summary": "third"},
            {"run_id": "TCK-A", "seq": 1, "ts": "t1", "phase": "P", "agent": "a", "status": "ok", "summary": "first"},
            {"run_id": "TCK-M", "seq": 2, "ts": "t2", "phase": "P", "agent": "a", "status": "ok", "summary": "second"},
        ]
        records = _load_events(tmp_path, events)
        assert [e["run_id"] for e in records] == ["TCK-Z", "TCK-A", "TCK-M"]
