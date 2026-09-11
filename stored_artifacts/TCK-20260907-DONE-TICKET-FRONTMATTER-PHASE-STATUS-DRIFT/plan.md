---
status: active
layer: testing
authority: P1
audience: agent
ticket_id: TCK-20260907-DONE-TICKET-FRONTMATTER-PHASE-STATUS-DRIFT
artifact_type: plan
tags: [process-improvement]
---

# Plan — TCK-20260907-DONE-TICKET-FRONTMATTER-PHASE-STATUS-DRIFT

Addresses all three causes in investigation.md §4. Order matters: enforcement lands last so it passes on
arrival.

## Step 1 — Cross-field consistency rule

Add to `tools/validate_frontmatter.py`: a ticket's `status`/`phase` must agree with the directory it sits in.

| Directory | Required |
|---|---|
| `tickets/done/` | `status: historical` and `phase: done` |
| `tickets/inprogress/` | `phase` is not `done` |

Build it as a location-aware function so `tickets/todos/` can be added later, but enforce only `done/` and
`inprogress/` now — the ticket scopes to `done/` and the evidence covers only that.

Also wire it into `done_checker_static.check_frontmatter_valid()`, as the ticket proposed. That gives fast
feedback at close time for pipeline runs. It is not sufficient on its own; Step 4 is.

## Step 2 — Decide `epic_scoped`

**Recommendation: normalize the 9 closed epics to `phase: done`, and do not add `epic_scoped` to
`PHASE_VALUES`.** `EPIC_SCOPED` describes an epic that is scoped but still open; all 9 sit in
`tickets/done/`, so `done` describes them accurately. Their body `## Status` fields are left alone — that is
the valid body vocabulary CLAUDE.md defines, and the ticket forbids body edits.

State the body split exactly: 2 of the 9 bodies say `## Status: EPIC_SCOPED` (E13, E53A), 7 say `DONE`.
For those 2, normalizing the frontmatter to `done` leaves the body saying `EPIC_SCOPED`. That's a known
inconsistency the ticket's no-body-edits rule forces us to accept, and it must be written down, not
described as "preserving the distinction".

Record this in Implementation Notes before touching the files. If Review prefers the other option — add
`epic_scoped` to the enum, following `TCK-20260804-BACKLOG-PHASE-VALIDATOR-FIX` — only Step 3's handling of
these 9 changes.

## Step 3 — Bulk remediation

Frontmatter-only, two fields per file, via a small one-off script that rewrites **only** the `status:` and
`phase:` lines inside the leading `---` block:

- `status` → `historical`
- `phase` → `done`

Covers every non-canonical file (395 as of 2026-09-11 — re-count at implementation time, it grows). Record
the before-count, run, then verify:

- after-count of non-canonical files is 0
- each changed file's diff touches exactly the `status`/`phase` lines
- **body bytes are identical** — hash everything after the closing `---` before and after, per file

Use a script with a dry-run mode, not per-file edits. Commit the remediation separately from the code
changes so the 395-file diff can be reviewed on its own.

## Step 4 — Path-independent enforcement

Add a test that runs the Step 1 rule over the **entire real `tickets/done/` corpus**. This is what fixes
cause 2: it catches every closing path — pipeline, hand-orchestrated, unrecorded — because it does not
depend on how the ticket was closed.

Cost is trivial (YAML parsing, no subprocess). The "never sweep" constraint from
`TCK-20260705-GATE-DET-MECHANICS-AUDITOR` concerned running pytest on every parity citation; it does not apply
here.

This test fails until Step 3 lands, which is intended: enforcement cannot be merged ahead of remediation.

## Step 5 — No workflow change; pin the existing instruction

`implement-ticket.js:1671` already instructs `phase: done` / `status: historical`; leave it unchanged. No
workflow has an epic-close step to add an instruction to (investigation.md §8, second correction), so there
is no prompt to change here.

- Add a static test pinning line 1671's instruction, so it can't be silently removed.
- Epic drift is covered by Step 4's corpus test, whoever moves the epic into `tickets/done/`.
- **File a follow-on ticket at close:** `implement-epic.js` has no step that closes the epic ticket itself
  (set `status: historical` / `phase: done`, move it to `tickets/done/`) once all children are done. Adding
  one is new workflow behavior and outside this ticket's metadata-consistency scope.

## Step 6 — Parity ledger

Step 1 changes what `check_frontmatter_valid()` / `validate_frontmatter.py` enforce. Update, via
`tools/parity_ledger_writer.write_entry()` only:

