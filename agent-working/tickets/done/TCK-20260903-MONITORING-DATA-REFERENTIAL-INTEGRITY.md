---
status: historical
layer: observability
authority: P1
audience: agent
ticket_id: TCK-20260903-MONITORING-DATA-REFERENTIAL-INTEGRITY
phase: done
date: 2026-09-03
tags: [agent-monitoring, observability, data-quality, schema]
---

# TCK-20260903-MONITORING-DATA-REFERENTIAL-INTEGRITY

## Title
Build referential-integrity verification across `runs`/`events`/`tools`
(`events.run_id → runs.run_id`, `tools.(run_id, seq) → events.(run_id, seq)`), cross-ISO-week-
boundary aware

## Status
DONE

## Tier
standard

## Type
feature

## Priority
P1

## Request Summary
Child 6 of `TCK-20260903-MONITORING-UNIFIED-WEEKLY-EPIC`, directly implementing the requester's
explicit instruction: *"verify if they are linked between (like foreign keys)"*.
`docs/agent-monitoring/schema.md` already documents this FK model in prose (confirmed via direct
read this session): `events.jsonl` is "One record per agent call within a workflow run. FK: `run_id →
runs.run_id`" (line 126, field table line 144); `tools.jsonl` is "Joined to events by `run_id` +
`seq`" (line 342), with `run_id` documented as "FK → runs.jsonl" (line 366) and `seq` as
"FK → events.seq" (line 367). **This contract has never been automated/verified — it is prose only.**
This ticket makes it a real, tested check.

**The single most important correctness requirement for this ticket, confirmed by direct
investigation this session:** a `run_id`'s `events`/`tools` rows can legitimately land in a
**different** week folder than its own `runs.jsonl` row, or than each other — whenever a run/session
crosses an ISO-week boundary. `TCK-20260728-MONITORING-PAUSE-RESUME-SEQ-COLLISION` already confirms
pause/resume-across-a-boundary is a real, previously-encountered scenario for this exact `(run_id,
seq)` join. A referential-integrity checker that assumes same-week-folder locality will produce false
positives on entirely legitimate data — the checker must load and join across **all** week folders
for a given `run_id`, never scope its lookup to one folder.

**Documented, schema-sanctioned exceptions the checker must NOT flag** (per `schema.md`'s own text,
confirmed this session):
- Retrieval-event shadow rows: `run_id` prefix `RETRIEVAL-EVENT-<slug>` intentionally has no matching
  `runs.jsonl` row (schema.md lines 325-335) — excluded from the `events.run_id → runs.run_id` check.
- `tools.jsonl` rows with `run_id: null` — tool calls made outside an active workflow run (interactive
  session use), not an FK violation (schema.md line 366).
- `context-packet-wrapper` shadow rows with negative `seq` (`seq <= 0`, schema.md lines 145, 310) —
  deliberately disjoint from the monotonic `seq` range, excluded from the
  `tools.(run_id, seq) → events.(run_id, seq)` check.

## Scope
- Build `tools/agent-monitoring/verify_referential_integrity.py` (new script, or a new function
  added to `validate.py` alongside its existing `compute_drift_report()`-style functions —
  implementer's choice, document which and why) that:
  - Loads all week folders' `runs`/`events`/`tools` files (reusing the dual-mode/glob loading pattern
    children 1-3 establish for the new layout, not a fourth independent loader).
  - For every `events` row (excluding `RETRIEVAL-EVENT-<slug>` `run_id`s), confirms its `run_id` has
    a matching `runs` row anywhere across all week folders.
  - For every `tools` row with a non-null `run_id` and `seq >= 1` (excluding `run_id: null` and
    `seq <= 0` shadow rows), confirms a matching `events` row exists at that exact `(run_id, seq)`
    anywhere across all week folders.
  - Produces a structured report (violation counts + concrete examples: `run_id`/`seq`/week-folder of
    each orphan), matching `validate.py`'s existing report-function output style.
- New pytest suite covering, at minimum: (a) same-week-only join (baseline correctness), (b) a
  `run_id` whose `events`/`tools` rows legitimately span 2+ week folders — must NOT be flagged, (c) a
  genuinely orphaned `tools` row with no matching `events` row anywhere — MUST be flagged, (d) a
  genuinely orphaned `events` row with no matching `runs` row anywhere — MUST be flagged, (e) each of
  the 3 documented exception shapes above — must NOT be flagged.
- Run the tool against the real, post-migration corpus and capture the real report in this ticket's
  Test Summary. If it finds real violations, they must be reported and explicitly triaged in
  Implementation Notes (accepted-as-known-legacy-noise vs. a real bug needing its own follow-up) —
  never silently suppressed or worked around to make the check report clean.

## Out of Scope
- Building a general-purpose relational/SQL referential-integrity engine — only these 2 specific FK
  relationships, matching the epic's own Out of Scope boundary.
- Wiring this check into `done_checker_static.py` as a new blocking DoD gate, or into CI, unless the
  real-corpus run above finds it needs to be — if it's added as a gate, that's a deliberate decision
  to record explicitly, not an assumed default.
- Repairing any orphan this check finds — this ticket verifies and reports, it does not fix upstream
  data-quality bugs beyond what children 1/3/4's own bug fixes already cover.
- Any change to the 3 per-line record schemas.

## Acceptance Criteria
- [x] All 5 test scenarios in Scope pass, each a testable assertion.
- [x] **Explicit cross-week-join test** (scenario b above) passes — this is the key architectural
      risk this ticket exists to cover; a same-week-only implementation must fail this test.
- [x] The tool runs successfully against the real post-migration corpus and its output (clean, or
      explicitly triaged violations) is captured in Test Summary.
- [x] The tool's report format is documented (either in the script's own docstring or a doc file) well
      enough for a future consumer (dashboard, gate check, or manual audit) to parse it.

## Related Tickets
- TCK-20260903-MONITORING-UNIFIED-WEEKLY-EPIC (parent epic)
- TCK-20260903-MONITORING-DATA-MIGRATION (child 2 — hard prerequisite: needs real migrated multi-week
  data to test against)
- TCK-20260903-MONITORING-DATA-CONSUMERS-CORE, -CONSUMERS-GATES-DASHBOARD, -CODEX-REMIGRATION
  (children 3-5 — independent, file-disjoint, parallelizable with this ticket once child 2 lands)
- TCK-20260728-MONITORING-PAUSE-RESUME-SEQ-COLLISION — confirms the cross-week-boundary `(run_id,
  seq)` scenario this ticket's core correctness requirement is built around.
- TCK-20260729-SHADOW-PACKET-CALL-SITE — established the negative-`seq` shadow-row exception this
  ticket must not flag.

## Related Docs
- `docs/agent-monitoring/schema.md` lines 126, 144, 342, 366-367 (the FK contract this ticket
  automates), lines 325-335 (the `RETRIEVAL-EVENT-<slug>` exception), lines 145, 310
  (the shadow-`seq` exception).

## Related Stored Artifacts
None yet.

## Related Code Areas
- `tools/agent-monitoring/validate.py` (existing report-function style/precedent to match)
- `tools/agent-monitoring/verify_referential_integrity.py` (new, exact filename implementer's choice)

## Assumptions / Open Questions
- Assumes child 2 has landed.
- Whether this becomes a new standalone script or a new function in `validate.py` is left to the
  implementer's judgment — document the choice and why.
- Whether any real violations found against the live corpus warrant their own follow-up
  hotfix/investigation ticket is a decision to make at implementation time based on what the real run
  actually finds, not pre-decided here.
- `layer: observability` matches this repo's established pattern; `schema` tag reflects this ticket's
  focus on the record-join/schema-contract dimension, matching the prior epic's migration child's use
  of the same tag for a related shape-contract concern.

## Implementation Notes

Implemented per `staging_artifacts/TCK-20260903-MONITORING-DATA-REFERENTIAL-INTEGRITY/plan.md`'s 7
steps, in order, with no deviations from the plan's design (module placement, function signatures,
report shape, and exit-code contract all match the plan's Ratified Decisions verbatim).

**New standalone script** (Decision on item 8 from plan.md): `tools/agent-monitoring/
verify_referential_integrity.py`, not a new function in `validate.py` — `validate.py`'s only read
path is the stale SQLite index, and this ticket must not depend on it.

- `load_all_weeks(data_dir, source) -> list[tuple[dict, str]]` — globs
  `sorted(data_dir.glob(f"*/{source}.jsonl"))`, reusing the exact pattern already established by
  `record_events.py::compute_tool_stats()`. Returns `(record, week_folder)` pairs so every violation
  can cite its week. No ISO-week-shaped filtering is applied — `unknown-week` participates exactly
  like any other folder.
- `check_events_to_runs(runs, events) -> (checked, violations)` — Check 1. `valid_run_ids` is built
  from the full, all-weeks `runs` list. Excludes `run_id is None` and `RETRIEVAL-EVENT-*` prefixes
  from the checked population.
- `check_tools_to_events(events, tools) -> (checked, violations)` — Check 2. `valid_keys` is a `set`
  populated by iterating every event row (never a `dict` comprehension that could drop a colliding
  key — the real corpus has 145 duplicate `(run_id, seq)` event keys). Excludes `run_id is None`,
  `seq is None`, and `seq <= 0` from the checked population.
- `ReferentialIntegrityReport` dataclass (`events_checked`, `events_violations`, `tools_checked`,
  `tools_violations`) + `.to_text(sample_size=20)`, mirroring `compute_tool_count_drift_report()`'s
  header/count/capped-sample/`"... and N more"` convention.
- `compute_referential_integrity_report(data_dir=DEFAULT_DATA_DIR)` — the library-callable entry
  point; `build_parser()`/`main(argv=None)` — the CLI wrapper. `main()` always exits 0 (Decision on
  item 4) — no `--strict` flag was added, per the plan's explicit scope guard.

**Test suite**: all 11 tests from test_plan.md landed in `tests/tools/
test_verify_referential_integrity.py`, all passing. The cross-week test
(`test_cross_week_run_id_not_flagged`) fixture places the `runs.jsonl` row in `<tmp>/data/2026-W10/`
and the matching `events.jsonl`/`tools.jsonl` rows in `<tmp>/data/2026-W11/` for the same `run_id` —
directly modeled on investigation.md's confirmed real-corpus shape
(`TCK-20260820-EPIC-WORLD-RENDERING-CORE`'s runs-in-W34/events-in-W35 split), not a synthetic guess.
`test_unknown_week_folder_included_in_join` covers both directions (run in `unknown-week`/event in a
real week, and vice versa). `test_duplicate_event_key_does_not_break_lookup` reproduces the real
145-duplicate-key shape with two `events` rows sharing one `(run_id, seq)` key. `test_real_corpus_smoke_run`
deliberately does not assert zero violations.

**Regression check**: `pytest tests/tools/test_validate_agent_monitoring.py
tests/tools/test_migrate_monitoring_data.py tests/tools/test_agent_monitoring_manifest.py
tests/tools/test_agent_monitoring_legacy_reader.py` shows 6 pre-existing failures (all in
`test_agent_monitoring_manifest.py`/`test_agent_monitoring_legacy_reader.py`, all
`FileNotFoundError` on the now-retired flat `agent-monitoring/events.jsonl`/`runs.jsonl` paths).
Confirmed via `git stash` that these 6 failures are identical and pre-existing on this branch before
any of this ticket's changes — unrelated to this ticket's diff, not touched or caused by it. All 69
other tests in that regression sweep pass unmodified.

**Step 6 — real-corpus findings, triaged:**
- Check 1 (`events.run_id -> runs.run_id`): **18 distinct `run_id`s** (117 individual event-row
  violations across those 18 `run_id`s — several have multiple `seq` rows, e.g. `run-E43B-1782052032`
  contributes 7) out of 9,018 events checked have no matching `runs.jsonl` row anywhere. This matches
  investigation.md's "~18 Check-1 orphans" figure exactly once counted by distinct `run_id` rather than
  by individual event row (investigation.md's own count was per-`run_id`; this tool's `violations`
  list is per-event-row by design, per plan.md's exact spec, so a future reader of raw counts should
  expect this — the report's `.to_text()` sample already shows both). No material difference from
  investigation.md.
- Check 2 (`tools.(run_id, seq) -> events.(run_id, seq)`): **17,471 of 136,001 checked tool-call rows
  (12.8%)** have no matching event at their exact `(run_id, seq)` — investigation.md found ~17,274 of
  135,804 (~12.7%). The small (~1.1%) increase in both checked and violation counts is consistent with
  ordinary corpus growth between investigation time and this implementation run (this session's own
  in-flight tool-call rows are themselves part of that growth — see below) — not a material
  discrepancy.
- **Triage — bulk of Check-2 volume**: consistent with investigation.md's conclusion, the large
  majority is attributable to already-documented, explicitly-not-backfilled historical corruption from
  `TCK-20260711-MONITORING-TOOLCOUNT-SIDECAR-COLLISION` and `TCK-20260824-SIDECAR-CROSS-SESSION-SCOPE`
  (pre-2026-08-24 rows).
- **Triage — `TCK-20260902-MONITORING-SHARD-MIGRATION`**: confirmed directly — exactly 229 Check-2
  violation rows across `seq` values `{1,2,3,4,5,6}`, all in week `2026-W36`, and confirmed zero
  matching rows in any `runs.jsonl`/`events.jsonl` file anywhere in the corpus. This matches
  investigation.md's finding exactly. **Not investigated or fixed further, per this ticket's explicit
  Out of Scope** — flagged in the new `docs/agent-monitoring/schema.md` Known Limitations entry as an
  open finding warranting possible follow-up.
- **Triage — this ticket's own in-flight rows**: confirmed this session's own `run_id`
  (`TCK-20260903-MONITORING-DATA-REFERENTIAL-INTEGRITY`) appears with 229 Check-2 violation rows
  (`seq` 1-3, its 3 completed phases' tool calls) at the time of the real-corpus run — expected and
  transient (its own phase-completion events had not yet been batch-written at that point in the
  pipeline), matching investigation.md's documented "benign class" explanation.
- No orphan was fixed, backfilled, or otherwise remediated — report-only, per Scope Guards.

**Docs**: added a "Referential Integrity Verification" subsection to `docs/agent-monitoring/
schema.md`'s Known Limitations section (between "Manual/ad hoc run_id convention" and "Full
evidence"), with the real Step 6 numbers above (not placeholders). Ran `make knowledge-index-update`
afterward — completed successfully (4 files re-embedded: this doc plus the 3 sibling epic-child
tickets moved into `tickets/inprogress/` earlier in this shared-worktree session, 3281 chunks from
cache, 0 deleted).

**Shared-worktree hygiene**: confirmed via `git status` before and after that
`src/api/agent_ops_dashboard/ingest.py`, `tests/tools/test_done_checker_static.py`, and
`tools/gate_checks/done_checker_static.py` were already modified by a concurrent child ticket's
session before this implementer started — none of these were touched by this implementation, per the
explicit "do not touch children 3/4/5's files" instruction.

No deviations from `plan.md` occurred; no update to `staging_artifacts/.../plan.md`'s own text was
needed.

## Test Summary

```
pytest tests/tools/test_verify_referential_integrity.py -v
========================= 11 passed in 1.48s =========================
```

All 11 tests pass: `test_same_week_only_join_baseline`, `test_cross_week_run_id_not_flagged`,
`test_orphan_tools_row_no_matching_event_anywhere_is_flagged`,
`test_orphan_event_no_matching_run_anywhere_is_flagged`,
`test_retrieval_event_run_id_excluded_from_check`,
`test_null_run_id_tools_row_excluded_from_check`,
`test_negative_and_zero_seq_tools_rows_excluded_from_check`,
`test_duplicate_event_key_does_not_break_lookup`, `test_unknown_week_folder_included_in_join`,
`test_report_output_matches_validate_py_style`, `test_real_corpus_smoke_run`.

Regression re-check:
```
pytest tests/tools/test_validate_agent_monitoring.py tests/tools/test_migrate_monitoring_data.py \
  tests/tools/test_agent_monitoring_manifest.py tests/tools/test_agent_monitoring_legacy_reader.py
