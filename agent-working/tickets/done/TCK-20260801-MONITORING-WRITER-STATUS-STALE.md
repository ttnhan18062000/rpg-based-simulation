---
status: historical
layer: ticket
authority: P1
audience: agent
ticket_id: TCK-20260801-MONITORING-WRITER-STATUS-STALE
phase: done
date: 2026-08-01
tags: [frontmatter, documentation, process-improvement]
---

# TCK-20260801-MONITORING-WRITER-STATUS-STALE

## Title
Correct stale lifecycle fields on TCK-20260721-MONITORING-WRITER-UNIFICATION

## Status
DONE

## Tier
hotfix

## Type
chore

## Priority
P2

## Request Summary
`tickets/done/TCK-20260721-MONITORING-WRITER-UNIFICATION.md` is genuinely complete —
it has a real Completion Summary and a real `DONE` entry in `tickets/working_log.csv`
(2026-07-22T16:06:22Z) — but its frontmatter and body lifecycle fields were never
updated out of their in-flight values when the ticket closed. Found during a prior
ticket's own investigation (`TCK-20260728-PHASE0-PREREQ-CONFIRMATION`), which flagged
it as "the only file among ~1096 in `tickets/done/` missing `phase: done`" and
deliberately left it out of that ticket's own scope as a separately-tracked defect.

Confirmed the correct target values by direct comparison against a real, correctly-closed
ticket (`tickets/done/TCK-20260730-CLAUDE-EXECUTION-IDENTITY.md`), not guessed:

- frontmatter `status: active` → `status: historical`
- frontmatter `phase: open` → `phase: done`
- body `## Status\nOPEN` → `## Status\nDONE`

## Scope
- Edit exactly those three field values on
  `tickets/done/TCK-20260721-MONITORING-WRITER-UNIFICATION.md`.
- Confirm the file passes `python3 tools/validate_frontmatter.py` and
  `tools/ticket_field_values.py`'s checks after the edit.

## Out of Scope
- Any change to the ticket's own content (Title, Scope, Acceptance Criteria,
  Completion Summary, or any other section) — only the three lifecycle field values
  change.
- Any change to any other ticket file. The known-adjacent finding this ticket
  originates from was scoped to exactly one file; do not sweep for other stale-status
  tickets as a drive-by.
- Any change to `docs/parity_ledger/` — this is a doc-hygiene fix with no source/test
  behavior change; no parity entry applies.

## Acceptance Criteria
- [x] `tickets/done/TCK-20260721-MONITORING-WRITER-UNIFICATION.md` frontmatter reads
      `status: historical` and `phase: done`.
- [x] The same file's body `## Status` section reads `DONE`.
- [x] `python3 tools/validate_frontmatter.py tickets/done/TCK-20260721-MONITORING-WRITER-UNIFICATION.md`
      passes with no violations.
- [x] No unrelated source, ticket, or documentation content changes. The only permitted
      non-target changes are the standard, reviewable `implement-ticket` lifecycle
      outputs for this candidate ticket itself (its own status/artifacts, one
      `working_log.csv` row, append-only monitoring records, and regenerated
      `docs/REGISTRY.yaml`), plus explicitly authorized scratch pilot evidence/config
      rollback artifacts if run live. The target historical ticket
      (`TCK-20260721-MONITORING-WRITER-UNIFICATION.md`) changes only in the three
      declared fields — monitoring history is append-only and must be
      prefix-preserved, not byte-identical, after a real run.

## Related Tickets
- TCK-20260721-MONITORING-WRITER-UNIFICATION (target of this fix; already DONE)
- TCK-20260728-PHASE0-PREREQ-CONFIRMATION (DONE; originally found and deliberately
  out-of-scoped this defect)
- TCK-20260730-CODEX-CONTROLLED-PILOT (this ticket is the proposed low-risk candidate
  for that ticket's live pilot operation — see
  `docs/plans/agent_infrastructure/codex_controlled_pilot_candidate_proposal_claude.md`)

## Related Docs
- docs/plans/agent_infrastructure/codex_controlled_pilot_candidate_proposal_claude.md

## Related Stored Artifacts
None (hotfix — no staging artifacts required).

## Related Code Areas
- tickets/done/TCK-20260721-MONITORING-WRITER-UNIFICATION.md

## Assumptions / Open Questions
- This ticket is deliberately scoped (Scope phase only) and left unimplemented at
  creation time. It exists as a candidate for `TCK-20260730-CODEX-CONTROLLED-PILOT`'s
  live pilot operation — Implement through Finalize are intentionally not run here, so
  real work remains for whichever execution (live Codex pilot, if authorized, or
  ordinary non-live implementation otherwise) completes it.
- If the live pilot is never authorized, this ticket remains eligible for ordinary
  non-live implementation like any other hotfix — nothing about its scope depends on
  which executor completes it.

## Implementation Notes
Released from `TCK-20260730-CODEX-CONTROLLED-PILOT`'s reservation and implemented as an ordinary
non-live hotfix, per that ticket's own stated fallback ("this ticket remains eligible for ordinary
non-live implementation ... nothing about its scope depends on which executor completes it") — the
pilot itself remains BLOCKED/deferred pending separate human authorization, and there was no reason
to hold this trivial fix hostage to that unresolved decision. User explicitly confirmed the release.

Edited exactly the three declared lifecycle fields on
`tickets/done/TCK-20260721-MONITORING-WRITER-UNIFICATION.md`:
`status: active` → `historical`, `phase: open` → `done`, body `## Status\nOPEN` → `DONE`. No other
line in that file was touched (confirmed via `git diff` showing only these three lines changed).

## Test Summary
`python3 tools/validate_frontmatter.py tickets/done/TCK-20260721-MONITORING-WRITER-UNIFICATION.md`
— OK, no violations. `tools/ticket_field_values.py::check_ticket_field_values` (the module has no
CLI entry point, invoked directly) — PASS on both `## Tier` (`standard`) and `## Priority` (`P1`),
both already canonical and untouched by this change.

## Files Changed
- `tickets/done/TCK-20260721-MONITORING-WRITER-UNIFICATION.md` — 3 lifecycle field values corrected
  (frontmatter `status`, frontmatter `phase`, body `## Status`); no other content changed.

## Completion Summary
Corrected the three stale lifecycle fields on `TCK-20260721-MONITORING-WRITER-UNIFICATION.md`
(the only file among ~1096 in `tickets/done/` missing `phase: done`, per the originating
investigation). Verified via `validate_frontmatter.py` and `ticket_field_values.py` — both pass.
No other content in the target ticket changed. This candidate ticket was explicitly released from
its reservation as the Codex controlled-pilot's live-pilot test case (that pilot remains
BLOCKED/deferred) and completed instead as an ordinary hotfix, per user decision.
