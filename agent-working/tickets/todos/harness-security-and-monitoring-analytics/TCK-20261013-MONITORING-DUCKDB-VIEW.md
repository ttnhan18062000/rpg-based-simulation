---
status: active
layer: ai
authority: P2
audience: agent
ticket_id: TCK-20261013-MONITORING-DUCKDB-VIEW
phase: open
date: 2026-10-13
tags: [ai, agent-monitoring, performance]
---

# TCK-20261013-MONITORING-DUCKDB-VIEW

## Title
A DuckDB view over the agent-monitoring JSONL shards (runs, events, gate verdicts), with EXPLAIN ANALYZE on the main retro queries

## Status
OPEN

## Tier
standard

## Type
feature

## Priority
P2

## Request Summary
The owner accepted lead-planner-u24's recommendation (item 4b) on 2026-10-13 and confirmed it in the
agent-working-planner terminal. The request: one queryable view over the per-week, per-session JSONL shards, as the
base for a later outcome-eval harness (gate pass rate and rework rate per agent and prompt version). `duckdb>=1.0.0`
is already in `pyproject.toml`. It is not installed in this host's `.venv` today, so install it from the existing pin;
no new dependency is added.

Prior art to reuse, not duplicate: `tools/agent-monitoring/build_index.py` (TCK-20260713-MONITORING-SQLITE-INDEX)
builds a read-only SQLite index from the old top-level `runs/events/tools.jsonl`. `query.py` reads it.
`monitoring_shard_paths.py` and the shard-aware loaders used by `generate_retro.py` (TCK-20261001) know the
`data/YYYY-Www/<batch>.{runs,events,gate_verdicts,...}.jsonl` layout.

## Scope
1. Investigate first, recording the results in investigation.md:
   - Does `build_index.py` read the per-week shards today, or only the old top-level files?
   - Which retro queries does `generate_retro.py` run, and how long do they take today?
   - Decide whether DuckDB complements the SQLite index or should later replace it. Replacing is out of scope here;
     record the recommendation.
2. `tools/agent-monitoring/duckdb_view.py`: build an in-memory or gitignored DuckDB database. Use `read_json` over the
   shard globs, found through `monitoring_shard_paths.py`, and define views `runs`, `events` and `gate_verdicts` with
   the same normalization as the SQLite index. Reuse `_resolve_status` and the other helpers by import; never
   re-implement them. Read-only toward the shards. The `.duckdb` file, if one is written, goes under the existing
   gitignored `agent-working/.index/`.
3. A CLI: `python3 tools/agent-monitoring/duckdb_view.py query "<sql>"` and
   `... explain <named-query>`. Name 3-5 queries: runs per week by status, gate pass rate per gate, rework rate (runs
   per ticket > 1) per agent, and the main retro aggregates.
4. Record `EXPLAIN ANALYZE` for each named query on this host's real data in
   `docs/agent-monitoring/duckdb_view.md`. Give the row counts, timings, host spec and commit, and compare with the
   current loader path for the same aggregates.
5. Tests in `tests/tools/`: the views over a small fixture shard set (two weeks, two batches, legacy and current record
   shapes) return the expected counts; the views never write to the fixture directory; the tool exits cleanly with a
   message when duckdb is not importable. Monitoring tools must never fail a workflow.

## Out of Scope
- The outcome-eval harness itself, and prompt-version tracking (later tickets).
- Replacing or removing `build_index.py` or `query.py`.
- Any CI job.

## Acceptance Criteria
- AC1: the three views load every current-week and past-week shard. Row counts match the shard-aware loaders for the
  same data.
- AC2: the named queries run, and their EXPLAIN ANALYZE output with timings is recorded in the doc, with host and commit.
- AC3: the tests pass. The no-write-to-shards check and the missing-duckdb path are covered.
- AC4: investigation.md states how this relates to the SQLite index, with a recommendation.

## Related Tickets
- TCK-20260713-MONITORING-SQLITE-INDEX; TCK-20261001-MONITORING-WEEK-CLOSE-COMMAND; TCK-20260607-MON-SCHEMA.

## Related Docs
- docs/agent-monitoring/schema.md; docs/guides/agent_monitoring.md.

## Related Stored Artifacts
- agent-working/stored_artifacts/TCK-20261013-MONITORING-DUCKDB-VIEW/ (created at close)

## Related Code Areas
- tools/agent-monitoring/{build_index,query,generate_retro,monitoring_shard_paths,gate_verdicts}.py, tests/tools/

## Assumptions / Open Questions
- Host: u24desktop. Timings are for this host only and are a dated record, not a gate.

## Implementation Notes

## Test Summary

## Files Changed

## Completion Summary
