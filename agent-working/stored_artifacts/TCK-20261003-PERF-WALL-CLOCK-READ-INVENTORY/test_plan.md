---
status: active
layer: performance
authority: P2
audience: agent
artifact_type: test_plan
ticket_id: TCK-20261003-PERF-WALL-CLOCK-READ-INVENTORY
date: 2026-10-03
tags: [performance, determinism, engine]
---

# Test Plan: TCK-20261003-PERF-WALL-CLOCK-READ-INVENTORY

## Scanner tests
`tests/tools/test_wall_clock_inventory.py` (16): direct, `from time import perf_counter as pc`, `import datetime as dt`,
`datetime.datetime.now` chains, `from datetime import datetime as DT`; source kinds; guards (if, conditional expression)
as written; environment variable names; unresolved receivers listed not guessed; non-reads ignored; prefilter skip;
import-graph reachability; stable ordering and numbering; `--check` pass (including a line shift), fail (added/removed read),
unreadable file; `--update-doc` rewrites only the block and refuses a document without markers; a real-`src` test that
parses everything and finds the PERF-D1 reads by function name (no line numbers, no totals); CLI byte-identical runs and
a check that running the script imports no `src` module.

## Completeness check against a text search (how it was done, repeatable)
For each source family, search `src/` line by line for: `time.time`, `perf_counter`, `monotonic`, `process_time`, `thread_time`,
`datetime.now|utcnow|today`, `date.today`, `getloadavg|cpu_count|sched_getaffinity`, `getrusage|get_traced_memory|gc.get_count|gc.get_stats`,
`psutil.`, `os.environ|getenv|environ`, `urandom|uuid.uuid1|uuid.uuid4|SystemRandom|random.seed`; skip comment lines; compare
`(file, line)` with the JSON report. Result on this tree: every match is a recorded read except `src/engine/observability.py:76`
(`except (psutil.NoSuchProcess, psutil.AccessDenied)`, an exception class). Also searched for module-level `random.<fn>(` and `secrets.`: none.

## Proof Plan

- Level: unit (scanner) plus document evidence.
- Proof kind: synthetic-source tests, a real-source property test, a determinism check, and a text-search comparison.
- Oracle source: hand-written synthetic modules with known reads; the line-by-line search above.
- Expected effect: the scanner reports each call form, kind, guard and environment name correctly and reproducibly.
- Selected commands: `pytest tests/tools/test_wall_clock_inventory.py tests/tools/test_test_scope_coverage_static.py tests/tools/test_hash_callsite_inventory.py tests/tools/test_perf_threshold_inventory.py -p no:cacheprovider`; `python3 tools/perf/wall_clock_inventory.py --check docs/performance/wall_clock_inventory.json`.
