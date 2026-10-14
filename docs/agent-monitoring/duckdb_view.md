---
status: active
layer: observability
authority: P2
audience: agent
date: 2026-10-13
tags: [observability, agent-monitoring, performance]
---

# Agent-monitoring DuckDB view

Ticket: TCK-20261013-MONITORING-DUCKDB-VIEW. Tool: `tools/agent-monitoring/duckdb_view.py`.

## What it is

An in-memory DuckDB database with four views (`runs`, `events`, `tools`, `gate_verdicts`) over the
`data/<ISO-week>/[<id>.]<kind>.jsonl` shards, read with `read_json`. Shard discovery is
`monitoring_shard_paths.shard_paths()`. Nothing is written: the database is in memory, the shards are only read and the
`query` command accepts one read statement (SELECT, WITH, EXPLAIN, DESCRIBE, SHOW, SUMMARIZE). `runs` adds `week` (the
shard directory), `resolved_status` (from `generate_retro._resolve_status`) and `workflow_inferred` (from
`vocabulary.infer_workflow`). The other views add `week`. If `duckdb` cannot be imported the tool prints one line and
exits 0.

```
python3 tools/agent-monitoring/duckdb_view.py list
python3 tools/agent-monitoring/duckdb_view.py query "SELECT week, count(*) FROM runs GROUP BY 1 ORDER BY 1"
python3 tools/agent-monitoring/duckdb_view.py explain gate_pass_rate_per_gate
```

Run it with an interpreter that has `duckdb` (the main checkout's `.venv` does: duckdb 1.5.3, from the `pyproject.toml`
pin `duckdb>=1.0.0`; no new dependency was added).

Fields not read by a view are ignored, and a value of the wrong type in an old record becomes NULL, so legacy and
current record shapes share one view. `gate_verdicts` rows with `row_kind` set are outcome and adjudication rows;
`gate_pass_rate_per_gate` counts verdict rows only (`row_kind IS NULL`). "Agent" in `rework_rate_per_agent` is the run's
`session_role`, which only 267 of the 2306 runs carry; the rest group under `(none)`.

## Relation to the SQLite index

`build_index.py` already reads the per-week shards (through `validate.load_data_glob`, which uses
`shard_paths()`), so it is not limited to old top-level files. It stores one raw-JSON row per record with a few indexed
columns (`runs`, `events`, `tools`), has no gate verdicts, needs a full rebuild, and is queried through `query.py`
filters. DuckDB reads the shards directly (no build step, always current) and answers aggregates in SQL. Recommendation:
keep both for now. The SQLite index serves `query.py`'s record lookups; use this view for aggregates and for the later
outcome-eval harness (which needs `gate_verdicts`). Replacing the SQLite index is out of scope; if it is ever done, `query.py`'s
filters would have to be reimplemented as SQL first.

## Measurements

Host: u24desktop (Intel Core i5-10400, 6 vCPUs, 8 GB RAM), Linux 7.0.0-38-generic, Python 3.13 venv,
duckdb 1.5.3. Code at commit b98dfcd97 plus this ticket's uncommitted files. Data as of 2026-10-13: runs 2306 rows,
events 14841, tools 272468, gate_verdicts 398, across 159/159/105/106 shard files (the `tools` shards are 105 MB).
Row counts equal the shard-aware loaders (`validate.load_data_glob`) for `runs`, `events` and `tools`, and the line
count of every `gate_verdicts` shard (the `tools` shards keep growing while a session works, so counts were compared in
one process). Status counts and per-tool counts also match the Python Counters. Timings are a dated record for this host, not a gate.

| named query | result rows | EXPLAIN ANALYZE total (s) | plain run, best of 3 (s) | Python loader path (s) |
|---|---|---|---|---|
| `runs_per_week_by_status` | 103 | 0.0423 | 0.015 | 0.0007 (Counter over `_resolve_status`, after a 0.023 load) |
| `gate_pass_rate_per_gate` | 12 | 0.0127 | 0.006 | no loader aggregate exists; `gate_verdicts` has no retro loader |
| `rework_rate_per_agent` | 11 | 0.0496 | 0.018 | 0.0005 (Counter over `ticket_id`, after the 0.023 load; per-agent split not done) |
| `retro_runs_by_workflow_and_tier` | 24 | 0.0242 | 0.015 | not timed separately; `generate_retro.py` runs several passes over the same list |
| `tool_calls_per_tool` | 20 | 0.222 | 0.129 | 0.089 (Counter over `tool`, after a 1.43 load) |

