---
status: historical
layer: ai
authority: P2
audience: agent
ticket_id: TCK-20261013-MONITORING-DUCKDB-VIEW
artifact_type: test_plan
tags: [ai, governance]
---

# test_plan — TCK-20261013-MONITORING-DUCKDB-VIEW

## Cases
- row counts equal the shard-aware loaders (two weeks, bare and per-batch files, legacy and current shapes)
- resolved_status equals `_resolve_status` for every run
- the data root is byte-identical after building views and running queries
- non-read statements are refused; EXPLAIN works; missing duckdb exits 0 with one line

## Proof Plan
- level: unit tests on fixture shards plus measurements on the real data
- proof kind: behavioural tests and recorded timings
- oracle source: ticket acceptance criteria AC1-AC4
- expected effect: the views agree with the existing loaders and never write
- selected commands: `pytest tests/tools/test_duckdb_view.py`; `python3 tools/agent-monitoring/duckdb_view.py explain <name>`
