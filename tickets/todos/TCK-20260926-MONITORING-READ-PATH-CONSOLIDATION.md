---
status: active
layer: observability
authority: P1
audience: agent
ticket_id: TCK-20260926-MONITORING-READ-PATH-CONSOLIDATION
phase: open
date: 2026-09-26
tags: [agent-monitoring, observability, data-quality]
---

# TCK-20260926-MONITORING-READ-PATH-CONSOLIDATION

## Title

Consolidate the ~8 independent `agent-monitoring/` read-side shard-glob call sites into one shared
resolver, mirroring `monitoring_batch_identifier.py`'s write-side consolidation

## Status

OPEN

## Tier

standard

## Type

refactor

## Priority

P2

## Request Summary

`TCK-20260925-MONITORING-SHARD-PER-PR-KEY-FIX` gave every monitoring **write** site one shared
resolver (`tools/agent-monitoring/monitoring_batch_identifier.py::resolve_write_target()`),
replacing five independently-drifted copies of the same write-target formula. No equivalent exists
on the **read** side. `TCK-20260925-MONITORING-STALE-READ-PATH-SWEEP` found and fixed 12 read-side
bugs across 11 files where a glob helper matched only the bare per-week filename
(`data/<week>/<source>.jsonl`) and never the per-identifier shape
(`data/<week>/<id>.<source>.jsonl`), then explicitly deferred consolidating them: "a shared
read-side helper is a reasonable future improvement but a larger, riskier change... than this
hotfix's job" (its own Out of Scope). This ticket tracks that deferred work; it does not implement
it.

**Correcting how that sweep's finding should be read, so this ticket isn't cited as evidence of
long-standing rot it wasn't.** Of the 12 sites the sweep fixed, only 2 were genuinely pre-existing
rot: `.claude/workflows/implement-epic.js:384` and `.claude/workflows/simq-audit.js:67`, both
reading the retired flat path, broken since the 2026-09-02 sharding migration
(`TCK-20260902-MONITORING-SHARD-WRITE-PATH`) retired it. The other ~7 sites
(`validate.py::load_data_glob_with_line_count`, `done_checker_static.py`'s
`_jsonl_rows_for_run_id_across_weeks`, `ingest.py::_week_shard_paths`,
`monitoring_shards.py::source_paths`, `manifest.py::_source_paths`, `bash_command_mix.py::week_shards`,
`generate_retro.py::_source_mtime`) were correct until the day before the sweep — their narrow
`data/<week>/<source>.jsonl` glob matched the bare per-week shard fine, and only stopped matching
when `TCK-20260925-MONITORING-SHARD-PER-PR-KEY-FIX`'s own per-key re-key introduced the
`<id>.<source>.jsonl` shape that same day. **That sweep was this epic cleaning up its own
fallout from a one-day-old change, not uncovering weeks or months of old rot** — the dashboard
blindness it fixed spans about a day, not the whole post-migration period. Say it plainly wherever
this ticket is cited.

**Related, separate operational note for whoever picks this up:** the per-PR write-side key only
takes effect for sessions running the fixed `post_tool_hook.py`/`monitoring_batch_identifier.py`.
A third concurrent session whose checkout predated that fix wrote 218 rows to the old shared
(non-per-identifier) `tools.jsonl` shard after the fix had already landed on `main`, simply because
its own checkout hadn't picked it up yet. That is expected transitional noise while old checkouts
roll forward, not a regression in the fix or evidence this ticket's read-side consolidation is
urgent — don't let a shared-file row on a future PR read as either without checking which checkout
wrote it first.

## Scope

1. Design and build one shared read-side resolver (in `tools/agent-monitoring/`, most likely
   alongside or extending `monitoring_batch_identifier.py`) that returns every matching shard path
   for a given `(week, source)` or `(source,)` query — both the bare per-week shape and the
   per-identifier shape — as the single source of truth every read call site uses.
