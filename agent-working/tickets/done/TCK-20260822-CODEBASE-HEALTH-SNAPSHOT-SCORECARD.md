---
status: historical
layer: observability
authority: P1
audience: agent
ticket_id: TCK-20260822-CODEBASE-HEALTH-SNAPSHOT-SCORECARD
phase: done
date: 2026-08-22
tags: [agent-monitoring]
---

# TCK-20260822-CODEBASE-HEALTH-SNAPSHOT-SCORECARD

## Title
Historical codebase-health snapshot mechanism and multi-dimension scorecard

## Status
INPROGRESS

## Tier
standard

## Type
feature

## Priority
P2

## Request Summary
The author wants a persistent, append-only mechanism — following the same pattern agent-monitoring/runs.jsonl already uses — that snapshots codebase-health metrics over time, plus a multi-dimension scorecard view over those snapshots. The scorecard must show trend arrows across dimensions, not collapse everything into a single aggregate score; the author is explicit that a single health score is out of scope, per the source audit's own guidance (docs/audits/D24_codebase_health_observatory.md §J/§M and docs/plans/codebase_health_observatory_tooling_epic.md "Out of scope"). Today there is no mechanism at all that persists these metrics across runs.

## Scope
- New module that calls tools/codebase_health_baseline.py::build_report() and serializes its dict as one JSON line appended to a new history file, following the agent-monitoring/runs.jsonl append-only pattern (no in-place rewrite of history).
- New scorecard reader/renderer that reads N historical snapshots and renders per-dimension trend arrows (up/down/flat), mirroring tools/personality_audit.py's Δ/↑↓→ pattern — no aggregate/combined score field anywhere in the output.
- Decide and document the scorecard's dimension set drawn from build_report()'s existing fields, and freeze/version the snapshot schema explicitly (or import the dict directly) so a future change to build_report() is a visible breaking change, not silent drift.
- Graceful degradation when only one historical snapshot exists: label metrics as having no trend data yet, do not crash or compute a spurious trend from a single point.
- New tests under tests/tools/ covering: two-invocation append-only persistence, per-dimension trend-arrow rendering, single-snapshot degradation, and schema freeze/versioning.
- Explicit, documented decision on Makefile wiring (on-demand target like the sibling codebase-health-baseline/codebase-health-impact targets, or state why not) — not CI-wired by default unless explicitly justified.

## Out of Scope
- PR / AI change-impact report generator — tracked separately as TCK-20260822-CHANGE-IMPACT-REPORT-GENERATOR.
- Any change to build_report()'s existing metric computation in tools/codebase_health_baseline.py — this ticket only consumes its dict output, never re-derives or duplicates metric logic.
- CI wiring of the new snapshot command as a required/blocking gate.
- A single aggregate/combined health score in any form, at any layer of the output.

## Acceptance Criteria
- [x] Running the new snapshot command twice appends two separate JSON-line records to the new history file without truncating or rewriting the first record — verified by re-reading the file after each invocation and asserting both records are present.
- [x] The scorecard view, given two or more historical snapshots, renders a directional trend indicator (up/down/flat) per individual metric/dimension, and its output contains no aggregate/combined 'score' field — verified by asserting absence of an aggregate field and presence of a per-dimension directional indicator.
- [x] Given only one historical snapshot, the scorecard renders without crashing and labels each metric as having no trend data yet, rather than computing a trend from a single data point.
- [x] The snapshot payload is built by calling tools/codebase_health_baseline.py's existing build_report() dict directly — no re-implementation/re-derivation of the underlying metrics computation and no parsing of format_report()'s printed text.

## Related Tickets
- TCK-20260817-CODEBASE-HEALTH-OBSERVATORY-TOOLING-EPIC
- TCK-20260819-STANDARD-CODEBASE-HEALTH-BASELINE-TARGET
- TCK-20260819-STANDARD-CODE-HEALTH-IMPACT-COMMAND
- TCK-20260817-CODEBASE-HEALTH-RESILIENCE-EPIC

## Related Docs
- docs/audits/D24_codebase_health_observatory.md
- docs/plans/codebase_health_observatory_tooling_epic.md

## Related Stored Artifacts
None.