Other numbers: building the views (the first touch of the `runs` shards, to fill the status and workflow maps) took
2.1 s; `count(*)` of `runs`, `events`, `tools`, `gate_verdicts`: 0.017, 0.016, 0.223, 0.007 s. Loading all `tools` shards
with `load_data_glob` took 1.43 s, `runs` 0.023 s.

Reading: DuckDB answers every named query in at most 0.13 s, and avoids the 1.4 s `tools` load that the Python path pays
before it can count anything. For `runs` alone the Python path is already fast (0.023 s load) and the SQL path has no
advantage in time, only in gate verdicts and ad-hoc SQL.

## EXPLAIN ANALYZE output

### runs_per_week_by_status

```
┌─────────────────────────────────────┐
│┌───────────────────────────────────┐│
││    Query Profiling Information    ││
│└───────────────────────────────────┘│
└─────────────────────────────────────┘
EXPLAIN ANALYZE SELECT week, coalesce(resolved_status, '(none)') AS status, count(*) AS runs FROM runs GROUP BY 1, 2 ORDER BY 1, 3 DESC
┌────────────────────────────────────────────────┐
│┌──────────────────────────────────────────────┐│
││              Total Time: 0.0423s             ││
│└──────────────────────────────────────────────┘│
└────────────────────────────────────────────────┘
┌───────────────────────────┐
│           QUERY           │
└─────────────┬─────────────┘
┌─────────────┴─────────────┐
│      EXPLAIN_ANALYZE      │
│    ────────────────────   │
│                           │
│           0 rows          │
│           0.00s           │
└─────────────┬─────────────┘
┌─────────────┴─────────────┐
│          ORDER_BY         │
│    ────────────────────   │
│          week ASC         │
│         runs DESC         │
│                           │
│                           │
│                           │
│          103 rows         │
│           0.00s           │
└─────────────┬─────────────┘
┌─────────────┴─────────────┐
│       HASH_GROUP_BY       │
│    ────────────────────   │
│          Groups:          │
│             #0            │
│             #1            │
│                           │
│        Aggregates:        │
│        count_star()       │
│                           │
│                           │
│                           │
│          103 rows         │
│           0.00s           │
└─────────────┬─────────────┘
┌─────────────┴─────────────┐
│         PROJECTION        │
│    ────────────────────   │
│            week           │
│           status          │
│                           │
│                           │
│                           │
│         2,306 rows        │
│           0.00s           │
└─────────────┬─────────────┘
┌─────────────┴─────────────┐
│         PROJECTION        │
│    ────────────────────   │
│            week           │
│      resolved_status      │
│                           │
│                           │
│                           │
│         2,306 rows        │
│           0.00s           │
└─────────────┬─────────────┘
┌─────────────┴─────────────┐
│         HASH_JOIN         │
│    ────────────────────   │
│      Join Type: LEFT      │
│                           │
│        Conditions:        │
│   run_id IS NOT DISTINCT  │
│         FROM run_id       ├───────────────────────────────────────────┐
│                           │                                           │
│                           │                                           │
│                           │                                           │
│         2,306 rows        │                                           │
│           0.00s           │                                           │
└─────────────┬─────────────┘                                           │
┌─────────────┴─────────────┐                             ┌─────────────┴─────────────┐
│         HASH_JOIN         │                             │         TABLE_SCAN        │
│    ────────────────────   │                             │    ────────────────────   │
│      Join Type: LEFT      │                             │           Table:          │
│                           │                             │ memory.main._workflow_map │
│        Conditions:        │                             │                           │
│    final_status IS NOT    │                             │   Type: Sequential Scan   │
│ DISTINCT FROM final_status│                             │    Projections: run_id    │
│   status IS NOT DISTINCT  ├──────────────┐              │                           │
│         FROM status       │              │              │                           │
│                           │              │              │                           │
│                           │              │              │                           │
│                           │              │              │           0.00s           │
│         2,306 rows        │              │              │         2,117 rows        │
│           0.01s           │              │              │          (0.00s)          │
└─────────────┬─────────────┘              │              └───────────────────────────┘
┌─────────────┴─────────────┐┌─────────────┴─────────────┐
│         PROJECTION        ││         TABLE_SCAN        │
│    ────────────────────   ││    ────────────────────   │
│           run_id          ││           Table:          │
│        final_status       ││  memory.main._status_map  │
│           status          ││                           │
│            week           ││   Type: Sequential Scan   │
│                           ││                           │
│                           ││        Projections:       │
│                           ││        final_status       │
│                           ││           status          │
│           0.00s           ││      resolved_status      │
│                           ││                           │
│                           ││                           │
│                           ││                           │
│         2,306 rows        ││          34 rows          │
│          (0.00s)          ││           0.00s           │
└─────────────┬─────────────┘└───────────────────────────┘
┌─────────────┴─────────────┐
│         TABLE_SCAN        │
│    ────────────────────   │
│    Function: READ_JSON    │
│                           │
│        Projections:       │
│           run_id          │
│        final_status       │
│           status          │
│          filename         │
│                           │
│   Total Files Read: 159   │
│                           │
│        Filename(s):       │
│    agent-working/agent    │
│ -monitoring/data/2026-W23 │
│ /runs.jsonl, agent-working│
│   /agent-monitoring/data  │
│   /2026-W24/runs.jsonl,   │
│     agent-working/agent   │
│ -monitoring/data/2026-W25 │
│ /runs.jsonl, agent-working│
│   /agent-monitoring/data  │
│   /2026-W26/runs.jsonl,   │
│     agent-working/agent   │
│ -monitoring/data/2026-W27 │
│      /runs.jsonl, ...     │
│                           │
│                           │
│                           │
│         2,306 rows        │
│           0.15s           │
└───────────────────────────┘
```

