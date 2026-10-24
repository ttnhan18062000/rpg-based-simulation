---
status: active
layer: performance
authority: P1
audience: agent
ticket_id: TCK-20261024-PERF-TOOLS-HELP-FLAG-NEVER-STARTS-A-RUN
phase: open
date: 2026-10-24
tags: [performance, benchmarking]
---

# TCK-20261024-PERF-TOOLS-HELP-FLAG-NEVER-STARTS-A-RUN

## Title
`--help` on a tools/perf script prints usage and exits; it never starts a benchmark

## Status
OPEN

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
- [ ] `--help` and `-h` on all four exit 0, print usage and start no run (the test proves it).
- [ ] An unknown flag exits non-zero without running.
- [ ] The documented invocations behave as before (each one found by the grep is listed in the ticket).
- [ ] The `--help` test covers every `__main__` entry point in `tools/perf/` plus `tools/bench_corpus_world.py`,
      and runs in under 30 s in total, with no heavy runs.
- [ ] `python3 -m codebase.health check` reports OK.

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

## Test Summary

## Files Changed

## Completion Summary
