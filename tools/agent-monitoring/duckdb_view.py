#!/usr/bin/env python3
"""
A DuckDB view over the agent-monitoring JSONL shards (TCK-20261013-MONITORING-DUCKDB-VIEW).

Builds an in-memory DuckDB database whose views `runs`, `events`, `tools` and `gate_verdicts` read the
`data/<ISO-week>/[<id>.]<kind>.jsonl` shards directly with `read_json`. Shard discovery is
`monitoring_shard_paths.shard_paths()`, the same resolver every other reader uses. Nothing is written: the
database is in memory, the shards are only read, and `query` accepts read statements only.

Normalization is reused, not re-implemented: `resolved_status` on `runs` calls generate_retro.py's
`_resolve_status()`, and `workflow_inferred` calls vocabulary.py's `infer_workflow()`; both are applied in Python to the
distinct input values and joined in (a scalar UDF would need numpy, which is not a declared dependency). The raw
`workflow` column is kept as recorded.

This complements `build_index.py` (SQLite, one table of raw JSON per kind, no gate verdicts); it does not replace it.

Usage:
  python3 tools/agent-monitoring/duckdb_view.py list
  python3 tools/agent-monitoring/duckdb_view.py query "SELECT count(*) FROM runs"
  python3 tools/agent-monitoring/duckdb_view.py explain runs_per_week_by_status

Needs `duckdb` (declared in pyproject.toml). When it is not importable the tool prints one line and exits 0:
monitoring tooling must never fail a workflow.
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent
if str(_HERE) not in sys.path:
    sys.path.insert(0, str(_HERE))
_REPO_ROOT = _HERE.parents[1]
if str(_REPO_ROOT) not in sys.path:
    sys.path.append(str(_REPO_ROOT))

from generate_retro import _resolve_status  # noqa: E402
from monitoring_shard_paths import shard_paths  # noqa: E402
from vocabulary import infer_workflow  # noqa: E402

from tools.agent_working_paths import AGENT_MONITORING  # noqa: E402

DEFAULT_DATA_ROOT = AGENT_MONITORING / "data"

# Columns read per kind. Anything else in a record is ignored, which keeps legacy and current shapes in one view.
# Types are fixed so a stray value of another type in an old shard becomes NULL, not a failed read.
_COLUMNS: dict[str, dict[str, str]] = {
    "runs": {
        "run_id": "VARCHAR", "ticket_id": "VARCHAR", "execution_id": "VARCHAR", "provider": "VARCHAR",
        "workflow": "VARCHAR", "tier": "VARCHAR", "start_ts": "VARCHAR", "end_ts": "VARCHAR",
        "final_status": "VARCHAR", "status": "VARCHAR", "agent_count": "BIGINT", "duration_s": "DOUBLE",
        "execution_mode": "VARCHAR", "session_role": "VARCHAR", "path_reason": "VARCHAR",
    },
    "events": {
        "run_id": "VARCHAR", "seq": "BIGINT", "workflow": "VARCHAR", "phase": "VARCHAR", "agent": "VARCHAR",
        "status": "VARCHAR", "ts": "VARCHAR", "summary": "VARCHAR",
    },
    "tools": {
        "run_id": "VARCHAR", "seq": "BIGINT", "workflow": "VARCHAR", "tool": "VARCHAR", "ts": "VARCHAR",
        "status": "VARCHAR",
    },
    "gate_verdicts": {
        "ts": "VARCHAR", "gate_verdict_id": "VARCHAR", "run_id": "VARCHAR", "ticket_id": "VARCHAR",
        "execution_mode": "VARCHAR", "gate_id": "VARCHAR", "gate_type": "VARCHAR", "phase": "VARCHAR",
        "verdict": "VARCHAR", "blocking": "BOOLEAN", "row_kind": "VARCHAR", "outcome": "VARCHAR",
        "adjudication": "VARCHAR", "followup_verdict_id": "VARCHAR",
    },
}

# Named queries. `{week}` is the ISO week folder name of the shard, taken from the file path.
NAMED_QUERIES: dict[str, str] = {
    "runs_per_week_by_status": (
        "SELECT week, coalesce(resolved_status, '(none)') AS status, count(*) AS runs "
        "FROM runs GROUP BY 1, 2 ORDER BY 1, 3 DESC"
    ),
    "gate_pass_rate_per_gate": (
        "SELECT gate_id, count(*) AS verdicts, "
        "count(*) FILTER (WHERE verdict = 'PASS') AS passed, "
        "round(100.0 * count(*) FILTER (WHERE verdict = 'PASS') / count(*), 1) AS pass_pct "
        "FROM gate_verdicts WHERE row_kind IS NULL GROUP BY 1 ORDER BY verdicts DESC"
    ),
    "rework_rate_per_agent": (
        "WITH per_ticket AS ("
        "  SELECT coalesce(session_role, '(none)') AS agent, ticket_id, count(*) AS n "
        "  FROM runs WHERE ticket_id IS NOT NULL GROUP BY 1, 2) "
        "SELECT agent, count(*) AS tickets, count(*) FILTER (WHERE n > 1) AS reworked, "
        "round(100.0 * count(*) FILTER (WHERE n > 1) / count(*), 1) AS rework_pct "
        "FROM per_ticket GROUP BY 1 ORDER BY tickets DESC"
    ),
    "retro_runs_by_workflow_and_tier": (
        "SELECT coalesce(workflow, workflow_inferred, '(none)') AS workflow, coalesce(tier, '(none)') AS tier, "
        "count(*) AS runs, round(avg(duration_s), 1) AS avg_duration_s, "
        "count(*) FILTER (WHERE resolved_status = 'DONE') AS done "
        "FROM runs GROUP BY 1, 2 ORDER BY runs DESC"
    ),
    "tool_calls_per_tool": (
        "SELECT tool, count(*) AS calls FROM tools GROUP BY 1 ORDER BY calls DESC LIMIT 20"
    ),
}

_READ_ONLY_START = re.compile(r"^\s*(select|with|explain|describe|show|summarize|from)\b", re.IGNORECASE)


class ViewError(Exception):
    """A user-facing problem (unsafe SQL, bad query name)."""


def _sql_str(value: str) -> str:
    return "'" + value.replace("'", "''") + "'"


def _read_json_sql(files: list[Path], kind: str) -> str:
    cols = ", ".join(f"{_sql_str(k)}: {_sql_str(v)}" for k, v in _COLUMNS[kind].items())
    listed = "[" + ", ".join(_sql_str(str(p)) for p in files) + "]"
    return (
        f"read_json({listed}, format='nd', columns={{{cols}}}, ignore_errors=true, "
        "maximum_object_size=16777216, filename=true)"
    )


def _empty_sql(kind: str) -> str:
    cols = ", ".join(f"CAST(NULL AS {t}) AS {k}" for k, t in _COLUMNS[kind].items())
    return f"SELECT {cols}, CAST(NULL AS VARCHAR) AS filename WHERE false"


def connect(data_root: Path = DEFAULT_DATA_ROOT):
    """An in-memory connection with the four views defined. Raises ImportError when duckdb is missing."""
    import duckdb

    con = duckdb.connect(":memory:")
    for kind in _COLUMNS:
        files = shard_paths(data_root, kind)
        source = f"SELECT * FROM {_read_json_sql(files, kind)}" if files else _empty_sql(kind)
        # The week is the shard's directory name (`2026-W42`), read from the path, never from a record.
        week = "regexp_extract(filename, '([^/]+)/[^/]+$', 1) AS week"
        con.execute(f"CREATE VIEW {'_runs_raw' if kind == 'runs' else kind} AS SELECT *, {week} FROM ({source})")
    # Normalization is the Python helpers' own, applied to the distinct inputs only (a scalar UDF would need numpy,
    # which is not a declared dependency). Joins are NULL-safe because legacy records lack these fields.
    con.execute("CREATE TABLE _status_map (final_status VARCHAR, status VARCHAR, resolved_status VARCHAR)")
    status_rows = [(f, st, _resolve_status({"final_status": f, "status": st}))
                   for f, st in con.execute("SELECT DISTINCT final_status, status FROM _runs_raw").fetchall()]
    if status_rows:
        con.executemany("INSERT INTO _status_map VALUES (?, ?, ?)", status_rows)
    con.execute("CREATE TABLE _workflow_map (run_id VARCHAR, workflow_inferred VARCHAR)")
    workflow_rows = [(r, infer_workflow(r) if r else None)
                     for (r,) in con.execute("SELECT DISTINCT run_id FROM _runs_raw").fetchall()]
    if workflow_rows:
        con.executemany("INSERT INTO _workflow_map VALUES (?, ?)", workflow_rows)
    con.execute(
        "CREATE VIEW runs AS SELECT r.*, m.resolved_status, w.workflow_inferred FROM _runs_raw r "
        "LEFT JOIN _status_map m ON r.final_status IS NOT DISTINCT FROM m.final_status "
        "AND r.status IS NOT DISTINCT FROM m.status "
        "LEFT JOIN _workflow_map w ON r.run_id IS NOT DISTINCT FROM w.run_id"
    )
    return con


def run_query(con, sql: str) -> tuple[list[str], list[tuple]]:
    if not _READ_ONLY_START.match(sql) or ";" in sql.strip().rstrip(";"):
        raise ViewError("only a single read statement (SELECT, WITH, EXPLAIN, DESCRIBE, SHOW, SUMMARIZE) is accepted")
    cur = con.execute(sql)
    return [d[0] for d in cur.description], cur.fetchall()


def _print_table(cols: list[str], rows: list[tuple], out=sys.stdout) -> None:
    out.write("\t".join(cols) + "\n")
    for row in rows:
        out.write("\t".join("" if v is None else str(v) for v in row) + "\n")


def main(argv: list[str] | None = None, out=sys.stdout, err=sys.stderr) -> int:
    parser = argparse.ArgumentParser(description="DuckDB view over the agent-monitoring shards (read-only).")
    parser.add_argument("--data-root", default=str(DEFAULT_DATA_ROOT))
    sub = parser.add_subparsers(dest="cmd", required=True)
    sub.add_parser("list", help="print the view names and the named queries")
    q = sub.add_parser("query", help="run one read statement against the views")
    q.add_argument("sql")
    e = sub.add_parser("explain", help="EXPLAIN ANALYZE a named query")
    e.add_argument("name", choices=sorted(NAMED_QUERIES))
    args = parser.parse_args(argv)

    if args.cmd == "list":
        out.write("views: " + ", ".join(_COLUMNS) + "\nnamed queries:\n")
        for name in NAMED_QUERIES:
            out.write(f"  {name}\n")
        return 0
    try:
        con = connect(Path(args.data_root))
    except ImportError:
        err.write("duckdb is not importable; install the pinned dependency (pyproject.toml) to use this view.\n")
        return 0
    except Exception as exc:  # noqa: BLE001 - a monitoring tool never fails a workflow
        err.write(f"duckdb_view: could not build the views: {exc}\n")
        return 0
    try:
        sql = args.sql if args.cmd == "query" else "EXPLAIN ANALYZE " + NAMED_QUERIES[args.name]
        cols, rows = run_query(con, sql)
    except ViewError as exc:
        err.write(f"duckdb_view: {exc}\n")
        return 2
    except Exception as exc:  # noqa: BLE001
        err.write(f"duckdb_view: query failed: {exc}\n")
        return 1
    if args.cmd == "explain":
        for _, plan in rows:
            out.write(plan + "\n")
    else:
        _print_table(cols, rows, out)
    return 0


if __name__ == "__main__":
    sys.exit(main())
