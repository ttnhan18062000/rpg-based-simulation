---
status: active
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20260928-MONITORING-LOADER-CWD-RELATIVE-PATHS
phase: open
date: 2026-09-28
tags: [process-improvement]
---

# TCK-20260928-MONITORING-LOADER-CWD-RELATIVE-PATHS

## Title

`generate_retro.py`'s shared run/event loader reads cwd-relative paths while the gate checks
that call it read everything else relative to the script's own location. Running a check from
a different checkout therefore compares two different corpora and reports false failures.

## Status

OPEN

## Tier

hotfix

## Type

bug

## Priority

P2

## Request Summary

Seen live on 2026-09-28 while verifying `ticket-corpus-guard-test-scope-map`. The implementer ran
pytest from the main checkout against the worktree's test files, because `.venv` exists only in the
main checkout. `tests/tools/test_monitoring_integrity_backlog_check.py::test_real_corpus_is_at_or_below_all_five_conditions`
then failed with "working_log DONE rows with no run record … live: 1 … Offending ticket_ids:
['TCK-20260927-PR-RENDER-NO-RECORDED-TICKET-EXCLUSION']". That ticket's run record exists
(`2026-W39/runs.jsonl`, run_id == ticket_id, plus 9 events). Run from inside the worktree, the
test passes.

Root cause, verified from the source at `53066e129`:

- `tools/gate_checks/monitoring_integrity_backlog_check.py` resolves `WORKING_LOG_PATH` and
  `DATA_DIR` from `_REPO_ROOT = Path(__file__)…`, which is the script's own checkout.
- Its run IDs come from `generate_retro._load_runs_and_events()`, which reads
  `DEFAULT_DB_PATH = Path("agent-monitoring-index/monitoring.db")` and falls back to
  `RUNS_FILE`/`EVENTS_FILE = Path("agent-monitoring/data")`. All three are **cwd-relative**.
- The result is a working_log from checkout A checked against run records from checkout B. A
  ticket closed on the branch shows up as "missing a run record" whenever B is behind A.

`generate_retro.py` already anchors `_DEFAULT_TICKETS_ROOT` to `Path(__file__)` a few lines
below those constants, so the module mixes the two conventions. The same cwd-relative defaults feed
every `tools/gate_checks/` module that calls `_load_runs_and_events()`, `_load_source()` or
`DEFAULT_TOOLS_FILE`: `duplicate_run_record_check`, `event_seq_integrity_check`,
`monitoring_anomaly_validator`, `monitoring_integrity_backlog_check`,
`sidecar_attribution_coverage_check` and `tool_call_count_mismatch_check`. It also feeds the
`tools/agent-monitoring/` consumers (`done_ticket_monitoring_coverage`,
`security_gate_firing_check`, `retrieval_baseline_metrics`, `read_ranged_baseline`,
`agent_tool_usage_baseline`, `skill_usage_metric`).

Hooks invoke these scripts by relative path (`python3 tools/agent-monitoring/…` in
`.claude/settings.json`), and Make targets run from the repo root, so for every normal
invocation the current directory and the script's own checkout are the same. Anchoring therefore
changes nothing for hooks and Make. It only changes the cross-checkout case, which is currently wrong.

## Scope

1. In `tools/agent-monitoring/generate_retro.py`, anchor `RUNS_FILE`, `EVENTS_FILE`, `RETRO_DIR`,
   `DEFAULT_DB_PATH` and `DEFAULT_TOOLS_FILE` to the repo root derived from `Path(__file__)`, the
   same way `_DEFAULT_TICKETS_ROOT` already is. Move `_DEFAULT_TICKETS_ROOT` above them, or derive a
   shared `_REPO_ROOT`, rather than computing the root twice.
2. Check that the CLI still accepts explicit path overrides (argparse defaults) unchanged, and that
   `build_index.build(...)` receives absolute strings without issue.
3. Regression test: from a `tmp_path` cwd that has no `agent-monitoring/` directory, assert that
   `generate_retro.RUNS_FILE` / `DEFAULT_DB_PATH` resolve under the repo root and that
   `_load_runs_and_events()` returns a non-empty run list. That second assertion would have failed
   before the fix, when the loader found nothing from a foreign cwd.
4. Run the bare `tests/tools/` directory **from the worktree**. Tests that `monkeypatch.chdir` into
   a `tmp_path` and relied on these five defaults resolving there must switch to monkeypatching the
   constants directly. 11 files in `tests/tools/` call `chdir`, so check each failure against this
   cause before changing anything.

## Out of Scope

- The other ~20 cwd-relative module constants across `tools/agent-monitoring/`,
  `tools/gate_checks/` and `tools/*.py` (e.g. `build_index.py`, `validate.py`, `query.py`,
  `working_log_writer.py`, `status_drift_check.py`). Each is self-consistent: it reads and
  writes one checkout's data. The defect here is specifically one check mixing an anchored
  source with a cwd-relative one through a shared loader. A repo-wide anchoring convention can be
  its own ticket if another mixed case appears.
- `build_index.py`'s own CLI defaults. It receives explicit paths from this loader.

## Acceptance Criteria

- AC1: The five constants in `generate_retro.py` are absolute paths under the module's own repo
  root, whatever the current directory.
- AC2: From the main checkout's cwd, running the worktree's
  `tests/tools/test_monitoring_integrity_backlog_check.py::test_real_corpus_is_at_or_below_all_five_conditions`
  passes on a branch with a ticket closed after the main checkout's HEAD. This is the exact
  2026-09-28 reproduction, recorded in Test Summary with both cwds.
- AC3: New regression test per Scope 3 passes and fails on the pre-fix constants (state how this
  was shown).
- AC4: bare `pytest tests/tools/` passes, run from the worktree.

## Related Tickets

- `TCK-20260928-CLOSED-TICKETS-RESURRECTED-INTO-TODOS`, `TCK-20260928-TEST-SCOPE-MAP-MISSES-TOOLS-SUBPACKAGES`:
  same batch. This one was found while verifying them.
- `TCK-20260926-MONITORING-READ-PATH-CONSOLIDATION`: the shared read-path resolver
  (`monitoring_shard_paths`). This ticket fixes where that path is rooted, not which files it matches.
- `TCK-20260811-AGENT-MONITORING-INDEX-SILENT-STALENESS`: the same loader's index-staleness rebuild.

## Related Docs

- `tools/agent-monitoring/generate_retro.py` docstring of `_load_runs_and_events()`

## Related Stored Artifacts

None.

## Related Code Areas

- `tools/agent-monitoring/generate_retro.py`
- `tools/gate_checks/monitoring_integrity_backlog_check.py` (reproduction; no change expected)
- `tests/tools/`

## Assumptions / Open Questions

- Assumes no caller intentionally depends on cwd-relative resolution to read a *different*
  checkout's corpus. Hooks and Make use relative invocation, so cwd equals the script root; no
  cross-checkout use was found. If a test relies on it, fix the test, not the anchoring.

## Implementation Notes

## Test Summary

## Files Changed

## Completion Summary
