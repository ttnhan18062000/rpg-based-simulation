---
status: historical
layer: observability
authority: P1
audience: agent
ticket_id: TCK-20260904-MONITORING-TEMPORAL-WEEK-CONSISTENCY-CHECK
phase: done
date: 2026-09-04
tags: [agent-monitoring, observability, data-quality]
---

# TCK-20260904-MONITORING-TEMPORAL-WEEK-CONSISTENCY-CHECK

## Title
Add a source-aware, report-only check verifying each record's own timestamp is consistent with the
ISO week of the folder it lives in, wired into `done_checker_static.py`'s Part A checklist

## Status
DONE

## Tier
standard

## Type
feature

## Priority
P1

## Request Summary
User request, verbatim: *"do you have tools for checking new rule (like data inside a weekly shard
must inside the date range) and wire them to the agent working"*.

Follows directly from `TCK-20260903-MONITORING-UNIFIED-WEEKLY-EPIC` (all 7 children DONE), which
unified `runs`/`events`/`tools` under `agent-monitoring/data/YYYY-Www/{runs,events,tools}.jsonl` and
built `tools/agent-monitoring/verify_referential_integrity.py` — a report-only FK checker across the
corpus. This ticket adds a second, complementary check: does each record's own timestamp field
actually fall within the ISO week its containing folder claims?

**Critical design constraint, already confirmed this session — this is NOT a uniform strict rule
across all 3 sources**: the epic's own write-path design (`TCK-20260903-MONITORING-DATA-WRITE-PATH-UNIFY`)
deliberately buckets by **write-time**, not by each record's own timestamp field:

- `tools.jsonl`: `post_tool_hook.py` computes `iso_week` from `now_dt` and writes the SAME `now_dt`
  as the record's own `ts` field — bucketing key and record timestamp are the identical value. A
  mismatch here is a genuine anomaly (data corruption, clock skew, or a future bug), not expected
  behavior.
- `events.jsonl`: `record_events.py` computes `iso_week` once per batch (write-time), but each
  event's own `ts` field is set earlier, at the moment that phase actually happened. Usually close to
  write-time, but not guaranteed identical — mismatches are plausible but should be rare.
- `runs.jsonl`: `record_run.py` buckets by write-time, but the record's own `start_ts` field is
  captured at session START, potentially far earlier. **A run whose `start_ts` and completion/write
  time fall in different ISO weeks is explicitly documented as "expected and legitimate, not a bug"**
  (the epic's own Assumptions section) — e.g. any long-running or paused/resumed ticket crossing a
  week boundary.

A single "must be inside the folder's week" rule applied uniformly would false-positive heavily on
legitimate `runs.jsonl` divergence, exactly the same class of mistake the referential-integrity
checker had to avoid for FK joins. This ticket must be source-aware from the start, per the
requester's own explicit choice (source-aware report-only, confirmed via AskUserQuestion this
session) — not treat all 3 sources identically.

**Wiring constraint, confirmed by direct source read this session**: `tools/gate_checks/
done_checker_static.py::run_static_precheck()` (line 555) aggregates a fixed tuple of `check_*`
functions, each returning `("PASS"|"FAIL"|"CLEANED", evidence_string)` — there is currently **no**
non-blocking status value (no `"WARN"`/`"INFO"`). The requester explicitly chose "report only,
never gates" for the rule itself, matching the referential-integrity tool's own philosophy, plus
"wired as a new done-checker DoD condition." Reconciling these two choices is this ticket's own
first design decision to make and record — the most direct path (recommended, not mandated) is: the
new check always returns `("PASS", <evidence carrying real findings>)`, extending the checklist
with real information every Verify run surfaces automatically, without ever contributing to a
`FAIL`/blocked ticket close. An alternative (extending the status vocabulary with a new non-blocking
value) is a legitimate but larger-blast-radius option — Plan should weigh both and record the choice
with rationale, not default silently.

