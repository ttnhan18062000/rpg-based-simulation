---
status: historical
layer: ai
authority: P2
audience: agent
ticket_id: TCK-20260904-WORKING-LOG-CSV-PARSER
artifact_type: plan
tags: [ai, data-quality]
---

# Implementation Plan — TCK-20260904-WORKING-LOG-CSV-PARSER

## Summary

Build a new, standalone tolerant-parser module (`tools/working_log_parser.py`) that reads
`tickets/working_log.csv` via `csv.reader` and classifies every physical data row into one of a
small set of explicit categories — `clean`, `field_count_mismatch` (with a `recoverable` sub-flag),
or `embedded_header_duplicate` — plus an orthogonal `is_duplicate` flag for exact-repeated raw
content. The field-count-mismatch recovery reuses the exact "status-token anchor + rejoin"
technique proven by `TCK-20260819-HOTFIX-WORKING-LOG-LEGACY-SCHEMA-ROWS`, generalized on both sides
of the split: on the left, searching for the status anchor rather than assuming a fixed column index
(needed because title itself can absorb extra fields and shift status's index — confirmed against
all 11 real rows below); on the right, a parenthesis-balance plausibility check to decide whether
`artifacts_path` is the trailing raw field alone or the last two raw fields rejoined (needed because
2 of the 11 rows, 1581/3174, have their unescaped comma inside `artifacts_path` itself rather than in
`title`/`summary` — verified by direct computation against both rows' real raw content, and
cross-checked against every genuinely-complete artifacts_path value elsewhere in the file to confirm
zero false positives). Irreducible ambiguity
(rows 1511/3104) is detected with Python's own built-in `csv.reader(..., strict=True)`, which raises
`csv.Error` on exactly those two rows and no others — verified empirically against all 11 real rows,
not assumed. `validate_working_log.py` adopts this parser as its row source (replacing bare
`DictReader`) while its three pre-existing checks (duplicate-ID, missing-log-entry, empty-field) are
left untouched in logic, only re-pointed at the parser's clean+recovered records. `knowledge_search.py`
gets a narrow, targeted guard (not a full parser swap, to avoid disturbing its intentionally more
lenient historical-column-variant tolerance) against the one concrete evidenced bug: indexing the
embedded duplicate header row (line 1594) as a real corpus document. The write-time half of the
tolerant-parser-vs-stricter-format decision is closed via a `docs/ai/ticket-lifecycle.md` wording
change requiring comma-bearing fields to be quoted going forward — no new CI gate is built (out of
this ticket's scope; flagged as a future-ticket recommendation only). No historical row in
`tickets/working_log.csv` is ever rewritten; all reconstruction happens in-memory only.

**Extension (Finding 3, added 2026-09-06):** a second, previously-undiscovered corruption class —
34 physical lines (17 distinct corrupted append events, each duplicated by Finding 2's mega-block,
same as 0 of the original 11) — coincidentally still parses to exactly 6 raw fields via
`csv.reader`, making it fully invisible to the `len(raw_fields) != 6` check that was, until now,
Step 1's only signal for "not clean." Step 1 is extended (not replaced) with a second, orthogonal
validity gate applied to every already-6-field row: a parenthesis-balance check on the parsed
`artifacts_path` field. A row that fails this gate gets a new, distinct classification value,
`quote_desync_masquerading_as_clean` (kept separate from `field_count_mismatch` rather than folded
into it, since the field count for these rows is genuinely 6 — reusing the mismatch label would
misdescribe the actual defect; see the classification-naming justification in Step 1 below).
Recovery reuses the same "fixed-vocabulary rejoin" style as Finding 1's paren-balance trailing-field
fix, but with a closed, evidence-only 3-string vocabulary (`N/A (hotfix`, `none (hotfix`,
`none (scope-only epic`) rather than a positional split — an unmatched row degrades to
`recoverable=False` rather than guessing a 4th shape. Total known corrupted-row surface is now
**45 physical lines flagged as not-clean** (11 `field_count_mismatch` physical lines from Finding 1
+ 34 `quote_desync_masquerading_as_clean` physical lines from Finding 3), matching
`ambiguous_row_count`'s own literal, undeduped, per-physical-row definition (see `ParseResult`'s
docstring in Step 1) and reconciling exactly against the file's known totals: 3376 total data rows =
3330 clean + 11 field_count_mismatch + 34 quote_desync_masquerading_as_clean + 1
embedded_header_duplicate. Note Finding 1's 11 rows are NOT themselves free of internal duplication:
3 of the 11 (lines 3104, 3174, 3253) are exact physical duplicates of 3 other rows within that same
set of 11 (lines 1511, 1581, 3245 respectively) — correctly caught by the ordinary, generic
`is_duplicate`/`duplicate_of_line` mechanism (Step 1) like every other duplicate row in the file, not
a bug. As additional context only (not the value any test asserts): the 45 flagged physical lines
correspond to roughly 8 distinct field_count_mismatch events (11 lines minus the 3 duplicates just
named) plus 17 distinct quote_desync events (34 lines, each duplicated once by Finding 2's
mega-block) — 25 distinct underlying append incidents once Finding 2's whole-block duplication is
accounted for. — up from the original 11/11.

## Steps

### Step 1 — New parser module: `tools/working_log_parser.py`
**Files:** `tools/working_log_parser.py` (new)
**Change:**
Create a new flat module (matching the existing flat-file convention of `tools/validate_working_log.py`,
`tools/ticket_stats_report.py`, `tools/knowledge_search.py` — no subpackage).

Import the canonical status enum from `tools/ticket_field_values.py:46-48`
(`WORKFLOW_STATUS_VALUES = frozenset({"OPEN", "INPROGRESS", "BLOCKED", "DONE", "EPIC_SCOPED"})`, cited
directly from that file) and extend it with two working-log-only historical status words that are
NOT in that ticket-body enum but appear as real historical status-column values in
`tickets/working_log.csv` today — confirmed via a direct `csv.reader` tally over the live file run
for this plan (2026-09-06): `AMENDED` (2 occurrences) and `BACKLOG` (2 occurrences), both real,
pre-dating enum canonicalization, not fabricated:
```python
STATUS_VOCAB: FrozenSet[str] = WORKFLOW_STATUS_VALUES | {"AMENDED", "BACKLOG"}
```

