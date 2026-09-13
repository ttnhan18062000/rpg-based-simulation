#!/usr/bin/env python3
"""
Build a derived, read-only SQLite index over agent-monitoring/{runs,events,tools}.jsonl.

Reads all 3 source JSONL files exactly once each (strictly read-only — never
writes back to them) and writes runs/events/tools tables into a gitignored
SQLite database at agent-monitoring-index/monitoring.db. Full-rebuild-only,
on-demand only: mirrors tools/knowledge_search.py::cmd_build()'s unconditional
"delete existing db, recreate from scratch" shape, not its cmd_build_incremental()
counterpart — no incremental-build mode exists here, ever.

Normalization is reused by import, not reimplementation: resolved_status and
completeness on the runs table call generate_retro.py's _resolve_status() and
validate.py's _record_is_complete() directly; workflow columns fall back to
vocabulary.py's infer_workflow() when the raw record lacks one.

TCK-20260623-TYPE-CHECKER's single legacy runs.jsonl record (no end_ts/
final_status/status at all) legitimately resolves to resolved_status=NULL —
this is a permanently-accepted exception (see docs/agent-monitoring/schema.md's
Known Limitations), not a bug for a future reader to "fix" by special-casing.

Usage:
  python3 tools/agent-monitoring/build_index.py
  make agent-monitoring-index
"""
import argparse
import json
import sqlite3
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from validate import (  # noqa: E402
    LEGACY_COMPLETION_FIELDS,  # noqa: F401
    LEGACY_TERMINAL_STATUS_VALUES,  # noqa: F401
    _record_is_complete,
    load_data_glob,
    load_jsonl,
)
from generate_retro import _resolve_status  # noqa: E402
from vocabulary import CANONICAL_TIERS, infer_workflow  # noqa: E402, F401

DEFAULT_RUNS_FILE = Path("agent-monitoring/data")
DEFAULT_EVENTS_FILE = Path("agent-monitoring/data")
DEFAULT_TOOLS_FILE = Path("agent-monitoring/data")
DEFAULT_DB_PATH = Path("agent-monitoring-index/monitoring.db")


def _load_source(path: Path, source: str) -> list:
    """path is either the agent-monitoring/data root (production default, a directory) or a
    literal single JSONL file (explicit --runs-file/--events-file/--tools-file override, or a
    test's SimpleNamespace injection) — dispatch accordingly. `source` ("runs"/"events"/"tools")
    is resolved statically by the caller, never inferred from the directory's own contents."""
    if path.is_dir():
        return load_data_glob(path, source)
    return load_jsonl(path)


def _infer_workflow_or_none(run_id):
    return infer_workflow(run_id) if run_id else None


def _create_schema(conn: sqlite3.Connection) -> None:
    conn.execute(
        """
        CREATE TABLE runs (
            id INTEGER PRIMARY KEY,
            run_id TEXT,
            workflow TEXT,
            tier TEXT,
            start_ts TEXT,
            resolved_status TEXT,
            is_complete INTEGER,
            raw_json TEXT NOT NULL
        )
        """
    )
    conn.execute("CREATE INDEX idx_runs_run_id ON runs(run_id)")

    conn.execute(
        """
        CREATE TABLE events (
            id INTEGER PRIMARY KEY,
            run_id TEXT,
            seq INTEGER,
            workflow TEXT,
            phase TEXT,
            agent TEXT,
            raw_json TEXT NOT NULL
        )
        """
    )
    conn.execute("CREATE INDEX idx_events_run_id_seq ON events(run_id, seq)")

    conn.execute(
        """
        CREATE TABLE tools (
            id INTEGER PRIMARY KEY,
            run_id TEXT,
            seq INTEGER,
            workflow TEXT,
            tool TEXT NOT NULL,
            raw_json TEXT NOT NULL
        )
        """
    )
    conn.execute("CREATE INDEX idx_tools_run_id_seq ON tools(run_id, seq)")


