---
status: historical
layer: observability
authority: P1
audience: agent
ticket_id: TCK-20260705-WORKING-LOG-BACKFILL
phase: done
date: 2026-07-05
tags: [agent-monitoring, data-quality]
---

# TCK-20260705-WORKING-LOG-BACKFILL

## Title
Backfill tickets/working_log.csv rows for legitimately-DONE tickets validate.py can now see

## Status
DONE

## Tier
standard

## Type
chore

## Priority
P2

## Request Summary
`TCK-20260705-MONITORING-VALIDATE-SCHEMA-GAP` fixed `validate.py`'s working-log cross-check to also read the legacy `status` field (not just `final_status`), which correctly surfaced additional tickets that are genuinely `DONE` but appear to have no matching row in `tickets/working_log.csv`. That ticket explicitly deferred the backfill question: "whether to backfill those specific `working_log.csv` rows is a separate, small follow-up decision, not part of fixing the validator itself."

**Disproven premise, corrected finding**: this ticket was filed on the premise that 62 `TCK-*` tickets are genuinely missing a `working_log.csv` row and need one appended. Investigation (`staging_artifacts/TCK-20260705-WORKING-LOG-BACKFILL/investigation.md`) and an independently re-confirming plan pass (`plan.md`) both establish that **all 62 flagged run_ids already have a row in `tickets/working_log.csv` today** — the premise is disproven. They are invisible to `validate.py`'s check for two reasons, neither of which is a missing row:
- **Reason A (39 of 62)**: a legacy block of rows places `ticket_id` in column 1 instead of column 2; `csv.DictReader`'s positional mapping reads column 2 as `ticket_id` for these rows, so the real id is silently missed even though the row exists and its content matches the ticket's `tickets/done/` file verbatim.
- **Reason B (23 of 62)**: the flagged `run_id` carries a hash/timestamp/`-run-N` suffix not present in the real ticket id; the run record's own `ticket_id` field (which `validate.py` never reads) or a base-id strip resolves to a ticket whose base id already has a wellformed row.

Zero of the 62 warrant a new `working_log.csv` row. Re-verified at implementation time (2026-07-05): `python3 tools/agent-monitoring/validate.py 2>&1 | grep -c "no working_log entry"` still reports exactly **62**, matching the investigation snapshot with no drift.

## Scope
- Re-verify (read-only) that `validate.py`'s 62-count still holds at implementation time — confirmed, no drift.
- Correct this ticket's own framing to state the disproven premise and the real finding, per `investigation.md`'s per-row disposition table (0 include / 62 exclude-with-reason).
- Append this ticket's own single completion row to `tickets/working_log.csv` (the routine per-ticket ledger entry every finished ticket gets) — **not** a backfill of the 62.
- Record (name only, do not create) two follow-up ticket recommendations: (a) a `validate.py` cross-check parser fix, (b) a `working_log.csv` malformed-row normalization pass.
- **Explicitly this is not a `runs.jsonl`/`events.jsonl` backfill** — those remain append-only and untouched; confirmed zero diff before and after this ticket's own work.

## Out of Scope
- Any change to `validate.py` itself — already fixed by the sibling ticket; this ticket only acts on what it now correctly surfaces.
- Any `runs.jsonl`/`events.jsonl` edits — strictly out of bounds, append-only.
- Tickets flagged as missing a `working_log.csv` entry that turn out, on inspection, to NOT actually be complete (should not exist given the schema-gap ticket's fix, but if found, flag and exclude rather than force a row).
- Re-running `make agent-monitoring-retro` to regenerate reports after the backfill — the reports' own DONE/gate-fail counts are computed from `runs.jsonl`, not `working_log.csv`, so this backfill doesn't change any retro numbers; no regeneration needed.

## Acceptance Criteria
- [x] Every `TCK-*` run_id `validate.py` currently flags as "DONE has no working_log entry" is either given a row in `tickets/working_log.csv`, or explicitly excluded with a documented reason (e.g. ticket file not found, status ambiguous). — Satisfied: 0 given a row, all 62 excluded, each with a specific reason (Reason A malformed-row or Reason B run_id-join gap) in `investigation.md`'s definitive table.
- [x] Re-running `python3 tools/agent-monitoring/validate.py` after the backfill shows zero (or a documented, justified residual) "no working_log entry" warnings. — **AC2 disposition (amended): satisfied via the residual clause.** All 62 warnings persist unchanged post-ticket by design — there is nothing to backfill, since every flagged id already has a row. This is a documented, justified residual (root cause: `validate.py`'s CSV parsing does not handle the legacy column-1-ticket_id shape and does not consult a run record's own `ticket_id` field), not a real data gap. Re-verified at implementation time: count is 62, unchanged.
- [x] Every added row is individually verified against `tickets/done/` (or an explicit terminal-status field) before being added — no blind bulk-append. — Trivially satisfied: zero rows added for the 62; the sole row added is this ticket's own routine completion entry, individually authored.
- [x] `runs.jsonl`/`events.jsonl` show zero diff (`git diff --stat agent-monitoring/runs.jsonl agent-monitoring/events.jsonl` empty) — confirms the append-only invariant was respected. — Confirmed empty both before (Step 1 baseline) and after this ticket's own manual edits (any subsequent workflow-tooling-driven append for this ticket's own run/event record is a separate, expected mechanism, not a manual edit).