### gate_pass_rate_per_gate

```
┌─────────────────────────────────────┐
│┌───────────────────────────────────┐│
││    Query Profiling Information    ││
│└───────────────────────────────────┘│
└─────────────────────────────────────┘
EXPLAIN ANALYZE SELECT gate_id, count(*) AS verdicts, count(*) FILTER (WHERE verdict = 'PASS') AS passed, round(100.0 * count(*) FILTER (WHERE verdict = 'PASS') / count(*), 1) AS pass_pct FROM gate_verdicts WHERE row_kind IS NULL GROUP BY 1 ORDER BY verdicts DESC
┌────────────────────────────────────────────────┐
│┌──────────────────────────────────────────────┐│
││              Total Time: 0.0127s             ││
│└──────────────────────────────────────────────┘│
└────────────────────────────────────────────────┘
┌───────────────────────────┐
│           QUERY           │
└─────────────┬─────────────┘
┌─────────────┴─────────────┐
│      EXPLAIN_ANALYZE      │
│    ────────────────────   │
│                           │
│           0 rows          │
│           0.00s           │
└─────────────┬─────────────┘
┌─────────────┴─────────────┐
│          ORDER_BY         │
│    ────────────────────   │
│     count_star() DESC     │
│                           │
│                           │
│                           │
│          12 rows          │
│           0.00s           │
└─────────────┬─────────────┘
┌─────────────┴─────────────┐
│         PROJECTION        │
│    ────────────────────   │
│             0             │
│          verdicts         │
│           passed          │
│          pass_pct         │
│                           │
│                           │
│                           │
│          12 rows          │
│           0.00s           │
└─────────────┬─────────────┘
┌─────────────┴─────────────┐
│       HASH_GROUP_BY       │
│    ────────────────────   │
│         Groups: #0        │
│                           │
│        Aggregates:        │
│        count_star()       │
│ count_star() FILTER (WHERE│
│       #0) Filter: #0      │
│                           │
│                           │
│                           │
│          12 rows          │
│           0.00s           │
└─────────────┬─────────────┘
┌─────────────┴─────────────┐
│         PROJECTION        │
│    ────────────────────   │
│          gate_id          │
│     (verdict = 'PASS')    │
│                           │
│                           │
│                           │
│          348 rows         │
│           0.00s           │
└─────────────┬─────────────┘
┌─────────────┴─────────────┐
│         PROJECTION        │
│    ────────────────────   │
│             #0            │
│             #1            │
│                           │
│                           │
│                           │
│          348 rows         │
│           0.00s           │
└─────────────┬─────────────┘
┌─────────────┴─────────────┐
│           FILTER          │
│    ────────────────────   │
│     (row_kind IS NULL)    │
│                           │
│                           │
│                           │
│          348 rows         │
│           0.00s           │
└─────────────┬─────────────┘
┌─────────────┴─────────────┐
│         TABLE_SCAN        │
│    ────────────────────   │
│    Function: READ_JSON    │
│                           │
│        Projections:       │
│          gate_id          │
│          verdict          │
│          row_kind         │
│                           │
│   Total Files Read: 106   │
│                           │
│        Filename(s):       │
│    agent-working/agent    │
│ -monitoring/data/2026-W41 │
│ /agent-working-batch-image│
│      -and-gate-ledger     │
│   .gate_verdicts.jsonl,   │
│     agent-working/agent   │
│ -monitoring/data/2026-W41 │
│    /agent-working-disk    │
│      -headroom-guard      │
│   .gate_verdicts.jsonl,   │
│     agent-working/agent   │
│ -monitoring/data/2026-W41 │
│    /agent-working-disk    │
│      -incident-batch      │
│   .gate_verdicts.jsonl,   │
│     agent-working/agent   │
│ -monitoring/data/2026-W41 │
│    /agent-working-guard   │
│      -quoted-text-fix     │
│   .gate_verdicts.jsonl,   │
│     agent-working/agent   │
│ -monitoring/data/2026-W41 │
│  /agent-working-handover  │
│       -main-checkout      │
│ .gate_verdicts.jsonl, ... │
│                           │
│                           │
│                           │
│          398 rows         │
│           0.01s           │
└───────────────────────────┘
```

