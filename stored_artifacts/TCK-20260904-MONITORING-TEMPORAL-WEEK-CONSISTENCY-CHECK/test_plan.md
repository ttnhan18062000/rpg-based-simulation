---
status: historical
layer: observability
authority: P2
audience: agent
ticket_id: TCK-20260904-MONITORING-TEMPORAL-WEEK-CONSISTENCY-CHECK
artifact_type: test_plan
tags: [agent-monitoring, observability, data-quality]
---

# Test Plan — TCK-20260904-MONITORING-TEMPORAL-WEEK-CONSISTENCY-CHECK

## Regression Surface

Existing tests that must keep passing, grouped by domain (this ticket touches only `tools/`-level
Python utilities and their tests — no `src/` or arena-combat surface at all):

**Unit — `tools/agent-monitoring/` corpus-health scripts:**
- `tests/tools/test_verify_referential_integrity.py` — all 13 tests must remain green, byte-for-byte
  unmodified behavior of the 2 existing FK checks. If the new check lands inside this module (see
  investigation.md's module-location discussion), every test in this file must still pass exactly
  as before — the new check must not alter `compute_referential_integrity_report()`'s return shape,
  `ReferentialIntegrityReport`'s fields, or `load_all_weeks()`'s signature/behavior.
- `tests/tools/test_migrate_monitoring_data.py` — must remain untouched and green; this ticket only
  *imports* `RUNS_FIELD_PRIORITY`/`EVENTS_FIELD_PRIORITY`/`bucket_lines_by_week_multi_field`-adjacent
  constants from `migrate_monitoring_data.py`, it does not modify that module.
- `tests/tools/test_migrate_tools_shards.py` (if present) — same reasoning for
  `_parse_ts_to_week`/`UNKNOWN_WEEK_KEY` imports from `migrate_tools_shards.py`.

**Unit — `tools/gate_checks/done_checker_static.py`:**
- `tests/tools/test_done_checker_static.py` — all existing tests must remain green. The one test
  that *must* change as part of this ticket's own diff (not a passive regression-surface item) is
  `test_run_static_precheck_all_pass_eligible` (currently asserting `len(results) == 7` at line 619)
  — it must be updated to `len(results) == 8` with the new check's `condition` name added to the
  fixture's implicit "everything passes" expectation. Every other `run_static_precheck`-level test
  (`test_run_static_precheck_surfaces_fail_not_masked`,
  `test_run_static_precheck_blocks_on_bad_priority`,
  `test_run_static_precheck_passes_valid_priority`) asserts on specific `by_condition[...]` keys, not
  on the total count, so they should need no changes — but must be re-run to confirm the new check
  doesn't accidentally FAIL against `_scaffold_precheck_repo`'s fixture repo (which creates no
  `agent-monitoring/data/` directory at all — see New Tests Required below for why this matters).

**Integration — nothing.** This ticket has no `src/` behavior change, no API surface, no simulation
tick logic — the entire diff is observability/gate tooling.

## New Tests Required

Per Scope's explicit minimum test list (items a-e) plus the module-level real-corpus discipline
`verify_referential_integrity.py`'s own test suite already established:

1. **`test_tools_ts_matches_folder_no_finding`**
   - Category: unit
   - Verifies: a `tools.jsonl` row whose `ts` maps to the same ISO week as its containing folder
     produces no anomaly and no divergence finding — the trivial pass case.
   - Location: new test module (see Module Location below), synthetic `tmp_path` fixture, mirroring
     `test_same_week_only_join_baseline`'s structure in
     `tests/tools/test_verify_referential_integrity.py`.

2. **`test_tools_ts_mismatch_flagged_as_genuine_anomaly`**
   - Category: unit
   - Verifies: a `tools.jsonl` row whose `ts` maps to a *different* ISO week than its folder is
     flagged, and specifically flagged under the "genuine anomaly" category/label, not lumped with
     `runs.jsonl`'s "expected divergence" framing — the report text (or a structured field, if the
     report is a dataclass with separate anomaly/divergence lists) must make the distinction visible,
     not just infer-able. Assert on the concrete field/list, not just report text substring
     presence, matching `test_orphan_tools_row_no_matching_event_anywhere_is_flagged`'s pattern of
     asserting on `violation["run_id"]`/`violation["seq"]`/`violation["week_folder"]` individually.
   - Location: same new test module, synthetic `tmp_path` fixture.

