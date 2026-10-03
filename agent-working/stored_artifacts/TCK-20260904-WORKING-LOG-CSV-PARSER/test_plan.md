---
status: historical
layer: ai
authority: P2
audience: agent
ticket_id: TCK-20260904-WORKING-LOG-CSV-PARSER
artifact_type: test_plan
tags: [ai, data-quality]
---

# Test Plan — TCK-20260904-WORKING-LOG-CSV-PARSER

## Regression Surface

No dedicated test file for `tools/validate_working_log.py` exists today (confirmed:
`tests/tools/` has no `test_validate_working_log.py` or similar) — this ticket creates it new, so
there is no direct pre-existing suite for that module to regress-guard beyond what this ticket
itself adds.

Existing tests that must keep passing, grouped by domain (all "unit" category — this is
process-tooling, not simulation/combat, so no "arena-combat" group applies):

- **unit — ticket_stats_report.py (the convention this ticket must mirror):**
  - `tests/tools/test_ticket_stats_report.py::test_compute_velocity_groups_by_day_and_week`
  - `tests/tools/test_ticket_stats_report.py::test_compute_velocity_counts_unparseable_rows_without_crashing`
  - `tests/tools/test_ticket_stats_report.py::test_compute_distribution_counts_unknown_for_missing_fields`
  - `tests/tools/test_ticket_stats_report.py::test_collect_done_tickets_extracts_layer_tier_type_priority`
  - `tests/tools/test_ticket_stats_report.py::test_collect_done_tickets_skips_sequence_md`
  - `tests/tools/test_ticket_stats_report.py::test_compute_artifact_completeness_detects_missing_files`
  - `tests/tools/test_ticket_stats_report.py::test_build_json_report_is_json_serializable`
  (full file — none of these should change behavior; `compute_velocity`'s own `unparseable_rows`
  int-counter convention is what AC3 must mirror, not replace.)
- **unit — knowledge_search.py corpus/row extraction:**
  - `tests/tools/test_hybrid_retrieval.py` (full file) — covers the hybrid BM25/dense retrieval path
    that consumes `_collect_corpus`'s output (which includes `_extract_working_log_rows`'s rows).
    Any change to `_extract_working_log_rows`'s return shape (adding an `ambiguous`/`flagged` field,
    filtering rows, etc.) must not break this suite's fixtures or assumptions about row dict shape.
  - Any existing `tools/knowledge_search.py`-specific test file, if one exists beyond
    `test_hybrid_retrieval.py` (re-check at Implement time — `test-scoper` should confirm the exact
    file set via its own scoped discovery rather than this list being treated as exhaustive).
- **unit — done-checker's Finalize self-check (indirect but load-bearing):**
  - Whatever test currently backs `done_checker_static.py`'s "exactly one `working_log.csv` row per
    closing ticket" check must keep passing — this ticket's parser output must not change what that
    check counts as "one row" for a normally-closing ticket (only ambiguous/legacy historical rows
    are in scope, not the live Finalize append path itself).

## New Tests Required

