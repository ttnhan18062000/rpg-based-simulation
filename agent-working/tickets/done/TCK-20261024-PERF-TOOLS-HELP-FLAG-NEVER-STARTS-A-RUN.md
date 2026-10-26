---
status: historical
layer: performance
authority: P1
audience: agent
ticket_id: TCK-20261024-PERF-TOOLS-HELP-FLAG-NEVER-STARTS-A-RUN
phase: done
date: 2026-10-24
tags: [performance, benchmarking]
---

# TCK-20261024-PERF-TOOLS-HELP-FLAG-NEVER-STARTS-A-RUN

## Title
`--help` on a tools/perf script prints usage and exits; it never starts a benchmark

## Status
DONE

## Tier
hotfix

## Type
bug

## Priority
P2

## Request Summary
On 2026-10-24, `python3 tools/perf/perf_baseline.py --help` started a real `run_perf_baseline.py` suite on the shared
host. It ran outside the heavy-run slot and the load gate for about 2 min before it was killed by PID. The cause:
`perf_baseline.py:main` reads `sys.argv` by hand, treats anything that isn't `--update` as "run", and runs
`RUN_SCRIPT`. A static check of `tools/perf/` and `tools/bench_corpus_world.py` found four entry points with no
argument parser:
- `perf_baseline.py`
- `run_perf_baseline.py`
- `perf_report.py`
- `turbo_run.py`

## Scope
- Give each of the four an `argparse` parser. `--help` and `-h` print usage and exit 0 before any import of
  `src/`, any kernel construction and any subprocess.
- Unknown arguments exit 2 (argparse's default), so they never fall through to a run.
- Keep the existing behaviour for the documented invocations: `perf_baseline.py` with no args runs, `--update`
  promotes. Grep the Makefile, workflows, docs and tests for every invocation of the four and keep them working.
- Add a test (in `tests/unit/perf/`) that every `tools/perf/*.py` entry point with a `__main__` block, plus
  `tools/bench_corpus_world.py`, exits 0 on `--help` within a few seconds and spawns no child process. Run each in
  a subprocess with a short timeout, and fail if it times out or a known run artefact appears. This stops the
  problem recurring.

## Out of Scope
- Changing what any tool measures, or its defaults beyond argument handling.
- Tools outside `tools/perf/` and `tools/bench_corpus_world.py`. If the test pattern is useful repo-wide, route it
  to agent-working-designer (`tools/**`).

## Acceptance Criteria
- [x] `--help` and `-h` on all four exit 0, print usage and start no run (the test proves it).
- [x] An unknown flag exits non-zero without running.
- [x] The documented invocations behave as before (each one found by the grep is listed in the ticket).
- [x] The `--help` test covers every `__main__` entry point in `tools/perf/` plus `tools/bench_corpus_world.py`,
      and runs in under 30 s in total, with no heavy runs.
- [x] `python3 -m codebase.health check` reports OK.

## Related Tickets
- `TCK-20261004-PERF-LATEST-JSON-SINGLE-WRITER` (made `run_perf_baseline.py` the single writer of `latest.json`)

## Related Docs
- `docs/performance/perf_baseline_policy.md`

## Related Stored Artifacts
- none

## Related Code Areas
- `tools/perf/perf_baseline.py`, `run_perf_baseline.py`, `perf_report.py`, `turbo_run.py`
- `tests/unit/perf/`

## Assumptions / Open Questions
- `turbo_run.py` may be dead code. If nothing invokes it, say so in the Completion Summary rather than delete it here.

## Implementation Notes
- `perf_baseline.py`: `build_parser()` with `--update`; `main(argv)` parses first, so `--help` and unknown flags exit before `run_benchmarks()`. The `main(["--update"])` call the existing tests make is unchanged.
- `perf_report.py`: a `main(argv)` with a no-argument parser, called from `__main__`.
- `run_perf_baseline.py` and `turbo_run.py` import `src` at module top, so a parser inside `main()` would be too late. Each now has `_reject_unknown_arguments()` called from the `__main__` guard before the `src` imports (E402 is not in the ruff selection, so no suppression is needed). Importing either module is unchanged.
- Documented invocations found by grep (Makefile, `.github`, `docs/performance`, `docs/guides`, `docs/engine`, `tests`, `tools`): `perf_baseline.py` with no argument (runs), `perf_baseline.py --update` (promotes; `tests/tools/test_perf_baseline_tool.py` calls `main(["--update"])`), and `run_perf_baseline.py`, `perf_report.py`, `turbo_run.py` with no arguments. No Makefile or workflow runs any of the four. Every one keeps its behaviour.
- `turbo_run.py`: nothing invokes it (references are a governance-epic note, an orphan-check test string and the scope-coverage map). It looks like dead code; not deleted here, as the ticket says.
- Guard test `tests/unit/perf/test_tools_help_never_runs.py`: runs every `tools/perf/*.py` with a `__main__` block plus `tools/bench_corpus_world.py` with `--help` in a subprocess (20 s timeout) with `subprocess.Popen` replaced by a function that raises, so a child process fails the run; checks exit 0, usage text and an empty working directory. A second test checks the four tools exit 2 on an unknown flag. Positive control: against the old `perf_baseline.py` both of its tests fail (Popen blocked, so no benchmark started).

## Test Summary
- `tests/unit/perf/test_tools_help_never_runs.py`: 29 passed in about 7 s (24 `--help` entry points including `bench_corpus_world.py`, 4 unknown-flag checks, 1 discovery check).
- `tests/tools/test_perf_baseline_tool.py`, `test_test_scope_coverage_static.py`, `test_tools_orphan_check.py` and `tests/unit/perf`: 401 passed.
- `python3 -m codebase.health check`: OK, 0 new, 0 worse.
- No tool was run without `--help`; no benchmark was started.

## Files Changed
- `tools/perf/perf_baseline.py`, `run_perf_baseline.py`, `perf_report.py`, `turbo_run.py`
- `tests/unit/perf/test_tools_help_never_runs.py` (new)
- this ticket

## Completion Summary
`--help` and `-h` on the four tools print usage and exit 0 before any `src` import or subprocess; an unknown flag exits 2. A guard test covers every `__main__` entry point in `tools/perf/` plus `tools/bench_corpus_world.py`. `turbo_run.py` has no caller and may be dead code (not deleted).