## Related Tickets
- TCK-20260705-MONITORING-VALIDATE-SCHEMA-GAP (fixed the validator that surfaces this gap; explicitly deferred the backfill decision to this ticket)
- Recommended follow-up (not created, named only): `validate.py` cross-check parser fix — parse legacy column shapes and consult a run record's own `ticket_id` field instead of blind `csv.DictReader` positional mapping keyed on `run_id`.
- Recommended follow-up (not created, named only): `working_log.csv` malformed-row normalization pass — own Investigate phase first, covering all 83 non-canonical rows across 7 column-count shapes (0×2, 4×6, 5×37, 7×5, 8×27, 9×5, 10×1).

## Related Docs
- docs/guides/agent_monitoring.md
- tickets/working_log.csv (the artifact being completed)

## Related Stored Artifacts
None yet — staging artifacts to be created under `staging_artifacts/TCK-20260705-WORKING-LOG-BACKFILL/` when implementation begins (standard tier, given the volume — 62 tickets to individually verify — warrants a real investigation/plan pass, not a hotfix-tier shortcut).

## Related Code Areas
- tickets/working_log.csv
- tickets/done/ (read-only — source of truth for verifying each backfilled row)
- agent-monitoring/runs.jsonl (read-only — do not modify)

## Assumptions / Open Questions
- Whether all 62 currently-flagged tickets are genuinely complete, or whether a small number might reveal a real, previously-undetected gap once individually checked, is exactly what this ticket's verification step exists to determine — not assumed here.
- Given the volume (62, not the originally-estimated 8-9), whether this is worth doing as one bulk pass or split into smaller batches is a Plan-phase call.

## Implementation Notes
- Step 1 (pre-flight re-verification, read-only): re-ran `python3 tools/agent-monitoring/validate.py 2>&1 | grep -c "no working_log entry"` — result `62`, exact match to `investigation.md`'s snapshot, no drift. `git diff --stat agent-monitoring/runs.jsonl agent-monitoring/events.jsonl` was empty before any edits.
- Step 2: corrected this ticket's own `Request Summary`/`Scope` to state the disproven premise (62 tickets are NOT missing rows — all 62 already have one, per `investigation.md`'s per-row disposition table: 39 Reason A malformed-column-order rows, 23 Reason B run_id≠ticket_id join gaps) and amended all four Acceptance Criteria with their actual disposition, per `plan.md`'s decision (Option B — zero content writes to the 62).
- No code, `validate.py`, or historical `working_log.csv` line was touched. Full per-row rationale lives in `staging_artifacts/TCK-20260705-WORKING-LOG-BACKFILL/investigation.md`'s Definitive Table; the independent spot-check confirming no mechanical fix is safe lives in `plan.md`'s Summary.
- Two follow-ups are recorded here (not created as tickets, per plan Step 6 and this ticket's Out of Scope):
  1. **`validate.py` cross-check parser fix** — consult a run record's own `ticket_id` field before falling back to `run_id`; parse legacy column shapes (or match the target ticket_id in any column) instead of blind `csv.DictReader` positional mapping.
  2. **`working_log.csv` malformed-row normalization pass** — requires its own Investigate phase first to enumerate/categorize all 83 non-6-column rows (confirmed via `csv.reader`: 0×2, 4×6, 5×37, 7×5, 8×27, 9×5, 10×1 column-count shapes) — this ticket's 39-row subset is not representative of the full malformed population, so no partial fix was attempted here.

## Test Summary
- `python3 tools/agent-monitoring/validate.py 2>&1 | grep -c "no working_log entry"` → `62` (pre-edit baseline, matches investigation; expected to remain `62` post-edit since none of the 62 flagged ids is this ticket's own id).
- `git diff --stat agent-monitoring/runs.jsonl agent-monitoring/events.jsonl` → empty, both pre- and post-edit (manual-edit invariant respected; any later workflow-tooling append for this ticket's own run/event record is a separate, expected mechanism outside this manual step list).
- Test/Parity/Verify gates for this ticket run separately, after this implementation pass, per the standard pipeline — not executed here.

## Files Changed
- `tickets/inprogress/TCK-20260705-WORKING-LOG-BACKFILL.md` (this file — Request Summary/Scope/Acceptance Criteria/Implementation Notes/Test Summary/Files Changed/Completion Summary sections).
- `tickets/working_log.csv` (one appended row — this ticket's own completion entry; zero pre-existing lines touched).

## Completion Summary
Investigation and an independently re-confirming plan pass both disproved this ticket's originating premise: none of the 62 `TCK-*` run_ids `validate.py` flags as "DONE has no working_log entry" is actually missing a row. All 62 already have one — 39 under a legacy malformed column order (`ticket_id` in column 1, invisible to `csv.DictReader`'s column-2 lookup) and 23 under a `run_id` that differs from the real `ticket_id` (hash/timestamp/`-run-N` suffixed), whose base ticket already has a wellformed row. Zero rows were backfilled; the ticket's four Acceptance Criteria are satisfied via the "documented, justified residual" clause rather than by adding data. Two follow-ups are recommended but not created as tickets: (a) fix `validate.py`'s cross-check to parse legacy column shapes and consult a run record's own `ticket_id` field, (b) a separately-scoped `working_log.csv` malformed-row normalization pass covering all 83 non-canonical rows (7 distinct column-count shapes), requiring its own Investigate phase first.
