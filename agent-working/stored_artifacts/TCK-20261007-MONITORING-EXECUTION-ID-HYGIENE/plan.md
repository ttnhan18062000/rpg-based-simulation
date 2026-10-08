---
status: historical
layer: observability
authority: P2
audience: agent
ticket_id: TCK-20261007-MONITORING-EXECUTION-ID-HYGIENE
artifact_type: plan
tags: [agent-monitoring, retro]
---

# Plan

## Decision (recorded in the ticket and the validator text)
**Tolerate by design** for `create-tickets` and `implement-epic`: the native workflow runtime cannot supply a clock or a shell, the sidecar writers omit `execution_id` deliberately, `post_tool_hook.py` and `run_dedup.py` already tolerate it (a row without one groups by `(run_id, start_ts)`). Fixing would mean inventing an identity source in a runtime that has none. The two `NATIVE-RUN-FAILING-GATE-PROBE` rows are classified "probe, ran without execution_id_suffix", also tolerated. No writer is changed, so the "if fixed, add a test" acceptance item does not apply (stated in the ticket). If the planner prefers a fix for the implement-ticket probe path, that is a separate ticket.

## Changes (all report-only; no gate, no exit-code change, no past-shard rewrite)
1. `tools/agent-monitoring/validate.py`: new `compute_execution_id_report(runs)`: counts rows without `execution_id`, split into `predates` (start_ts before 2026-07-30, the date of TCK-20260730-CLAUDE-EXECUTION-IDENTITY), `by design` (workflow in {create-tickets, implement-epic}), `unexplained` (everything else), each with per-week counts and the run_ids of the unexplained ones; printed after the existing drift report.
2. `compute_tool_row_report(data_dir)`: counts tools-shard lines the loader cannot parse, naming `file:line` (capped list); "none" on a clean corpus.
3. `compute_since_week_summary(warnings_with_runs, since_week)` plus a `--since-week` flag (default `2026-W40`): prints `W40+ warnings: N of M (filter: run start_ts ISO week >= 2026-W40; a run without start_ts counts as unknown)`, split by class (incomplete, DONE-without-working_log; the Scope/seq=1 collisions are a report, counted separately). Needs the warnings to carry their run_id: keep the printed text identical, collect `(class, run_id)` tuples beside the strings.
4. Non-canonical tiers, null-tier and Scope/seq=1 collisions: already reported by `compute_drift_report` / `compute_multi_invocation_collision_report`; the ticket text is updated to say so rather than duplicating them.

## Before / after
Before (recorded now, current main): 165 total; W40+ number computed by the new flag at implementation time and written to the ticket together with the method. After: same number (report-only), plus the new sections. The ticket states both, as required.

## Scope guards
No backfill, no shard rewrite (a test hashes shards), no blocking gate, `main()` exit code unchanged.

## Questions for the planner
1. OK to leave the false-positive "DONE has no working_log entry" class (reads the CSV only, misses working_log shards) alone, as the ticket says, or file it as a separate ticket? It is about 126 of the 165 warnings.
2. OK to tolerate the probe rows (classified, not fixed)?
