---
status: historical
layer: observability
authority: P1
audience: agent
ticket_id: TCK-20260915-MONITORING-INTEGRITY-BACKLOG
phase: done
date: 2026-09-15
tags: [agent-monitoring, data-quality]
---

# TCK-20260915-MONITORING-INTEGRITY-BACKLOG

## Title
`make agent-monitoring-validate` is red today, 34 September closures have no run record, and 9 working_log rows break the CSV schema — a backlog of integrity debt that no report surfaces

## Status
DONE

## Tier
standard

## Type
repair

## Priority
P2

## Request Summary
Five related integrity defects, grouped because each is small and they share one question: which of
these do we fix, and which do we accept and document?

**1. The integrity gate is failing right now.** `make agent-monitoring-validate` exits non-zero with
19 warnings of the form "Run marked DONE has no working_log entry". All 19 are June-era
(`TCK-20260619-*`, `TCK-20260629-SIMQ-*`). A permanently-red gate trains people to ignore it — the
same failure mode `TCK-20260913-PARITY-BASELINE-EQUALITY-GATE-PENALIZES-IMPROVEMENT` describes.

**2. 34 September closures have no run record at all**, clustered on 2026-09-02 (4), 09-03 (13),
09-04 (14), 09-05 (3). The tight clustering points at one hand-orchestrated batch rather than steady
leakage — the gap `TCK-20260903-HAND-ORCHESTRATED-TICKETS-MISSING-MONITORING-COVERAGE` addressed.

**3. 9 of 2,013 `working_log.csv` rows (0.4%) do not match the 6-column schema** — 4 rows with 7
fields, 2 with 8, 3 with 9. Cause is unescaped commas in the **title** field, e.g.
`"Clan lifecycle -- joining, leaving, and succession-on-death (M4 idea 40)"`, which shifts every
later column so the status column contains prose. Any status-based query silently misreads them;
this review hit exactly that while counting closures by status.

**4. 66 runs and 55 events carry an unusable `ts`** (None, or a float/int epoch where consumers
expect an ISO string). All 66 runs are W24–W27 (June), so recent windows are not deflated — but any
time-windowed query silently drops them.

**5. `agent-monitoring/data/unknown-week/` holds 34 rows** — the shard rows land in when no week
key can be derived (29 of them have `ts: None`).

## Scope
- For each of the five: fix, or accept with a written reason. A per-item disposition is the
  deliverable; a blanket "cleanup" is not.
- Item 1 specifically needs a decision on the gate: backfill the 19, exclude pre-schema records, or
  ratchet — but it should not stay red indefinitely.
- Item 3 needs the **writer** fixed (title-field quoting) as well as any decision about the 9
  existing rows.

## Out of Scope
- Rewriting `working_log.csv` history beyond the 9 malformed rows, if repair is chosen at all.
- The duplicate-row ratchets from `TCK-20260914-MONITORING-SURFACE-DEAD-MECHANISMS` (84 duplicate
  `ticket_id`s, 46 `(ticket_id, title)` pairs) — those deliberately freeze a historical baseline and
  are not this ticket's to touch.

## Acceptance Criteria
- [x] `make agent-monitoring-validate` now passes (exit 0) against the real corpus — the true cause
      of its redness was the undocumented "no events" ERROR class (6 legacy instances), not the
      "no working_log entry" WARNING class the ticket text named (warnings never gate this
      script's exit code — confirmed by reading `validate.py`'s own `if errors: sys.exit(1)`).
- [x] Each of the five items has a recorded disposition — see investigation.md's Disposition
      summary table: item 1 fixed, item 2 accept+document+ratchet (with a corrected, much larger
      real baseline: 218, not 34), item 3 fixed (writer) + repaired (9 rows), item 4 and item 5
      accept+document+ratchet.
- [x] The working_log writer already quotes fields containing commas (`csv.writer(...,
      quoting=csv.QUOTE_MINIMAL)`, unchanged) — a new explicit test,
      `test_comma_bearing_title_round_trips`, proves a real comma-bearing title round-trips exactly.
- [x] Every new detector ratchets from a measured baseline; none asserts zero — 4 conditions in
      `monitoring_integrity_backlog_check.py` (218/66/55/34), plus `validate.py`'s own date-cutoff
      exclusion (not a zero-tolerance assertion either).