Define:
```python
@dataclass
class ParsedRow:
    line_no: int                  # 1-based physical line number (csv.reader's reader.line_num after
                                   # consuming this row — correctly reflects multi-line quoted fields
                                   # too, though none are known to exist in this file today)
    raw_fields: list[str]         # exact csv.reader() split, never mutated
    classification: str           # "clean" | "field_count_mismatch" | "embedded_header_duplicate"
                                   # | "quote_desync_masquerading_as_clean" (Finding 3, see below)
    recoverable: Optional[bool]   # meaningful when classification == "field_count_mismatch" (True =
                                   # rejoin succeeded, record populated; False = irreducibly
                                   # ambiguous, record left None) OR
                                   # "quote_desync_masquerading_as_clean" (True = parsed summary ended
                                   # with one of the 3 known vocabulary fragments and reconstruction
                                   # succeeded, record populated; False = unbalanced parens but no
                                   # known fragment matched — a new, not-yet-seen sub-shape, record
                                   # left None, never guessed). None for "clean"/
                                   # "embedded_header_duplicate".
    record: Optional[dict]        # {"timestamp","ticket_id","title","status","summary",
                                   # "artifacts_path"} — populated for "clean" rows and for
                                   # recoverable field_count_mismatch / quote_desync_masquerading_as_
                                   # clean rows ONLY. Never fabricated for an irreducibly-ambiguous,
                                   # unmatched-fragment, or embedded-header-duplicate row.
    is_duplicate: bool            # True iff this row's raw physical line text exactly matches an
                                   # earlier-seen row's raw line text (2nd+ occurrence only — the
                                   # first occurrence of a repeated line is never itself flagged)
    duplicate_of_line: Optional[int]
    reason: str                   # human-readable, e.g. "csv.Error under strict=True: ',' expected
                                   # after '\"'" or "field-count 7 != 6, status anchor found at index 4"

@dataclass
class ParseResult:
    rows: list[ParsedRow]                    # exactly one per physical data row, same order/count
                                              # as a plain csv.reader pass (never dropped/merged)
    ambiguous_row_count: int                 # count of rows whose classification is anything other
                                              # than "clean" or "embedded_header_duplicate" — i.e.
                                              # every row that would have been silently WRONG if
                                              # treated as ordinary clean data, regardless of which
                                              # detection signal caught it. Today this is
                                              # "field_count_mismatch" (Finding 1: field-count != 6,
                                              # 11 rows, both recoverable and irreducible) UNION
                                              # "quote_desync_masquerading_as_clean" (Finding 3:
                                              # field-count == 6 but artifacts_path paren-unbalanced,
                                              # 34 physical lines, both recoverable and unmatched) —
                                              # a live-file total of 45 (11 + 34), the literal,
                                              # undeduped, per-physical-row count per this field's own
                                              # definition above (3376 total = 3330 clean + 11
                                              # field_count_mismatch + 34
                                              # quote_desync_masquerading_as_clean + 1
                                              # embedded_header_duplicate). See "Justification: why quote-desync
                                              # rows count toward ambiguous_row_count" below Step 1's
                                              # algorithm. embedded_header_duplicate is deliberately
                                              # excluded: record is always None for that class, so it
                                              # can never be silently mistaken for valid data the way
                                              # an unflagged quote-desync row could — mirrors
                                              # ticket_stats_report.py::compute_velocity's
                                              # `unparseable_rows` convention (tools/ticket_stats_report.py:109-141):
                                              # a bare, always-present int, incremented without
                                              # crashing or dropping the row, now generalized to any
                                              # detection signal that proves a row unsafe-as-clean.
    quote_desync_count: int                  # count of rows with classification ==
                                              # "quote_desync_masquerading_as_clean" (both
                                              # recoverable and unmatched) — a dedicated named
                                              # counter, mirroring embedded_header_duplicate_count's
                                              # pattern, since this is its own distinct, evidenced
                                              # pattern with its own recovery semantics. Always a
                                              # subset of ambiguous_row_count.
    duplicate_row_count: int                 # count of rows with is_duplicate == True
    embedded_header_duplicate_count: int     # count of rows whose 6 parsed fields exactly equal the
                                              # header row's fields

def parse_working_log(path: Path) -> ParseResult: ...
```

**Classification algorithm** (per row, in order):
1. Read the header line once (`timestamp,ticket_id,title,status,summary,artifacts_path`, confirmed
   at `tickets/working_log.csv:1`) and split it for comparison.
2. For each subsequent physical row, parse with a plain lenient `csv.reader` to get `raw_fields`
   and `reader.line_num` (giving `line_no`).
