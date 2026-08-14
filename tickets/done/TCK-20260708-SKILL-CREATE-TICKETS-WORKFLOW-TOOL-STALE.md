---
status: historical
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20260708-SKILL-CREATE-TICKETS-WORKFLOW-TOOL-STALE
phase: done
date: 2026-07-08
tags: [ai, documentation, workflows, skills]
---

# TCK-20260708-SKILL-CREATE-TICKETS-WORKFLOW-TOOL-STALE

## Title
Fix stale "Workflow tool" primary-path instructions in .claude/skills/create-tickets/SKILL.md

## Status
DONE

## Tier
hotfix

## Type
chore

## Priority
P2

## Request Summary
`.claude/skills/create-tickets/SKILL.md`'s Action section (lines 25-31) instructs the executing agent to
first "Invoke the Workflow tool with: `name: "create-tickets"` ..." and only "If the Workflow tool is
unavailable, execute the pipeline inline using the steps below." No `Workflow` tool exists in this
environment (confirmed via tool search — only `EnterWorktree`/`ExitWorktree` and unrelated tools match
that name fragment; no generic workflow-invocation tool is registered).

Its sibling skills were already corrected for this: `.claude/skills/implement-ticket/SKILL.md` and
`.claude/skills/implement-epic/SKILL.md` both flatly state "**Do not call the Workflow tool — it is not
available.** Execute the workflow directly:" and go straight to the JS-to-tool-call translation
instructions, with no "if unavailable" branching. `create-tickets/SKILL.md` was not updated to match,
so it's the only one of the three ticket-workflow skills still describing a two-path
(Workflow-tool-first, inline-fallback) execution model that doesn't reflect the actual environment.

The pipeline phase list itself in this same file (Comprehend/Investigate/Structure/Write/Link) was
verified accurate against `.claude/workflows/create-tickets.js`'s live `phase()` call sites (lines 39,
208, 450, 716, 893) and against `docs/ai/workflows.md`'s already-corrected entry from
`TCK-20260705-WORKFLOWS-DOC-STALENESS-REPAIR` — no drift there, this ticket is scoped to the Action
section's tool-invocation instructions only.

## Scope
- Rewrite the "## Action" section of `.claude/skills/create-tickets/SKILL.md` to match the pattern
  already established in `implement-ticket/SKILL.md` and `implement-epic/SKILL.md`: state plainly that
  no `Workflow` tool is available and execute the pipeline directly via the JS-to-tool-call translation,
  rather than presenting a "try the Workflow tool first" primary path.
- Preserve the existing instruction not to skip or abbreviate the Investigate phase — that constraint is
  still correct and load-bearing, just needs to move into the corrected inline-execution instructions.

## Out of Scope
- The Pipeline phase list (Comprehend/Investigate/Structure/Write/Link) — already verified accurate,
  do not touch.
- Any change to `.claude/workflows/create-tickets.js` or any file under `.claude/agents/`.
- `docs/ai/workflows.md` or `docs/ai/skills.md` — already corrected for `create-tickets` by
  `TCK-20260705-WORKFLOWS-DOC-STALENESS-REPAIR`; out of scope here.
- `TCK-20260708-SKILL-IMPLEMENT-TICKET-PHASE-DRIFT` — sibling finding, tracked separately.

## Acceptance Criteria
- [ ] `create-tickets/SKILL.md`'s Action section no longer instructs the agent to attempt a `Workflow`
      tool call as the primary path.
- [ ] The corrected Action section matches the phrasing/structure convention used by
      `implement-ticket/SKILL.md` and `implement-epic/SKILL.md` ("Do not call the Workflow tool — it is
      not available. Execute the workflow directly: ...").
- [ ] The "do not skip or abbreviate the Investigate phase" instruction is preserved somewhere in the
      corrected section.
- [ ] No other content in `SKILL.md` (Usage, Input, Pipeline, Notes sections) is modified.
- [ ] No file outside `.claude/skills/create-tickets/SKILL.md` is changed.

## Related Tickets
- TCK-20260705-WORKFLOWS-DOC-STALENESS-REPAIR (prior sweep — corrected `docs/ai/workflows.md` and
  `docs/ai/skills.md` for `create-tickets`; did not touch this SKILL.md's own Action section)
- TCK-20260708-SKILL-IMPLEMENT-TICKET-PHASE-DRIFT (sibling finding from the same review pass)

## Related Docs
None (pure `.claude/skills/` internal fix; no `docs/` file references the `Workflow` tool availability
question).

## Related Stored Artifacts
None.

## Related Code Areas
- `.claude/skills/create-tickets/SKILL.md` (edit target)
- `.claude/skills/implement-ticket/SKILL.md` (read-only reference — pattern to match)
- `.claude/skills/implement-epic/SKILL.md` (read-only reference — pattern to match)

## Assumptions / Open Questions
None — self-evident fix, the corrected pattern already exists twice in-repo as precedent.

## Implementation Notes
Rewrote the `## Action` section of `.claude/skills/create-tickets/SKILL.md` to match the pattern in
`implement-ticket/SKILL.md` and `implement-epic/SKILL.md`: leads with "**Do not call the Workflow tool —
it is not available.** Execute the workflow directly:", then a numbered JS-to-tool-call translation
(read `.claude/workflows/create-tickets.js` in full, execute phase blocks in order, a translation table
for `phase()`/`log()`/`await agent(...)`/`await writeMonitoring(finalStatus)`/`return {...}`, and a step
to carry variables across phases — using this file's own variable names `comprehension`,
`validInvestigations`, `structured`, `outputFolder` in place of implement-ticket's `tier`/`tid`/etc.).
The "do not skip or abbreviate the Investigate phase" instruction was preserved as the final numbered
step in the corrected Action section rather than dropped. No other section of the file (Usage, Input,
Pipeline, Notes) was touched, and no other file was modified. Verified via `git diff --stat` that only
this one file changed and via `git diff` that the hunk is confined to the Action section.

## Test Summary
Documentation-only change; no pytest applies. Verified by manual diff: `git diff .claude/skills/create-tickets/SKILL.md`
shows the Action section now matches the structural/phrasing convention of `implement-ticket/SKILL.md`
and `implement-epic/SKILL.md` ("Do not call the Workflow tool — it is not available. Execute the workflow
directly: ..." followed by a numbered JS-translation table), and that the Pipeline/Usage/Input/Notes
sections are byte-identical to before (diff shows only the Action section hunk).

## Files Changed
- `.claude/skills/create-tickets/SKILL.md`

## Completion Summary
Fixed the stale two-path (Workflow-tool-first, inline-fallback) Action section in
`create-tickets/SKILL.md` so it now flatly states the Workflow tool is unavailable and directs the agent
straight to inline JS-to-tool-call execution, consistent with its sibling skills. The Investigate-phase
"do not skip or abbreviate" instruction was preserved. All three ticket-workflow skills
(`create-tickets`, `implement-ticket`, `implement-epic`) now describe the same single execution model.