## Related Tickets
- `TCK-20260915-MONITORING-ANOMALY-DETECTION-EPIC` (parent)
- `TCK-20260903-HAND-ORCHESTRATED-TICKETS-MISSING-MONITORING-COVERAGE` (done)
- `TCK-20260912-WORKING-LOG-APPEND-HELPER` (done) — established the sole sanctioned writer
- `TCK-20260914-MONITORING-SURFACE-DEAD-MECHANISMS` (done)

## Related Docs
- `agent-monitoring/retro/RETRO-LAST14D.md`
- `docs/agent-monitoring/schema.md`

## Related Stored Artifacts
- `stored_artifacts/TCK-20260912-WORKING-LOG-APPEND-HELPER/`

## Related Code Areas
- `tools/agent-monitoring/validate.py`
- `tools/working_log_writer.py` (`append_working_log_row`)
- `tools/agent-monitoring/record_run.py`, `record_events.py`
- `agent-monitoring/data/unknown-week/`

## Assumptions / Open Questions
- Items 1, 4 and 5 are all historical (June-era). Accepting them with an explicit exclusion may be
  more honest than backfilling records nobody can reconstruct. Resolved: accepted and ratcheted.
- Item 2's clustering strongly suggests one batch; identifying which session closed those 34 would
  confirm it, and is worth doing before deciding. Resolved with a correction: the September
  clustering is real but is a small fraction of a much larger (218, all-time) gap the ticket's own
  framing did not capture — see investigation.md. A ~18-record overlap with `FOLDER-*`/`EPIC-*`
  batch coverage was checked via a substring-match heuristic (not proof); the remaining ~200 are
  genuinely unexplained and not further traceable to one identifiable session within this ticket's
  reasonable scope.

## Implementation Notes
See `staging_artifacts/TCK-20260915-MONITORING-INTEGRITY-BACKLOG/investigation.md` for the full
per-item re-derivation (two corrections found: item 1's stated root cause was wrong — warnings
never gate `validate.py`'s exit code, only the undocumented "no events" ERROR class does; item 2's
stated count of 34 undercounts the true all-time gap of 218 by nearly 6x).

- **Item 1**: `validate.py` gained `EVENTS_REQUIRED_START = "2026-07-08"` and
  `_run_effective_start_ts()` (checks `start_ts`/`ts`/`started_at` in that order, mirroring the
  file's own existing `LEGACY_COMPLETION_FIELDS` multi-name pattern). The "no events" ERROR check
  now skips runs whose own start timestamp predates the cutoff; a run with no determinable start
  timestamp is conservatively NOT excluded. Module docstring corrected to state plainly that only
  ERRORs (not WARNINGs) gate the exit code.
- **Item 2**: no code fix possible (218 historical records, unreconstructable). New ratchet
  condition in `monitoring_integrity_backlog_check.py` freezes 218.
- **Item 3 (writer)**: no change needed — `append_working_log_row` already uses
  `csv.writer(..., quoting=csv.QUOTE_MINIMAL)`. Added an explicit regression test.
- **Item 3 (9 rows)**: hand-mapped each malformed row's true field boundaries (status is always one
  of a small closed enum and never itself contains a comma) and repaired via a surgical one-off
  script touching exactly those 9 physical lines — a full-file re-serialization was tried first and
  reverted after it silently changed the CSV quoting style of ~70 unrelated, already-correct rows
  (`git diff --stat` caught it immediately, before committing).
- **Items 4/5**: no code fix (historical, June-era, unreconstructable). Both get their own ratchet
  condition (66/55 for item 4, 34 for item 5) in the same new check module.
- New `tools/gate_checks/monitoring_integrity_backlog_check.py`: 4 independently-ratcheted
  conditions in one module, mirroring this epic's established `check_*()` / `MARKER:` +
  `json.dumps()` shape exactly. Wired into the `Makefile` (`monitoring-integrity-backlog-check`
  target + `.PHONY`).

## Test Summary
- `tests/tools/test_validate_agent_monitoring.py`: 3 new `_run_effective_start_ts` unit tests + a
  new `TestNoEventsLegacyExclusion` class (4 tests: pre-cutoff excluded, at/after-cutoff still
  errors, unknown-ts still errors, legacy field name also honored). Full file: 48 passed together
  with `test_working_log_writer.py`'s own suite.
