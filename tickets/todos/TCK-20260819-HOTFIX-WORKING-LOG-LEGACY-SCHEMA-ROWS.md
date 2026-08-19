---
status: active
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20260819-HOTFIX-WORKING-LOG-LEGACY-SCHEMA-ROWS
phase: open
date: 2026-08-19
tags: [ai, documentation]
---

# TCK-20260819-HOTFIX-WORKING-LOG-LEGACY-SCHEMA-ROWS

## Title
tickets/working_log.csv has ≥2 legacy-schema row blocks that break validate_working_log.py's duplicate-ID and empty-field checks

## Status
OPEN

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
- [ ] `tools/validate_working_log.py`'s "duplicate ticket IDs" output contains only real,
      ticket-shaped IDs — no date fragments, status words, or bare UUIDs.
- [ ] Both identified legacy-schema blocks are reformatted to the current schema with no
      information loss.
- [ ] A full-file schema-shape sweep confirms no other legacy-schema blocks remain undetected (or,
      if more are found, they're reformatted too).
- [ ] The "265 missing working_log entries" figure has been sample-verified with a documented
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
(pending)

## Test Summary
(pending)

## Files Changed
(pending)

## Completion Summary
(pending)