3. **If `len(raw_fields) == 6`:**
   - If `tuple(f.strip() for f in raw_fields) == tuple(header_fields)` → `embedded_header_duplicate`
     (this is the exact, concrete case found at `tickets/working_log.csv:1594` — confirmed via
     `grep -n "^timestamp,ticket_id,..."` returning lines 1 and 1594 only, per investigation.md
     Finding 2). `record = None` (deliberately not indexed as data — it isn't).
   - **Else (Finding 3 — new gate, added 2026-09-06): before treating a 6-field row as `clean`, check
     parenthesis balance on the positionally-mapped `artifacts_path` candidate (`raw_fields[5]`)**:
     `raw_fields[5].count("(") != raw_fields[5].count(")")`. This is the same style of check the
     original Step 1 already used for Finding 1's 1581/3174 rejoin (a paren-balance plausibility
     check on a trailing-field candidate), now applied as a general validity gate on every 6-field
     row rather than only during a mismatch-branch recovery attempt. Verified zero-false-positive
     against all 3365 real six-field rows' `artifacts_path` values (1378 distinct) per
     investigation.md Finding 3 — every balanced-paren value is left alone.
     - **If unbalanced:** this row is NOT `clean`. Search the positionally-mapped `summary`
       candidate (`raw_fields[4]`) for whether it ends with one of exactly 3 known vocabulary
       fragments, each preceded by a literal comma: `",N/A (hotfix"`, `",none (hotfix"`,
       `",none (scope-only epic"` (`QUOTE_DESYNC_SUMMARY_FRAGMENTS`, a closed, evidence-only tuple —
       see Anti-Drift Notes; never add a 4th fragment).
       - **If a match is found:** `classification="quote_desync_masquerading_as_clean"`,
         `recoverable=True`. Reconstruct: `fragment = <matched fragment text, without the leading
         comma>` (e.g. `"N/A (hotfix"`); `new_summary = raw_fields[4]` with the trailing
         `",{fragment}"` suffix stripped; `new_artifacts_path = fragment + "," + raw_fields[5]`
         (e.g. `"N/A (hotfix" + "," + " no staging artifacts)"` →
         `"N/A (hotfix, no staging artifacts)"`, byte-identical to the clean convention used
         elsewhere in the file). `record` populated with `summary=new_summary`,
         `artifacts_path=new_artifacts_path`, all other fields mapped positionally as usual.
       - **Else (unbalanced parens, no known fragment match):** this is a new, not-yet-seen
         sub-shape of the quote-desync pattern. `classification="quote_desync_masquerading_as_clean"`,
         `recoverable=False`, `record=None` (never guess a reconstruction for an unevidenced shape —
         same safe-degradation discipline as Finding 1's rejoin heuristic). Not observed in the
         current 34 lines, but required for any future occurrence of this class outside the closed
         3-fragment vocabulary.
     - **If balanced:** proceed exactly as the original algorithm did — continue to the duplicate
       check below and classify `clean`.
   - Duplicate check (applies to both the `clean` and the `quote_desync_masquerading_as_clean`
     paths above, same mechanism): if this exact raw line text was seen at an earlier line_no →
     `is_duplicate=True`, `duplicate_of_line=<first line_no>`; else `is_duplicate=False`. (For
     `clean` rows, `record` was already populated normally above; for
     `quote_desync_masquerading_as_clean` rows, `record` is whatever the branch above set it to —
     `is_duplicate` is orthogonal to `classification` and computed identically regardless of which
     path a row took, exactly as it already was for the pre-Finding-3 algorithm.)

**Justification: why quote-desync rows count toward `ambiguous_row_count`.** AC1 requires "every
row classified as clean or ambiguous/unparseable, never silently dropped or merged." Read narrowly,
that framing was written against Finding 1's field-count signal alone. Finding 3 proves a `clean`
classification based on field-count==6 alone is insufficient — a row can pass the field-count check
and still carry silently-wrong `summary`/`artifacts_path` values. Since `ambiguous_row_count`'s
entire purpose (per `ticket_stats_report.py::compute_velocity`'s mirrored convention) is to surface
"this data is not safely usable as-is" as a first-class, always-present signal, a
`quote_desync_masquerading_as_clean` row is the same fundamental problem as a
`field_count_mismatch` row — just caught by a different signal (paren-balance vs. raw field count)
— and must count the same way. `embedded_header_duplicate` remains excluded from
`ambiguous_row_count` because it was never at risk of being silently mistaken for valid data
(`record` is always `None` for it, by construction) — that exclusion is unaffected by this change.
4. **If `len(raw_fields) != 6`:** this is the field-count-mismatch case (11 real rows today, per
   investigation.md Finding 1's table — lines 1511, 3104, 1581, 3174, 3245, 3253, 3284, 3287, 3289,
   3294, 3307).
   - Attempt `next(csv.reader([raw_line_text], strict=True))`. **Empirically verified for this
     plan** (direct script run against the real file, 2026-09-06): this raises `csv.Error` (`"','
     expected after '\"'"`) for exactly lines 1511 and 3104, and does NOT raise for the other 9
     confirmed mismatch lines (1581, 3174, 3245, 3253, 3284, 3287, 3289, 3294, 3307) — this is
     `csv.reader`'s own built-in RFC4180-strict-mode validation, not a hand-rolled heuristic, and it
     is the load-bearing distinguishing signal between "irreducibly ambiguous" and "safely
     recoverable." **Do not substitute a hand-written regex/quote-counting heuristic for this** —
     an earlier draft of this plan tried "count embedded `\"` characters" and "check raw-line total
     quote-char parity," both of which misclassify at least one of the 11 real rows (verified by
     direct computation during planning); `strict=True` is the only tested rule that classifies all
     11 correctly.
     - If `csv.Error` raised → `classification="field_count_mismatch"`, `recoverable=False`,
       `record=None` (never guessed/reinterpreted — the raw `raw_fields` list is still present in
       the output for inspection, satisfying "never silently dropped").
     - Else (no strict error): search `raw_fields` for the status anchor — the first index `i` with
       `2 <= i <= len(raw_fields) - 2` where `raw_fields[i].strip() in STATUS_VOCAB`. (Search starts
       at index 2, not a fixed index 3, because title itself can absorb extra fields when it
       contains an unescaped comma — confirmed for rows 3245/3284/3287/3307, where status is found
       at index 4, 4, 5, and 5 respectively, not always index 3. Verified by direct computation
       against the real file, 2026-09-06: `csv.reader` on line 3245 yields status-candidate index
       `[4]`, line 3284 yields `[4]`, line 3287 yields `[5]`, line 3307 yields `[5]` — an earlier
       draft of this plan cited "4, 3, 5, and 4," which was wrong for 3284 and 3307; corrected here.
       This is a prose-citation fix only — the anchor-search algorithm itself is a dynamic search,
       not a hardcoded index list, so it already produced the correct anchor for all four rows
       regardless of the stale prose.)
       - If zero or more-than-one candidate index is found → `classification="field_count_mismatch"`,
         `recoverable=False`, `record=None` (never guess between ambiguous candidates). Not observed
         in the current 11 rows, but must degrade safely for any future row shape.
       - If exactly one such index is found, `title=",".join(raw_fields[2:i])` and
         `status=raw_fields[i]` are fixed — but `raw_fields[i+1:]` (call it `remaining`) must still be
         split correctly between `summary` and `artifacts_path`. **An earlier draft of this plan
         hard-assumed `artifacts_path = remaining[-1]` alone and `summary =
         ",".join(remaining[:-1])` unconditionally.** This is WRONG for rows 1581/3174
         (`TCK-20260820-EPIC-WORLD-RENDERING-CORE`): their real defect (confirmed by direct
         `csv.reader` inspection of the live file, 2026-09-06) is an unescaped comma **inside**
         `artifacts_path` itself — the true value is `none (epic, scope-only)`, but the unescaped
         comma splits it into two raw fields, `remaining[-2] = 'none (epic'` and
         `remaining[-1] = ' scope-only)'`. Blindly taking `remaining[-1]` alone as `artifacts_path`
         yields the truncated ` scope-only)` (losing the `none (epic` prefix), and
         `summary=",".join(remaining[:-1])` wrongly appends `none (epic` onto the end of the real
         summary text — silently corrupting both fields while still reporting `recoverable=True`,
         which is exactly the "guessed shape" AC2 prohibits.

         **Fix: determine how many of `remaining`'s trailing fields belong to `artifacts_path` via a
         parenthesis-balance plausibility check, trying the smallest candidate first:**
         1. **Candidate `n=1`** (`artifacts_path = remaining[-1]` alone): plausible iff
            `remaining[-1].count("(") == remaining[-1].count(")")`.
         2. **Candidate `n=2`** (`artifacts_path = ",".join(remaining[-2:])`, only tried if
            `len(remaining) >= 2`): plausible iff
            `",".join(remaining[-2:]).count("(") == ",".join(remaining[-2:]).count(")")`.
         3. Use the smallest `n` (1 before 2) whose candidate passes. If none passes →
            `classification="field_count_mismatch"`, `recoverable=False`, `record=None`
            (irreducibly ambiguous — no trailing-field split length is plausible; never guess). Not
            observed in the current 11 rows, but this is the safe-degradation path for any future
            row shape this heuristic cannot confirm (e.g. a genuine 3-way split, which no current row
            exhibits).
         4. Once `n` is chosen: `artifacts_path = ",".join(remaining[-n:])`,
            `summary = ",".join(remaining[:-n])`.

         **Verified against all 11 real rows, not asserted (direct computation, 2026-09-06):** the 9
         rows that reach this branch (1511/3104 are excluded — they fail the `strict=True` check
         earlier) split into two subgroups by real root cause: 7 whose comma is inside
         `title`/`summary` (3245, 3253, 3284, 3287, 3289, 3294, 3307) and 2 whose comma is inside
         `artifacts_path` itself (1581, 3174).
         - For the 7 title/summary-defect rows, `remaining[-1]` is one of `stored_artifacts/TCK-.../`
           (a path with zero parens) or the literal string `none` (also zero parens) —
           `count("(") == count(")") == 0` trivially passes the `n=1` check, so these 7 rows
           correctly use `n=1` and are unaffected by this fix (same reconstructed values as before).
         - For 1581/3174: `remaining[-1] = ' scope-only)'` has 0 `(` and 1 `)` → `n=1` fails balance.
           `",".join(remaining[-2:]) = 'none (epic, scope-only)'` has 1 `(` and 1 `)` → `n=2` passes.
           Result: `artifacts_path = "none (epic, scope-only)"` (correct, matches
           investigation.md Finding 1's confirmed root cause exactly) and `summary` no longer has the
           `,none (epic` fragment appended.
         - Cross-checked against every genuinely complete, single-field `artifacts_path` value that
           appears anywhere in the file's ~1378 distinct clean (6-field) rows containing a paren
           (`N/A (hotfix, no staging artifacts)`, `none (epic)`, `none (epic -- see children's
           stored_artifacts)`, `none (superseded before Implement)`, etc., 2026-09-06 scan): every one
           has balanced parens on its own — zero false positives where a genuinely-complete
           single-field `artifacts_path` would be wrongly flagged as needing an `n=2` merge.

         This is still the same "locate the status anchor and rejoin the surrounding fragments with
         `,`" technique from
         `tickets/done/TCK-20260819-HOTFIX-WORKING-LOG-LEGACY-SCHEMA-ROWS.md:111-112` ("fixed
         generically: locate the literal `DONE` token as the status anchor and rejoin the surrounding
         fragments with `,`"), generalized from a literal `"DONE"` search to a `STATUS_VOCAB`
         membership search on the left side of the split (title/status boundary) and extended with
         this evidenced paren-balance check on the right side (summary/artifacts_path boundary) —
         the left-side generalization alone was insufficient because it silently assumed the
         right-side boundary was always exactly one field wide, which real row content disproves.
   - Duplicate check (same as step 3's `clean` branch) is still applied after this: if the raw line
     text was seen before, set `is_duplicate=True` regardless of `recoverable`.

**Do NOT touch:** `tools/validate_working_log.py`'s existing duplicate-ticket-ID, missing-log-entry,
and empty-field check *logic* — this module only supplies rows; Step 4 wires it in without changing
those three checks' behavior. Do NOT attempt to detect/flag the ~1586-row mega-block from
investigation.md Finding 2 as a special case beyond the same generic `is_duplicate` mechanism every
other row also gets — no mega-block-specific code path.

**Verify:** `tests/tools/test_validate_working_log.py::test_clean_row_parses_with_expected_fields`,
`test_field_count_mismatch_row_is_flagged_ambiguous_not_dropped_or_merged`,
`test_irreducibly_ambiguous_quote_desync_row_is_not_heuristically_repaired` (Step 2, below),
`test_trailing_field_comma_split_rows_reconstruct_correct_artifacts_path` (Step 3, below — the
real-file regression test for the paren-balance trailing-field-count fix), and (Finding 3)
`test_quote_desync_masquerading_as_clean_rows_are_reclassified_and_reconstructed`,
`test_quote_desync_row_with_unmatched_fragment_degrades_to_unrecoverable` (Step 2, below), and
`test_all_34_confirmed_live_quote_desync_lines_are_flagged` (Step 3, below).

---

### Step 2 — Unit tests for the parser module (fixture-based)
**Files:** `tests/tools/test_validate_working_log.py` (new file)
**Change:**
Create the new test file (confirmed today: `tests/tools/` has no `test_validate_working_log.py` or
similarly-named file — ticket Scope's own "no dedicated test file exists today" claim, re-confirmed
directly for this plan via `ls tests/tools/`). Import both `tools.working_log_parser` and
`tools.validate_working_log` (via the `sys.path.insert(0, str(_TOOLS_DIR))` pattern already used by
`tests/tools/test_ticket_stats_report.py:9-11`).

Add, using `tmp_path` fixture CSV files (mirroring `test_ticket_stats_report.py`'s
`_write_ticket`-style helper pattern):

- `test_clean_row_parses_with_expected_fields` — a well-formed 6-field row, including one field with
  a correctly double-quoted comma-bearing value (matching the file's own real quoting convention,
  e.g. `tickets/working_log.csv:1581`'s summary field), parses to a dict with all 6 keys correct and
  `classification == "clean"`.
- `test_field_count_mismatch_row_is_flagged_ambiguous_not_dropped_or_merged` — at least 3 fixture
  rows, one per distinct real root-cause pattern from investigation.md Finding 1: (a) unescaped
  comma inside `artifacts_path` (mirrors line 1581's shape exactly: `none (epic, scope-only)`),
  (b) unescaped comma inside `title` (mirrors line 3245's shape: an unquoted title containing a
  literal `,`), (c) the quote-desync case (mirrors line 1511's shape: a quoted summary field
  containing an internal un-doubled `"`). Assert each fixture row is present in `result.rows` with
  `classification == "field_count_mismatch"` — never absent, never silently merged into a 6-field
  `clean` record. For fixture (a) specifically, additionally assert `recoverable is True` and the
  exact reconstructed values: `record["artifacts_path"] == "none (epic, scope-only)"` (not the
  truncated `" scope-only)"`) and `record["summary"]` does NOT end with the corrupted
  `,none (epic` fragment — this is a direct regression test for the paren-balance trailing-field
  fix (Step 1), proving `artifacts_path` is correctly rejoined from the last two raw fields rather
  than truncated to the last raw field alone.
- `test_irreducibly_ambiguous_quote_desync_row_is_not_heuristically_repaired` — the line 1511/3104
  shape fixture specifically. Assert `recoverable is False` and `record is None`, and that
  `raw_fields` is still present unmodified (proving the row is surfaced, not dropped, while also
  proving no guessed reconstruction was substituted).
- `test_duplicate_content_rows_are_flagged_not_fixed` — a fixture CSV with the line 3245/3253 shape
  repeated verbatim as two rows. Assert both rows remain as two independent `ParsedRow` entries
  (never merged/deleted) and the second carries `is_duplicate=True`, `duplicate_of_line` pointing at
  the first; the first is not itself flagged (`is_duplicate=False`).
- A fixture covering the embedded-header-duplicate shape (a data row whose 6 values exactly equal
  the header's own text) → `classification == "embedded_header_duplicate"`, `record is None`.
- `test_ambiguous_row_count_is_first_class_signal_matching_ticket_stats_report_convention` — a
  fixture file with a known mix of clean/mismatch rows; assert `ParseResult.ambiguous_row_count`
  equals the exact expected int and is always present (never omitted) even when 0 (a fixture with
  zero mismatches). Updated for Finding 3: the fixture mix now includes one
  `quote_desync_masquerading_as_clean` row alongside the pre-existing clean/mismatch rows, and the
  expected `ambiguous_row_count` asserted includes it (proving the union, not just
  `field_count_mismatch` alone).
- `test_quote_desync_masquerading_as_clean_rows_are_reclassified_and_reconstructed` (Finding 3) — at
  least 2-3 fixture rows built from real Finding-3 examples (investigation.md's 17-row table), one
  per distinct vocabulary fragment: line 1100's shape (`N/A (hotfix`), line 1318's shape
  (`none (hotfix`), and line 1400's shape (`none (scope-only epic`). Each fixture row has exactly 6
  raw fields (never trips the field-count check) with `artifacts_path` paren-unbalanced. Assert each
  is present in `result.rows` with `classification == "quote_desync_masquerading_as_clean"` (never
  `"clean"`), `recoverable is True`, and the exact reconstructed values — e.g. for the line-1100-shape
  fixture, `record["artifacts_path"] == "N/A (hotfix, no staging artifacts)"` (not the truncated
  `" no staging artifacts)"`) and `record["summary"]` does NOT end with the corrupted
  `,N/A (hotfix` fragment. This is the fixture-level regression test for the new paren-balance gate
  and fixed-vocabulary rejoin.
- `test_quote_desync_row_with_unmatched_fragment_degrades_to_unrecoverable` (Finding 3) — a synthetic
  fixture row (no real occurrence exists today, per investigation.md's full-file sweep) with exactly
  6 raw fields, `artifacts_path` paren-unbalanced, but `summary` does NOT end with any of the 3 known
  vocabulary fragments. Assert `classification == "quote_desync_masquerading_as_clean"`,
  `recoverable is False`, `record is None`, and `raw_fields` still present unmodified — proving the
  gate correctly flags the row as unsafe-as-clean while refusing to guess a reconstruction for an
  unevidenced shape (mirrors `test_irreducibly_ambiguous_quote_desync_row_is_not_heuristically_repaired`'s
  safe-degradation intent for Finding 1, applied to the new gate).

**Do NOT touch:** any assertions about the real committed `tickets/working_log.csv` in this step —
that belongs to Step 3 (integration tests). Do NOT add a test here for the ~1586-row mega-block's
exact count — out of scope per the ticket's own Out-of-Scope item and investigation's explicit
recommendation to keep the live-file duplicate assertion narrow.

**Verify:** `pytest tests/tools/test_validate_working_log.py -v` (new tests pass; this step has no
prior baseline to regress).

---

### Step 3 — Integration tests against the real committed `tickets/working_log.csv`
**Files:** `tests/tools/test_validate_working_log.py` (same file, additional tests)
**Change:**
Add tests that invoke `parse_working_log(Path("tickets/working_log.csv"))` against the real repo
file (not a fixture), matching this repo's established real-corpus-test pattern (same style as the
`test_manifest_run_against_real_corpus_produces_zero_diff` precedent referenced in test_plan.md):

- `test_round_trip_parses_full_file_without_exception` — parsing completes with no exception, and
  `len(result.rows) == len(list(csv.reader(open("tickets/working_log.csv"))) ) - 1` (minus 1 for the
  header), computed independently in the test via the stdlib `csv` module as an oracle — i.e. every
  physical data row produces exactly one `ParsedRow`, none dropped or merged, for the full current
  file (3336+ data rows, confirmed 3376 data rows / 3377 physical lines as of this investigation's
  scan).
- `test_all_11_confirmed_live_mismatch_rows_are_flagged` — asserts the exact set of line numbers
  `{1511, 3104, 1581, 3174, 3245, 3253, 3284, 3287, 3289, 3294, 3307}` all appear in
  `result.rows` with `classification == "field_count_mismatch"` (matched by `line_no`, not by a bare
  count, per test_plan.md's explicit requirement that a future drift in this set must fail loudly
  rather than silently pass a stale count). Within that set, additionally assert `recoverable is
  False` for exactly `{1511, 3104}` and `recoverable is True` for the other 9 — this directly proves
  the `strict=True` distinguishing rule classifies all 11 real rows correctly, not just in the
  abstract.
- `test_trailing_field_comma_split_rows_reconstruct_correct_artifacts_path` — for lines 1581 and 3174
  specifically (the 2 of the 9 recoverable rows whose real defect is an unescaped comma inside
  `artifacts_path` rather than `title`/`summary`), assert against the real parsed record:
  `record["artifacts_path"] == "none (epic, scope-only)"` (the correct, complete value — proving the
  paren-balance trailing-field-count check correctly used `n=2` and rejoined `remaining[-2:]`) and
  `record["summary"]` ends with `"...uncalibrated illustrative placeholders."` with no trailing
  `,none (epic` fragment appended. This is a direct regression test against the real committed file
  for the Step 1 fix — the earlier draft's `artifacts_path = remaining[-1]` assumption would fail
  this test (it would produce `artifacts_path == " scope-only)"` and a corrupted `summary`).
- `test_ambiguous_row_count_matches_45_for_real_file` (renamed/updated from the pre-Finding-3
  `test_ambiguous_row_count_matches_11_for_real_file`) — `result.ambiguous_row_count == 45` against
  the real file today (11 `field_count_mismatch` physical lines + 34 `quote_desync_masquerading_as_clean`
  physical lines; this is the literal, undeduped, per-physical-row count per `ambiguous_row_count`'s
  own dataclass docstring definition — reconciles exactly: 3376 total data rows = 3330 clean + 11
  field_count_mismatch + 34 quote_desync_masquerading_as_clean + 1 embedded_header_duplicate.
  Documents the current, expected value; if it drifts, this is a deliberate future update per
  test_plan.md's guidance, not flakiness).
- `test_all_34_confirmed_live_quote_desync_lines_are_flagged` (Finding 3) — asserts the exact set of
  34 line numbers from investigation.md's Finding 3 table (both the 17 originals and their 17
  `+1593`-offset duplicates inside Finding 2's mega-block: `{1100, 1101, 1102, 1103, 1318, 1320,
  1329, 1332, 1337, 1400, 1401, 1415, 1453, 1457, 1459, 1460, 1462, 2693, 2694, 2695, 2696, 2911,
  2913, 2922, 2925, 2930, 2993, 2994, 3008, 3046, 3050, 3052, 3053, 3055}`) all appear in
  `result.rows` with `classification == "quote_desync_masquerading_as_clean"` (matched by `line_no`,
  never by a bare count — same discipline as
  `test_all_11_confirmed_live_mismatch_rows_are_flagged` for Finding 1). Additionally asserts
  `recoverable is True` for all 34 (none of the real 17 distinct events hit the unmatched-fragment
  degrade path).
- `test_quote_desync_line_1100_reconstructs_to_known_vocabulary_artifacts_path` (Finding 3) — for the
  real committed line 1100 (`TCK-20260720-MONITORING-PIPELINE-BUGFIXES`, per investigation.md's
  table), assert against the real parsed record: `record["artifacts_path"] ==
  "N/A (hotfix, no staging artifacts)"` (proving the fixed-vocabulary rejoin correctly matched the
  `N/A (hotfix` fragment and rebuilt the complete value, not the truncated
  `" no staging artifacts)"`) and `record["summary"]` does not end with the corrupted `,N/A (hotfix`
  fragment. This is the direct regression test against the real committed file for the Finding 3
  fix, mirroring `test_trailing_field_comma_split_rows_reconstruct_correct_artifacts_path`'s role for
  Finding 1's 1581/3174 fix.
- `test_historical_rows_are_never_rewritten_byte_identical_after_run` — copy
  `tickets/working_log.csv` into `tmp_path`, run `parse_working_log` against the copy, assert the
  copy's bytes/mtime are unchanged before vs. after (architecture guard: the parser opens the file
  read-only, `open(path, newline="")` with no write mode anywhere in `working_log_parser.py`).

**Do NOT touch:** the real `tickets/working_log.csv` file itself in any of these tests — always
operate on a `tmp_path`-copied version for the byte-identical guard test; the round-trip/count tests
may read the real file directly (read-only) but must never open it for writing.

**Verify:** `pytest tests/tools/test_validate_working_log.py -v` (all tests, including Step 2's,
green).

---

### Step 4 — `validate_working_log.py` adopts the new parser
**Files:** `tools/validate_working_log.py`
**Change:**
Replace the current bare `csv.DictReader` row-loading (`tools/validate_working_log.py:33-38`) with a
call to `working_log_parser.parse_working_log(log_path)`. Refactor the three existing checks (lines
40-67: duplicate ticket IDs, missing done/ entries, empty fields) out of `main()` into a new
testable function, e.g. `run_validation(log_path: Path, done_dir: Path) -> dict`, returning
`{"errors": [...], "row_count": N, "done_count": M, "ambiguous_row_count": X,
"duplicate_row_count": Y}` — mirroring `ticket_stats_report.py`'s existing pattern of separating pure
check functions from the `main()` CLI wrapper (`tools/ticket_stats_report.py:109` shows this same
separation for `compute_velocity`). `main()` becomes a thin wrapper: call `run_validation`, print
errors + the new counts, `sys.exit(1)` on any error (preserving current exit-code semantics exactly
— this ticket does not change when the script exits 0 vs 1 for the three pre-existing checks).

**Every other writer to `tickets/working_log.csv` and to `validate_working_log.py`'s output
contract:** confirmed via `grep -rn "working_log.csv" tools/ src/` (investigation.md's own scan) —
all touches are read-only (`tools/validate_working_log.py` itself, `tools/knowledge_search.py`,
`tools/ticket_stats_report.py`, `tools/agent-monitoring/{validate,epic_staleness_check}.py`,
`tools/agent_codex_pilot_entrypoint/preparation.py`, `tools/codebase_health_baseline.py`,
`tools/gate_checks/done_checker_static.py`); none opens the file in write/append mode, and none of
those other readers calls into `validate_working_log.py`'s functions directly (each does its own
independent read) — so this step's refactor has no ordering/race interaction with any other writer,
only with `validate_working_log.py`'s own three pre-existing checks, whose input list changes from
raw `DictReader` rows to `[r.record for r in result.rows if r.record is not None]` (i.e., `clean` +
recoverable `field_count_mismatch` rows only — `embedded_header_duplicate` and irreducibly-ambiguous
rows contribute no record, same as they would have contributed garbled/wrong data under the old
`DictReader` restkey behavior, except now that garbling is explicit and countable instead of silent).

**Confirmed: no further wiring change needed here for Finding 3.** This filter is `r.record is not
None`, a generic predicate on the dataclass field, not a hardcoded `classification == "clean"` (or
`== "field_count_mismatch"`) check. Step 1's Finding 3 extension populates `record` for recoverable
`quote_desync_masquerading_as_clean` rows exactly the same way it populates `record` for recoverable
`field_count_mismatch` rows, so those 17 rows' corrected `record`s flow through to the three existing
checks automatically, with zero additional code in this step. Unmatched-fragment
(`recoverable=False`) quote-desync rows correctly contribute no record, same as irreducibly-ambiguous
`field_count_mismatch` rows already do.

**Do NOT touch:** the internal logic of the duplicate-ticket-ID check (`tools/validate_working_log.py:40-49`),
the missing-log-entry check (`:51-59`), or the empty-field check (`:61-67`) — only the `rows` list
that feeds them changes source (from `DictReader` output to the new parser's clean+recovered
records); the check logic itself (loop bodies, error message formats) is unchanged, per the ticket's
explicit Out-of-Scope/Anti-Drift guidance that these three checks are unrelated to the
field-count-mismatch problem this ticket scopes.

**Verify:**
`tests/tools/test_validate_working_log.py::test_ambiguous_row_count_is_first_class_signal_matching_ticket_stats_report_convention`
(Step 2, now exercised through `run_validation()` too) plus a new
`test_run_validation_preserves_existing_duplicate_id_and_missing_entry_checks` fixture test proving
those two checks still fire correctly on a small fixture with a real duplicate ID and a real missing
`done/` entry, unchanged from current behavior.

---

### Step 5 — `knowledge_search.py` gets a narrow embedded-header-duplicate guard
**Files:** `tools/knowledge_search.py`, `tests/tools/test_knowledge_search.py`
**Change:**
In `_extract_working_log_rows` (`tools/knowledge_search.py:95-130`), add one explicit guard
immediately alongside the existing `if not ticket_id and not title: continue` line
(`tools/knowledge_search.py:118`): skip (and count) a row whose extracted `ticket_id` value is the
literal string `"ticket_id"` (i.e., equals the header's own column name) — this is the exact,
concrete, already-live bug from investigation.md Finding 2 (`tickets/working_log.csv:1594`, the
embedded duplicate header row, which today passes the existing guard because both `ticket_id` and
`title` come back truthy as `"ticket_id"`/`"title"`). Track a local counter of skipped rows across the
function's loop; if `> 0` at the end, print a `Warning: skipped N embedded-header-duplicate row(s)
in {csv_path}` message via the same `print(..., file=sys.stderr)` pattern already used at
`tools/knowledge_search.py:128-129` for the function's existing broad `except Exception` handler —
this satisfies AC3's "report the ambiguous-row count as a first-class visible signal" for this module
without changing `_extract_working_log_rows`'s return type (`list[dict]`, unchanged), so
`_collect_corpus` and every other caller of this function is unaffected.

**Do NOT touch:** `_extract_working_log_rows`'s existing multi-column-name-variant tolerance
(`ticket_id`/`id`/`ID`, `title`/`Title`/`name`, etc., lines 104-117) — this is intentionally more
lenient than `validate_working_log.py`'s strict current-6-column-schema contract (it supports
historical schema variants per investigation.md's own "Existing parsers" section), and swapping it
to use `working_log_parser.py` wholesale would regress that lenience for genuinely old-schema rows.
This step is a targeted guard addition only, not a parser swap.

**Confirmed: no change needed here for Finding 3.** `knowledge_search.py::_extract_working_log_rows`
does not import or call `tools/working_log_parser.py` at all (per the Dependency Map: Step 5 is
"fully independent of Steps 1-4"), so Finding 3's new classification value and paren-balance gate
have no surface here. This module's own DictReader-based extraction never validated `artifacts_path`
shape either before or after this plan, so the 17 quote-desync rows' presence in the corpus is
unaffected by this ticket's scope — they were already silently indexed with whatever
positionally-mapped values `DictReader` produced, and remain so; fixing that would require the same
kind of parser swap Step 5 explicitly declines to make, and is out of scope for this ticket.

**Verify:** new test `tests/tools/test_knowledge_search.py::TestExtractWorkingLogRows::test_does_not_index_embedded_header_duplicate_row`
(added to the existing `TestExtractWorkingLogRows` class at `tests/tools/test_knowledge_search.py:669-693`,
following its existing fixture-CSV pattern) — a fixture CSV containing a mid-file duplicate header
row asserts no returned row has `id == "ticket_id"`. Also re-run
`tests/tools/test_knowledge_search.py` (full file) and `tests/tools/test_hybrid_retrieval.py` (full
file) to confirm no regression — `_collect_corpus`'s consumers are unaffected since the function's
return shape is unchanged.

---

### Step 6 — Close the write-time gap: `docs/ai/ticket-lifecycle.md` Finalize wording
**Files:** `docs/ai/ticket-lifecycle.md`
**Change:**
This is the "stricter format going forward" half of the tolerant-parser-vs-stricter-format decision
(see Summary and the Acceptance Criteria Map below for the justification). Update the Finalize-phase
`Append tickets/working_log.csv:` example (`docs/ai/ticket-lifecycle.md:567-570`, confirmed by direct
read: shows a literal unquoted example row today,
`2026-06-06T00:00:00Z,TCK-20260606-COMBAT-RELATION,Relation Projection,DONE,Added relation
projection wrapper into combat target classification,stored_artifacts/TCK-20260606-COMBAT-RELATION`,
with no CSV quoting demonstrated anywhere) to add an explicit instruction sentence plus a
comma-bearing example, e.g.:

```
3. Append `tickets/working_log.csv`:
   ```
   2026-06-06T00:00:00Z,TCK-20260606-COMBAT-RELATION,Relation Projection,DONE,Added relation projection wrapper into combat target classification,stored_artifacts/TCK-20260606-COMBAT-RELATION
   ```
   **If any field (title/summary/artifacts_path) contains a literal comma, wrap that field in
   double quotes** (RFC4180), e.g.:
   ```
   2026-06-06T00:00:00Z,TCK-20260606-COMBAT-RELATION,Relation Projection,DONE,"Added relation projection wrapper, including tests, into combat target classification",stored_artifacts/TCK-20260606-COMBAT-RELATION
   ```
   Un-quoted embedded commas silently split this row into extra columns for every downstream reader
   (`validate_working_log.py`, `knowledge_search.py`, `ticket_stats_report.py`) — this is a real,
   recurring corruption source (see `TCK-20260904-WORKING-LOG-CSV-PARSER`).
```

No new CI/gate check is built to enforce this at write time — investigation.md's Risk #1 floated a
`done_checker_static.py`-style gate as a possible option (ii), but that is more machinery than this
ticket's Scope calls for (Scope only requires the parser + reporting changes, not a new
enforcement gate). **Recommend filing this as a separate follow-up ticket** if the doc-instruction
alone proves insufficient in practice (same "file tickets for workflow gaps" convention this project
already follows for Finding 2's `merge=union` gap) — do not build it here.

**Do NOT touch:** any other section of `docs/ai/ticket-lifecycle.md` outside the Finalize step 3
example block.

**Verify:** no automated test applies (doc-only change); `done-checker`'s Finalize self-check
(`tools/gate_checks/done_checker_static.py`'s "exactly one working_log.csv row" check) is unaffected
— confirmed by not changing that script or its inputs.

## Scope Guards

- Never rewrite, reformat, or reinterpret any historical row's bytes in `tickets/working_log.csv`
  itself — all classification/reconstruction happens in memory (`ParsedRow.record`), the file on
  disk is opened read-only everywhere in this plan (Steps 1, 3, 4, 5 all only `open(path, "r"...)` /
  `newline=""` read mode).
- Do not attempt to fix, clean up, or specially-remediate Finding 2's ~1586-row whole-block
  duplication — the generic `is_duplicate` mechanism (Step 1) will naturally also flag those rows as
  a byproduct of detecting *any* exact-duplicate content, which is acceptable detection, not
  remediation; no test in this plan asserts an exact count against that mega-block (Steps 2/3 keep
  duplicate-content assertions scoped to the small named 3245/3253 pair, plus Finding 3's exact
  34-line set — a real, evidenced count for those specific 17 events, not the mega-block as a
  whole). This includes Finding 3's 17 quote-desync events: their duplication aspect (each one
  appearing twice, at `line` and `line+1593`) stays flagged-only via `is_duplicate`, exactly like
  every other row in the mega-block — this ticket fixes their field-boundary corruption, not their
  duplication.
- Do not touch `tools/validate_working_log.py`'s duplicate-ticket-ID or missing-log-entry check
  *logic* (Step 4 only changes their row *source*, not their behavior).
- Do not fix or merge the 2-3 duplicate rows the ticket names, or any other duplicate rows found —
  flag only, per `is_duplicate`/`duplicate_of_line`.
- Rows 1511/3104 must always classify `recoverable=False`, `record=None` — never routed through the
  rejoin heuristic, regardless of any future generalization of the anchor-search logic (guarded by
  Step 2's `test_irreducibly_ambiguous_quote_desync_row_is_not_heuristically_repaired`).
- `QUOTE_DESYNC_SUMMARY_FRAGMENTS` is a closed, evidence-only 3-string vocabulary (`N/A (hotfix`,
  `none (hotfix`, `none (scope-only epic`) — never add a 4th fragment or generalize the match into a
  regex/prefix-family match. A 6-field row with unbalanced `artifacts_path` parens that does not
  match one of these exact 3 must degrade to `recoverable=False`, never a guess (guarded by Step 2's
  `test_quote_desync_row_with_unmatched_fragment_degrades_to_unrecoverable`).
- Do not treat `len(raw_fields) == 6` alone as sufficient evidence of `clean` anywhere in this
  module — every 6-field, non-header row must also pass the `artifacts_path` paren-balance gate
  before being classified `clean` (Finding 3's central fix; see Anti-Drift Notes).
- Do not swap `knowledge_search.py::_extract_working_log_rows`'s lenient multi-column-variant
  extraction for the new strict-schema parser — Step 5 is a narrow guard addition only.
- Do not build a new CI/gate check for write-time comma-quoting enforcement — Step 6 is doc-wording
  only; a gate is explicitly deferred to a possible future ticket, not built here.
- `docs/parity_ledger/*.yaml` is untouched — confirmed out of scope by both this investigation and
  the prior `TCK-20260705-WORKING-LOG-BACKFILL` investigation (no simulation-subsystem surface here).

## Dependency Map

- Step 1 (parser module) has no dependencies; everything else depends on it.
- Step 2 (unit tests) depends on Step 1.
- Step 3 (integration tests) depends on Step 1; independent of Step 2 (can run in parallel once
  Step 1 lands, though both live in the same file so are naturally done together).
- Step 4 (`validate_working_log.py` adoption) depends on Step 1 (imports the parser).
- Step 5 (`knowledge_search.py` guard) is fully independent of Steps 1-4 — it does not use the new
  parser module at all.
- Step 6 (doc wording) is fully independent of all other steps.

## Acceptance Criteria Map

| AC from ticket | Implemented by step(s) | Verified by test |
|---|---|---|
| AC1: Round-trip parse of full file, exactly one record per physical row, every row classified clean or ambiguous/unparseable (mismatch), never dropped/merged | Step 1 (algorithm, extended by Finding 3's paren-balance gate), Step 3 (real-corpus proof) | `test_round_trip_parses_full_file_without_exception`, `test_all_34_confirmed_live_quote_desync_lines_are_flagged` |
| AC2: Each of the 11 confirmed mismatch rows (now 45 physical lines: 11 field-count-mismatch + 34 quote-desync-masquerading, corresponding to roughly 8 + 17 = 25 distinct underlying append incidents once duplication is accounted for) surfaced as explicitly flagged/ambiguous, not auto-corrected/reinterpreted into a guessed shape | Step 1 (all 11 `field_count_mismatch` rows get a distinct non-"clean" tag as before; all 34 quote-desync physical lines now also get a distinct non-"clean" tag, `quote_desync_masquerading_as_clean`, rather than silently passing as `clean`; the 2 irreducible `field_count_mismatch` rows and any unmatched-fragment quote-desync row get `record=None`, never a guessed value; both the paren-balance-on-trailing-field check (Finding 1) and the paren-balance-on-artifacts_path gate + closed 3-fragment vocabulary rejoin (Finding 3) are verified mechanical reconstructions, not guesses), Step 3 (proves this against the real 11 + real 34 lines) | `test_all_11_confirmed_live_mismatch_rows_are_flagged`, `test_irreducibly_ambiguous_quote_desync_row_is_not_heuristically_repaired`, `test_trailing_field_comma_split_rows_reconstruct_correct_artifacts_path`, `test_all_34_confirmed_live_quote_desync_lines_are_flagged`, `test_quote_desync_line_1100_reconstructs_to_known_vocabulary_artifacts_path`, `test_quote_desync_row_with_unmatched_fragment_degrades_to_unrecoverable` |
| AC3: `validate_working_log.py`/`knowledge_search.py` adopt the new parser or report ambiguous-row count as a first-class signal, matching `ticket_stats_report.py`'s convention | Step 4 (`validate_working_log.py` adopts parser fully — `ambiguous_row_count` now unions both classifications with no extra wiring, confirmed in Step 4's Change text), Step 5 (`knowledge_search.py` narrow guard + stderr count signal, confirmed unaffected by Finding 3) | `test_ambiguous_row_count_is_first_class_signal_matching_ticket_stats_report_convention`, `test_ambiguous_row_count_matches_45_for_real_file`, `test_does_not_index_embedded_header_duplicate_row` |
| AC4: If stricter future-write schema adopted, pre-cutover rows stay byte-identical, any normalized view is a separate derived file | Step 1/4/5 (read-only everywhere — no derived-file mechanism is built since none is needed for this ticket's scope), Step 6 (doc-instruction-only stricter-format half, no rewrite of any existing row) | `test_historical_rows_are_never_rewritten_byte_identical_after_run` |

**Note on AC1 being satisfied more completely by the Finding 3 extension than the original
field-count-only design would have:** AC1's "every row classified as clean or ambiguous/unparseable,
never silently dropped or merged" was originally implemented (pre-Finding-3) using field-count==6 as
the sole test for "clean." Finding 3 proves that test alone is insufficient — 17 real, distinct rows
pass field-count==6 while carrying silently-wrong `summary`/`artifacts_path` values, which is exactly
the "silently... merged [into a wrong shape]" failure AC1 exists to prevent, just not the literal
"dropped" or field-count-mismatch shape the AC's authors evidently had in mind when the ticket was
written. The Step 1 extension (paren-balance gate on every 6-field row's `artifacts_path`) closes
this gap for the one now-known corruption class that field-count blindness misses; this is a
stronger, evidence-backed satisfaction of AC1's actual spirit ("no row is silently treated as valid
when it isn't"), not a scope expansion — no other corruption class beyond Finding 1 and Finding 3 is
searched for or assumed to exist.

**Note on AC2's literal wording vs. Step 1's rejoin reconstruction:** AC2 says the 11 rows must be
"not auto-corrected or reinterpreted into a guessed shape." Read together with the ticket's
Assumptions/Open Questions section (which explicitly defers the tolerant-parser-vs-stricter-format
choice, including this exact trade-off, to Plan) and the direct precedent of
`TCK-20260819-HOTFIX-WORKING-LOG-LEGACY-SCHEMA-ROWS` (which performed the identical status-anchor
rejoin and explicitly treated it as "no information loss," not forbidden reinterpretation), this
plan reads the constraint as: (a) the on-disk file is never rewritten (satisfied — everything is
in-memory), and (b) no row is ever silently reclassified as indistinguishable-from-clean (satisfied
— all 11 keep `classification="field_count_mismatch"`, a visibly distinct, always-flagged tag, even
the 9 that also get a `record`). The `strict=True`-verified deterministic rejoin is a mechanical,
lossless reversal of an unintended delimiter split (verified per-row, not guessed), not the kind of
fabrication ("guessed shape") the constraint is aimed at — consistent with investigation's own
recommendation to reuse this exact technique. This resolution is recorded here rather than left
implicit, per this project's fact-verification discipline.

The identical reasoning extends to Finding 3's 17 rows: all 17 keep `classification=
"quote_desync_masquerading_as_clean"`, a visibly distinct, always-flagged tag, never silently
reclassified as `"clean"`, even though 17/17 also get a `record`. The fixed-vocabulary rejoin is
mechanical and evidence-confirmed against real, independently-occurring, correctly-quoted instances
of the identical fragments elsewhere in the file (investigation.md Finding 3's "Recovery" section),
not a guess — the same "no information loss, no fabrication" standard as Finding 1's rejoin. A
6-field row with unbalanced parens that matches none of the 3 known fragments correctly stays
`recoverable=False`, `record=None` — never guessed.

## Anti-Drift Notes

- **Do not substitute a hand-rolled quote-counting/parity heuristic for `csv.reader(...,
  strict=True)`** as the irreducible-ambiguity detector. During planning, both "any `"` present in
  overflow fields" and "raw-line total quote-char parity (odd/even)" were tried and computationally
  verified to misclassify at least one of the 11 real rows (the first wrongly flags row 3245, the
  second fails to distinguish 1511/3104 from the 9 recoverable rows at all — both raw-line quote
  counts came back even). Only `strict=True` was verified to classify all 11 correctly.
- **Anchor search must start at index 2, not a fixed index 3** — title can absorb extra fields when
  it contains an unescaped comma (confirmed for 4 of the 11 real rows: 3245, 3284, 3287, 3307),
  shifting the true status-column index rightward. A fixed-index assumption would misfire on these.
- **Do not assume `artifacts_path = remaining[-1]` alone is always correct** — 2 of the 11 real rows
  (1581/3174) have their unescaped comma inside `artifacts_path` itself, not `title`/`summary`, so
  the trailing field alone is a truncated fragment (` scope-only)`), not the complete value. The
  paren-balance check (`count("(") == count(")")`, tried at `remaining[-1]` then, if that fails,
  `",".join(remaining[-2:])`) is the load-bearing distinguishing signal for how many trailing raw
  fields belong to `artifacts_path` — verified against all 11 rows (the 7 non-artifacts_path-defect
  recoverable rows all trivially pass at `n=1` since their trailing field has zero parens; 1581/3174
  only pass at `n=2`) and cross-checked against every genuinely-complete artifacts_path value
  elsewhere in the file's clean rows (all balanced, zero false positives). If neither `n=1` nor `n=2`
  passes, degrade to `recoverable=False` rather than guessing a 3-way split — not observed in the
  current 11 rows, but the required safe-degradation path for any future row shape.
- **Finding 2's ~1586-row mega-block is real and large, but this ticket does not remediate it** —
  the generic duplicate-detection mechanism will surface it as a byproduct, which is acceptable
  (detection, not fixing), but no test may hardcode an exact count against it; only the small named
  3245/3253 pair gets an exact-count assertion.
- **`_extract_working_log_rows`'s multi-column-name-variant tolerance is intentional, historical,
  and out of scope to remove** — Step 5's fix is additive (one new guard condition), never a
  replacement of that tolerance.
- **`csv.DictReader`'s `restkey`/`restval` leniency is not real tolerance** — it silently drops extra
  fields into an unread `None` key and fills missing fields with `None`, which is exactly the
  "silently mis-mapping columns" failure mode this ticket exists to close (investigation.md's own
  explicit warning). The new parser must never rely on `DictReader` for anything touching the
  6-column current schema; `DictReader` remains fine only for `knowledge_search.py`'s intentionally
  looser variant-tolerant extraction, which Step 5 does not change.
- **`docs/parity_ledger/*.yaml`, `docs/mechanics/`, `docs/engine/`** — none apply; this is
  process/tooling work with zero mechanics-bible or engine-contract surface, confirmed by two
  independent investigations (this one and `TCK-20260705-WORKING-LOG-BACKFILL`).
- **Never treat `len(raw_fields) == 6` alone as sufficient evidence of `clean` (Finding 3).** A row
  can pass field-count==6 and still carry silently-wrong `summary`/`artifacts_path` values — this was
  the entire, previously-invisible failure mode Finding 3 discovered (34 real lines / 17 distinct
  events). Every 6-field, non-header row must also pass the `artifacts_path` paren-balance gate
  (`count("(") == count(")")`) before being classified `clean`. This is a second, independent
  validity gate layered on top of the pre-existing field-count check, not a replacement for it — both
  must pass.
- **`QUOTE_DESYNC_SUMMARY_FRAGMENTS` is a closed, evidence-only vocabulary of exactly 3 strings**
  (`N/A (hotfix`, `none (hotfix`, `none (scope-only epic`) — confirmed against a full-file sweep
  (investigation.md Finding 3: two independent detection signals both converge on the identical 34
  lines, zero drift). **Do not invent a 4th fragment or generalize the match into a regex/prefix
  family** — a 6-field row with unbalanced `artifacts_path` parens that matches none of these 3 exact
  strings must degrade to `recoverable=False`, `record=None`, never a guessed reconstruction. This
  mirrors the same safe-degradation discipline already established for Finding 1's rejoin heuristic
  (rows 1511/3104) and for Finding 1's paren-balance trailing-field check (no plausible `n` found).

## Deviations (recorded during Implement, 2026-09-06)

No implementation deviated from any Step's specified code path — all 6 Steps were implemented exactly
as written above, and every empirical claim in this plan (strict=True classification of all 11 rows,
status-anchor indices, the n=1/n=2 reconstruction for 1581/3174, the exact 34-line Finding-3 set and
its 3-fragment reconstruction) was independently re-derived from the real committed file before coding
and matched exactly, with zero discrepancies requiring escalation.

One place where this plan's own **justification prose** (not its specified code) proved slightly
imprecise, discovered by diffing `validate_working_log.py`'s real-file output before vs. after the
Step 4 refactor: the Step 4 Change text states that rows excluded from the parser's `record` set
"contribute no record, same as they would have contributed garbled/wrong data under the old
`DictReader` restkey behavior" — implying old-vs-new behavior parity for the three pre-existing checks.
For rows 1511/3104 specifically this is not quite true: under the old bare `DictReader`, `ticket_id`
(raw field index 1) was positionally unaffected by the corruption further right in the row, so it was
*accidentally* extracted correctly for both rows despite the row being otherwise garbled — meaning
`TCK-20260817-RUNTIMEMODE-BENCH-SCOPING` silently counted as "logged" under the old duplicate-ID and
missing-log-entry checks. Under the new parser, correctly honoring AC2 (never fabricate a record for
an irreducibly-ambiguous row) excludes both rows entirely, so this ticket_id no longer appears in
either check's input at all. Net effect on the real file: the "Duplicate ticket IDs" error list loses
this one entry, and the "missing working_log entry" list gains it (163→164); the script's overall exit
code is unchanged (1, in both the old and new versions, due to many other genuine pre-existing data
issues in the file). This is judged a correct, evidenced consequence of the ticket's own AC2 — not a
defect and not something to route around — but is recorded here because the plan's justification
implied a stronger old-vs-new equivalence than the real file actually exhibits for this specific pair.
See `tickets/inprogress/TCK-20260904-WORKING-LOG-CSV-PARSER.md`'s Implementation Notes for the full
verification detail (diffed old-vs-new script output line-by-line against the real file).