def _ingest_runs(conn: sqlite3.Connection, records: list) -> int:
    n = 0
    for record in records:
        run_id = record.get("run_id")
        workflow = record.get("workflow") or _infer_workflow_or_none(run_id)
        tier = record.get("tier")
        if tier is not None and tier not in CANONICAL_TIERS:
            print(
                f"WARNING: runs.jsonl record has non-canonical tier {tier!r} (run_id={run_id!r})",
                file=sys.stderr,
            )
        start_ts = record.get("start_ts")
        resolved_status = _resolve_status(record)
        is_complete = 1 if _record_is_complete(record) else 0
        raw_json = json.dumps(record, sort_keys=True)
        conn.execute(
            "INSERT INTO runs (run_id, workflow, tier, start_ts, resolved_status, is_complete, raw_json) "
            "VALUES (?, ?, ?, ?, ?, ?, ?)",
            (run_id, workflow, tier, start_ts, resolved_status, is_complete, raw_json),
        )
        n += 1
    return n


def _ingest_events(conn: sqlite3.Connection, records: list) -> int:
    n = 0
    for record in records:
        run_id = record.get("run_id")
        seq = record.get("seq")
        workflow = record.get("workflow") or _infer_workflow_or_none(run_id)
        phase = record.get("phase")
        agent = record.get("agent")
        raw_json = json.dumps(record, sort_keys=True)
        conn.execute(
            "INSERT INTO events (run_id, seq, workflow, phase, agent, raw_json) VALUES (?, ?, ?, ?, ?, ?)",
            (run_id, seq, workflow, phase, agent, raw_json),
        )
        n += 1
    return n


def _ingest_tools(conn: sqlite3.Connection, records: list) -> tuple:
    n = 0
    skipped = 0
    for record in records:
        # Key presence, not value non-nullness: interactive-use tool calls legitimately
        # carry run_id=null/seq=null (same "run_id and seq is not None" guard
        # compute_tool_count_drift_report uses to exclude them from a run's count without
        # excluding them from tools.jsonl itself). Only the 3 confirmed off-schema shapes
        # are missing the run_id/seq/tool *keys* outright.
        if "run_id" not in record or "seq" not in record or not isinstance(record.get("tool"), str):
            print(
                f"WARNING: tools.jsonl record skipped (missing run_id/seq/tool): {record!r}",
                file=sys.stderr,
            )
            skipped += 1
            continue
        run_id = record.get("run_id")
        seq = record.get("seq")
        tool = record["tool"]
        workflow = record.get("workflow") or _infer_workflow_or_none(run_id)
        raw_json = json.dumps(record, sort_keys=True)
        conn.execute(
            "INSERT INTO tools (run_id, seq, workflow, tool, raw_json) VALUES (?, ?, ?, ?, ?)",
            (run_id, seq, workflow, tool, raw_json),
        )
        n += 1
    return n, skipped


def build(args) -> int:
    runs_path = Path(args.runs_file)
    events_path = Path(args.events_file)
    tools_path = Path(args.tools_file)
    db_path = Path(args.db_path)

    runs = _load_source(runs_path, "runs")
    events = _load_source(events_path, "events")
    tools = _load_source(tools_path, "tools")

    db_path.parent.mkdir(parents=True, exist_ok=True)
    if db_path.exists():
        db_path.unlink()

    conn = sqlite3.connect(str(db_path))
    _create_schema(conn)

    n_runs = _ingest_runs(conn, runs)
    n_events = _ingest_events(conn, events)
    n_tools, n_skipped = _ingest_tools(conn, tools)

    conn.commit()
    conn.close()

    print(
        f"runs: {n_runs} rows, events: {n_events} rows, tools: {n_tools} rows ({n_skipped} skipped)",
        file=sys.stderr,
    )
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Rebuild the derived read-only SQLite index over agent-monitoring JSONL logs."
    )
    parser.add_argument("--runs-file", default=str(DEFAULT_RUNS_FILE))
    parser.add_argument("--events-file", default=str(DEFAULT_EVENTS_FILE))
    parser.add_argument("--tools-file", default=str(DEFAULT_TOOLS_FILE))
    parser.add_argument("--db-path", default=str(DEFAULT_DB_PATH))
    args = parser.parse_args()
    return build(args)


if __name__ == "__main__":
    sys.exit(main())
