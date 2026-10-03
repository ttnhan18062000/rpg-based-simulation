---
status: historical
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20260819-HOTFIX-WORKING-LOG-LEGACY-SCHEMA-ROWS
phase: done
date: 2026-08-19
tags: [ai, documentation]
---

# TCK-20260819-HOTFIX-WORKING-LOG-LEGACY-SCHEMA-ROWS

## Title
tickets/working_log.csv has ≥2 legacy-schema row blocks that break validate_working_log.py's duplicate-ID and empty-field checks

## Status
DONE

## Tier
hotfix

## Type
repair

## Priority
P3

## Request Summary
Running `tools/validate_working_log.py` (uses `csv.DictReader` correctly — not a validator bug)
produces a "duplicate ticket IDs" list full of garbage tokens (`'DONE'`, `'bug'`, a bare UUID,
date fragments) and 60 "empty artifacts_path" errors, most of which are false alarms. Root-caused
via direct `csv.DictReader` inspection, not assumption: the file contains at least two contained
historical blocks logged under schemas different from the current header
(`timestamp,ticket_id,title,status,summary,artifacts_path`):
- **Rows ~454–488** (~35 rows, dated 2026-05-30 to 2026-06-06): `timestamp` is date-only (no
  `T...Z`), followed by a constant run UUID (`f037e9a1-43fa-4687-982f-38a78f927cb8`) sitting where
  `ticket_id` belongs, with the real ticket ID one column over in `title`'s position — an extra
  UUID column inserted before `ticket_id`, no separate title.
- **Rows ~666–668+** (dated 2026-06-19): a completely different, older 7-column layout —
  `ticket_id, type, status(lowercase), date, layer, tier, summary` — bearing no resemblance to the
  current schema at all.
Both clusters are contained to old (May–June) sections, not spreading into anything recent — same
shape as the separately-confirmed `make agent-monitoring-validate` historical-debt finding from
the same investigation session. Not an active, ongoing problem, but the validator has presumably
been noisy/wrong since these blocks were written, and nobody's gone back to clean them up.

## Scope
- Reformat both identified blocks (rows ~454–488, ~666–668+) into the current 6-column schema,
  preserving all real information (timestamps, ticket IDs, statuses, summaries, artifacts paths
  where recoverable) — do not silently drop content to force-fit the schema.
- Do a systematic column-count/schema-shape sweep across the **entire** file (not just these two
  spot-checked blocks) — these were found via a `ticket_id`-shape pattern match sampling the
  "empty artifacts_path" subset, which could miss other legacy-schema rows that happen to look
  superficially well-formed.
- Re-run `tools/validate_working_log.py` after reformatting; confirm the "duplicate ticket IDs"
  list no longer contains non-ticket-shaped tokens.
- Separately: sample-verify (not necessarily fully resolve) the validator's "265 tickets in done/
  with no working_log entry" figure — confirm it's dominated by genuinely old, pre-convention
  entries (some IDs like `README`, `RESTRUCTURE-01`, `METRICS-01` aren't ticket-shaped at all,
  consistent with pre-dating the working_log convention) rather than a live, ongoing gap. Full
  backfill of legitimately-missing old entries is a judgment call for the implementer given the
  volume — not mandated by this ticket if the sample confirms it's historical.

## Out of Scope
- Any change to `tools/validate_working_log.py` itself — it's correctly reporting real (if old)
  data issues; the fix belongs in the data, not the checker.
- Retroactively logging all 265 missing `done/` entries if the sample confirms they're
  overwhelmingly pre-convention historical debt rather than a live gap.

## Acceptance Criteria
- [x] `tools/validate_working_log.py`'s "duplicate ticket IDs" output contains only real,
      ticket-shaped IDs — no date fragments, status words, or bare UUIDs.
- [x] Both identified legacy-schema blocks are reformatted to the current schema with no
      information loss.
