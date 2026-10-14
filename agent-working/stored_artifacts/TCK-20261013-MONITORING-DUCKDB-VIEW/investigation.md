---
status: historical
layer: ai
authority: P2
audience: agent
ticket_id: TCK-20261013-MONITORING-DUCKDB-VIEW
artifact_type: investigation
tags: [ai, governance]
---

# investigation — TCK-20261013-MONITORING-DUCKDB-VIEW

- build_index.py reads all three kinds through `load_data_glob` -> `shard_paths`, so it already sees the per-week shards. It has no gate_verdicts and needs a full rebuild; query.py filters records.
- generate_retro loads with the same shard-aware loaders and aggregates in Python; `_resolve_status` is a one-line fallback (final_status or status).
- Recommendation: DuckDB complements the SQLite index (aggregates, gate verdicts, always current). Replacing the SQLite index is out of scope; it would need query.py's filters rewritten as SQL first.
- Python/numpy: a DuckDB UDF needs numpy; not declared, so the helpers run on distinct values in Python.
