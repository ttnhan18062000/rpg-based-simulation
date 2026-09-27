---
status: historical
layer: observability
authority: P1
audience: agent
ticket_id: TCK-20260926-MONITORING-READ-PATH-CONSOLIDATION
phase: done
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

1. Whether the shared resolver lives in `monitoring_batch_identifier.py` itself or a new sibling
   module. — **RESOLVED: new sibling module, `tools/agent-monitoring/monitoring_shard_paths.py`.**
   `monitoring_batch_identifier.py`'s own scope is narrowly "what identifier does this one write/
   read belong to" (git-branch/PR resolution with its own detached-HEAD/sidecar fallback chain);
   this ticket's callers span a much wider footprint (`tools/gate_checks/`,
   `tools/agent_replay_codex/`, `tools/agent-monitoring/` itself, and `src/api/agent_ops_dashboard/`,
   which already reaches across into `tools/` for exactly this reason) — a new, narrowly-scoped
   module matches that existing precedent rather than deepening the write-side module's own more
   specific responsibility.
2. Whether every site's fallback nuance is worth preserving. — **RESOLVED per site, see
   investigation.md's table.** No site's fallback is dropped; every one keeps its own post-glob
   logic exactly as before (mtime computation, line counting, run_id filtering, the `(dict,
   source_path)` tuple shape, the scratch/legacy single-file fallback), with only the path-
   discovery expression itself replaced by a call to the shared resolver.

## Implementation Notes

Re-enumerated the read-site list from scratch per explicit instruction rather than trusting the
ticket's own ~8-site count: found **9** real sites, including one (`verify_referential_
integrity.py`) named by neither this ticket nor the design peer's own grep — its own comment cited
the prior sweep ticket as having widened it, but that ticket's Files Changed never named this file;
it carried an independent, drifted copy rather than calling the shared function its sibling
(`validate.py::load_data_glob_with_line_count`) docstring claimed it used. Also corrected two false
"doesn't match my regex" claims from the design peer's own brief (`validate.py`'s and
`generate_retro.py`'s functions both do contain the idiom; their regex likely anchored on a bare
`return`-statement shape the intermediate-local-variable form doesn't match) — verified by reading
the code directly, not by re-running their tool.

Built `tools/agent-monitoring/monitoring_shard_paths.py` (`shard_paths()`, `per_identifier_shard_
paths()`) and migrated all 9 read-widening sites plus `monitoring_consolidation.py`'s own narrower,
correctly-scoped-but-independently-hand-rolled per-identifier-only glob (folded in on proliferation
grounds, not because it was broken — see investigation.md). `record_events.py`'s own `Path(".")`-
prefixed glob is normalized to a plain relative path via the shared resolver; confirmed by reading
`pathlib` semantics that `Path(".").glob(x)` and a bare relative `Path(y).glob(z)` are behaviorally
identical for CWD-relative resolution, so this was a code-cleanliness fix, not a distinct behavioral
bug the way it initially read.

AC5's static guard exceeds what was asked: rather than "exactly one occurrence, in the shared
module," the new module eliminates the idiom's fragile textual shape structurally (explicit
per-week-directory iteration, never a second repo-wide double-glob call), so the guard asserts
**zero** occurrences anywhere in the repo — confirmed to correctly find all 9 real pre-migration
sites when run before migration (not merely assumed to work from the regex alone), and zero after.

## Test Summary

- New `tests/tools/test_monitoring_shard_paths.py` (9 tests): `shard_paths()`/
  `per_identifier_shard_paths()` correctness across every combination (bare-only, per-identifier-
  only, both, neither, multi-week, missing data_root), and the AC5 static guard.
- Each of the 10 migrated files' own existing test suite re-run unmodified: `test_done_checker_
  static.py` (142), `test_monitoring_shards.py` + `test_monitoring_shards_no_literal_paths.py` (18),
  `test_bash_command_mix.py` (29), `test_generate_retro.py` (171), `test_validate_agent_
  monitoring.py` (37), `test_agent_monitoring_manifest.py` (10), `test_verify_referential_
  integrity.py` (12), `test_agent_ops_dashboard_ingest.py` (49), `test_record_events.py` (31),
  `test_monitoring_consolidation.py` (14) — all pass, zero edits needed to any of them (AC4).
- Combined run of all 11 files above: **522 passed**, 0 failed.
- Full cross-cutting regression: `tests/tools/ tests/agent_replay_codex/ tests/api/ -m "not slow
  and not extra_slow"` — **3270 passed**, 30 skipped, 28 deselected, 1 xfailed, 0 failed.

## Files Changed

- `tools/agent-monitoring/monitoring_shard_paths.py` (new) — the shared resolver.
- `tools/gate_checks/done_checker_static.py` — `_jsonl_rows_for_run_id_across_weeks()` migrated.
- `tools/agent_replay_codex/monitoring_shards.py` — `source_paths()` migrated.
- `tools/agent-monitoring/bash_command_mix.py` — `week_shards()` migrated.
- `tools/agent-monitoring/generate_retro.py` — `_source_mtime()` migrated (local var renamed to
  avoid shadowing the imported function).
- `tools/agent-monitoring/validate.py` — `load_data_glob_with_line_count()` migrated; docstring's
  stale claim about `verify_referential_integrity.py` being a caller corrected.
- `tools/agent-monitoring/manifest.py` — `_source_paths()` migrated.
- `tools/agent-monitoring/verify_referential_integrity.py` — its own independent copy migrated.
- `src/api/agent_ops_dashboard/ingest.py` — `_week_shard_paths()` migrated.
- `tools/agent-monitoring/record_events.py` — inline glob in `compute_tool_stats()` migrated,
  `Path(".")` prefix normalized away.
- `tools/agent-monitoring/monitoring_consolidation.py` — `consolidate_jsonl_kind()`'s own
  per-identifier-only glob migrated to `per_identifier_shard_paths()`.
- `tests/tools/test_monitoring_shard_paths.py` (new) — 9 tests.
- `staging_artifacts/TCK-20260926-MONITORING-READ-PATH-CONSOLIDATION/
  {investigation,plan,test_plan}.md` (new).
- `docs/REGISTRY.yaml` — regenerated as part of ticket close (routine, unconditional per the
  Finalize rule).

## Completion Summary

Consolidated the ~8 (really 9) independent read-side shard-glob call sites `TCK-20260925-
MONITORING-STALE-READ-PATH-SWEEP` fixed and explicitly deferred into one shared resolver module,
mirroring `monitoring_batch_identifier.py`'s own write-side consolidation. Re-enumerated the site
list from scratch per instruction rather than trusting either this ticket's or the design peer's
own count, finding a real 9th site and correcting two of the peer's own false negatives — evidence-
checked, not taken on report. Every site's own fallback/legacy nuance is preserved exactly, per-
site, with the reasoning recorded (AC3). The AC5 static guard delivers a stronger guarantee than
asked for: the fragile idiom is structurally eliminated, not merely centralized, so the guard
asserts zero remaining occurrences rather than exactly one.

No known material gap. `data_runs_clean` is expected to behave properly on this close per T1's own
fix landing earlier in this batch — if it still misbehaves, that is a T1 regression worth
reporting, not noise to wave off.