3. **`test_runs_start_ts_earlier_week_flagged_as_expected_divergence_not_anomaly`**
   - Category: unit
   - Verifies: a `runs.jsonl` row whose `start_ts` is in an ISO week strictly earlier than its
     folder's week is reported under the "expected divergence" category, explicitly distinct from
     the anomaly category used for `tools.jsonl` mismatches — this is the single most important
     correctness guard in this suite (directly analogous to
     `test_cross_week_run_id_not_flagged`'s role in `test_verify_referential_integrity.py`'s own
     suite: "the one test a [naively uniform] implementation would fail while passing every other
     test trivially"). Must assert the record is NOT present in whatever anomaly/violation list a
     `tools.jsonl`-style mismatch would populate.
   - Location: same new test module, synthetic `tmp_path` fixture, week-folder split modeled on the
     real corpus shape (a `start_ts` in an earlier week than the `runs.jsonl` folder it's found in —
     `investigation.md`'s Real Corpus Findings shows this specific shape does not yet exist in the
     live corpus, so this test's fixture is necessarily synthetic, same situation
     `test_cross_week_run_id_not_flagged` was already in when it modeled a real-but-different-ticket
     shape).

4. **`test_unknown_week_records_exempt_no_finding_either_way`**
   - Category: unit
   - Verifies: a record (one per source — `tools`, `events`, `runs`) placed in the `unknown-week`
     folder produces no finding in *either* the anomaly or the expected-divergence bucket — it must
     be a third, explicitly exempt bucket, not silently absorbed into "match" (which would
     undercount) or "mismatch" (which would falsely flag legacy/unparseable data as new
     anomalies). Assert an explicit exempt-count field or list, not just absence from the other two.
   - Location: same new test module, synthetic `tmp_path` fixture.

5. **`test_no_usable_timestamp_field_in_known_folder_skipped_not_counted_as_match_or_mismatch`**
   - Category: unit (not in Scope's literal item list, but required by investigation.md's Malformed/
     Missing Timestamp Fields finding — 0/196,630 real rows hit this today, but the code path is
     unexercised by real data and must still be defensively tested, matching
     `verify_referential_integrity.py`'s own precedent of testing the `RETRIEVAL-EVENT-*`/
     `run_id: null`/`seq <= 0` exclusions even where the real corpus currently has zero occurrences
     of one of them).
   - Verifies: a `runs.jsonl` (or `events.jsonl`) record in a real, known ISO-week folder, with none
     of `RUNS_FIELD_PRIORITY`'s (or `EVENTS_FIELD_PRIORITY`'s) fields present/truthy, is placed in a
     distinct "unparseable, skipped" bucket — not silently counted as a match (which would be a false
     clean bill) and not counted as a mismatch/anomaly (which would misrepresent "we couldn't check
     this" as "this failed the check").
   - Location: same new test module, synthetic `tmp_path` fixture.

6. **`test_field_priority_reused_from_migration_not_reinvented`**
   - Category: architecture guard
   - Verifies: the new check's module imports `RUNS_FIELD_PRIORITY`/`EVENTS_FIELD_PRIORITY` from
     `tools/agent-monitoring/migrate_monitoring_data.py` (and `_parse_ts_to_week`/`UNKNOWN_WEEK_KEY`
     from `migrate_tools_shards.py`) rather than re-declaring an independent copy — e.g. by
     asserting `new_module.RUNS_FIELD_PRIORITY is migrate_monitoring_data.RUNS_FIELD_PRIORITY`
     (identity, not just equality, to catch a copy-pasted-then-diverged list) or by asserting the
     new module has no its own `RUNS_FIELD_PRIORITY = [...]` module-level literal via source
     inspection. This is the anti-drift guard investigation.md's own "Do not re-type
     `RUNS_FIELD_PRIORITY`/`EVENTS_FIELD_PRIORITY` by hand" hazard calls for directly.
   - Location: same new test module.

7. **`test_report_distinguishes_anomaly_from_expected_divergence_in_text`**
   - Category: unit (report-format contract, mirrors
     `test_report_output_matches_validate_py_style` in `test_verify_referential_integrity.py`)
   - Verifies: `.to_text()` (or equivalent) output contains clearly distinct section headers/labels
     for "genuine anomaly" vs. "expected divergence" vs. "exempt (unknown-week)" vs. "skipped
     (unparseable)" — Scope's own AC wording ("a reader must not have to infer which is which")
     is directly machine-checkable by asserting distinct label substrings appear near each
     category's own counts, not just that all 4 numbers appear somewhere in the text.
   - Location: same new test module.

8. **`test_done_checker_new_check_wired_and_returns_pass_with_evidence`**
   - Category: unit / architecture guard
   - Verifies: `run_static_precheck()`'s `checks` tuple includes the new
     `check_temporal_week_consistency`-style entry (by `condition` name), and that it returns
     `("PASS", <non-trivial evidence string>)` even when called against `_scaffold_precheck_repo`'s
     existing fixture (which creates no `agent-monitoring/data/` directory at all) — confirming the
     new check degrades gracefully (empty/absent corpus is not an error) exactly like
     `verify_referential_integrity.py`'s `load_all_weeks()` already does for a missing `data_dir`
     (an empty glob, not an exception). Also assert `len(results) == 8` here (or update the existing
     `test_run_static_precheck_all_pass_eligible` in place — implementer's choice, document which).
   - Location: `tests/tools/test_done_checker_static.py`, extending the existing
     `run_static_precheck (aggregate)` section (around line 593) — reuses `_scaffold_precheck_repo`.

9. **`test_real_corpus_smoke_run`** (real-corpus discipline, not a synthetic-fixture test)
   - Category: unit / smoke
   - Verifies: the check runs successfully against the real `agent-monitoring/data/` directory,
     returns a well-formed report, and — per this ticket's own AC #4 — the ticket's Test Summary
     captures the actual real numbers found (investigation.md's Pass 2 table:
     runs 1394 total/5 exempt/0 skipped/1389 match/0 mismatch; events 9024/28/0/8996/0; tools
     186212/1/0/186211/0, understanding these will have grown slightly by implementation time).
     Deliberately does NOT assert zero mismatches as a hardcoded expectation baked into the test
     logic itself (the corpus is live and could contain a genuine future anomaly) — only asserts the
     report executes cleanly and the returned structure is well-typed, mirroring
     `test_real_corpus_smoke_run` in `test_verify_referential_integrity.py` verbatim in spirit.
   - Location: same new test module.

## Module Location for New Tests

Per investigation.md's recommendation (new sibling script
`tools/agent-monitoring/verify_temporal_week_consistency.py`, not extending
`verify_referential_integrity.py`), the new tests 1-7 and 9 above land in a new
`tests/tools/test_verify_temporal_week_consistency.py`, mirroring
`test_verify_referential_integrity.py`'s own file structure (synthetic `tmp_path` fixtures first,
real-corpus smoke test last, `_write_jsonl` helper reused/duplicated at the top). Test 8 (done-checker
wiring) lands in `tests/tools/test_done_checker_static.py` regardless of where the check itself lives,
since `run_static_precheck` is the wiring point under test, not the check module. If Plan/
implementation instead extends `verify_referential_integrity.py` directly, tests 1-7 and 9 move into
`tests/tools/test_verify_referential_integrity.py` in a new section, without changing their own
individual content/assertions.

