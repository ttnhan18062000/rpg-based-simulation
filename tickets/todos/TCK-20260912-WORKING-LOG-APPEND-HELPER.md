---
status: active
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20260912-WORKING-LOG-APPEND-HELPER
phase: open
date: 2026-09-12
tags: [data-quality, process-improvement]
---

# TCK-20260912-WORKING-LOG-APPEND-HELPER

## Title
One sanctioned writer for `tickets/working_log.csv` rows — Finalize agents currently hand-roll the append

## Status
OPEN

## Tier
standard

## Type
refactor

## Priority
P2

## Request Summary
`TCK-20260911-WORKING-LOG-LINE-ENDING-UNION-DUPLICATION` (PR #167) fixed a CRLF row writer in
`tools/agent-monitoring/record_hand_orchestrated_closure.py`. Chasing the one row that fix did **not**
explain showed the defect had a second, independent source, and that the real problem is one level up.

**Evidence (2026-09-11/12):** commit `c4d42635` added two working-log rows — one LF, one CRLF. The CRLF
one was written by the Finalize subagent for `TCK-20260907-DONE-TICKET-FRONTMATTER-PHASE-STATUS-DRIFT`
(subagent transcript `agent-a29533cff39b93b7c`, session `7276a580`, `agentType: general-purpose`) using an
improvised heredoc:

```
python3 - <<'EOF'
import csv
row = ["2026-09-11T09:06:03Z", "TCK-20260907-...", ...]
```

`csv.writer` defaults to `lineterminator="\r\n"`. The same defect as the closure script's, written on the
fly rather than living in a file — and the mechanism that duplicated `working_log.csv` blocks on 3 of 4
recent batch merges.

**Why a prompt line is not the fix.** `implement-ticket.js`'s Finalize step 4 specifies the row's
*format* ("Append to tickets/working_log.csv (one new row, comma-separated): timestamp,ticket_id,…") but
not *how* to write it, so each agent improvises. Telling them "use LF" fixes `csv.writer`'s default
specifically and leaves the class untouched: the next improvisation can differ in quoting, column order,
or where the row lands. The two CRLF defects were identical *because* two independent write paths
existed; reducing it to one is the durable fix.

**What is not already true** (checked, so this ticket does not rest on a false premise):
- CLAUDE.md's After Work section says only "Append to the **bottom** of `tickets/working_log.csv` (never
  insert after the header)". There is no existing "never hand-roll the write" rule to enforce.
- `record_hand_orchestrated_closure.py` cannot serve as the sanctioned path as it stands: `--events` is
  required and it always writes a monitoring run record plus events. Pipeline runs already record their
  own run via the workflow's `writeMonitoring`, so routing Finalize through it would double-record every
  ticket. It has no log-only mode.
- No other working-log append helper exists in `tools/`; that script's `writerow` is the only one.

## Scope
- Add one small sanctioned writer module owning the working-log row format: LF line endings,
  `QUOTE_MINIMAL`, the documented column order, bottom-append, `newline=""`. Read-side parsing stays in
  `tools/working_log_parser.py`; this is its write-side counterpart.