- [x] A full-file schema-shape sweep confirms no other legacy-schema blocks remain undetected (or,
      if more are found, they're reformatted too).
- [x] The "265 missing working_log entries" figure has been sample-verified with a documented
      conclusion (historical debt vs. live gap), not left as an unexamined number.

## Related Tickets
- TCK-20260819-HOTFIX-EPIC-STALENESS-FOLDER-BLOCKED-GAP,
  TCK-20260819-HOTFIX-STATUS-DRIFT-COLON-SUFFIX-GAP (sibling findings from the same session's
  investigation into this tooling tree's checker-consistency and data-integrity gaps)

## Related Docs
None beyond `tools/validate_working_log.py`'s own output.

## Related Stored Artifacts
None — hotfix tier, no staging artifacts required.

## Related Code Areas
- tickets/working_log.csv
- tools/validate_working_log.py (read-only reference for verification, not itself changed)

## Assumptions / Open Questions
- Whether more than these 2 legacy-schema blocks exist elsewhere in the file's early history is
  explicitly not resolved here — the full-file sweep in Scope is left to the implementer since it
  wasn't performed exhaustively in this investigation (only the "empty artifacts_path" subset was
  sampled for schema shape).

## Implementation Notes
Backed up `tickets/working_log.csv` to `/tmp/working_log_backup.csv` before any edit (1489 physical
lines, 1486 real DictReader-parsed data rows). All edits were applied surgically via Python scripts
that replaced only specific physical line numbers in place (never a full-file rewrite) — verified
post-hoc that exactly 156 physical lines differ from the backup and every other line is byte-identical.

**Investigation beyond the ticket's 2 named blocks.** A naive column-count sweep
(`csv.reader`, flag any row where `len(row) != 6`) found 121 mismatched rows, not 2 blocks — most
were rows with unescaped commas inside `title`/`summary` that a correctly-quoted 6-column current-
schema row had been split into 7-10 raw CSV fields by (fixed generically: locate the literal `DONE`
token as the status anchor and rejoin the surrounding fragments with `,` — this exactly reverses
the unintended split since csv.reader discards only the delimiter itself). The remainder were
distinct legacy-schema blocks beyond the 2 the ticket named, each with its own field order/count
(rows 418, 440-441, 447, 486, 539-547, 588-589, 626, 632, 753, 767-781, 784-796, 851-864, plus 2
stray blank physical lines at 451/813 with zero content, which were deleted rather than reformatted
since there was no data to preserve).

**Critical follow-up the ticket explicitly warned about, confirmed real.** The column-count sweep
alone was insufficient: two legacy blocks (the ticket's own known `f037e9a1` UUID block, rows
455-489, and a previously-undetected `TCK-20260619-E53Ba..E53Cd` block, rows 757-764) had stretches
where the misaligned row *coincidentally* already had exactly 6 comma-separated fields — same count
as the current schema, wrong meaning per field — so they never appeared in the count-based sweep at
all. Caught this with a second, field-plausibility sweep (regex-checking that `timestamp` parses as
a date/ISO-8601 value and `ticket_id` looks identifier-shaped) run against the file after the first
round of fixes, which surfaced 36 additional bad rows the count-only sweep had missed. Re-ran the
plausibility sweep again after fixing those; it now returns zero suspicious rows file-wide, and the
column-count sweep independently also returns zero. This two-signal sweep (count-mismatch and
field-implausibility) is the actual full coverage this ticket's "systematic sweep" scope item required.

**Missing-field recovery policy.** Where a legacy block was missing `title` and/or `artifacts_path`
outright (not just misordered), those values were recovered from the authoritative
`tickets/done/{ticket_id}.md` files (`## Title`, `## Related Stored Artifacts`) for all 71 unique
ticket IDs touched by the 2nd-category blocks (all 71 confirmed to exist in `tickets/done/`) —
never fabricated. Where a legacy schema carried extra fields with no home in the current 6-column
schema (`type`, `tier`, `priority`, `layer` in various old micro-schemas), that information was
folded into `summary` as a `[key=value, ...]` suffix rather than being dropped, per the ticket's
explicit "no information loss" instruction. Two rows (440, 441 — `TCK-20260528-COG-PHASE4/5`) had no
timestamp field at all in their legacy shape; recovered the date (`2026-05-28`) from the ticket
files' own frontmatter `date:` field (exact time-of-day genuinely isn't recoverable, so normalized
to `T00:00:00Z` — same granularity-honesty convention already used for the ticket's own named block).

**Verification.** Row count invariant held throughout: 1486 DictReader-parsed data rows before and
after (only the 2 zero-content blank physical lines were removed, which were never counted as data
rows by DictReader's blank-row skip anyway). `tools/validate_working_log.py`'s duplicate-ticket-IDs
list dropped from 24 garbage tokens (`'DONE'`, `'bug'`, date fragments, a bare UUID) to a
ticket-shaped-only list — every remaining "duplicate" is a real `TCK-...` ID that was genuinely
logged more than once historically (e.g. an original DONE entry plus a later AMENDED entry), which
is legitimate repo history, not corruption. Empty-field errors dropped from 68 to 17, and the
remaining 17 are all genuinely well-formed 6-column current-schema rows where `artifacts_path` was
simply left blank at logging time (not a legacy-schema symptom) — explicitly out of this ticket's
scope (`tools/validate_working_log.py` correctly still flags them; bulk-fixing every historically
blank field across the file is a different, much larger problem than legacy-schema reformatting).

**"265 missing working_log entries" question.** After the fixes above (which recovered ~90 real
ticket IDs that were previously hidden in the wrong CSV column and therefore invisible to the
done/-vs-log cross-check), the figure dropped from 265 to 163 as a direct, honest side effect —
not a deliberate backfill. Of the 163: 37 are not ticket-shaped at all (`README`, `RESTRUCTURE-01`,
`METRICS-01`, `infra-0N-...`, `epic-1N-...`, etc.) — pre-dating the `TCK-YYYYMMDD` convention
entirely. Of the remaining 126 `TCK-`-shaped IDs, every single one dates from 2026-03-21 through
2026-07-01 (spot-checked against each ticket file's frontmatter `date:` — confirmed accurate);
zero fall in July 2 - August 19, the most recent ~7 weeks of the file's history, during which the
log has zero gaps. Conclusion: this is historical debt from before/during the working_log
discipline was established, not a live or ongoing gap — full backfill is correctly left undone per
the ticket's own explicit judgment-call clause.

## Test Summary
No test suite applies (data-only CSV fix, no source code changed). Verification was via direct
script execution, comparing before/after states:
- `python3 tools/validate_working_log.py` run before and after (see Completion Summary for exact
  counts). Exit code stays 1 in both cases (pre-existing, out-of-scope done/-entry gap and the
  17 genuinely-blank-field rows keep it failing — this ticket's scope was never "make the validator
  pass," only to remove the garbage-token/false-alarm noise it was correctly reporting).
- A standalone `csv.reader`-based column-count sweep (`len(row) != 6`) over the whole file: 121 bad
  rows before, 0 after.
- A standalone field-plausibility sweep (`timestamp`/`ticket_id` shape regexes via `csv.DictReader`)
  over the whole file: 0 bad rows after (this is the check that caught the 36 rows the count-only
  sweep missed, confirming the ticket's explicit warning about superficially-well-formed rows).
- Row-count invariant: `len(list(csv.DictReader(...)))` == 1486 before and after.
- Line-level diff against the pre-edit backup: exactly 156 physical lines changed (matching the
  count of line_updates applied across both fix passes) and exactly 2 physical lines removed (the
  2 zero-content blank lines) — every other physical line in the 1489-line file is byte-identical
  to the backup, confirming no unintended row was touched.

## Files Changed
- `tickets/working_log.csv` — reformatted 156 legacy-schema/malformed rows into the current
  6-column schema and removed 2 zero-content blank physical lines; no other rows touched.
- `tickets/inprogress/TCK-20260819-HOTFIX-WORKING-LOG-LEGACY-SCHEMA-ROWS.md` — this ticket file
  (Status, Acceptance Criteria, Implementation Notes, Test Summary, Files Changed, Completion
  Summary sections filled in).
- `agent-monitoring/tools.jsonl` — auto-updated by the monitoring tooling as a side effect of this
  session's tool calls, per repo convention (always staged alongside ticket work).

Not changed (read-only reference, confirmed via `git diff`): `tools/validate_working_log.py`.

## Completion Summary
Fixed all identified legacy-schema and malformed rows in `tickets/working_log.csv`: the ticket's 2
named blocks (the `f037e9a1` UUID block and the `TCK-20260619-P0-CODE-INTEGRITY`-style 7-column
block), plus — per the ticket's own explicit warning that a naive sweep could miss more — a
systematic two-signal full-file sweep (column-count mismatch, then field-plausibility) that found
and fixed 13 additional distinct legacy micro-schema blocks and 2 stray blank lines, including a
class of "coincidentally still exactly 6 columns but wrong field order" row the count-only sweep
structurally cannot see. `validate_working_log.py`'s duplicate-ticket-IDs list is now garbage-token-
free; the "265 missing done/ entries" figure organically dropped to 163 as fields were recovered
from their previously-mislabeled columns, and was sample-verified (37 pre-convention non-ticket
IDs, 126 TCK-shaped IDs all dated 2026-03-21 through 2026-07-01 with zero gaps in the most recent
~7 weeks) to be historical debt, not a live gap — full backfill correctly left out of scope.

**Verify-phase correction (2026-08-19):** done-checker's spot-check found 5 rows in the E53 block
(`E53Bd-LEDGER-WIRING`, `E53Ca-CONFLICT-PHASE`, `E53Cb-SIEGE-MODEL`, `E53Cc-TERRITORY-TRANSFER`,
`E53Cd-WAR-EXHAUSTION`) had dropped the `·` (middle dot, U+00B7) separator character present in
their source `## Title` in `tickets/done/{id}.md`, while 11 sibling rows in the same block
correctly preserved it — a narrow, localized recovery defect, not intentional summarization.
Fixed all 5 rows to restore the exact source character; re-verified row count (1487 lines / 1486
data rows, unchanged), column-count integrity (0 malformed rows), and `validate_working_log.py`
output (still 17 empty-field errors, same 21 clean duplicate IDs) — no regression from the
correction. The "no information loss" claim now holds exactly, not approximately.