### rework_rate_per_agent

```
┌─────────────────────────────────────┐
│┌───────────────────────────────────┐│
││    Query Profiling Information    ││
│└───────────────────────────────────┘│
└─────────────────────────────────────┘
EXPLAIN ANALYZE WITH per_ticket AS (  SELECT coalesce(session_role, '(none)') AS agent, ticket_id, count(*) AS n   FROM runs WHERE ticket_id IS NOT NULL GROUP BY 1, 2) SELECT agent, count(*) AS tickets, count(*) FILTER (WHERE n > 1) AS reworked, round(100.0 * count(*) FILTER (WHERE n > 1) / count(*), 1) AS rework_pct FROM per_ticket GROUP BY 1 ORDER BY tickets DESC
┌────────────────────────────────────────────────┐
│┌──────────────────────────────────────────────┐│
││              Total Time: 0.0496s             ││
│└──────────────────────────────────────────────┘│
└────────────────────────────────────────────────┘
┌───────────────────────────┐
│           QUERY           │
└─────────────┬─────────────┘
┌─────────────┴─────────────┐
│      EXPLAIN_ANALYZE      │
│    ────────────────────   │
│                           │
│           0 rows          │
│           0.00s           │
└─────────────┬─────────────┘
┌─────────────┴─────────────┐
│          ORDER_BY         │
│    ────────────────────   │
│     count_star() DESC     │
│                           │
│                           │
│                           │
│          11 rows          │
│           0.00s           │
└─────────────┬─────────────┘
┌─────────────┴─────────────┐
│         PROJECTION        │
│    ────────────────────   │
│             0             │
│          tickets          │
│          reworked         │
│         rework_pct        │
│                           │
│                           │
│                           │
│          11 rows          │
│           0.00s           │
└─────────────┬─────────────┘
┌─────────────┴─────────────┐
│       HASH_GROUP_BY       │
│    ────────────────────   │
│         Groups: #0        │
│                           │
│        Aggregates:        │
│        count_star()       │
│ count_star() FILTER (WHERE│
│       #0) Filter: #0      │
│                           │
│                           │
│                           │
│          11 rows          │
│           0.00s           │
└─────────────┬─────────────┘
┌─────────────┴─────────────┐
│         PROJECTION        │
│    ────────────────────   │
│           agent           │
│          (n > 1)          │
│                           │
│                           │
│                           │
│         1,396 rows        │
│           0.00s           │
└─────────────┬─────────────┘
┌─────────────┴─────────────┐
│         PROJECTION        │
│    ────────────────────   │
│             0             │
│             n             │
│                           │
│                           │
│                           │
│         1,396 rows        │
│           0.00s           │
└─────────────┬─────────────┘
┌─────────────┴─────────────┐
│       HASH_GROUP_BY       │
│    ────────────────────   │
│          Groups:          │
│             #0            │
│             #1            │
│                           │
│        Aggregates:        │
│        count_star()       │
│                           │
│                           │
│                           │
│         1,396 rows        │
│           0.01s           │
└─────────────┬─────────────┘
┌─────────────┴─────────────┐
│         PROJECTION        │
│    ────────────────────   │
│           agent           │
│         ticket_id         │
│                           │
│                           │
│                           │
│         1,468 rows        │
│           0.00s           │
└─────────────┬─────────────┘
┌─────────────┴─────────────┐
│         PROJECTION        │
│    ────────────────────   │
│         ticket_id         │
│        session_role       │
│                           │
│                           │
│                           │
│         1,468 rows        │
│           0.00s           │
└─────────────┬─────────────┘
┌─────────────┴─────────────┐
│         HASH_JOIN         │
│    ────────────────────   │
│      Join Type: LEFT      │
│                           │
│        Conditions:        │
│   run_id IS NOT DISTINCT  │
│         FROM run_id       ├───────────────────────────────────────────┐
│                           │                                           │
│                           │                                           │
│                           │                                           │
│         1,468 rows        │                                           │
│           0.00s           │                                           │
└─────────────┬─────────────┘                                           │
┌─────────────┴─────────────┐                             ┌─────────────┴─────────────┐
│         HASH_JOIN         │                             │         TABLE_SCAN        │
│    ────────────────────   │                             │    ────────────────────   │
│      Join Type: LEFT      │                             │           Table:          │
│                           │                             │ memory.main._workflow_map │
│        Conditions:        │                             │                           │
│    final_status IS NOT    │                             │   Type: Sequential Scan   │
│ DISTINCT FROM final_status│                             │    Projections: run_id    │
│   status IS NOT DISTINCT  ├──────────────┐              │                           │
│         FROM status       │              │              │                           │
│                           │              │              │                           │
│                           │              │              │                           │
│                           │              │              │           0.00s           │
│         1,468 rows        │              │              │         2,117 rows        │
│           0.00s           │              │              │          (0.00s)          │
└─────────────┬─────────────┘              │              └───────────────────────────┘
┌─────────────┴─────────────┐┌─────────────┴─────────────┐
│           FILTER          ││         TABLE_SCAN        │
│    ────────────────────   ││    ────────────────────   │
│  (ticket_id IS NOT NULL)  ││           Table:          │
│                           ││  memory.main._status_map  │
│                           ││                           │
│                           ││   Type: Sequential Scan   │
│                           ││                           │
│           0.00s           ││        Projections:       │
│                           ││        final_status       │
│                           ││           status          │
│                           ││                           │
│                           ││                           │
│                           ││                           │
│         1,468 rows        ││          34 rows          │
│          (0.00s)          ││           0.00s           │
└─────────────┬─────────────┘└───────────────────────────┘
┌─────────────┴─────────────┐
│         TABLE_SCAN        │
│    ────────────────────   │
│    Function: READ_JSON    │
│                           │
│        Projections:       │
│           run_id          │
│         ticket_id         │
│        final_status       │
│           status          │
│        session_role       │
│                           │
│   Total Files Read: 159   │
│                           │
│        Filename(s):       │
│    agent-working/agent    │
│ -monitoring/data/2026-W23 │
│ /runs.jsonl, agent-working│
│   /agent-monitoring/data  │
│   /2026-W24/runs.jsonl,   │
│     agent-working/agent   │
│ -monitoring/data/2026-W25 │
│ /runs.jsonl, agent-working│
│   /agent-monitoring/data  │
│   /2026-W26/runs.jsonl,   │
│     agent-working/agent   │
│ -monitoring/data/2026-W27 │
│      /runs.jsonl, ...     │
│                           │
│                           │
│                           │
│         2,306 rows        │
│           0.17s           │
└───────────────────────────┘
```

