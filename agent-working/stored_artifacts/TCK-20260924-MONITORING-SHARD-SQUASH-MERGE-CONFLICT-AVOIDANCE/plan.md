---
status: active
layer: observability
authority: P2
audience: agent
artifact_type: plan
ticket_id: TCK-20260924-MONITORING-SHARD-SQUASH-MERGE-CONFLICT-AVOIDANCE
date: 2026-09-24
tags: [agent-monitoring, data-quality, process-improvement]
---

# Plan — TCK-20260924-MONITORING-SHARD-SQUASH-MERGE-CONFLICT-AVOIDANCE

**Scope reduction in effect** (investigation.md): JSONL files only (`runs`/`events`/`tools`).
`tickets/working_log.csv`'s write path is untouched in this ticket.

## Edits (all additive; every existing caller with `ticket_id`/`run_id` absent is unaffected)

1. **`tools/agent-monitoring/post_tool_hook.py`**: `tools_file` becomes
   `agent-monitoring/data/<week>/<ticket_id>.tools.jsonl` when `ticket_id` is truthy, else
   unchanged (`tools.jsonl`).
2. **`tools/agent-monitoring/record_run.py`**: `runs_file` becomes
   `agent-monitoring/data/<week>/<run_id>.runs.jsonl` when `record["run_id"]` is truthy (always
   true once `validate_record` passes, but keep the fallback for defense).
3. **`tools/agent-monitoring/record_events.py`**: group `records` by `run_id`; write each group to
   its own `agent-monitoring/data/<week>/<run_id>.events.jsonl` via `write_lines` (one lock
   acquisition per group, preserving the existing per-batch-contiguity contract for each group).
   `compute_tool_stats()`'s glob widened to also read `agent-monitoring/data/*/*.tools.jsonl`.

## New module: `tools/agent-monitoring/monitoring_consolidation.py`
- `consolidate_jsonl_kind(week_dir, kind) -> int` — folds every `<TCK-ID>.<kind>.jsonl` in
  `week_dir` into the canonical `<kind>.jsonl` via `writer.write_lines`, deletes the per-ticket
  file only after a successful canonical write, returns the count consolidated.
- `consolidate_week(week_dir) -> dict` — runs the above for `runs`/`events`/`tools`.
- `consolidate_all(data_dir=...) -> dict` — every week directory under `agent-monitoring/data/`.
- `main()` CLI — `python3 tools/agent-monitoring/monitoring_consolidation.py [--data-dir ...]
  [--json]`. Read of per-ticket files, one write to canonical, one delete per file — no other side
  effect. Never raises to its caller (wraps `consolidate_all` in try/except, matching every other
  hook/writer in this module's fail-open convention).

## Wiring
- `tools/agent-monitoring/generate_retro.py`: call `monitoring_consolidation.consolidate_all()`
  once, near the top of report generation, before `_load_runs_and_events()` reads the canonical
  files — so a retro run always sees fully-folded data, and the existing retro cadence becomes the
  default consolidation trigger with zero extra scheduling.
- `Makefile`: new `agent-monitoring-consolidate` target running the module's CLI directly, for
  on-demand consolidation between retro runs (Scope item 4).

## Tests: `tests/tools/test_monitoring_consolidation.py`
1. **AC1 — real throwaway git repo.** Two branches off one base commit, each adding a *different*
   per-ticket file under `agent-monitoring/data/<week>/` (`TCK-A.tools.jsonl`,
   `TCK-B.tools.jsonl`). Squash-apply branch A's diff onto `main` as one commit (simulating a
   GitHub squash-merge), then apply branch B's diff (still based on the pre-A state) onto the new
   `main` tip via `git apply`/`git cherry-pick`. Assert zero conflict — the two diffs touch
   disjoint file paths and can never collide, proven by real git plumbing, not asserted by
   inspection.
2. **AC2 — round-trip equivalence.** Fixture per-ticket files consolidated, then
   `bash_command_mix.load_tools_rows`/`validate.compute_vocabulary_drift_counts`-style readers
   (or a direct row-count/content comparison) confirm the consolidated canonical file is
   byte-for-byte equivalent, per row, to what a direct-append writer would have produced for the
   same logical rows.
3. **AC4 — idempotency.** Running `consolidate_week` twice on the same starting fixture: the
   second run consolidates zero files (all already deleted) and the canonical file is unchanged
   after the second run.
4. **AC5 — done-checker and `compute_tool_stats` unaffected.**
   `test_delivery_pr_status`-style regression: `compute_tool_stats()` finds the correct
   `(tool_call_count, cost_proxy_score)` for a `(run_id, seq)` whose rows live only in a per-ticket
   file, not yet consolidated. A second test confirms `check_working_log_exactly_one_row` was not
   touched (source-diff assertion) and `tests/tools/test_done_checker_static.py` still passes
   unchanged.
5. A test asserting `write_line`/`write_lines` in `writer.py` are unchanged (no source diff) —
   this ticket's entire mechanism rests on that module already being path-agnostic; a future
   session must not "helpfully" hardcode a path back into it.
6. Recorded once run.

## Out-of-scope guardrails
- No change to `tickets/working_log.csv`'s write path, `append_working_log_row()`, or
  `check_working_log_exactly_one_row()` — disclosed scope reduction, not silently dropped (see
  investigation.md).
- No historical data migration — only new writes from this ticket forward use per-ticket targets.
- No blocking behavior anywhere in the new module.
