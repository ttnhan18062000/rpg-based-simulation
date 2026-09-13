---
status: active
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20260911-IMPLEMENT-EPIC-CLOSE-STEP-MISSING
phase: open
date: 2026-09-11
tags: [workflows, process-improvement]
---

# TCK-20260911-IMPLEMENT-EPIC-CLOSE-STEP-MISSING

## Title
`implement-epic.js` has no step that closes the epic ticket itself once all children are done

## Status
OPEN

## Tier
standard

## Type
feature

## Priority
P2

## Request Summary
Follow-on from `TCK-20260907-DONE-TICKET-FRONTMATTER-PHASE-STATUS-DRIFT`'s investigation
(`staging_artifacts/TCK-20260907-DONE-TICKET-FRONTMATTER-PHASE-STATUS-DRIFT/investigation.md`
§8, second correction). No workflow in this repo ever closes an *epic ticket itself*:

- `implement-ticket.js`'s epic-tier routing path returns `EPIC_SCOPED` for a ticket tagged
  `## Tier: epic` and never touches the epic ticket file's own frontmatter or location.
- `implement-epic.js` (482 lines) only moves a finished `tickets/todos/{folder}/` directory once
  all its child tickets are done — it never updates or moves the epic ticket file itself.
- `create-tickets.js`'s Link phase looks up the epic only to append child ticket IDs to it — also
  not a close step.

As a result, every epic ticket that has ever reached `tickets/done/` got there by a human/agent
manually editing its frontmatter and `git mv`-ing it (or via a bulk PR squash merge), with no
workflow instruction and no automated check. Investigation's evidence: of 12 epic tickets with an
`implement-epic` run record, 11 (91.7%) still show frontmatter drift by the time they land in
`tickets/done/` — the highest drift rate of any closing path measured (vs. 24.6% for
`implement-ticket` ticket-tier closes, which at least have Finalize's instruction to fall back on).

Confirmed real, not hypothetical: the 9+1 `phase: epic_scoped` tickets found in that investigation
(E13/E21/E31/E32/E33/E41/E42/E43/E53A/E53D) are exactly this — closed epics whose frontmatter was
never normalized by any workflow step, only by TCK-20260907's own bulk remediation.

## Scope
- Add an epic-close step to `implement-epic.js` (the natural home, since it already owns the
  "all children done" detection that currently only triggers the `tickets/todos/{folder}/` →
  `tickets/done/{folder}/` move) that, once triggered:
  - Sets the epic ticket's own frontmatter `phase: done` / `status: historical` (matching
    `tickets/done/`'s location-aware rule added by TCK-20260907, in
    `tools/validate_frontmatter.py::check_ticket_location_consistency`).
  - Sets the epic ticket's own body `## Status` per whatever value CLAUDE.md's epic vocabulary
    settles on (`DONE` vs `EPIC_SCOPED` — CLAUDE.md documents `EPIC_SCOPED` as a valid body status
    for epics; TCK-20260907 found live disagreement even among the 10 existing epics, 7 say
    `DONE` and 3 say `EPIC_SCOPED` post-normalization — this ticket should settle which is
    canonical going forward, not just replicate the existing split).
  - Moves the epic ticket file itself: `tickets/inprogress/{epic_id}.md` (or wherever it lives)
    → `tickets/done/{epic_id}.md`, alongside the existing folder move.
- Add a static/regression test proving the new step actually fires and produces canonical
  frontmatter, following this repo's established raw-source-text-parsing pattern for `.js`
  workflow files (see `tests/tools/test_finalize_knowledge_index_refresh.py`,
  `tests/tools/test_finalize_phase_status_instruction_pin.py`).

## Out of Scope
- Re-normalizing the 9-10 already-closed epic tickets' frontmatter — already done by
  `TCK-20260907-DONE-TICKET-FRONTMATTER-PHASE-STATUS-DRIFT`'s Step 3 bulk remediation.
- Any change to `tools/validate_frontmatter.py`'s location-aware rule itself, or to the
  `tickets/done/` corpus test — both already exist and are what this new workflow step must
  satisfy, not something this ticket needs to touch.
- Deciding the DONE-vs-EPIC_SCOPED body-status question in isolation from the workflow-step work —
  investigate both together, since the workflow step needs to know which value to write.

## Acceptance Criteria
- [ ] `implement-epic.js` sets the epic ticket's frontmatter to `phase: done` /
      `status: historical` and moves the file to `tickets/done/` once all children are confirmed
      done, in the same step that already moves the `tickets/todos/{folder}/` directory.
- [ ] The new step also resolves and writes the epic ticket's own body `## Status` value
      (DONE vs EPIC_SCOPED — decide which is canonical as part of this ticket).
- [ ] A test proves the step fires (raw-source-text pin, following
      `tests/tools/test_finalize_knowledge_index_refresh.py`'s pattern — no JS test runner exists
      in this repo for `.claude/workflows/*.js`).
- [ ] `tools/validate_frontmatter.py::check_ticket_location_consistency`'s `tickets/done/` rule
      passes on an epic closed through the new step, without needing a follow-up bulk-remediation
      ticket.

## Related Tickets
- `TCK-20260907-DONE-TICKET-FRONTMATTER-PHASE-STATUS-DRIFT` (done) — filed this ticket at its own
  Finalize; added the `tickets/done/` location-aware validator rule and corpus test this ticket's
  new workflow step must satisfy, and bulk-remediated the 9-10 already-closed epics' frontmatter
  as a one-time fix (not a durable one — this ticket is the durable fix for epics going forward).

## Related Docs
- `staging_artifacts/TCK-20260907-DONE-TICKET-FRONTMATTER-PHASE-STATUS-DRIFT/investigation.md`
  §8 (second correction) — the evidence this ticket is based on.

## Related Stored Artifacts
None yet — Investigate should produce `investigation.md`/`plan.md`/`test_plan.md` per this
ticket's `standard` tier.

## Related Code Areas
- `.claude/workflows/implement-epic.js`
- `.claude/workflows/create-tickets.js` (Link phase — confirm it stays out of scope, or is the
  better home, during Investigate)
- `tools/validate_frontmatter.py` (`check_ticket_location_consistency` — consumed, not modified)

## Assumptions / Open Questions
- Whether `implement-epic.js` or a different workflow file is the correct place for this step —
  Scope's best guess is `implement-epic.js` since it already owns "all children done" detection,
  but Investigate should confirm rather than assume.
- Whether DONE or EPIC_SCOPED should be the canonical body `## Status` for a fully-closed epic —
  open per the existing 7/3 split found in the live corpus.

## Implementation Notes

## Test Summary

## Files Changed

## Completion Summary
