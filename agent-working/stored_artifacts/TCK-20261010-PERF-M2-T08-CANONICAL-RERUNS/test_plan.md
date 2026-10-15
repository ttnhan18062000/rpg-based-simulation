---
status: historical
layer: performance
authority: P2
audience: agent
artifact_type: test_plan
ticket_id: TCK-20261010-PERF-M2-T08-CANONICAL-RERUNS
date: 2026-10-13
tags: [performance, benchmarking, regression]
---

# Test plan: TCK-20261010-PERF-M2-T08-CANONICAL-RERUNS

- `tests/unit/perf/test_rerun_baselines.py`: the tool builds a record with `signal_contract=canonical`, the profile named in the old file, `runner.controlled=false`, an all-NORMAL mode sequence; a corpus record carries `content.world_id`; a missing old file or an unknown name is a usage error, not a guess; promotion through `baseline_lifecycle` is the only writer (the tool never writes under `tests/perf/baselines/`).
- A corpus guard: every committed `tests/perf/baselines/*.json` is a valid record or one of the remaining listed legacy files (`baseline_lifecycle check` exits 0); the legacy set no longer names a removed file.
- `tests/perf/test_perf_regression_baseline.py -m slow` run before (INCONCLUSIVE, legacy) and after (a real head run against the promoted record) and kept.
- `tests/integration/observability/test_baseline_comparison_flow.py` passes; `python3 -m src compare-sweep` and `python3 -m src gate` exit 0 on the new `docs/observability/baselines/latest.json` (output kept); a unit test asserts `latest.json` parses as `BaselineConfig` and carries the current `cost_accounting_version`.
- Guards: `tests/tools/test_agent_working_paths_guard.py`, docs frontmatter/registry tests, `codebase.health check`.

## Proof Plan
- **Level:** unit and tool-level, plus measured runs. **Proof kind:** deterministic unit tests for the tool's selection, median and NOISY rules (fake subprocesses), a committed-file test that the sweep-gate baseline parses as `BaselineConfig` and is comparable, and real measurements (13 records x 3 fresh-process runs) recorded in `evidence.md`.
- **Oracle:** `baseline_lifecycle promote` (refuses a non-NORMAL run, a dirty `src/`, a missing cause), `baseline_lifecycle check`, `python3 -m src compare-sweep` and `gate` exit codes, and the 15 % spread rule from perf-planner's review. A measured number is evidence about one loaded host on one day, never a capacity claim.