- Call it from `tools/agent-monitoring/record_hand_orchestrated_closure.py` in place of that script's own
  `csv.writer` call (PR #167 must merge first — it edits the same line).
- Point `implement-ticket.js`'s Finalize step 4 at the helper instead of describing a row for the agent to
  write however it likes.
- Add the rule to CLAUDE.md's After Work bullet: append via the helper, never hand-roll the write.
- Guard it: a test asserting no module other than the helper writes `tickets/working_log.csv`, so a future
  second path fails in CI rather than on the next merge.

## Out of Scope
- The row format itself (columns, timestamp precision, quoting). This ticket centralizes who writes it,
  not what is written.
- Monitoring run/event recording, which stays with `record_hand_orchestrated_closure.py`.
- Retrofitting historical rows. PR #167 already normalized line endings on `main`.
- `agent-monitoring/data/*/*.jsonl` writers: `tools/agent-monitoring/writer.py` already owns those and
  emits LF.

## Acceptance Criteria
- [ ] Exactly one module in the repo writes `tickets/working_log.csv` rows; a test enforces it.
- [ ] The helper emits LF, `QUOTE_MINIMAL`, the documented column order, and appends at the bottom, with
      unit tests including a field containing a comma, a quote, and an embedded newline.
- [ ] `record_hand_orchestrated_closure.py` uses the helper; its existing tests pass unmodified.
- [ ] Finalize step 4 in `implement-ticket.js` instructs the helper, pinned by a static test the way
      `TCK-20260907`'s instruction pin is.
- [ ] CLAUDE.md's After Work bullet states the rule.
- [ ] `tests/integrity/test_merge_union_no_cr_bytes.py` still passes (it is the backstop, not the fix).

### Remediation note for existing branches (2026-09-12)

Any branch cut before PR #167 carries CRLF rows in its **own commits**; `eol=lf` normalizes at commit
time and does not rewrite them. Each such branch needs one pass: merge `origin/main`, then
`git add --renormalize tickets/working_log.csv agent-monitoring/data`, then commit if anything staged.

**Verify the committed blob, not the working tree** — they can disagree:

```
git show HEAD:tickets/working_log.csv | python3 -c "import sys;print(sys.stdin.buffer.read().count(b'\r'))"
```

`git add --renormalize` rewrites the **index** and deliberately leaves the working copy alone;
`git checkout HEAD -- <path>` then silently no-ops, because git's normalized comparison considers the
file unchanged even when its raw bytes differ. `rpg-implementer` hit this on PRs #168 and #169: a
clean renormalize, a committed blob at 0 CR, and a working-tree check still printing 8. Forcing real
bytes onto disk required `rm` plus a re-checkout.

The committed blob is the object `merge=union` operates on, so it is the one that decides whether the
defect recurs — check that one. (Reported by `rpg-feature-planning`, 2026-09-12; the working-tree
check circulated earlier in this ticket's thread targets the wrong object.)

## Related Tickets
- `TCK-20260911-WORKING-LOG-LINE-ENDING-UNION-DUPLICATION` (PR #167) — fixed the first writer; this
  ticket closes the class. **Must merge first.**
- `TCK-20260906-WORKING-LOG-MERGE-UNION-DUPLICATION-GAP` (done) — original duplication incident.
- `TCK-20260907-DONE-TICKET-FRONTMATTER-PHASE-STATUS-DRIFT` (done) — precedent for pinning a workflow
  instruction with a static test.

## Related Docs
- `CLAUDE.md` (After Work)
- `.gitattributes` (the `merge=union` caveat blocks)

## Related Stored Artifacts
- `stored_artifacts/TCK-20260911-WORKING-LOG-LINE-ENDING-UNION-DUPLICATION/`

## Related Code Areas
- `tools/agent-monitoring/record_hand_orchestrated_closure.py` (`writerow`, ~line 207)
- `tools/working_log_parser.py` (read side)
- `.claude/workflows/implement-ticket.js` (Finalize step 4)
- `tests/integrity/test_merge_union_no_cr_bytes.py`

## Assumptions / Open Questions
- Whether the helper belongs beside the parser (`tools/working_log_writer.py`) or inside it as a write
  function is an Implement-time call; the constraint is one owner, not a particular file.
- Agents can still bypass any helper by writing the file directly. The enforcement here is the
  instruction plus the CI guard, not a hard lock — state that honestly rather than claiming prevention.
- This is the second domain this week where the fix was consolidating parallel implementations of one job
  rather than correcting each copy (noted by `rpg-feature-planning`, from the RPG side's own deletions).
  Worth recording in the Completion Summary as a pattern, not just this instance.

## Implementation Notes

## Test Summary

## Files Changed

## Completion Summary