- `tests/tools/test_working_log_writer.py`: 1 new test, a real comma-bearing title round-tripping
  through `append_working_log_row` → `parse_working_log`.
- `tests/tools/test_monitoring_integrity_backlog_check.py` (new, 19 tests): per-function unit
  coverage for all 3 helper functions, the aggregate check's all-pass and each-condition-FAIL
  shapes, a ceiling-pin test, a real-corpus pass test, and a Makefile-wiring test.
- `tests/tools/test_validate_working_log.py`: fixing the 9 real malformed rows was a genuine,
  intended improvement to the real corpus, so 2 pre-existing tests pinned to the old 9-mismatch
  state drifted (same "hardcoded baseline drifted by a legitimate change" category CLAUDE.md's own
  CI-triage guidance names, not a regression) — full run caught this immediately. Updated both in
  place: `test_all_9_confirmed_live_mismatch_rows_are_flagged` → renamed
  `test_all_9_formerly_mismatched_rows_are_now_clean_and_repaired_correctly`, now asserts all 9
  lines parse `clean` and spot-checks 4 reconstructed titles for exact, lossless content;
  `test_ambiguous_row_count_matches_26_for_real_file` → renamed
  `test_ambiguous_row_count_matches_17_for_real_file` (26 - 9 = 17, the 9 mismatch rows no longer
  counted, the unrelated 17 quote-desync rows unaffected). All 19 tests in this file pass.
- Full `tests/tools/` suite run twice: first run (before the working_log repair test-pin fix)
  surfaced exactly the 2 stale-pin failures above plus one unrelated,
  order-dependent flake in `test_agent_monitoring_manifest.py::test_manifest_cli_reproducible_byte_identical_across_two_runs`
  (runs a real CLI manifest generator twice against the live `agent-monitoring/` directory and
  diffs the output; this session's own concurrent Bash-tool-call hook writes to
  `agent-monitoring/data/2026-W38/tools.jsonl` during a ~4-minute full-suite run can land between
  the two subprocess calls — confirmed by re-running the test alone, where it passed cleanly. Not
  caused by any change in this ticket; not fixed here, matching CLAUDE.md's own
  environment-dependent-flake triage category). Second full run (after both real fixes): all
  failures gone.
- Manual: `make agent-monitoring-validate` — exit 0 against the real corpus (was exit 1 before).
- Manual: `python3 tools/gate_checks/monitoring_integrity_backlog_check.py` — all 4 conditions PASS
  against the real corpus, each exactly at its measured ceiling.
- Manual: `tickets/working_log.csv` re-parsed post-repair — 0 malformed rows (was 9); `git diff
  --stat` confirms exactly 9 lines changed.

## Files Changed
- `tools/agent-monitoring/validate.py` — `EVENTS_REQUIRED_START`, `_run_effective_start_ts()`, the
  "no events" check's legacy exclusion, corrected module docstring.
- `tools/gate_checks/monitoring_integrity_backlog_check.py` (new) — items 2/4/5 ratchets.
- `Makefile` — new `monitoring-integrity-backlog-check` target + `.PHONY` entry.
- `tests/tools/test_validate_agent_monitoring.py`, `tests/tools/test_working_log_writer.py`,
  `tests/tools/test_monitoring_integrity_backlog_check.py` (new),
  `tests/tools/test_validate_working_log.py` — test coverage above.
- `tickets/working_log.csv` — 9 malformed physical lines repaired in place; no other line touched.

## Completion Summary
Investigated and independently re-derived all 5 named integrity items rather than trusting the
ticket's own stated numbers, per this epic's standing discipline — found and corrected two real
inaccuracies (item 1's actual root cause was a different, undocumented ERROR class than the one
named; item 2's true scope is 218 all-time, not 34 September-only). Fixed item 1 (gate now passes)
and item 3 (writer already safe, 9 existing rows repaired in place with a minimal, surgical diff).
Items 2, 4, and 5 are historical, unreconstructable data debt — accepted, documented with corrected
baselines, and ratcheted in one new check module so a future regression in any of the three still
surfaces. No detector in this ticket asserts zero.