## Scope
- A new function in `tools/agent-monitoring/verify_referential_integrity.py` (extend the existing
  report-only tool, matching its own module docstring's framing as the home for corpus-health
  checks) OR a new sibling script — implementer's choice, document which and why, following the
  same reasoning `TCK-20260903-MONITORING-DATA-REFERENTIAL-INTEGRITY` used for its own
  standalone-vs-`validate.py` decision.
- Reads the real multi-week `agent-monitoring/data/*/` corpus (reuse `load_all_weeks()` or an
  equivalent pattern — do not build a 4th independent loader).
- For each source, determine the correct authoritative timestamp field(s) to check against the
  containing folder's own ISO week (parsed from the folder name, e.g. `2026-W36`):
  - `tools.jsonl`: `ts` — expected to always match; any mismatch is a real anomaly to report clearly
    as such (not lumped in with expected divergence).
  - `events.jsonl`: `ts` — expected to usually match; report mismatches, but do not imply they are
    necessarily bugs.
  - `runs.jsonl`: `start_ts` — expected to sometimes legitimately diverge; report as informational
    count/examples, explicitly framed as "expected divergence," not implicitly equated with
    `tools.jsonl`'s anomaly framing.
- Produces a structured, human-readable report (counts + concrete examples per source, matching
  `verify_referential_integrity.py`'s existing `.to_text()` style) distinguishing "genuine anomaly"
  from "expected divergence" in the output itself — a reader must not have to infer which is which.
- Wire into `tools/gate_checks/done_checker_static.py::run_static_precheck()` as a new
  `check_temporal_week_consistency()`-style function, following the exact `(status, evidence)`
  tuple convention every other check already uses, and add it to the `checks` tuple. Update the
  docstring's "Aggregate all 7 Part A checks" count.
- Handle the `unknown-week` fallback folder explicitly: no ISO week to compare against, so records
  in `unknown-week` are structurally exempt from this check, not silently miscounted as a mismatch.
- New pytest coverage: at minimum (a) a `tools.jsonl` record whose `ts` matches its folder — no
  finding; (b) a `tools.jsonl` record whose `ts` does NOT match its folder — flagged as a genuine
  anomaly; (c) a `runs.jsonl` record whose `start_ts` is in an earlier week than its folder — flagged
  as expected divergence, not an anomaly; (d) a record in `unknown-week` — exempt, no finding either
  way; (e) `done_checker_static.py`'s new check wired in and returning `PASS` with real evidence
  against a real or synthetic multi-week fixture.
- Run the real script against the live corpus once implemented, capture genuine findings in this
  ticket's Test Summary (same discipline as the referential-integrity ticket — report what's
  actually found, don't assume clean).

## Out of Scope
- Modifying `post_tool_hook.py`/`record_run.py`/`record_events.py`'s write-time bucketing design —
  this ticket only verifies the existing design's consequences, does not change bucketing logic.
- Repairing, re-bucketing, or backfilling any record found to be a genuine anomaly — report-only,
  matching every prior corpus-health tool in this repo's history.
- Extending `done_checker_static.py`'s status vocabulary beyond `PASS`/`FAIL`/`CLEANED` unless Plan
  explicitly decides that's the right design (see Request Summary's wiring-constraint discussion) —
  if Plan chooses the always-`PASS`-with-evidence approach, this is out of scope by construction.
- Any change to the referential-integrity FK checks themselves (`check_events_to_runs`/
  `check_tools_to_events`) — this is an additive, independent check.

## Acceptance Criteria
- [x] The new check reads the real multi-week corpus and correctly distinguishes, per source,
      genuine timestamp/week anomalies from expected write-time-vs-record-time divergence (`runs.jsonl`
      in particular must not false-positive on legitimate week-spanning tickets).
