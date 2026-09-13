---
status: active
layer: ticket
authority: P1
audience: agent
ticket_id: TCK-20260913-DONE-CHECKER-WORKING-LOG-ROW-COUNT-REJECTS-LEGITIMATE-REOPEN
phase: open
date: 2026-09-13
tags: [data-quality]
---

# TCK-20260913-DONE-CHECKER-WORKING-LOG-ROW-COUNT-REJECTS-LEGITIMATE-REOPEN

## Title
`done_checker_static.check_working_log_exactly_one_row` counts every row for a `ticket_id` across the whole file's history, so a ticket legitimately closed `BLOCKED` then later reopened and closed `DONE` always reports a false "duplicate Finalize run"

## Status
OPEN

## Tier
hotfix

## Type
bug

## Priority
P2

## Request Summary
**Same family as the parity baseline's exact-count assertion and the working_log sole-writer guard
that scans for writers rather than duplicates** (per peer review, added 2026-09-13): all three
gates measure a *proxy* for the property they actually care about (no duplicate write) rather than
the property itself, and all three can be fooled — this one by a legitimate second write, not just
a real duplicate. Worth keeping that pattern in mind for whoever designs the real fix, not just this
one check's own row count.

Found while closing `TCK-20260912-KNOWLEDGE-INVESTIGATION-LAYER-INERT-NO-FACTS-NO-LEADS`, which was
legitimately closed once as `BLOCKED` (a real, correctly-recorded working_log row, since the
CLAUDE.md ticket-format's own `## Status` enum lists `BLOCKED` as a valid value alongside
`OPEN | INPROGRESS | BLOCKED | DONE`) and, once its blockers were resolved, reopened and closed
again as `DONE` (a second, equally real row). `tools/gate_checks/done_checker_static.py`'s
`check_working_log_exactly_one_row()` (`tools/gate_checks/done_checker_static.py:824-832`) counts
**every** row in `tickets/working_log.csv` matching the ticket's own ID, with no awareness of
status or timestamp ordering:

```python
def check_working_log_exactly_one_row(...) -> tuple[str, str]:
    count = _count_rows_for_ticket(csv_path, ticket_id)
    if count == 1:
        return ("PASS", ...)
    if count == 0:
        return ("FAIL", "no working_log row found — Finalize did not append")
    return ("FAIL", f"{count} rows found — duplicate Finalize run")
```

For a ticket closed twice legitimately (once `BLOCKED`, once later `DONE`), `count == 2` and this
reports `FAIL: 2 rows found — duplicate Finalize run` — indistinguishable from the real defect this
check exists to catch (an actual duplicate write from two independent hand-rolled appends, the
shape `TCK-20260912-WORKING-LOG-APPEND-HELPER` fixed). The check cannot currently tell "this ticket
was reopened, both rows are real" from "this ticket's Finalize ran twice by mistake."

## Scope
- Distinguish a legitimate multi-row history (prior rows are non-`DONE` statuses, e.g. `BLOCKED`,
  from an earlier real closure attempt) from a real duplicate write (two rows for the same
  Finalize run, or two `DONE` rows for the same ticket).
- Likely shape: check for at most one row per *(ticket_id, status)* pair rather than at most one
  row per ticket_id — or, narrower, check that the *current* Finalize call only wrote one new row
  since the check started (requires passing a `before_count`/timestamp baseline into the check
  rather than reading the file fresh). Pick on evidence, not by default.
- Confirm whether `Part B` (`run_finalize_selfcheck`)'s own docstring/caller expectations
  (`.claude/workflows/implement-ticket.js`'s Finalize step) already assume single-closure-ever, or
  whether this is purely this one function's own gap.

## Out of Scope
- Any change to `tools/working_log_writer.py` itself — that module's own sole-writer guarantee is
  unaffected; this is a read-side counting gap, not a write-side duplicate.
- Retroactively "fixing" any existing multi-row ticket in `tickets/working_log.csv` — those rows
  are each individually real and correct; nothing needs correcting there.

## Acceptance Criteria
- [ ] A real fix that lets `check_working_log_exactly_one_row` (or its replacement) distinguish a
      legitimate reopen-and-reclose from a real duplicate write.
- [ ] Real test coverage: a ticket with one prior `BLOCKED` row and one new `DONE` row passes; two
      `DONE` rows for the same ticket still fails as a real duplicate.
- [ ] No change to `working_log_writer.py`'s own sole-writer contract.

## Related Tickets
- `TCK-20260912-KNOWLEDGE-INVESTIGATION-LAYER-INERT-NO-FACTS-NO-LEADS` (done — the ticket whose own
  legitimate BLOCKED→DONE reopen surfaced this)
- `TCK-20260912-WORKING-LOG-APPEND-HELPER` (done — fixed the real duplicate-write defect this check
  exists to catch; this ticket is about the check's own false-positive on a different, legitimate
  case, not a regression of that fix)

## Related Docs
None yet.

## Related Stored Artifacts
None yet — hotfix tier, no staging artifacts required.

## Related Code Areas
- `tools/gate_checks/done_checker_static.py:824-832` (`check_working_log_exactly_one_row`)
- `tickets/working_log.csv` (the data this check reads, unaffected)

## Assumptions / Open Questions
- Whether a per-status check or a baseline-count-passed-in approach is the right shape — not
  decided here.

## Implementation Notes
_(pending — filed, not yet picked up)_

## Test Summary
_(pending)_

## Files Changed
_(pending)_

## Completion Summary
_(pending)_
