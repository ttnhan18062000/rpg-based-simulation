---
status: active
layer: ai
authority: P2
audience: agent
ticket_id: TCK-20260911-IMPLEMENT-EPIC-CLOSE-STEP-MISSING
artifact_type: investigation
tags: [workflows, process-improvement]
---

# Investigation — TCK-20260911-IMPLEMENT-EPIC-CLOSE-STEP-MISSING

## 1. Confirmed: no workflow closes an epic ticket today, in practice

Directly confirmed (not re-derived) via `TCK-20260907-DONE-TICKET-FRONTMATTER-PHASE-STATUS-DRIFT`'s
own investigation.md §8, and independently re-checked here against the live code:

- `implement-ticket.js`'s epic-tier path (`.claude/workflows/implement-ticket.js:494-502`) returns
  `EPIC_SCOPED` immediately after Scope and never touches the epic ticket file again. It runs once,
  before any children exist, and is never re-invoked once children are done — it has no "all
  children done" awareness at all and structurally cannot acquire it without a new re-entry
  convention that doesn't exist anywhere else in this repo.
- `create-tickets.js`'s Link phase (`.claude/workflows/create-tickets.js:862-886`) only appends new
  child ticket IDs to the epic's `## Related Tickets` section, at ticket-*creation* time. This fires
  before any child is implemented — the wrong lifecycle stage entirely, not just an incomplete
  implementation of the right idea.
