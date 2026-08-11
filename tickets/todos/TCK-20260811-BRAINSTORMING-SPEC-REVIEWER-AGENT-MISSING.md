---
status: active
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20260811-BRAINSTORMING-SPEC-REVIEWER-AGENT-MISSING
phase: open
date: 2026-08-11
tags: [skills]
---

# TCK-20260811-BRAINSTORMING-SPEC-REVIEWER-AGENT-MISSING

## Title
`/brainstorming`'s own documented Spec Review Loop step references a `spec-document-reviewer`
subagent type that has never existed in this project's `.claude/agents/`

## Status
OPEN

## Tier
hotfix

## Type
bug

## Priority
P1

## Request Summary
Found while running `/brainstorming` this session for an adventure/cognition-strategy merge design.
`SKILL.md`'s own step 7 ("Spec review loop") and its "After the Design" section both instruct:
"Dispatch spec-document-reviewer subagent (see spec-document-reviewer-prompt.md)." Attempting this
literally (`Agent(subagent_type: "spec-document-reviewer", ...)`) fails with `Agent type
'spec-document-reviewer' not found` — confirmed this session, not a one-off fluke.

Root-caused directly, not assumed: `.claude/skills/brainstorming/spec-document-reviewer-prompt.md`
(and its `.agents/` mirror, confirmed byte-identical) is a real, detailed prompt TEMPLATE — but its
own content reveals the original design was never a distinct named agent type at all. The template's
own header states `**Dispatch after:** Spec document is written to docs/superpowers/specs/` (an
upstream generic-skill-library path convention, not this repo's real
`docs/architecture/YYYY-MM-DD-<topic>-design.md` convention) and its own dispatch instructions read
`Task tool (general-purpose): description: "Review spec document"` — i.e., the intended mechanism
was always "dispatch the generic `general-purpose` agent type, using this template's content as its
full prompt," not a dedicated registered agent. `git log --all -- .claude/agents/spec-document-reviewer.md`
returns zero history — no such file was ever created or deleted; the gap has existed since this
skill was adopted into this repo, not a recent regression.

This session worked around it once by substituting `architecture-reviewer` (this repo's own
established, real review agent) for the spec-review step — functionally adequate for that one
instance, but not a fix, since `architecture-reviewer`'s own definition is scoped to
durable-state/API-boundary/Mechanics-Bible verification, not spec completeness/consistency/scope/
YAGNI checking, which is a different, real review lens the prompt template was specifically written
for.

**User decision (already made, not open for reconsideration):** register a real, named
`spec-document-reviewer` agent, consistent with how every other review role in this project
(`architecture-reviewer`, `doc-updater`, `done-checker`, `mechanics-auditor`, `security-reviewer`)
is a registered, reusable, named agent type — not the ad-hoc general-purpose+inline-prompt pattern
the original upstream template used.

## Scope
- Create `.claude/agents/spec-document-reviewer.md` (and its `.agents/` mirror, if this repo's own
  dual-location convention for agent definitions requires one — confirm the real convention by
  checking how the other 13 existing agents in `.claude/agents/` are mirrored, or not, before
  assuming)
- Adapt the existing prompt template's content (`.claude/skills/brainstorming/spec-document-reviewer-prompt.md`)
  as the new agent's system prompt — correcting its own stale `docs/superpowers/specs/` reference to
  this repo's real `docs/architecture/YYYY-MM-DD-<topic>-design.md` convention, and its stale
  "Task tool (general-purpose)" framing (no longer applicable once this becomes a named type)
- Update `.claude/skills/brainstorming/SKILL.md`'s own step 7 and "After the Design" section wording
  to correctly reference dispatching the new named agent type, matching this project's own
  established `Agent(subagent_type: "...")` dispatch convention used by every other skill
  (`implement-ticket`, `create-tickets`, etc.)
- Verify the new agent actually gets picked up (confirm `Agent(subagent_type: "spec-document-reviewer", ...)`
  succeeds, not just that the file exists)

## Out of Scope
- Any change to `architecture-reviewer`'s own definition — it correctly served as a substitute this
  session but is not being repurposed or merged with the new agent
- Any change to the brainstorming skill's other steps (visual companion, clarifying-questions flow,
  create-tickets handoff) — confirmed unaffected by this gap

## Acceptance Criteria
- [ ] `.claude/agents/spec-document-reviewer.md` exists and is a real, invocable agent type
      (`Agent(subagent_type: "spec-document-reviewer", ...)` succeeds, not just file-exists)
- [ ] The new agent's prompt correctly references this repo's real spec-doc convention
      (`docs/architecture/YYYY-MM-DD-<topic>-design.md`), not the stale upstream
      `docs/superpowers/specs/` path
- [ ] `SKILL.md`'s own step 7 / "After the Design" wording updated to match the real dispatch
      mechanism
- [ ] A real `/brainstorming` run's Spec Review Loop step succeeds end-to-end using the new agent,
      not a workaround substitution

## Related Tickets
None yet.

## Related Docs
- .claude/skills/brainstorming/SKILL.md
- .claude/skills/brainstorming/spec-document-reviewer-prompt.md

## Related Stored Artifacts
None.

## Related Code Areas
- .claude/agents/ (existing 13 agent definitions, for convention precedent)
- .claude/skills/brainstorming/

## Assumptions / Open Questions
- Whether `.claude/agents/` definitions need a `.agents/` mirror copy (like skills apparently do,
  per the `.agents/skills/brainstorming/spec-document-reviewer-prompt.md` mirror found this
  session) — not confirmed, check real convention before assuming either way at Implement time

## Implementation Notes

## Test Summary

## Files Changed

## Completion Summary
