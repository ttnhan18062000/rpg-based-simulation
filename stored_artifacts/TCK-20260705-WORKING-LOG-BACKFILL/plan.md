---
status: historical
layer: observability
authority: P2
audience: agent
ticket_id: TCK-20260705-WORKING-LOG-BACKFILL
artifact_type: plan
tags: [agent-monitoring, data-quality, working-log, csv-parsing]
---

# Implementation Plan — TCK-20260705-WORKING-LOG-BACKFILL

## Summary

Investigation's central finding (62/62 "exclude, already logged") is independently re-confirmed here by
direct spot-check: `working_log.csv` has 861 wellformed 6-column rows, and the remaining **83** malformed
rows span **7 distinct column counts** (0×2, 4×6, 5×37, 7×5, 8×27, 9×5, 10×1 — confirmed via Python's
`csv.reader`, which correctly respects quoted fields; an initial pass used a naive `awk -F','` field count
and produced an inflated, incorrect "189 rows / 11+ shapes" figure by miscounting commas *inside* quoted
summary text as field separators — corrected here). Three malformed rows read directly (lines 539, 774, and
the `TCK-20260701-HAZARD-NATIVE-IMMUNITY` triplet) each have a *different* field order/count from one
another, and the shifted-column rows carry no recoverable `title` in the expected position — recovering one
requires a fresh lookup into `tickets/done/*.md` per row, not a mechanical column reorder. This confirms
investigation's claim and rules out a "safe mechanical subset can be fixed now" middle path: there is no
subset where a regex or fixed reorder is sufficient, because (a) the malformation isn't a consistent
transposition across all 83 and (b) the shifted-column cases are missing a whole field that must be sourced
externally per row.

**Decision: Option B — zero `working_log.csv` content writes to the 62 flagged tickets.** Correct the
ticket's own text to state the disproven premise and real finding, append this ticket's *own* completion row
(standard one-row-per-finished-ticket step, not a "backfill" of the 62), and recommend — but do not create —
two separately-scoped follow-up tickets: (a) a `validate.py` parser fix, (b) a `working_log.csv`
malformed-row normalization pass (own Investigate phase required first, given 83 rows across 7 shapes —
see Step 6 for the full breakdown).

## Steps

### Step 1 — Pre-flight re-verification (read-only)
- **Files:** none.
- **Do:** Re-run `python3 tools/agent-monitoring/validate.py 2>&1 | grep -c "no working_log entry"`; confirm
  count matches investigation's 62 (or note+justify a small delta if concurrent work landed). Run
  `git diff --stat agent-monitoring/runs.jsonl agent-monitoring/events.jsonl` to confirm empty baseline
  before any edits.
- **Do NOT touch:** any file.
- **Verify:** command output recorded in ticket's Test Summary; matches investigation snapshot or delta is
  explained.