## Related Code Areas
- tools/codebase_health_baseline.py
- tools/code_health_impact.py
- agent-monitoring/runs.jsonl
- docs/agent-monitoring/schema.md
- tools/personality_audit.py
- tests/tools/test_codebase_health_baseline.py
- tests/tools/test_code_health_impact.py
- Makefile
- expected: tools/codebase_health_snapshot.py
- expected: tests/tools/test_codebase_health_snapshot.py

## Assumptions / Open Questions
- build_report()'s exact dict schema (tools/codebase_health_baseline.py lines 233-253) is treated as the de facto snapshot payload contract; this ticket freezes/versions the snapshot schema explicitly (or imports the dict directly) so a future change there is a visible breaking change rather than silent drift.
- This ticket decides the scorecard's dimension set (which of build_report()'s ~13 fields become dimensions) and how many historical points define a "trend" — the epic's own AC only requires "at least two runs" and nothing else will make this decision, so it is treated as in-scope here.
- No existing generic JSONL-append utility exists in tools/ (each JSONL writer inlines its own append logic); this ticket may add a small shared append helper or continue the repo's existing inline-append pattern at the implementer's discretion.
- TCK-20260822-CHANGE-IMPACT-REPORT-GENERATOR is explicitly sequenced after this ticket and may depend on this ticket's snapshot output shape — this ticket's scope must not creep into that ticket's report-generator surface.
- `layer: observability` was chosen (registered note: "Agent monitoring, dashboards, event bus, telemetry") since this ticket builds a dashboard/telemetry-style scorecard over codebase-health metrics and explicitly reuses the agent-monitoring append-only pattern; flagged for reviewer judgment since the code itself lives in tools/, not src/observability/.

## Implementation Notes

Implemented exactly per `staging_artifacts/TCK-20260822-CODEBASE-HEALTH-SNAPSHOT-SCORECARD/plan.md`'s
9 steps, with 3 deviations recorded in that file's own "Deviations (recorded during Implement)"
section (added this run) rather than applied silently:

