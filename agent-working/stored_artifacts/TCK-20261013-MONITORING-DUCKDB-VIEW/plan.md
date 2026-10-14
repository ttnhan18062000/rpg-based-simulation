---
status: historical
layer: ai
authority: P2
audience: agent
ticket_id: TCK-20261013-MONITORING-DUCKDB-VIEW
artifact_type: plan
tags: [ai, governance]
---

# plan — TCK-20261013-MONITORING-DUCKDB-VIEW

1. Compare with build_index.py and the loaders.
2. Build views with read_json over shard_paths(); reuse the Python helpers by import.
3. CLI with read-only guard; named queries.
4. Measure on real data; record the doc.
5. Tests.