- `implement-epic.js`'s only per-batch completion step is folder-mode's own cleanup block
  (`implement-epic.js:389-411`, `if (batchStatus === 'DONE' && folder)`), which moves the
  `tickets/todos/{folder}/` directory. **This has no equivalent for `epic_id` mode at all** — not a
  smaller version of it, a bare `if` with nothing inside. Folder mode has no epic ticket file to
  close in the first place (`epic_ticket_path = ""` for folder mode, per Discover's own contract) —
  only `epic_id` mode ever has a real epic ticket file that needs this.

**Confirmed via re-checking real closed epics, not just trusting the citation — corrected once
already (see Correction below), and re-verified against a recursive glob:** `tickets/done/` holds
epic tickets both directly (`tickets/done/TCK-*.md`) and inside per-batch subfolders
(`tickets/done/{folder}/TCK-*.md`, produced by the folder-move step CLAUDE.md's own "After Work"
rule describes) — a first pass here only globbed the top-level directory and undercounted by 25
tickets. The correct, recursive-glob population is **79** `tier: epic` tickets in `tickets/done/`
(78 with correct frontmatter — see the OPEN case below): **71 (89.9%)** already read body
`## Status: DONE`, **7 (8.9%)** read `EPIC_SCOPED` despite sitting in `tickets/done/` with all
children complete (E13-CONTENT-FOUNDATION, E53A/E53B/E53C/E53D, E61-PROGRESSION,
ENTITY-LIFECYCLE-IMPROVEMENT-EPIC) — a live symptom of the same underlying gap surfacing in a
second field (body status) that TCK-20260907's frontmatter-only bulk fix never touched — and **1
(1.3%)** reads `## Status: OPEN` (`TCK-20260710-AGENT-BOOKKEEPING-DETERMINISM-EPIC`) — neither
`DONE` nor `EPIC_SCOPED`, a third drift shape distinct from the other two, confirming this field
drifts in more than one direction once nothing ever writes it. The 89.9%/DONE majority is still
strong, independent evidence for which body-status value is the real convention (§4 below) — the
correction changes the exact count, not the conclusion.

**The new step's fix is unconditional, not conditional on the current value** — Step 2 of the
close-step prompt (§ plan.md, Implementation Notes) says "set the body `## Status` section to
DONE," full stop, regardless of what it currently reads. This means it corrects all three observed
drift shapes (`EPIC_SCOPED`, `OPEN`, and any other stale value) the same way, not just the
`EPIC_SCOPED` case this investigation happened to notice first.

**How epics actually reach `tickets/done/` today, confirmed by TCK-20260907's own investigation**:
"by hand or in batch commits" (e.g. a PR squash-merge that happened to include a manual
frontmatter/location edit alongside other files) — never through any workflow step whose job is
specifically to close the epic. The 91.7% drift rate for `implement-epic`-run epics (11 of 12) is
exactly this: an `implement-epic` run completed all children, and a human then closed the epic file
by hand afterward, sometimes correctly, mostly not.

## 2. Why this changes the shape of the fix

This is not "add a missing call in an obvious place." There is no natural home today — the ticket's
own Scope-time guess (`implement-epic.js`, since it already owns "all children done" detection) is
correct, but *within* that file the only existing completion-time step (folder cleanup) has zero
epic_id-mode counterpart to extend. The real work is deciding where the step belongs and building it
from nothing, not wiring an existing near-miss.

## 3. Options considered

**A. Extend `implement-epic.js`'s `epic_id` mode with a close step, symmetric to the existing
folder-mode cleanup block.** Runs at the same point (`batchStatus === 'DONE'`, right after the
existing folder-cleanup `if`), guarded on `epicId` instead of `folder`. `implement-epic.js` already
has every fact this step needs in scope at that point: `epicId`, `discovery.epic_ticket_path`,
`doneCount`, `ticketIds.length` — nothing new needs to be threaded in from elsewhere.

**B. Add a close phase to `implement-ticket.js`'s epic-tier path.** Rejected: that path runs once,
synchronously, right after Scope, before any child ticket exists — it has no mechanism to be
"woken up" again once children finish, and inventing one (a new re-entry convention, keyed on
somehow re-running Scope for an already-scoped epic) would be new infrastructure with no precedent
in this repo, not a natural extension of an existing pattern.

**C. A separate close command/tool, invoked once children are done.** Rejected: `implement-epic.js`
is the only place that already computes "are all children done" as a natural side effect of its own
per-ticket loop (`batchStatus`, `doneCount` vs `ticketIds.length`). A separate command would need to
recompute that same fact independently (re-reading `## Related Tickets`, re-checking each child
against `tickets/done/`) — genuine duplicated logic for no benefit, and one more thing a user has to
remember to run rather than something that happens automatically as part of the batch that already
exists for exactly this purpose.

**Recommendation: A.** It is the only option that reuses existing state instead of duplicating or
inventing infrastructure, and it makes `epic_id` mode symmetric with `folder` mode's own
already-shipped completion step — the same shape, applied to the one mode that actually has a file
worth closing.

## 4. Canonical body `## Status` value: DONE, not EPIC_SCOPED

`tools/ticket_field_values.py::WORKFLOW_STATUS_VALUES` includes both `DONE` and `EPIC_SCOPED`, and
CLAUDE.md documents `EPIC_SCOPED` as a valid epic body status — so this isn't a case of removing an
invalid value, it's deciding which one this *new automated step* should write.

`EPIC_SCOPED` is `implement-ticket.js`'s own return status immediately after an epic ticket is first
scoped, before any children exist — a genuinely *mid-flight* meaning ("scoped, not yet resolved into
children"), not a terminal one. Live-corpus evidence (§1, corrected) shows 71/79 (89.9%) of
already-closed epics use `DONE`; the 7 `EPIC_SCOPED` + 1 `OPEN` exceptions are drift artifacts of
the exact same missing-close-step problem this ticket fixes, manifesting in the body-status field
instead of frontmatter (TCK-20260907's bulk remediation only ever touched frontmatter, never body
`## Status`). There is no case in the live corpus of a *deliberately* EPIC_SCOPED-and-done (or
OPEN-and-done) epic with a documented reason — every instance found is drift, not intent.

**Decision: the new close step writes `## Status: DONE`.** `EPIC_SCOPED` remains valid vocabulary
for its original, narrower meaning (the mid-flight state right after Scope) — this ticket does not
remove it from `WORKFLOW_STATUS_VALUES`, only stops using it as a terminal value for an epic this
step itself closes.

## 5. Out of scope, confirmed unaffected

- `create-tickets.js`'s Link phase is confirmed structurally the wrong lifecycle stage (§1) — no
  change needed there, and Investigate confirms the ticket's own uncertainty on this point.
- Re-normalizing the 6 already-closed EPIC_SCOPED-in-`tickets/done/` epics is out of scope per the
  ticket text (already covered by TCK-20260907's bulk remediation for frontmatter; the body-status
  half of that drift is a separate, smaller cleanup this ticket does not need to also do to satisfy
  its own Acceptance Criteria, which are about the *workflow step* going forward).
- `tools/validate_frontmatter.py::check_ticket_location_consistency` and its corpus test are
  consumed, not modified — confirmed still asserting exactly `status: historical` / `phase: done`
  for `tickets/done/`, which is what the new step must (and will) produce.
