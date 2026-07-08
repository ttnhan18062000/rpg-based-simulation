---
status: historical
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20260708-SKILL-IMPLEMENT-TICKET-PHASE-DRIFT
phase: done
date: 2026-07-08
tags: [ai, documentation, workflows, skills]
---

# TCK-20260708-SKILL-IMPLEMENT-TICKET-PHASE-DRIFT

## Title
Fix stale pipeline summary in .claude/skills/implement-ticket/SKILL.md

## Status
DONE

## Tier
hotfix

## Type
chore

## Priority
P2

## Request Summary
`.claude/skills/implement-ticket/SKILL.md`'s "Pipeline (standard tier)" section (lines 43-61) lists only
9 phases and is missing two phases that exist in the live `.claude/workflows/implement-ticket.js`:
**Architecture-Verify** (phase 5b, post-Implement static backstop against the real diff, skipped for
hotfix) and **Security-Review** (phase 7b, conditional gate that fires for security-tagged tickets).
The SKILL.md's "Hotfix tier skips phases 2-4" line also doesn't account for Architecture-Verify being
skipped for hotfix too (it's effectively phase 6 in the SKILL's own undercounted list).

Confirmed during a comparison of `implement-ticket.js` against every agent `.md` it invokes: the `.js`'s
own `meta.phases` array and its 9 `agent()` calls are internally consistent and correctly documented in
`docs/ai/workflows.md`'s `implement-ticket` entry (verified — that doc already lists all 11 phases
including Architecture-Verify, so `TCK-20260705-WORKFLOWS-DOC-STALENESS-REPAIR`'s prior staleness sweep
did not need to touch it and did not cover this SKILL.md). The drift is isolated to this one file.

Since the SKILL.md's own Action section instructs the executing agent to "Read
`.claude/workflows/implement-ticket.js` in full before doing anything else" and execute each phase block
directly from the `.js`, this is unlikely to cause a functional pipeline skip — but the stale summary
misleads anyone (human or agent) who reads only the Pipeline section without opening the full `.js`.

## Scope
- Update the "Pipeline (standard tier)" list in `.claude/skills/implement-ticket/SKILL.md` to include
  all 11 phases from the live `.claude/workflows/implement-ticket.js` `meta.phases` array, in order:
  Scope, Investigate, Plan, Review, Implement, Architecture-Verify, Test, Parity, Security-Review,
  Verify, Finalize.
- Correct the "Hotfix tier skips phases 2-4" note to also state that Architecture-Verify is skipped for
  hotfix (matching the `.js`'s `if (tier !== 'hotfix')` guard around that phase).
- Note that Security-Review is conditional (fires only when the ticket's tags include `security` or
  `suggested_skills` includes `/security-review`), not tier-gated — do not conflate it with the
  hotfix-skip list.

## Out of Scope
- Any change to `.claude/workflows/implement-ticket.js` or any file under `.claude/agents/` — this is a
  documentation-only fix, zero pipeline behavior changes.
- `docs/ai/workflows.md` — already verified accurate for `implement-ticket`, do not touch.
- The other drift found in the same review pass, `create-tickets/SKILL.md`'s stale "Workflow tool"
  invocation instructions — tracked separately in
  `TCK-20260708-SKILL-CREATE-TICKETS-WORKFLOW-TOOL-STALE`.

## Acceptance Criteria
- [ ] `.claude/skills/implement-ticket/SKILL.md`'s Pipeline section lists all 11 phases, matching
      `.claude/workflows/implement-ticket.js`'s `meta.phases` order exactly.
- [ ] The hotfix-skip note correctly lists every phase skipped for hotfix tier (Investigate, Plan,
      Review, Architecture-Verify), not just phases 2-4.
- [ ] No other content in `SKILL.md` is modified beyond the Pipeline section and the hotfix-skip note.
- [ ] No file outside `.claude/skills/implement-ticket/SKILL.md` is changed.

## Related Tickets
- TCK-20260705-WORKFLOWS-DOC-STALENESS-REPAIR (prior sweep — fixed `docs/ai/workflows.md`'s stale phase
  lists for 4 other workflows; did not cover this file, established the precedent this ticket follows)
- TCK-20260708-SKILL-CREATE-TICKETS-WORKFLOW-TOOL-STALE (sibling finding from the same review pass)

## Related Docs
- `docs/ai/workflows.md` (read-only reference — already-accurate source of truth for the correct phase
  list)

## Related Stored Artifacts
None.

## Related Code Areas
- `.claude/skills/implement-ticket/SKILL.md` (edit target)
- `.claude/workflows/implement-ticket.js` (read-only reference — source of truth for phase names, lines
  1-17 `meta.phases`)

## Assumptions / Open Questions
None — self-evident fix, source of truth (`meta.phases` in the `.js`) is unambiguous.

## Implementation Notes
Updated `.claude/skills/implement-ticket/SKILL.md`'s "Pipeline (standard tier)" section (previously lines
43-61) to list all 11 phases from `.claude/workflows/implement-ticket.js`'s `meta.phases` array (lines
1-17), in order: Scope, Investigate, Plan, Review, Implement, Architecture-Verify, Test, Parity,
Security-Review, Verify, Finalize. Renumbered the list 1-11 (context search remains item 0, unchanged).
Added a one-line description for Architecture-Verify (post-Implement backstop re-invoking
architecture-reviewer against the actual diff, skipped for hotfix) and Security-Review (conditional gate
firing on `security` tag or `/security-review` in `suggested_skills`, not tier-gated). Corrected the
"Hotfix tier skips phases 2-4" note to "Hotfix tier skips Investigate, Plan, Review, and
Architecture-Verify" per the `.js`'s `if (tier !== 'hotfix')` guard around that phase. No other content
in SKILL.md was touched. `.claude/workflows/implement-ticket.js`, `.claude/agents/`, `docs/ai/workflows.md`,
and `.claude/skills/create-tickets/SKILL.md` were not modified, per scope guards.

## Test Summary
No automated tests apply — documentation-only change to a Claude Code skill file. Verified via manual
diff against `.claude/workflows/implement-ticket.js`'s `meta.phases` array (lines 1-17), confirming the
SKILL.md's Pipeline section phase names and order now match exactly.

## Files Changed
- `.claude/skills/implement-ticket/SKILL.md` (Pipeline section and hotfix-skip note corrected)

## Completion Summary
Updated the "Pipeline (standard tier)" list in `.claude/skills/implement-ticket/SKILL.md` to include all
11 phases matching `.claude/workflows/implement-ticket.js`'s `meta.phases` array exactly in order (added
Architecture-Verify and Security-Review, which were previously missing). Corrected the "Hotfix tier skips
phases 2-4" note to correctly list Investigate, Plan, Review, and Architecture-Verify as skipped for
hotfix. No automated tests apply (docs-only change to a Claude Code skill file); verified via manual diff
against `meta.phases` lines 1-17 that phase names and order match exactly.