- **INFRA-180** — validator enforcement scope: add the location-aware cross-field rule.
- **INFRA-305** — cites `check_frontmatter_valid()` at specific line numbers: refresh them after Step 1.

Not INFRA-278: it covers `## Tier`/`## Priority` body-field enums (`check_ticket_field_values_valid()`),
and its support_boundary explicitly excludes `## Status`/`layer:`. Step 1 changes nothing it describes
(corrected after Review round 2).

Add a new entry only if the corpus-wide test (Step 4) is judged a distinct durable behavior. Otherwise fold
it into INFRA-180.

## Out of scope

- Ticket body content, including the 9 epics' `## Status` fields.
- Re-reviewing the substance of any of the 395 closures.
- `tickets/todos/` consistency — left designable in Step 1, not enforced.
- `tools/agent-monitoring/record_hand_orchestrated_closure.py` — it does not touch ticket files, and Step 4
  catches hand-orchestrated drift regardless.

## Risks

- **The count grows during the work.** Tickets close every day. Re-count immediately before Step 3, and
  land Step 4 in the same PR so nothing new drifts in between.
- **Merge conflicts.** 395 files are touched by one commit, and other sessions close tickets constantly. The
  remediation commit is mechanical and re-runnable: on conflict, re-run the script against the new tree
  rather than hand-merging.
- **Stale drift reports.** Other tools that count frontmatter states will see different numbers after Step 3.

## Deviations (recorded at Implement, 2026-09-11)

- **Step 1's location rule is NOT folded into `_validate_ticket`/`validate_file`.** The plan's own wording
  ("Add to `tools/validate_frontmatter.py`... Also wire it into `done_checker_static.check_frontmatter_valid()`")
  is consistent with either an implicit (baked into `_validate_ticket`, inherited by every `validate_file`
  call) or explicit (a standalone function, called only where wanted) design. Implicit was tried first and
  rejected: ~15 pre-existing fixtures in `tests/tools/test_validate_frontmatter.py` construct ticket
  frontmatter under `tmp_path/tickets/done/` using `_ticket_fm()`'s non-canonical default
  (`status: active`), and would have needed editing to keep passing — collateral changes to unrelated,
  already-passing tests for a rule that's supposed to be additive. The explicit design (a standalone
  `check_ticket_location_consistency(path, fm)` function, called only by `check_frontmatter_valid()` and the
  Step 4 corpus test) needed zero edits to any pre-existing test — confirmed by running the full pre-existing
  `test_validate_frontmatter.py` + `test_done_checker_static.py` suite (206 tests) unchanged before adding
  any new test. Kept the explicit design for that reason.
- **Bulk remediation (Step 3) and the corpus test (Step 4) are scoped to files whose `ticket_id` matches
  `^TCK-\d{8}-`**, not literally every `.md` under `tickets/done/`. Discovered at implementation time: 77
  folder-level `SEQUENCE.md` files have no frontmatter at all (trivially out of scope), and 37 more files
  have frontmatter but a non-TCK-shaped `ticket_id` — `tickets/done/README.md` (`ticket_id: INDEX`, a
  docs-site index page predating the ticket schema, already failing today's validator for an unrelated,
  pre-existing reason: no `phase` field at all) plus 36 pre-TCK-convention legacy files
  (`METRICS-01.md`, `bug-01-diagonal-hunt-move-conflict.md`, `infra-0X-*.md`, `resource_v2_*.md`, etc.).
  Scoping out these 37 files, the fresh non-canonical count is exactly 395 — unchanged from investigation's
  2026-09-11 snapshot. Fixing README.md's missing-`phase`-field gap is a separate, pre-existing schema issue
  outside this ticket's status/phase-drift scope, not addressed here.
- **A 10th epic-scoped-shaped ticket found beyond investigation's 9**: `TCK-20260619-E53D-HISTORY.md` has
  `status: epic_scoped` / `phase: scoped` (fields transposed relative to the other 9's
  `status: done` / `phase: epic_scoped`), which is why investigation §5's `grep "^phase: epic_scoped"`
  missed it. Step 2's decision (normalize to `historical`/`done`, leave body `## Status` alone) was applied
  to it too for consistency — see the ticket's Implementation Notes for the resulting 3-of-10 (not 2-of-9)
  frontmatter/body disagreement disclosure.
- **`implement-epic.js` epic-close follow-on filed as `TCK-20260911-IMPLEMENT-EPIC-CLOSE-STEP-MISSING`**,
  in `tickets/todos/` (standard tier) rather than `tickets/inprogress/` — it's real future work, not urgent
  enough to start immediately alongside this ticket's own closure.