### retro_runs_by_workflow_and_tier

```
┌─────────────────────────────────────┐
│┌───────────────────────────────────┐│
││    Query Profiling Information    ││
│└───────────────────────────────────┘│
└─────────────────────────────────────┘
EXPLAIN ANALYZE SELECT coalesce(workflow, workflow_inferred, '(none)') AS workflow, coalesce(tier, '(none)') AS tier, count(*) AS runs, round(avg(duration_s), 1) AS avg_duration_s, count(*) FILTER (WHERE resolved_status = 'DONE') AS done FROM runs GROUP BY 1, 2 ORDER BY runs DESC
┌────────────────────────────────────────────────┐
│┌──────────────────────────────────────────────┐│
││              Total Time: 0.0242s             ││
│└──────────────────────────────────────────────┘│
└────────────────────────────────────────────────┘
┌───────────────────────────┐
│           QUERY           │
└─────────────┬─────────────┘
┌─────────────┴─────────────┐
│      EXPLAIN_ANALYZE      │
│    ────────────────────   │
│                           │
│           0 rows          │
│           0.00s           │
└─────────────┬─────────────┘
┌─────────────┴─────────────┐
│          ORDER_BY         │
│    ────────────────────   │
│     count_star() DESC     │
│                           │
│                           │
│                           │
│          24 rows          │
│           0.00s           │
└─────────────┬─────────────┘
┌─────────────┴─────────────┐
│         PROJECTION        │
│    ────────────────────   │
│             0             │
│             1             │
│            runs           │
│       avg_duration_s      │
│            done           │
│                           │
│                           │
│                           │
│          24 rows          │
│           0.00s           │
└─────────────┬─────────────┘
┌─────────────┴─────────────┐
│       HASH_GROUP_BY       │
│    ────────────────────   │
│          Groups:          │
│             #0            │
│             #1            │
│                           │
│        Aggregates:        │
│        count_star()       │
│          avg(#2)          │
│ count_star() FILTER (WHERE│
│       #1) Filter: #1      │
│                           │
│                           │
│                           │
│          24 rows          │
│           0.00s           │
└─────────────┬─────────────┘
┌─────────────┴─────────────┐
│         PROJECTION        │
│    ────────────────────   │
│          workflow         │
│            tier           │
│         duration_s        │
│ (resolved_status = 'DONE')│
│                           │
│                           │
│                           │
│         2,306 rows        │
│           0.01s           │
└─────────────┬─────────────┘
┌─────────────┴─────────────┐
│         HASH_JOIN         │
│    ────────────────────   │
│      Join Type: LEFT      │
│                           │
│        Conditions:        │
│   run_id IS NOT DISTINCT  │
│         FROM run_id       ├───────────────────────────────────────────┐
│                           │                                           │
│                           │                                           │
│                           │                                           │
│         2,306 rows        │                                           │
│           0.00s           │                                           │
└─────────────┬─────────────┘                                           │
┌─────────────┴─────────────┐                             ┌─────────────┴─────────────┐
│         HASH_JOIN         │                             │         TABLE_SCAN        │
│    ────────────────────   │                             │    ────────────────────   │
│      Join Type: LEFT      │                             │           Table:          │
│                           │                             │ memory.main._workflow_map │
│        Conditions:        │                             │                           │
│    final_status IS NOT    │                             │   Type: Sequential Scan   │
│ DISTINCT FROM final_status│                             │                           │
│   status IS NOT DISTINCT  ├──────────────┐              │        Projections:       │
│         FROM status       │              │              │           run_id          │
│                           │              │              │     workflow_inferred     │
│                           │              │              │                           │
│                           │              │              │                           │
│                           │              │              │                           │
│           0.01s           │              │              │         2,117 rows        │
│          (0.01s)          │              │              │           0.00s           │
└─────────────┬─────────────┘              │              └───────────────────────────┘
┌─────────────┴─────────────┐┌─────────────┴─────────────┐
│         TABLE_SCAN        ││         TABLE_SCAN        │
│    ────────────────────   ││    ────────────────────   │
│    Function: READ_JSON    ││           Table:          │
│                           ││  memory.main._status_map  │
│        Projections:       ││                           │
│           run_id          ││   Type: Sequential Scan   │
│          workflow         ││                           │
│            tier           ││        Projections:       │
│        final_status       ││        final_status       │
│           status          ││           status          │
│         duration_s        ││      resolved_status      │
│                           ││                           │
│   Total Files Read: 159   ││                           │
│                           ││                           │
│        Filename(s):       ││                           │
│    agent-working/agent    ││           0.00s           │
│ -monitoring/data/2026-W23 ││                           │
│ /runs.jsonl, agent-working││                           │
│   /agent-monitoring/data  ││                           │
│   /2026-W24/runs.jsonl,   ││                           │
│     agent-working/agent   ││                           │
│ -monitoring/data/2026-W25 ││                           │
│ /runs.jsonl, agent-working││                           │
│   /agent-monitoring/data  ││                           │
│   /2026-W26/runs.jsonl,   ││                           │
│     agent-working/agent   ││                           │
│ -monitoring/data/2026-W27 ││                           │
│      /runs.jsonl, ...     ││                           │
│                           ││                           │
│                           ││                           │
│                           ││                           │
│         2,306 rows        ││          34 rows          │
│           0.06s           ││          (0.00s)          │
└───────────────────────────┘└───────────────────────────┘
```

