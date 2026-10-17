---
status: active
layer: performance
authority: P2
audience: agent
artifact_type: test_plan
ticket_id: TCK-20261016-PERF-CORPUS-BASELINES-ON-LIFECYCLE-RECORDS
date: 2026-10-18
tags: [performance, benchmarking]
---

# Test plan: TCK-20261016-PERF-CORPUS-BASELINES-ON-LIFECYCLE-RECORDS

No heavy run. Scoped runs: `tests/unit/perf`, `tests/tools/test_corpus_perf_baseline.py`, `tools/perf/baseline_lifecycle.py check`, tools perf/baseline/inventory tests, docs checks, paths guard.

| Case | Test | Expect |
|---|---|---|
| normal | corpus test with `crowded_frontier.json` removed | passes via the record |
| normal | raw-dict worlds | fixed key set present |
| edge | a world gains a `.v0001.json` | the test takes the record branch (tmp baselines dir) |
| failure | `--commit` passed | argparse exit 2 |
| failure | a module writes `simq_corpus_*.json` | pin test fails (mutation check: add one in a scratch copy, see it fail for that reason) |
| regression | `LEGACY_TRIPWIRE_REFERENCES` length | 8; `check` rc=0 |
| regression | `idle_100_local.json` absent | corpus test still passes (simulated in a scratch baselines dir) |
