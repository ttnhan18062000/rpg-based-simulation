---
status: active
layer: performance
authority: P2
audience: agent
ticket_id: TCK-20261028-PARITY-INFRA-430-431-PERF-SCHEMA-DRIFT
artifact_type: investigation
tags: [benchmarking]
---

# Investigation

Code at origin/main fdfc5f9fd: SCHEMA_VERSION = "1.4" (src/perf/benchmark_record.py:59); LEGACY_TRIPWIRE_REFERENCES = 6 files (tools/perf/baseline_lifecycle.py:54): mixed_200_concurrent, mixed_200_local, simq_corpus_frontier_extended, simq_corpus_frontier_marches, strategic_100_concurrent, strategic_100_local. tests/perf/baselines holds exactly those 6 non-versioned files. compare() treats only a MAJOR schema_version mismatch as INCONCLUSIVE (benchmark_record.py:820). INFRA-430 said schema 1.0; INFRA-431 said 15 files (also in its support_boundary).