### tool_calls_per_tool

```
┌─────────────────────────────────────┐
│┌───────────────────────────────────┐│
││    Query Profiling Information    ││
│└───────────────────────────────────┘│
└─────────────────────────────────────┘
EXPLAIN ANALYZE SELECT tool, count(*) AS calls FROM tools GROUP BY 1 ORDER BY calls DESC LIMIT 20
┌────────────────────────────────────────────────┐
│┌──────────────────────────────────────────────┐│
││              Total Time: 0.222s              ││
│└──────────────────────────────────────────────┘│
└────────────────────────────────────────────────┘
┌───────────────────────────┐
│           QUERY           │
└─────────────┬─────────────┘
┌─────────────┴─────────────┐
│      EXPLAIN_ANALYZE      │
│    ────────────────────   │
│                           │
│           0 rows          │
│           0.00s           │
└─────────────┬─────────────┘
┌─────────────┴─────────────┐
│           TOP_N           │
│    ────────────────────   │
│          Top: 20          │
│                           │
│         Order By:         │
│     count_star() DESC     │
│                           │
│                           │
│                           │
│          20 rows          │
│           0.00s           │
└─────────────┬─────────────┘
┌─────────────┴─────────────┐
│       HASH_GROUP_BY       │
│    ────────────────────   │
│         Groups: #0        │
│                           │
│        Aggregates:        │
│        count_star()       │
│                           │
│                           │
│                           │
│          53 rows          │
│           0.08s           │
└─────────────┬─────────────┘
┌─────────────┴─────────────┐
│         PROJECTION        │
│    ────────────────────   │
│            tool           │
│                           │
│                           │
│                           │
│        272,469 rows       │
│           0.00s           │
└─────────────┬─────────────┘
┌─────────────┴─────────────┐
│         TABLE_SCAN        │
│    ────────────────────   │
│    Function: READ_JSON    │
│     Projections: tool     │
│   Total Files Read: 105   │
│                           │
│        Filename(s):       │
│    agent-working/agent    │
│ -monitoring/data/2026-W24 │
│    /tools.jsonl, agent    │
│ -working/agent-monitoring │
│ /data/2026-W25/tools.jsonl│
│   , agent-working/agent   │
│ -monitoring/data/2026-W26 │
│    /tools.jsonl, agent    │
│ -working/agent-monitoring │
│ /data/2026-W27/tools.jsonl│
│   , agent-working/agent   │
│ -monitoring/data/2026-W28 │
│     /tools.jsonl, ...     │
│                           │
│                           │
│                           │
│        272,469 rows       │
│           0.91s           │
└───────────────────────────┘
```
