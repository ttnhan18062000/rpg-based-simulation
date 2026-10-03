---
status: historical
layer: performance
authority: P2
audience: agent
ticket_id: TCK-20261004-PERF-LATEST-JSON-SINGLE-WRITER
phase: done
date: 2026-10-04
tags: [performance, benchmarking]
---

# TCK-20261004-PERF-LATEST-JSON-SINGLE-WRITER

## Title
Give `reports/perf/latest.json` one writer and one shape, and make `perf_baseline.py --update` refuse to promote anything else

## Status
DONE

## Tier
hotfix

## Type
bug

## Priority
P2

## Request Summary
Finding 5 of `docs/performance/benchmark_identity_schema.md` §1 (row F7). Two scripts write `reports/perf/latest.json` in incompatible shapes:
- `tools/perf/run_perf_baseline.py` writes a scenario-keyed dict of `BenchHarness` result dicts (`IDLE_100` … `MIXED_1000`).
- `tests/perf/bench_worker_throughput.py` (lines ~70-75) writes one flat worker-throughput dict (`entity_count`, `duration_ms`, `throughput_ips`, …).

`tools/perf/perf_baseline.py` makes it worse. Its default run step executes `bench_worker_throughput.py`, and its `--update` step copies whatever `latest.json` holds to `reports/perf/baseline.json` without checking the shape. `tools/release/generate_optimization_proof.py` reads `baseline.json` as the scenario-keyed shape. If the flat shape is promoted, every lookup misses and silently falls back to `1.0`, which the next ticket in this batch fixes on the reader side. This ticket fixes the writer side.

## Scope
1. `tests/perf/bench_worker_throughput.py`: write its report to its own file, `reports/perf/worker_throughput.json`, and nothing to `latest.json`. Keep its stdout behavior and `--json` flag
2. `tools/perf/perf_baseline.py`:
   - The run step invokes `tools/perf/run_perf_baseline.py`, the scenario-keyed writer, instead of `bench_worker_throughput.py`.
   - `--update` validates `latest.json` before copying. It must be a non-empty dict whose every value is a dict carrying at least `scenario_id`, `profile`, `sample_ticks`, `compute_tps` (or `avg_tps`), `tick_ms` and `mem_rss_mb`, each `scenario_id` equal to its key. If validation fails, exit non-zero with a message naming the first offending key, and leave `baseline.json` untouched.
   - Replace `datetime.utcnow()` with a timezone-aware equivalent; it is deprecated.
3. Tests, in `tests/tools/test_perf_baseline_tool.py` (new). Use `tmp_path` and `monkeypatch` only, and never run a benchmark. Cover:
   - `--update` with a valid scenario-keyed file copies it;
   - the flat worker-throughput shape is refused with a non-zero exit and `baseline.json` unchanged;
   - an empty dict is refused;
   - a missing `latest.json` exits non-zero;
   - the run step builds a command naming `run_perf_baseline.py`. Patch `subprocess.run` and assert on the call, without executing it;
   - `bench_worker_throughput.py`'s output path constant (or equivalent) is `worker_throughput.json`. A static or source-level assertion is acceptable, so the script never has to run.
4. Register the new owner, so changes to `perf_baseline.py` are scoped to its test:
   - add `"perf_baseline.py": "tests/tools/"` to `_TOOLS_PERF_BASENAME_MAP` in `tools/gate_checks/test_scope_coverage_static.py`;
   - add the module to the `tests/tools/` override list in the `tools/perf/*.py` row of `.claude/agents/test-scoper.md`, and remove it from the no-dedicated-test list there;
   - update any test that pins either list (`tests/tools/test_test_scope_coverage_static.py`).
5. In `docs/performance/benchmark_identity_schema.md`, add one line under §1 finding 5 and in the F7 row: "fixed by `TCK-20261004-PERF-LATEST-JSON-SINGLE-WRITER`", with what changed. Do not rewrite the finding

## Out of Scope
- Running any benchmark, baseline or profile script for real, or producing any performance number (RPG-core entry gate)
- Any edit under `src/`
- Changing what `run_perf_baseline.py` measures (scenarios, profiles, tick counts)
- Committing any file under `reports/`

## Acceptance Criteria
- [x] Only `run_perf_baseline.py` writes `reports/perf/latest.json` (verified by `grep -rn "latest.json" tools/ tests/`)
- [x] `perf_baseline.py --update` refuses a non-scenario-keyed file and leaves `baseline.json` unchanged; the tests prove it without running a benchmark
- [x] `pytest tests/tools/test_perf_baseline_tool.py tests/tools/test_test_scope_coverage_static.py tests/tools/test_tools_orphan_check.py tests/static -q` passes
- [x] No file under `reports/` or `data/runs/` is committed

## Related Tickets
- TCK-20261003-PERF-M2-T02-BENCHMARK-IDENTITY-SCHEMA (finding 5, row F7)
- TCK-20261004-PERF-OPTIMIZATION-PROOF-HONEST-CLAIMS (the reader side, same batch)

## Related Docs
- `docs/performance/benchmark_identity_schema.md` §1

## Related Stored Artifacts
- `agent-working/stored_artifacts/TCK-20261003-PERF-M2-T02-BENCHMARK-IDENTITY-SCHEMA/`

## Related Code Areas
- `tools/perf/perf_baseline.py`, `tools/perf/run_perf_baseline.py`, `tests/perf/bench_worker_throughput.py`, `tools/gate_checks/test_scope_coverage_static.py`, `.claude/agents/test-scoper.md`

## Assumptions / Open Questions
- Owner approved this tools-only batch on 2026-10-04 while the entry gate and the `src/` freeze hold.

## Implementation Notes
- `perf_baseline.py` now exposes `validate_latest()`, `run_benchmarks()`, `update_baseline()` and `main(argv)` returning an exit code; the `__main__` guard does `sys.exit(main())`. Validation runs before the timestamp is added. Required keys: scenario_id (equal to its dict key), profile, sample_ticks, tick_ms, mem_rss_mb, and compute_tps or avg_tps. Unparseable JSON is also refused.
- `bench_worker_throughput.py` gets `REPORT_FILENAME = "worker_throughput.json"`; stdout and `--json` unchanged.
- Scope map: `perf_baseline.py` added to `_TOOLS_PERF_BASENAME_MAP` and the test-scoper.md tools/perf row; one parametrized case added to `test_test_scope_coverage_static.py`.
- Schema doc: one "Fixed by" line under finding 5 and in the F7 row.
- Not run: any benchmark, baseline or proof script.

## Test Summary
199 passed, 2 skipped, 1 xfailed: tests/tools/test_perf_baseline_tool.py (11 new), test_test_scope_coverage_static.py, test_tools_orphan_check.py, test_perf_tag_test_scoper_wiring.py, tests/static, tests/docs (not slow). `grep -rn latest.json tools tests` shows only run_perf_baseline.py as writer.

## Files Changed
- tools/perf/perf_baseline.py, tests/perf/bench_worker_throughput.py
- tests/tools/test_perf_baseline_tool.py (new), tests/tools/test_test_scope_coverage_static.py
- tools/gate_checks/test_scope_coverage_static.py, .claude/agents/test-scoper.md
- docs/performance/benchmark_identity_schema.md (two Fixed-by lines)
- this ticket, docs/REGISTRY.yaml, monitoring shards

## Completion Summary
latest.json has one writer and one shape; perf_baseline.py --update refuses anything else.