1. **New module `tools/codebase_health_snapshot.py`** with the sibling-module skeleton
   (`_TOOLS_DIR`/`_REPO_ROOT`), a second `sys.path.insert` for the hyphenated
   `tools/agent-monitoring/` directory (`from writer import write_line`), the frozen
   `EXPECTED_SNAPSHOT_KEYS` allowlist (hand-copied from `build_report()`'s real 14-key return
   dict — see Deviations below on the plan's "13" prose miscount), `SNAPSHOT_SCHEMA_VERSION = 1`,
   and `DEFAULT_HISTORY_PATH`.
2. **`build_snapshot_record(repo_root)`** calls `build_report()` directly, validates
   `set(report.keys()) == EXPECTED_SNAPSHOT_KEYS` exactly and raises `RuntimeError` with the
   missing/added key diff on mismatch, then stamps `snapshot_schema_version`.
   **`write_snapshot(repo_root, history_path)`** has no default for `history_path` (load-bearing
   per the plan's Anti-Drift Notes), serializes via `json.dumps(record, separators=(",", ":"))`,
   and calls `write_line(history_path, line)`, returning its bool unchanged. A `history_path.parent.mkdir(...)`
   call was added immediately before `write_line` — not explicit in the plan, but required because
   `write_line` acquires its lock file (a sibling path) before its own `mkdir` call, so the parent
   directory must already exist; mirrors `record_run.py`'s identical workaround for `RUNS_FILE`.
3. **`read_snapshots(history_path)`** returns `[]` for a missing file, else parses each line.
   **`build_scorecard(snapshots)`** always compares only the two most recent snapshots; 11 scalar
   dimensions get `{latest, previous, diff, arrow, trend_label}`; `registry_size_lines` is the only
   rendered row for the registry-size fold (`registry_size_bytes` still captured in every record,
   never its own row); `unused_core_dependencies` gets `{latest, previous, changed, trend_label}`
   with no `arrow`/`diff` key at all (routed through `_build_non_scalar_row`, never the scalar
   arrow branch).
4. **Graceful degradation** built into `build_scorecard`/`_build_scalar_row`/`_build_non_scalar_row`
   via a shared `previous is None` branch: 0 snapshots → `{"no_snapshots_yet": True, "dimensions": {}}`;
   1 snapshot → every dimension row carries `"trend_label": NO_TREND_DATA_LABEL` ("no trend data
   yet") instead of a fabricated diff/arrow — same dimension-row shape as the 2+-snapshot case, per
   the plan's explicit "do not introduce a second, divergent dimension list" instruction.
5. **`format_scorecard(scorecard)`** renders a fixed-width table (label column padded, value
   right-aligned) covering all 3 cases; **`main(argv=None)`** uses an argparse subcommand
   (`snapshot` / `scorecard`) — `--repo-root`/`--history-path` (defaulting to `DEFAULT_HISTORY_PATH`)
   on the snapshot subcommand, `--history-path` only on the scorecard subcommand.
   `DEFAULT_HISTORY_PATH` is used as a default nowhere else in the module. On `write_snapshot`
   returning `False`, `main()` prints a `WARNING` to stderr and still returns `0`.
6. **Makefile**: added `codebase-health-snapshot`/`codebase-health-scorecard` targets immediately
   after `codebase-health-impact`, matching the `## ... (on-demand only — not CI)` comment
   convention, and added both names to `.PHONY`. Deviation: both target bodies pass `$(ARGS)`
   through to the underlying script (the plan's literal Step 6 snippet did not), needed so
   `test_make_target_runs_successfully_end_to_end` can redirect `--history-path` to a `tmp_path`
   location when shelling out to the real `make` binary — otherwise that test would have had no
   way to avoid writing to the real `agent-monitoring/codebase_health_history.jsonl`, violating the
   plan's own Scope Guard. Mirrors the pre-existing `codebase-health-impact: ... $(ARGS)` precedent
   in the same file.
7. **13 tests** added in `tests/tools/test_codebase_health_snapshot.py`, covering all of Steps 2-6's
   `**Verify**` lists plus the Review-added
   `test_no_test_target_path_resolves_under_real_agent_monitoring_dir` literal-source-scan guard
   (mirrors `tests/tools/test_monitoring_writer.py:31-51` exactly). Every test passes an explicit
   `tmp_path`-derived `history_path`; none rely on `DEFAULT_HISTORY_PATH`.
8. **New doc** `docs/agent-monitoring/codebase_health_history_schema.md`: file path, append-only
   contract statement (mirroring `schema.md`'s "Historical Corrections" language), a full field
   table for all 14 `EXPECTED_SNAPSHOT_KEYS` names + `snapshot_schema_version` (see Deviations on
   the 13-vs-14 count), and the version-bump discipline (paired allowlist edit + version bump + doc
   update, same commit).
9. **Epic doc** `docs/plans/codebase_health_observatory_tooling_epic.md`: struck through the
   "Historical metric snapshots" bullet and added a `**Resolved** (TCK-20260822-CODEBASE-HEALTH-SNAPSHOT-SCORECARD,
   2026-08-23)` paragraph matching the two sibling bullets' formatting/detail level.

Full deviation rationale (key-count prose correction, the `mkdir` fix, and the Makefile `$(ARGS)`
addition) is recorded in `staging_artifacts/TCK-20260822-CODEBASE-HEALTH-SNAPSHOT-SCORECARD/plan.md`'s
own "Deviations (recorded during Implement)" section, not just here.

## Test Summary

- `pytest tests/tools/test_codebase_health_snapshot.py -v` — **13 passed**.
- `pytest tests/tools/ -k "codebase_health or code_health or monitoring_writer" -v` — **62 passed,
  4 skipped** (the 4 skips are `code_health_impact.py`'s pre-existing `@_requires_graphify`
  real-path tests, skipped because `graphify-out/graph.json` does not exist in this worktree —
  unrelated to this ticket's own change, same skip behavior as before this ticket).
- `pytest tests/docs/test_doc_integrity.py -v` — **10 passed, 1 skipped** (pre-existing
  environment-conditional skip, unrelated to this ticket).
- `python3 tools/validate_frontmatter.py` — passed for the new doc and this ticket file.
- Confirmed no test in this run wrote to the real `agent-monitoring/codebase_health_history.jsonl`
  (checked via `git status`/directory listing after the full test run).

## Files Changed

- `tools/codebase_health_snapshot.py` (new)
- `tests/tools/test_codebase_health_snapshot.py` (new)
- `docs/agent-monitoring/codebase_health_history_schema.md` (new)
- `Makefile` (edited: 2 new targets + `.PHONY` entries)
- `docs/plans/codebase_health_observatory_tooling_epic.md` (edited: resolved bullet)
- `docs/plans/architecture_resilience_remediation_roadmap.md` (Document-Update phase: a real gap
  found and fixed — this doc mirrors the epic doc's own Epic K item list/status but the Implement
  phase's edit didn't reach it, leaving it stale. Updated Epic K's status-line cell and resolved
  the matching "Historical metric snapshots" bullet in its own §J/§L/§M section.)
- `tickets/todos/codebase-health-resilience/TCK-20260817-CODEBASE-HEALTH-RESILIENCE-EPIC.md`
  (Document-Update phase: same gap, one level up the epic-tracking chain — this is Epic K's own
  parent tracking ticket, present and committed in this worktree. Updated its Epic K status-line
  cell, added a dated narrative paragraph recording this ticket's resolution, and added this
  ticket to its Related Tickets list.)
- `tickets/inprogress/TCK-20260822-CODEBASE-HEALTH-SNAPSHOT-SCORECARD.md` (this file — Implementation
  Notes/Test Summary/Files Changed/Completion Summary/Acceptance Criteria filled in)
- `staging_artifacts/TCK-20260822-CODEBASE-HEALTH-SNAPSHOT-SCORECARD/plan.md` (edited: added
  "Deviations (recorded during Implement)" section)
- `staging_artifacts/TCK-20260822-CODEBASE-HEALTH-SNAPSHOT-SCORECARD/investigation.md` (new — the
  standard Investigate-phase artifact for this standard-tier ticket; never previously committed in
  this worktree)
- `staging_artifacts/TCK-20260822-CODEBASE-HEALTH-SNAPSHOT-SCORECARD/test_plan.md` (new — the
  standard Investigate-phase artifact for this standard-tier ticket; never previously committed in
  this worktree)

## Completion Summary

Built `tools/codebase_health_snapshot.py`, a new module that appends `build_report()`'s live
metrics dict as one JSON line to a new append-only `agent-monitoring/codebase_health_history.jsonl`
(reusing `tools/agent-monitoring/writer.py::write_line`, never a plain unlocked append), guarded by
a frozen 14-key schema allowlist plus a `snapshot_schema_version` field that turns any future
`build_report()` shape drift into a loud `RuntimeError` instead of silent corruption. Added a
companion scorecard reader/renderer (`read_snapshots`/`build_scorecard`/`format_scorecard`) that
shows per-dimension `↑`/`↓`/`→` trend arrows across the two most recent snapshots — 11 scalar
dimensions, one folded registry-size row, and `unused_core_dependencies` rendered as a raw
value/count rather than a forced arrow — with explicit, tested graceful degradation for zero and
one historical snapshots, and with no aggregate/combined score anywhere in either the structured
output or the printed text, per this epic's own out-of-scope constraint. Two new on-demand Makefile
targets (`codebase-health-snapshot`, `codebase-health-scorecard`) were wired in, not CI-bound. All
13 new tests pass, all regression-surface tests pass, and the epic doc's corresponding bullet was
marked resolved.

Document-Update phase found and fixed a real gap the Implement phase's doc edit didn't reach: this
ticket resolves item 3 of a multi-level epic-tracking chain (this ticket → Epic K's own tracking
doc → the batch-wide resilience roadmap → the resilience epic's own parent ticket), and two of
those upstream docs (`docs/plans/architecture_resilience_remediation_roadmap.md` and
`tickets/todos/codebase-health-resilience/TCK-20260817-CODEBASE-HEALTH-RESILIENCE-EPIC.md`) mirror
Epic K's status/item list independently of the epic doc Implement already updated, and both were
left stale until this fix. Both are now updated with the matching resolved-bullet/status-line
treatment (Architecture-Verify NEEDS_CHANGES round, caught as a ticket-hygiene omission and fixed
directly).