## Scoped Pytest Commands

```bash
# New/extended check module + its own tests
pytest tests/tools/test_verify_temporal_week_consistency.py -v
# (or, if extended in-place: pytest tests/tools/test_verify_referential_integrity.py -v)

# done-checker wiring + full regression surface for the aggregate function
pytest tests/tools/test_done_checker_static.py -v

# Full tools/agent-monitoring/ domain regression sweep (catches any accidental cross-module breakage
# from the RUNS_FIELD_PRIORITY/EVENTS_FIELD_PRIORITY/_parse_ts_to_week import reuse)
pytest tests/tools/test_verify_referential_integrity.py tests/tools/test_migrate_monitoring_data.py \
  tests/tools/test_migrate_tools_shards.py tests/tools/test_done_checker_static.py \
  tests/tools/test_verify_temporal_week_consistency.py -v
```

Never `pytest tests/` — scoped to the `tools/agent-monitoring`/`tools/gate_checks` domain per
CLAUDE.md's Testing Rule.

## Anti-Drift Test Guards

- **`test_runs_start_ts_earlier_week_flagged_as_expected_divergence_not_anomaly`** (test 3 above) is
  the single highest-priority guard in this suite — a naive, uniform "flag every mismatch the same
  way" implementation would pass every other test in this plan trivially while failing this one, and
  would immediately false-positive on the first real long-running/paused ticket that crosses an ISO
  week boundary post-migration (exactly the class of false alarm the ticket's Request Summary warns
  against).
- **`test_field_priority_reused_from_migration_not_reinvented`** (test 6) guards against a
  hand-retyped copy of the field-priority lists silently drifting from the real migration source of
  truth over time — a plausible, easy-to-miss regression since nothing else in the test suite would
  catch a copy that starts identical but is edited independently later.
- **`test_no_usable_timestamp_field_in_known_folder_skipped_not_counted_as_match_or_mismatch`**
  (test 5) guards the 3-way (match / mismatch / unparseable-skip) classification from silently
  collapsing to 2-way, which would either inflate the "clean" match count with data the check never
  actually verified, or inflate the anomaly count with data that isn't actually a divergence — either
  direction misrepresents the report's own honesty guarantee.
- **`test_done_checker_new_check_wired_and_returns_pass_with_evidence`** (test 8) guards the specific
  reconciliation decision this ticket must make explicit (report-only vs. `PASS`/`FAIL`-only
  checklist) — if a future change accidentally lets this check return `FAIL` on a real finding, this
  test (asserting `PASS` even against a fixture with no `agent-monitoring/data/` at all, and — if
  extended with a mismatch-injecting fixture — `PASS` even when the underlying report contains real
  anomaly findings) is what would catch the regression before it silently starts blocking ticket
  closes project-wide.
- **Existing `test_run_static_precheck_surfaces_fail_not_masked`/`test_run_static_precheck_blocks_
  on_bad_priority` continuing to pass unmodified** is itself an anti-drift guard: it confirms adding
  an 8th check does not change how any *other* check's FAIL status propagates through
  `run_static_precheck`'s aggregation — the new check must be additive, not disruptive to the
  existing 7.