2. Migrate each of the ~8 current independent call sites to use it:
   `tools/agent-monitoring/validate.py::load_data_glob_with_line_count()`,
   `tools/gate_checks/done_checker_static.py::_jsonl_rows_for_run_id_across_weeks()`,
   `src/api/agent_ops_dashboard/ingest.py::_week_shard_paths()`,
   `tools/agent_replay_codex/monitoring_shards.py::source_paths()`,
   `tools/agent-monitoring/manifest.py::_source_paths()`,
   `tools/agent-monitoring/bash_command_mix.py::week_shards()`,
   `tools/agent-monitoring/generate_retro.py::_source_mtime()`,
   `tools/agent-monitoring/record_events.py`'s own inline `tools_paths` glob.
3. Before migrating each site, read its own existing fallback/legacy-shape nuances (several have
   their own scratch-shape fallback docstrings per the sweep ticket's Implementation Notes) and
   decide per site whether the shared resolver subsumes it cleanly or whether the site keeps a
   documented local addition on top of the shared base — don't assume they're interchangeable
   without checking.

## Out of Scope

- Changing the write-side resolver or the per-identifier shard-key shape itself.
- Any change to what data is captured or how `runs.jsonl`/`events.jsonl`/`tools.jsonl` are
  structured.
- Re-litigating whether the per-identifier keying scheme itself was the right call — settled by
  `TCK-20260925-MONITORING-SHARD-PER-PR-KEY-FIX`.

## Acceptance Criteria

1. One shared read-side resolver module/function exists, unit-tested directly (not only through a
   caller).
2. All ~8 call sites listed in Scope use it; no independent glob-widening logic for monitoring
   shard paths remains duplicated across them.
3. Each site's pre-existing fallback/legacy-shape behavior is preserved, or its removal is
   explicitly justified in the ticket's Implementation Notes — not silently dropped.
4. Full regression suite for every touched file passes, plus the existing detection-proving tests
   `TCK-20260925-MONITORING-STALE-READ-PATH-SWEEP` added for each site still pass unmodified (or
   are updated with an explicit reason).
5. A future change to the shard-key shape requires editing exactly one function, not ~8 call sites
   — demonstrated by the consolidation itself, not merely asserted.

## Related Tickets

- `TCK-20260925-MONITORING-STALE-READ-PATH-SWEEP` — found and fixed the 12 read-path bugs this
  ticket's consolidation would have prevented from recurring; explicitly deferred the
  consolidation itself.
- `TCK-20260925-MONITORING-SHARD-PER-PR-KEY-FIX` — the write-side precedent
  (`monitoring_batch_identifier.py::resolve_write_target()`) this ticket mirrors, and the same-day
  re-key that (per the correction above) is what actually broke the ~7 non-rot sites.
- `TCK-20260902-MONITORING-SHARD-WRITE-PATH` — the original sharding migration that retired the
  flat files the 2 genuinely-old-rot sites still (wrongly) targeted.

## Related Docs

- `docs/agent-monitoring/schema.md` — shard-path shape and write/read attribution reference.

## Related Stored Artifacts

_None yet — not scoped/planned._

## Related Code Areas

- `tools/agent-monitoring/monitoring_batch_identifier.py`
- `tools/agent-monitoring/validate.py`
- `tools/gate_checks/done_checker_static.py`
- `src/api/agent_ops_dashboard/ingest.py`
- `tools/agent_replay_codex/monitoring_shards.py`
- `tools/agent-monitoring/manifest.py`
- `tools/agent-monitoring/bash_command_mix.py`
- `tools/agent-monitoring/generate_retro.py`
- `tools/agent-monitoring/record_events.py`

## Assumptions / Open Questions

1. Whether the shared resolver lives in `monitoring_batch_identifier.py` itself (co-locating
   read/write shard-path logic in one module) or a new sibling module — not decided here, left for
   whoever scopes the implementation.
2. Whether every site's fallback nuance is worth preserving as-is, or whether the shape has now
   stabilized enough (two independent keying schemes deep) that some sites' legacy fallbacks are
   themselves dead weight worth removing — needs a per-site read before implementation, not a
   blanket assumption either way.

## Implementation Notes

_Not implemented — this ticket is filed for future scoping only, per explicit instruction. Left in
`tickets/todos/`._

## Test Summary

_Not implemented._

## Files Changed

_Not implemented._

## Completion Summary

_Not implemented._