Per acceptance criteria, one entry per required new test (file: new
`tests/tools/test_validate_working_log.py`, mirroring `test_ticket_stats_report.py`'s structure/
naming per this ticket's Scope item):

1. **`test_round_trip_parses_full_file_without_exception`**
   Category: integration (reads the real repo `tickets/working_log.csv`, not a fixture).
   Verifies: parsing the actual current file (3336+/3376+ data rows) completes with no exception
   and returns exactly one record per physical data row (row count == `len(csv.reader(...))` for
   the real file, computed independently in the test via the stdlib `csv` module as an oracle).
   Location: `tests/tools/test_validate_working_log.py`.

2. **`test_clean_row_parses_with_expected_fields`**
   Category: unit (uses a `tmp_path` fixture file, mirroring
   `test_compute_velocity_groups_by_day_and_week`'s pattern).
   Verifies: a well-formed 6-field row (including one with a correctly double-quoted comma-bearing
   field, matching the file's own existing quoting convention) parses to the correct dict with all
   6 fields correctly assigned and is classified `clean`, not `ambiguous`.
   Location: `tests/tools/test_validate_working_log.py`.

3. **`test_field_count_mismatch_row_is_flagged_ambiguous_not_dropped_or_merged`**
   Category: unit (fixture rows built from the 11 real confirmed mismatch shapes — at minimum one
   fixture per distinct root-cause pattern found in Finding 1: plain embedded-comma split, and the
   quote-desync case matching lines 1511/3104's `result[mode_sequence"]` shape).
   Verifies: each fixture row is present in the parser's output as a flagged/ambiguous record (not
   silently dropped, not silently merged into a guessed 6-field shape), and the flagged count
   matches the fixture's expected count exactly.
   Location: `tests/tools/test_validate_working_log.py`.

4. **`test_all_11_confirmed_live_mismatch_rows_are_flagged`**
   Category: integration (runs the real parser against the actual repo `tickets/working_log.csv`).
   Verifies: parsing the real file flags at least the 11 specific lines confirmed in this
   investigation (1511, 3104, 1581, 3174, 3245, 3253, 3284, 3287, 3289, 3294, 3307) as
   ambiguous/unparseable — asserted by line number or by ticket_id-substring match on the raw row
   text, not just a bare count (a bare count of "11" would pass even if the specific rows found
   drifted after a future append). If the live file's confirmed-mismatch count changes over time
   (new rows appended with the same defect, or a future fix reduces it), this test's expected set
   must be updated deliberately, not silently — treat any failure here as a real signal, not test
   flakiness.
   Location: `tests/tools/test_validate_working_log.py`.

5. **`test_irreducibly_ambiguous_quote_desync_row_is_not_heuristically_repaired`**
   Category: unit — specifically targets rows 1511/3104's shape (embedded literal `"` mid-field
   breaking quote-tracking state).
   Verifies: the parser does NOT attempt to silently rejoin/guess a 6-field shape for this specific
   row class the way it may for plain-comma-split rows — it must surface as ambiguous with no
   inferred/reinterpreted field values substituted for the original raw content. This guards the
   ticket's hard constraint ("never rewrite/reinterpret historical rows") specifically against the
   one row shape in this investigation where a naive rejoin heuristic would produce a plausible-
   looking but wrong result.
   Location: `tests/tools/test_validate_working_log.py`.

6. **`test_duplicate_content_rows_are_flagged_not_fixed`**
   Category: unit + integration (unit fixture covering the 3245/3253
   `TCK-20260831-HOTFIX-TEST-SCOPER-BARE-DIRECTORY-RULE` exact-duplicate pair; integration variant
   optionally checking the real file still contains both duplicate physical lines byte-identical
   post-parse).
   Verifies: exact-duplicate-content rows are surfaced (e.g. as a `duplicate` flag or a separate
   reported count) but are never merged into one row, never deleted, never rewritten — this is an
   Out-of-Scope item per the ticket ("flag as discovered-but-out-of-scope, do not silently fix
   inline"), so the test's job is to prove the parser leaves them exactly as two independent
   records, not that it fixes them. Given Finding 2 (this investigation's discovery of ~1586
   duplicate rows from a whole-block git-merge duplication, far larger than the 2-3 the ticket
   named), this test should NOT assert an exact total duplicate count against the live file unless
   Plan explicitly scopes duplicate-detection as a first-class signal — keep the live-file
   assertion narrow (the specific named pair) unless Plan says otherwise.
   Location: `tests/tools/test_validate_working_log.py`.

7. **`test_historical_rows_are_never_rewritten_byte_identical_after_run`**
   Category: architecture guard (verifies no mutation of durable state — this repo's Testing Rule
   requires exactly this kind of check for any read-only/decision-logic path).
   Verifies: running the new parser/validator against a copy of `tickets/working_log.csv` (via
   `tmp_path`, copying the real file or a representative fixture) produces byte-identical file
   content before and after — the parser is read-only regardless of which tolerant-parser-vs-
   stricter-format branch Plan picks, and regardless of whatever "separate derived file" mechanism
   (if any) is built for a normalized view. Applies whichever persistence mechanism is chosen: if a
   derived/cache file is written, this test also confirms `tickets/working_log.csv` itself is never
   the file mutated.
   Location: `tests/tools/test_validate_working_log.py`.

8. **`test_ambiguous_row_count_is_first_class_signal_matching_ticket_stats_report_convention`**
   Category: unit.
   Verifies: whatever `validate_working_log.py` and/or `knowledge_search.py::_extract_working_log_rows`
   is updated to report includes a plain, always-present int count (never omitted, never raising)
   for ambiguous rows — mirroring `compute_velocity`'s `unparseable_rows` key shape exactly (see
   investigation.md's "Existing parsers" section for the precise contract this must match: a bare
   int counter in the returned structure, incremented without crashing, present even when zero).
   Location: `tests/tools/test_validate_working_log.py` (and/or a `knowledge_search.py`-side test
   file, per whichever module Plan decides owns the primary parser).

9. **`test_knowledge_search_does_not_index_the_embedded_header_duplicate_row`**
   Category: regression / unit — directly targets the concrete, already-live bug this investigation
   found (line 1594, a literal second header row silently indexed as a bogus `ticket_id="ticket_id"`
   / `title="title"` corpus document today, since both are truthy and bypass
   `_extract_working_log_rows`'s `if not ticket_id and not title: continue` guard).
   Verifies: a fixture CSV containing a mid-file duplicate header row does NOT produce a corpus
   entry with `id=="ticket_id"` — either by field-count/plausibility check, or by explicit
   detection that a data row's values equal the header's own values.
   Location: `tests/tools/test_hybrid_retrieval.py` or a new
   `tests/tools/test_knowledge_search_working_log_rows.py`, whichever this repo's existing
   `knowledge_search.py` test convention prefers (confirm exact file at Implement time).

10. **`test_paren_imbalanced_artifacts_path_row_is_flagged_despite_6_field_count`**
    Category: unit — targets Finding 3's class directly (fixture rows built from the confirmed
    real shape, e.g. a row whose raw content mirrors line 1100's
    `...,N/A (hotfix", no staging artifacts)` tail).
    Verifies: a row that `csv.reader` parses to exactly 6 fields, but whose last field
    (`artifacts_path`) has an unbalanced parenthesis count (`count("(") != count(")")`), is still
    flagged ambiguous/unparseable — proving the parser's plausibility layer runs even when the
    field-count check alone would report "clean." This is the regression guard for the exact gap
    this investigation's Finding 3 found (34 real lines silently pass field-count==6 today).
    Location: `tests/tools/test_validate_working_log.py`.

11. **`test_strict_mode_alone_does_not_catch_finding3_class_documented_as_known_gap`**
    Category: unit / documentation-guard.
    Verifies: `csv.reader([raw], strict=True)` does NOT raise for a Finding-3-shaped fixture row
    (confirming the investigation's own negative-result finding stays true), while it DOES raise
    for a Finding-1-shaped fixture row (1511/3104's shape). This test exists specifically so a
    future change to the parser's detection strategy cannot silently start relying on
    `strict=True` alone without this test failing first — it pins down the documented gap.
    Location: `tests/tools/test_validate_working_log.py`.

12. **`test_all_34_confirmed_finding3_lines_are_flagged_in_the_real_file`**
    Category: integration (runs the real parser against the actual repo `tickets/working_log.csv`).
    Verifies: parsing the real file flags at least the 34 specific lines confirmed in this
    investigation's Finding 3 (1100, 1101, 1102, 1103, 1318, 1320, 1329, 1332, 1337, 1400, 1401,
    1415, 1453, 1457, 1459, 1460, 1462, 2693, 2694, 2695, 2696, 2911, 2913, 2922, 2925, 2930, 2993,
    2994, 3008, 3046, 3050, 3052, 3053, 3055) as ambiguous/unparseable — asserted by line number or
    ticket_id-substring, matching test 4's convention for Finding 1's 11 rows. Same caveat as test
    4: if the live file's confirmed set changes over time, update this test's expected set
    deliberately.
    Location: `tests/tools/test_validate_working_log.py`.

13. **`test_finding3_reconstructable_row_is_flagged_not_silently_repaired`**
    Category: unit — mirrors test 5's discipline but for Finding 3's class specifically.
    Verifies: even though Finding 3's 17 rows have a single unambiguous reconstruction candidate
    (confirmed against byte-identical clean siblings elsewhere in the file — e.g.
    `N/A (hotfix, no staging artifacts)` appearing correctly quoted 10 times), the parser does NOT
    silently substitute the reconstructed value into its output — it must appear as
    flagged/ambiguous with the original raw (corrupted) field values preserved, same as any other
    ambiguous row. Guards against a future "high-confidence reconstruction, so just fix it inline"
    scope-creep that would violate the ticket's hard "never rewrite/reinterpret historical rows"
    constraint.
    Location: `tests/tools/test_validate_working_log.py`.

## Scoped Pytest Commands

```
pytest tests/tools/test_validate_working_log.py -v
pytest tests/tools/test_ticket_stats_report.py -v
pytest tests/tools/test_hybrid_retrieval.py -v
pytest tests/tools/ -k "working_log or knowledge_search" -v
```

Never `pytest tests/` (full suite) — scope stays within `tests/tools/`, the domain this ticket's
Related Code Areas (`tools/validate_working_log.py`, `tools/knowledge_search.py`,
`tools/ticket_stats_report.py`) all live under. Always pass the bare `tests/tools/` directory (or an
explicit `-k` filter within it) to any scoped test-coverage gate check, never a hand-picked file
list — per this repo's established `test_scope_coverage_static` convention.

## Anti-Drift Test Guards

- **A test asserting `validate_working_log.py`'s duplicate-ticket-ID and missing-log-entry checks
  are unchanged** (existing behavior, lines 40-59 of the current file) — this ticket's Scope permits
  updating row-extraction/ambiguous-row reporting only; a regression here would mean scope crept
  into unrelated existing checks.
- **A test proving no row is silently dropped or count-reduced** — assert
  `len(parsed_rows_including_ambiguous) == len(list(csv.reader(open(path))))` (excluding header) for
  the full real file, so a future refactor cannot accidentally start filtering out
  ambiguous/duplicate rows from the returned record set instead of flagging them in place.
- **A test proving the 2 irreducibly-ambiguous rows (1511, 3104) are never "fixed" by a future
  change to the rejoin heuristic** — guards against someone later generalizing the plain-comma
  rejoin logic broadly enough that it starts silently reinterpreting the quote-desync rows too,
  which would violate the hard "never reinterpret historical rows" constraint.
- **A test proving `tickets/working_log.csv` byte size / mtime is unchanged after any parser/
  validator run** (belt-and-suspenders alongside test 7 above) — catches an accidental in-place
  write introduced by a future edit to either module.
- **A test proving `docs/parity_ledger/*.yaml` files are untouched by this ticket's changes** — this
  is tooling/process work with zero mechanics-bible or engine-contract surface; a stray parity-ledger
  edit would indicate scope drift into simulation-subsystem territory that doesn't belong here.
- **A test proving a "clean" (field-count == 6, balanced parens) row is never flagged ambiguous by
  the new plausibility layer** — the flip side of test 10: adding a parenthesis-balance check to
  catch Finding 3's class must not start false-positiving against the file's other 1378 distinct
  `artifacts_path` shapes (e.g. `stored_artifacts/TCK-.../`, `none (hotfix)`, free-text descriptions
  with no parens at all). Guards against an overly-aggressive plausibility check silently
  reclassifying thousands of genuinely-clean rows as ambiguous.
- **A test proving Finding 3's 34 lines and Finding 1's 11 lines are never double-counted as a
  single flagged set without distinction** — if the implementation's ambiguous-row output doesn't
  distinguish root-cause class (field-count-mismatch vs. paren-imbalance-despite-6-fields), a
  future consumer could conflate "11 field-count rows" language elsewhere in the docs/tickets with
  the true combined 45-line total; this test guards that Finding 1's and Finding 3's counts stay
  independently inspectable in the parser's output shape.