### Step 2 — Correct the ticket's own text
- **Files:** `tickets/inprogress/TCK-20260705-WORKING-LOG-BACKFILL.md`.
- **Do:**
  - Rewrite `Request Summary`/`Scope` framing to state plainly: the "62 missing rows" premise is disproven;
    all 62 already have a row, either under legacy malformed column order (39) or under a
    suffixed/hashed/renamed `run_id` whose base `ticket_id` is already logged correctly (23).
  - Amend AC2's disposition: record that 62/62 warnings persist post-ticket as an explicitly **documented,
    justified residual** (per AC2's own "or a documented, justified residual" clause), backed by
    `investigation.md`'s 62-row disposition table — not a gap.
  - Fill `Implementation Notes` referencing `investigation.md`'s table and this plan's Step 1 re-verification
    output.
  - Fill `Test Summary` with the Step 1/Step 7 command outputs.
  - Fill `Files Changed`: this ticket file, `stored_artifacts/TCK-20260705-WORKING-LOG-BACKFILL/*`,
    `tickets/working_log.csv` (one appended row only — this ticket's own completion, see Step 3).
  - Fill `Completion Summary`: zero backfill performed on the 62; root cause is CSV-parsing and run_id-join
    gaps, not missing data; two follow-ups recommended (Step 6).
- **Do NOT touch:** `tickets/working_log.csv` content for the 62 rows, `agent-monitoring/runs.jsonl`,
  `agent-monitoring/events.jsonl`, `tools/agent-monitoring/validate.py`.
- **Verify:** manual diff read of the ticket file; confirm no residual "backfill" language implying rows were
  or should be added for the 62.

### Step 3 — Append this ticket's own completion row (standard finalize step, not a "backfill")
- **Files:** `tickets/working_log.csv`.
- **Do:** Append exactly one line at EOF in the canonical 6-column shape:
  `<ISO8601 timestamp>,TCK-20260705-WORKING-LOG-BACKFILL,<title from ## Title>,DONE,<summary>,stored_artifacts/TCK-20260705-WORKING-LOG-BACKFILL/`.
  Use this exact `<summary>` text (not a generic completion blurb), so the row is unambiguous even if read in
  isolation from the ticket file: "Investigated 62 validate.py-flagged tickets; all 62 already logged (39
  malformed-row, 23 run_id-join gap); zero rows backfilled; two follow-ups recommended (validate.py parser
  fix, working_log.csv normalization pass)." This is the routine per-ticket ledger row every completed
  ticket gets (per CLAUDE.md's "Append to the bottom of `tickets/working_log.csv`"), distinct in kind from
  the 62-ticket backfill this ticket's Scope originally called for and investigation disproved.
- **Do NOT touch:** any pre-existing line.
- **Verify:** `git diff --stat tickets/working_log.csv` shows exactly `1 insertion(+), 0 deletions(-)`;
  `tail -1 tickets/working_log.csv | awk -F',' '{print NF}'` reports `6`.

### Step 4 — Move ticket to done + migrate staging artifacts
- **Files:** `tickets/done/TCK-20260705-WORKING-LOG-BACKFILL.md` (moved from `inprogress/`);
  `stored_artifacts/TCK-20260705-WORKING-LOG-BACKFILL/{plan.md,investigation.md,test_plan.md}` (moved from
  `staging_artifacts/`).
- **Do:** standard finalize move; set ticket frontmatter `status: active` remains as-is per repo convention
  (done tickets keep original frontmatter `status` field value — confirm by checking one existing
  `tickets/done/*.md` file's frontmatter before assuming otherwise).
- **Do NOT touch:** any other ticket's `tickets/done/` file.
- **Verify:** `ls tickets/inprogress/` no longer lists the file; `ls tickets/done/` lists it;
  `staging_artifacts/TCK-20260705-WORKING-LOG-BACKFILL/` is empty/removed.

### Step 5 — Cleanup pass (Definition of Done housekeeping)
- **Files:** `data/runs/*`, `reports/release_proof/*` if present.
- **Do:** `rm -rf data/runs/* reports/release_proof/*` (expected no-op — this ticket generates no simulation
  run data).
- **Do NOT touch:** anything else.
- **Verify:** `git status` shows no stray untracked run artifacts.

### Step 6 — Record (not create) the two follow-up recommendations
- **Files:** none beyond Step 2's ticket edit (`Related Tickets` / `Completion Summary` sections).
- **Do:** Name both recommended follow-ups explicitly enough to scope later, but do not create their ticket
  files under this ticket's own scope (that would be scope creep beyond this chore):
  - (a) `validate.py` cross-check fix: consult a run record's own `ticket_id` field before falling back to
    `run_id`; parse legacy column shapes (or treat any row containing the target ticket_id in any column as
    a hit) instead of blind `csv.DictReader` positional mapping.
  - (b) `working_log.csv` malformed-row normalization: requires its own Investigate phase to enumerate and
    categorize **all 83** non-6-column rows first (counts by shape, per this plan's own `csv.reader`-based
    count: 0×2, 4×6, 5×37, 7×5, 8×27, 9×5, 10×1) — this ticket's own 39-row subset is not representative of
    the full malformed population, so no partial fix should be attempted piecemeal from this ticket.
- **Do NOT:** create new ticket files, do NOT attempt any row rewrite as part of this ticket.
- **Verify:** `Related Tickets`/`Completion Summary` sections name both follow-ups with the counts above.

### Step 7 — Final verification pass
- **Files:** none (read-only).
- **Do:** Re-run the 4 Scoped Pytest/CLI commands from `test_plan.md`:
  1. `python3 tools/agent-monitoring/validate.py 2>&1 | grep -c "no working_log entry"` → expect 62
     (this ticket's own new row does not remove any of the 62 pre-existing warnings, since none of the 62
     flagged ids is this ticket's own id — expected, not a regression).
  2. `git diff --stat agent-monitoring/runs.jsonl agent-monitoring/events.jsonl` → expect empty for the
     62-backfill-specific content (the standard workflow's own automatic run/event append for *this* ticket's
     execution, per CLAUDE.md's "every workflow run must record a run entry," is a separate, tooling-driven
     mechanism outside this plan's manual step list — it is not a violation of AC4's intent, which targets
     prevention of retroactively fabricating/rewriting historical entries for the 62 old tickets, not this
     session's own new record).
  3. `git diff --stat tickets/working_log.csv` → expect exactly the Step 3 addition, zero deletions.
  4. Spot-check 3 disposition-table rows unchanged: `git show HEAD:tickets/working_log.csv | grep -n "TCK-20260610-ARCHETYPE-DEFAULT-PATH,"` etc.
- **Verify:** all four match expectations above; discrepancies block finalize until explained.

## Scope Guards

- No content edit/rewrite of any pre-existing `tickets/working_log.csv` line — append-only, and only one
  append (this ticket's own row).
- No `tools/agent-monitoring/validate.py` code change.
- No `agent-monitoring/runs.jsonl` / `events.jsonl` manual edit or backfill for the 62 historical tickets.
- No new follow-up ticket files created under this ticket's implementation — recommendation only.
- No bulk-append of rows for the 62 flagged ids under any circumstance — investigation and this plan's
  independent spot-check both confirm zero of the 62 warrant a new row.

## Dependency Map

- Step 2 depends on Step 1's fresh count (do not restate a stale number).
- Step 3 is independent of Steps 1/2's findings — it is the routine per-ticket ledger append every ticket
  gets, and must use the canonical 6-column shape confirmed in `investigation.md`.
- Step 4 depends on Steps 2 and 3 being complete (ticket text finalized, ledger row appended) before the
  move to `tickets/done/`.
- Step 7 depends on all prior steps; it is the final gate before commit.
- Steps 6's follow-up recommendations have no code dependency on this ticket's own completion — they can be
  spun off independently at any time, by any future session.

## Acceptance Criteria Map

| AC | Original wording | Disposition | Verified by |
|---|---|---|---|
| AC1 | Every flagged run_id given a row or explicitly excluded with documented reason | Satisfied — 0 given a row, 62 excluded, each with a specific reason in `investigation.md`'s table | Manual review of the 62-row table (Step 2 references it) |
| AC2 | Re-running `validate.py` shows zero, or documented justified residual, warnings | Satisfied via residual clause — 62/62 documented as justified (not a real gap), ticket text amended (Step 2) to state this explicitly | Step 1 + Step 7 command #1 output = 62, cross-checked against table |
| AC3 | Every added row individually verified, no blind bulk-append | Trivially satisfied — zero rows added for the 62; the one row added (Step 3) is this ticket's own, individually authored, not bulk | Step 3's git diff shows exactly 1 insertion |
| AC4 | `runs.jsonl`/`events.jsonl` show zero diff for the 62-backfill content | Satisfied — no manual edit to either file for backfill purposes; any new line from the standard workflow's own monitoring append is a separate, expected mechanism (see Step 7 note) | Step 1 (baseline) + Step 7 command #2 |

## Anti-Drift Notes

- Do not let "zero backfill" read as "nothing to do" — the ticket's own text must be corrected (Step 2) so a
  future reader doesn't re-open this as a live gap; the 62 must be legible as *resolved-by-explanation*, not
  *forgotten*.
- Do not conflate Step 3 (this ticket's own routine ledger row) with the 62-ticket backfill the ticket was
  originally scoped for — they are different in kind and must not be described interchangeably in the
  Completion Summary.
- Do not attempt even a "safe subset" mechanical fix of the 39/83 malformed rows under this ticket — the
  independent spot-check in this plan's Summary confirms there is no uniform safe subset; every malformed row
  is missing a `title` field that requires an external lookup, which is an edit/rewrite operation, not an
  append, and is explicitly out of this ticket's scope.
- If Step 1's re-run count differs materially from 62 (i.e., not explainable by a small number of tickets
  completed in the interim), stop and re-investigate before proceeding — do not silently adjust the plan's
  numbers.