========================= 6 failed, 69 passed, 3 skipped =========================
```
The 6 failures are pre-existing (confirmed via `git stash` to reproduce identically before this
ticket's changes) — `FileNotFoundError` on the retired flat `agent-monitoring/{runs,events}.jsonl`
paths in `test_agent_monitoring_manifest.py`/`test_agent_monitoring_legacy_reader.py`, unrelated to
this ticket's diff.

**Real-corpus run** (`python3 tools/agent-monitoring/verify_referential_integrity.py`, exit code 0):

```
--- Referential Integrity Report ---

Check 1: events.run_id -> runs.run_id
  Events checked (excludes RETRIEVAL-EVENT-* run_ids): 9018
  Violations (no matching runs.jsonl row anywhere): 117   [18 distinct run_ids]

Check 2: tools.(run_id, seq) -> events.(run_id, seq)
  Tool rows checked (excludes run_id: null and seq <= 0): 136001
  Violations (no matching events row anywhere): 17471   (12.8%)
```

See Implementation Notes above for the full triage of these numbers against investigation.md.

## Files Changed
- `tools/agent-monitoring/verify_referential_integrity.py` (new)
- `tests/tools/test_verify_referential_integrity.py` (new)
- `docs/agent-monitoring/schema.md` (modified — new "Referential Integrity Verification" Known
  Limitations subsection)
- `tickets/inprogress/TCK-20260903-MONITORING-DATA-REFERENTIAL-INTEGRITY.md` (this file — Status,
  Acceptance Criteria, Implementation Notes, Test Summary, Files Changed, Completion Summary)

Not created/modified by this implementer, but pre-existing in this shared worktree at the time this
run started (staging artifacts for this ticket, authored during this ticket's own earlier
Investigate/Plan phases before this Implement run began — not rewritten by this run):
- `staging_artifacts/TCK-20260903-MONITORING-DATA-REFERENTIAL-INTEGRITY/plan.md`
- `staging_artifacts/TCK-20260903-MONITORING-DATA-REFERENTIAL-INTEGRITY/investigation.md`
- `staging_artifacts/TCK-20260903-MONITORING-DATA-REFERENTIAL-INTEGRITY/test_plan.md`

Not touched (concurrent children 3/4/5 work already present in this shared worktree, verified via
`git status` before and after): `src/api/agent_ops_dashboard/ingest.py`,
`tests/tools/test_done_checker_static.py`, `tools/gate_checks/done_checker_static.py`,
`agent-monitoring/data/2026-W36/tools.jsonl` (monitoring-tooling auto-write from concurrent-session
activity, not an edit made by this implementer).

## Completion Summary
Built `tools/agent-monitoring/verify_referential_integrity.py`, a new, standalone, report-only script
that automates both documented FK relationships in `docs/agent-monitoring/schema.md`
(`events.run_id -> runs.run_id`; `tools.(run_id, seq) -> events.(run_id, seq)`) via a multi-week-aware
loader that reads the union of every `agent-monitoring/data/<week>/` folder, never scoping a join to a
single week. Added an 11-test suite (`tests/tools/test_verify_referential_integrity.py`), all passing,
with the cross-week test modeled directly on real corpus shapes found during investigation. Ran the
finished tool against the real corpus (18 distinct Check-1 orphan `run_id`s; 17,471/136,001, 12.8%,
Check-2 orphans), triaged the findings into this ticket, and added a new "Referential Integrity
Verification" entry to `docs/agent-monitoring/schema.md`'s Known Limitations section with the real
numbers. Implementation work is complete; the ticket remains `INPROGRESS` pending the Test/Parity/
Verify/Finalize phases of the pipeline.

Independently re-verified through the full standard-tier pipeline: Test phase (test-scoper)
independently re-ran all 11 tests, confirmed the cross-week test's fixture is genuine (real
different-week folders, not a same-week test in disguise), confirmed `main()` never exits nonzero
by reading the code directly, and confirmed the 6 "pre-existing" regression failures match the
already-known set from child 2's own Deviations. Architecture-Verify (architecture-reviewer):
**APPROVED** — confirmed pure read-only (no `open()` write calls anywhere), zero scope creep, no
SQLite dependency, no remediation of the real violations found. Verify (done-checker): **READY TO
CLOSE**, 13/13 Definition-of-Done conditions PASS.