- [x] `unknown-week` records are structurally exempt, not miscounted.
- [x] The check is wired into `done_checker_static.py::run_static_precheck()`'s Part A checklist and
      runs automatically at Verify time for every future ticket, never blocking/failing a ticket close
      on its own (report-only, per the requester's explicit choice).
- [x] Real findings from a run against the live corpus are captured in this ticket's Test Summary,
      not assumed clean.
- [x] All new tests pass; existing `done_checker_static.py`/`test_done_checker_static.py` tests still
      pass with the new check added to the fixed checklist tuple.

## Related Tickets
- TCK-20260903-MONITORING-UNIFIED-WEEKLY-EPIC (parent epic — established the unified layout and
  write-time bucketing design this check verifies the consequences of)
- TCK-20260903-MONITORING-DATA-WRITE-PATH-UNIFY (child 1 — the write-time bucketing design itself,
  confirmed via direct source read this session: `post_tool_hook.py`'s `ts`==bucketing-key identity
  for `tools.jsonl`, `record_events.py`'s once-per-batch `iso_week` computation for `events.jsonl`,
  `record_run.py`'s write-time-not-`start_ts` decision for `runs.jsonl`, with its own recorded
  rationale)
- TCK-20260903-MONITORING-DATA-REFERENTIAL-INTEGRITY (child 6 — the report-only FK-verification tool
  this ticket's own report-only design and likely code location directly follow)
- TCK-20260810-MONITORING-NEGATIVE-DURATION-TIMESTAMP-BUG /
  TCK-20260810-MONITORING-NEGATIVE-DURATION-BULK-CLEANUP — prior precedent for handling a different
  class of timestamp-quality issue (`end_ts` before `start_ts`) in this same corpus; useful precedent
  for how this repo has previously balanced "genuine bug" vs. "acceptable historical noise" framing.

## Related Docs
- `docs/agent-monitoring/schema.md` — documents each source's timestamp field and the write-time
  bucketing design this check verifies against; may need a new Known Limitations entry once real
  findings are captured (decide at implementation time, matching child 6's own precedent).

## Related Stored Artifacts
None yet.

## Related Code Areas
- `tools/agent-monitoring/verify_referential_integrity.py` (likely extension point, implementer's
  choice to confirm)
- `tools/gate_checks/done_checker_static.py` (`run_static_precheck()`, new `check_*` function)
- `tests/tools/test_done_checker_static.py`
- `tests/tools/test_verify_referential_integrity.py` (if the check lands in that module)

## Assumptions / Open Questions
- Whether the new check lives in `verify_referential_integrity.py` or a new sibling script is left to
  the implementer's judgment, matching child 6's own precedent for this exact kind of decision —
  document the choice and why.
- Whether to reconcile "report-only" with "wired into done-checker's PASS/FAIL-only checklist" via
  always-PASS-with-evidence (recommended, smaller blast radius) or a new non-blocking status value
  (larger blast radius, touches the shared checklist schema every other check also uses) is a real
  design decision for Plan to make explicitly, not silently default.
- `layer: observability` matches this repo's established pattern for all `agent-monitoring`-adjacent
  tooling tickets.

## Implementation Notes

Implemented all 8 plan.md steps in order, exactly as specified — no deviations from plan.md.

1. **Scaffolded `tools/agent-monitoring/verify_temporal_week_consistency.py`.** Imports
   `load_all_weeks`/`DEFAULT_DATA_DIR` from `verify_referential_integrity.py` and
   `RUNS_FIELD_PRIORITY`/`EVENTS_FIELD_PRIORITY` from `migrate_monitoring_data.py` (identity-checked
   by test 6, never re-declared). Added `TOOLS_FIELD_PRIORITY = ["ts"]` as a new, independent,
   local constant (not a re-typed copy of the 2 imported lists — explicitly commented as such).
   `_select_ts_value()` reuses the truthy-first-match idiom already used by
   `bucket_lines_by_week_multi_field()` (by description, not by import — that function operates on
   raw JSONL line strings, this one on already-parsed dicts). `SourceFinding` dataclass carries
   `source`, `category_label`, `checked`, `matched`, `mismatches`, `exempt_unknown_week`,
   `skipped_unparseable`. `check_temporal_consistency()` classifies each `(record, week_folder)` pair
   into exactly one of 4 buckets (exempt / skipped / matched / mismatch).
2. **Runs' "expected divergence" / events' "possible divergence" categorization** — no additional
   code beyond Step 1's `category_label` parameter, already correctly wired per source at the
   `compute_temporal_week_consistency_report()` call sites. Verified by test 3 (the single
   highest-priority test in the suite).
3. **`unknown-week` exemption** — already implemented in Step 1's first branch (checked before any
   field-selection attempt); verified as a distinct bucket from `skipped_unparseable` by test 4 (one
   record per source, including a real-corpus-shaped numeric-epoch-float `start_ts` in
   `unknown-week/runs.jsonl`, matching investigation.md's confirmed real-corpus shape).
4. **"No usable/parseable field" skip bucket** — already implemented in Step 1's two
   `skipped_unparseable`-incrementing branches; verified distinct from match/mismatch by test 5, and
   the import-identity guard (not just equality) verified by test 6.
5. **`TemporalWeekConsistencyReport` dataclass + `.to_text()` + `main()` CLI.** `.to_text()` renders
   one section per source via a shared `_section()` helper, each header explicitly naming its own
   category in capitalized form (`GENUINE ANOMALIES`, `POSSIBLE DIVERGENCES`, `EXPECTED DIVERGENCE,
   NOT BUGS`) so no reader has to infer severity from position/ordering. A summary line at the top
   states the total rows examined across all 3 sources, explicitly warning that a 0-mismatch count
   does not mean the check is inert (investigation.md's Risk #3). `main()`/`build_parser()` mirror
   `verify_referential_integrity.py`'s own CLI exactly — always exits 0, no `--strict` flag.
6. **Wired `check_temporal_week_consistency()` into `done_checker_static.py`.** Added the
   `_MONITORING_DIR` sys.path insertion and import alongside the existing `_TOOLS_DIR` setup;
   new `check_temporal_week_consistency()` function always returns `("PASS", evidence)` per Decision 2
   (never introduces a new status value; `NA` already means tier-skip, not "informational"). Added
   `("temporal_week_consistency", check_temporal_week_consistency())` as the 8th entry in
   `run_static_precheck()`'s `checks` tuple; updated the docstring "7" -> "8".
   **Regression fix landed**: `tests/tools/test_done_checker_static.py`'s
   `test_run_static_precheck_all_pass_eligible` updated from `assert len(results) == 7` to
   `assert len(results) == 8`, with its explanatory comment's addition-history line extended
   (5->6->7->8). Added new test `test_done_checker_new_check_wired_and_returns_pass_with_evidence`
   confirming the new check is present, always `PASS`, carries non-trivial evidence, and degrades
   gracefully against `_scaffold_precheck_repo`'s fixture (no `agent-monitoring/data/` directory at
   all — `load_all_weeks()`'s empty glob, not an exception).
7. **Real-corpus smoke run — real findings, not assumed clean.** See Test Summary below for the
   actual transcribed numbers.
8. **`docs/agent-monitoring/schema.md` Known Limitations entry** added, titled "Temporal Week
   Consistency Verification", placed immediately after the existing "Referential Integrity
   Verification" entry, mirroring its structure and citing Step 7's real numbers plus the "why zero
   is expected right now, not proof the check is inert" caveat. Ran `make knowledge-index-update`
   afterward (17 files re-embedded, 3290 from cache — succeeded).

No conflicts with the plan were discovered; no architectural issue surfaced during implementation.

## Test Summary

New test module `tests/tools/test_verify_temporal_week_consistency.py` (8 tests, all synthetic-fixture
tests plus one real-corpus smoke test) — all pass:

```
tests/tools/test_verify_temporal_week_consistency.py::test_tools_ts_matches_folder_no_finding PASSED
tests/tools/test_verify_temporal_week_consistency.py::test_tools_ts_mismatch_flagged_as_genuine_anomaly PASSED
tests/tools/test_verify_temporal_week_consistency.py::test_runs_start_ts_earlier_week_flagged_as_expected_divergence_not_anomaly PASSED
tests/tools/test_verify_temporal_week_consistency.py::test_unknown_week_records_exempt_no_finding_either_way PASSED
tests/tools/test_verify_temporal_week_consistency.py::test_no_usable_timestamp_field_in_known_folder_skipped_not_counted_as_match_or_mismatch PASSED
tests/tools/test_verify_temporal_week_consistency.py::test_field_priority_reused_from_migration_not_reinvented PASSED
tests/tools/test_verify_temporal_week_consistency.py::test_report_distinguishes_anomaly_from_expected_divergence_in_text PASSED
tests/tools/test_verify_temporal_week_consistency.py::test_real_corpus_smoke_run PASSED
8 passed in 1.64s
```

`tests/tools/test_done_checker_static.py` — 104 tests (103 pre-existing + 1 new
`test_done_checker_new_check_wired_and_returns_pass_with_evidence`), all pass, including the updated
`test_run_static_precheck_all_pass_eligible` (`len(results) == 8`).

Full scoped regression sweep (per test_plan.md's Scoped Pytest Commands):

```
pytest tests/tools/test_verify_referential_integrity.py tests/tools/test_migrate_monitoring_data.py \
  tests/tools/test_migrate_tools_shards.py tests/tools/test_done_checker_static.py \
  tests/tools/test_verify_temporal_week_consistency.py -q
142 passed, 5 skipped in 3.55s
```

(5 skips are pre-existing, unrelated to this ticket's diff.)

**Real-corpus findings (Step 7), run 2026-09-04 via
`python3 tools/agent-monitoring/verify_temporal_week_consistency.py` against the live
`agent-monitoring/data/` directory:**

| Source | Total rows | Checked | Matched | Mismatches | Exempt (unknown-week) | Skipped (unparseable) |
|---|---|---|---|---|---|---|
| `tools.jsonl` | 186,273 | 186,272 | 186,272 | **0** (genuine anomaly) | 1 | 0 |
| `events.jsonl` | 9,024 | 8,996 | 8,996 | **0** (possible divergence) | 28 | 0 |
| `runs.jsonl` | 1,394 | 1,389 | 1,389 | **0** (expected divergence) | 5 | 0 |

**Total rows examined across all 3 sources: 196,691. Zero mismatches anywhere.**

This is honestly framed as the *expected* first-run result, not a retroactive finding: the corpus's
own current week-folder layout was constructed by the equivalent of this exact same
field-priority-lookup + tolerant-parser logic (the same lists/parser this check imports and reuses),
and no `runs.jsonl` row has yet been through a full week-spanning pause/resume cycle since the unified
write-time-bucketing design went live (`TCK-20260903-MONITORING-DATA-WRITE-PATH-UNIFY`, 2026-09-03) —
this check and that design landed within the same ISO week (`2026-W36`). This check's real value is
**prospective** (catching the first genuine future write-time-vs-record-time divergence, e.g. the
next long-running ticket whose `start_ts` and `runs.jsonl` write land in different weeks) — **not
retrospective**. Nothing was found broken today; nothing was fixed. No record was repaired, re-bucketed,
or backfilled (report-only, per Scope Guards).

## Files Changed

- `tools/agent-monitoring/verify_temporal_week_consistency.py` (new) — the check module itself
  (`SourceFinding`, `check_temporal_consistency()`, `TemporalWeekConsistencyReport`,
  `compute_temporal_week_consistency_report()`, `main()`/`build_parser()` CLI).
- `tools/gate_checks/done_checker_static.py` (modified) — added the `_MONITORING_DIR` sys.path
  insertion + import, new `check_temporal_week_consistency()` function, wired as the 8th entry in
  `run_static_precheck()`'s `checks` tuple, docstring count "7" -> "8".
- `tests/tools/test_verify_temporal_week_consistency.py` (new) — 8 tests covering all 4 buckets
  per source, the field-priority import-identity guard, the report-text anomaly/divergence
  distinction, and a real-corpus smoke run.
- `tests/tools/test_done_checker_static.py` (modified) — `test_run_static_precheck_all_pass_eligible`
  updated `len(results) == 7` -> `8` (comment history extended); new
  `test_done_checker_new_check_wired_and_returns_pass_with_evidence` test added.
- `docs/agent-monitoring/schema.md` (modified) — new "### Temporal Week Consistency Verification"
  Known Limitations entry, placed after the existing "Referential Integrity Verification" entry,
  citing Step 7's real numbers.
- `staging_artifacts/TCK-20260904-MONITORING-TEMPORAL-WEEK-CONSISTENCY-CHECK/plan.md`,
  `investigation.md`, `test_plan.md` — created during this run's own Investigate/Plan phases
  (pre-existing at the start of this Implement run, part of this run's real changeset).
- `tickets/inprogress/TCK-20260904-MONITORING-TEMPORAL-WEEK-CONSISTENCY-CHECK.md` (modified) — this
  file: Implementation Notes, Test Summary, Files Changed, Completion Summary filled in; Acceptance
  Criteria checked off.

Not changed (confirmed by design, per Scope Guards): `verify_referential_integrity.py`'s own
`ReferentialIntegrityReport`/`check_events_to_runs`/`check_tools_to_events`/`load_all_weeks`;
`migrate_monitoring_data.py`'s `RUNS_FIELD_PRIORITY`/`EVENTS_FIELD_PRIORITY`; `post_tool_hook.py`,
`record_run.py`, `record_events.py`'s write-time bucketing design; `docs/mechanics/*.md`,
`docs/engine/*.md`, `docs/parity_ledger/*.yaml` (none govern agent-monitoring tooling, per
investigation.md).

## Completion Summary

Added a new, source-aware, report-only script
(`tools/agent-monitoring/verify_temporal_week_consistency.py`) that checks whether each record's own
timestamp field in the multi-week `agent-monitoring/data/<week>/{runs,events,tools}.jsonl` corpus is
consistent with the ISO week of the folder it physically lives in, distinguishing `tools.jsonl`
genuine anomalies from `events.jsonl` possible divergence and `runs.jsonl` expected (legitimate)
divergence, with `unknown-week` records structurally exempt and unparseable-field records in a
separate skip bucket. Wired into `done_checker_static.py::run_static_precheck()` as an 8th Part A
check that always returns `PASS` with real evidence, never blocking a ticket close. A real run against
the live corpus (196,691 rows) found zero mismatches across all 3 sources — the expected first-run
result, documented honestly in both the ticket and a new `docs/agent-monitoring/schema.md` Known
Limitations entry as prospective (not retroactive) value. All 8 plan.md steps completed with no
deviations; 8 new unit tests plus a done-checker wiring test all pass, alongside the full existing
regression suite (142 passed, 5 pre-existing skips).

`graphify update .` was deliberately deferred both during Implement and again at Verify — this
worktree's own attempts consistently hit a node-count mismatch warning (`34306` vs. `34353`) caused
by another concurrently-active, locked worktree (`m2-foundational-systems-tickets`) also writing to
the shared `graphify-out/graph.json` state; `--force` was correctly avoided both times to not clobber
that session's in-progress graph state. This is a non-durable, safely-re-runnable local convenience
index (not one of the 13 Definition-of-Done conditions), so it does not block Finalize — recorded
here explicitly, not silently skipped, as a fast follow-up once the other worktree's lock clears.

Independently re-verified through the full standard-tier pipeline: Test phase (test-scoper)
independently re-ran 142/142, read both critical correctness-guard tests in full (runs.jsonl
expected-divergence, tools.jsonl genuine-anomaly) and confirmed genuine, confirmed the `len(results)
==7→8` regression fix and the always-`PASS` contract by reading the actual code. Architecture-Verify
(architecture-reviewer): **APPROVED** — pure read-only, zero scope creep, `done_checker_static.py`'s
existing check contract preserved, the report-clarity design goal confirmed as a structural property
of the output text itself. Verify (done-checker): **READY TO CLOSE**, 13/13 Definition-of-Done
conditions PASS, with 2 minor non-blocking notes (a test-count arithmetic slip in this Test Summary,
now corrected; the graphify deferral, now documented above) — neither required reopening Implement.
