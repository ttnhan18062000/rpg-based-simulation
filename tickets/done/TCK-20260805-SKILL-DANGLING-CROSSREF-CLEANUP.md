---
status: historical
layer: ai
authority: P2
audience: agent
ticket_id: TCK-20260805-SKILL-DANGLING-CROSSREF-CLEANUP
phase: done
date: 2026-08-05
tags: [skills, workflows]
---

# TCK-20260805-SKILL-DANGLING-CROSSREF-CLEANUP

## Title
Reconcile dangling cross-references in frontend-design, doc-coauthoring, brainstorming

## Status
DONE

## Tier
hotfix

## Type
bug

## Priority
P2

## Request Summary
Child ticket #7 of `TCK-20260804-SKILL-CATALOG-MODERNIZATION-EPIC`. `frontend-design`,
`doc-coauthoring`, and `brainstorming` reference sibling first-party-style conventions (a
`spec-document-reviewer` subagent, a `writing-plans` skill) that do not exist as actual
files/agents in this repo — reading as copied from an Anthropic example skill set rather than a
third-party community pack. Distinct remediation shape from the community-swap tickets: not "swap
for a popular alternative," but "remove or correct references to skills/agents this repo doesn't
actually have."

## Scope
- Locate every dangling reference in the 3 named skills.
- For each: either remove the reference, or replace it with the actual in-repo equivalent if one
  exists (e.g. `brainstorming`'s reference to a spec-review step might map to this repo's own
  `architecture-reviewer` agent or the mandatory investigation.md/plan.md staging gate).

## Out of Scope
- `architecture`'s dangling `@[skills/...]` references — different remediation category
  (disclosed-community swap), covered by `TCK-20260805-COMMUNITY-SKILL-SWAP-DISCLOSED`.
- Reopening the `frontend-design` trigger-exclusion question — separate scope, covered by
  `TCK-20260805-FRONTEND-DESIGN-TRIGGER-REOPEN`. This ticket only cleans up dangling text
  references, regardless of whether the trigger question is later reopened.

## Acceptance Criteria
- [x] Every located dangling reference in the 3 skills is either removed or correctly repointed
      (only `brainstorming/SKILL.md` had any — `frontend-design` and `doc-coauthoring` were
      verified clean and left untouched; see Implementation Notes).
- [x] No other content in the 3 SKILL.md files modified.

## Related Tickets
- TCK-20260804-SKILL-CATALOG-MODERNIZATION-EPIC (parent epic)
- TCK-20260805-COMMUNITY-SKILL-SWAP-DISCLOSED (different remediation category, kept separate)
- TCK-20260805-FRONTEND-DESIGN-TRIGGER-REOPEN (separate scope, no dependency)

## Related Docs
None new.

## Related Stored Artifacts
None (hotfix tier).

## Related Code Areas
- `.claude/skills/frontend-design/SKILL.md`
- `.claude/skills/doc-coauthoring/SKILL.md`
- `.claude/skills/brainstorming/SKILL.md`

## Assumptions / Open Questions
None — self-evident cleanup once each dangling reference is located.

## Implementation Notes
Re-verified the ticket's own premise before touching anything (per this session's discipline of
not trusting an inherited framing without re-checking it against the real files). Findings:
- `.claude/skills/frontend-design/SKILL.md` — read in full. **No dangling references at all** —
  it's a fully self-contained aesthetic-guidance skill with zero mentions of any sibling
  skill/agent. The ticket's original premise about this file was wrong.
- `.claude/skills/doc-coauthoring/SKILL.md` — read in full. **No dangling skill/agent references.**
  It does reference generic Claude.ai-style tool names (`create_file`, `str_replace`) that don't
  match this environment's actual tool names (Artifact/Write/Edit) — a different staleness class
  (tool-name mismatch, not "reference to a nonexistent skill/agent") and out of this ticket's
  scope; not touched.
- `.claude/skills/brainstorming/SKILL.md` — **genuine dangling references found and fixed**:
  - `writing-plans` skill (5 occurrences, including "the ONLY skill you invoke after
    brainstorming") — does not exist anywhere in `.claude/skills/`. Replaced every occurrence with
    the actual in-repo equivalent: `/create-tickets` (which produces investigation-backed tickets)
    followed by `/implement-ticket`'s own Plan phase (step 3 of that pipeline), since this repo
    has no separate planning skill.
  - `mcp-builder` skill (1 occurrence, in a "do NOT invoke X" list) — also does not exist in this
    repo; removed from the list rather than replaced (nothing to repoint it to).
  - `elements-of-style:writing-clearly-and-concisely` skill (1 occurrence, "if available" hedge)
    — plugin-style reference with no in-repo equivalent; removed per Scope's "remove or replace
    with actual in-repo equivalent if one exists" (none exists here).
  - `spec-document-reviewer` (2 occurrences) — investigated and confirmed **NOT actually
    dangling**: it's a self-contained generic-agent dispatch (`Agent(prompt: ...)`, no
    `subagent_type` required) backed by a real, present local template file
    (`spec-document-reviewer-prompt.md`, in the same skill directory) — matches this repo's own
    established `agent(prompt, {label: 'L'})` pattern from `implement-ticket.js`. Left unchanged.

## Test Summary
No pytest applies (pure prose). Verification: `grep -n "writing-plans\|mcp-builder\|elements-of-style"
.claude/skills/brainstorming/SKILL.md` after the edit returns only the corrective sentences that
now explicitly state these skills don't exist — zero remaining dangling invocations. Manually
re-read the full edited file to confirm the dot-diagram node name change (`"Invoke writing-plans
skill"` → `"Invoke /create-tickets"`) is consistent between its declaration and its one inbound
edge (both updated). Confirmed `frontend-design` and `doc-coauthoring` genuinely needed no edits
by reading each in full before deciding not to touch them.

## Files Changed
- `.claude/skills/brainstorming/SKILL.md` — replaced all `writing-plans` references with the real
  in-repo `/create-tickets` → `/implement-ticket` Plan-phase path; removed the nonexistent
  `mcp-builder` and `elements-of-style:...` mentions.

## Parity
`expected_subsystems_for_files(['.claude/skills/brainstorming/SKILL.md'])` → `{}` (no `src/` path).
No parity ledger entry needed — pure agent-instruction prose, same precedent as ticket #1.

## Completion Summary
Fixed the one file that actually had dangling references (`brainstorming/SKILL.md`) rather than
mechanically touching all 3 named files — `frontend-design` and `doc-coauthoring` were
investigated and found clean, and are explicitly documented as such above so this finding isn't
silently lost. All `writing-plans`/`mcp-builder`/`elements-of-style` references removed or
repointed to this repo's real `/create-tickets` → `/implement-ticket` flow.
`spec-document-reviewer` was investigated and confirmed to be a legitimate self-contained
generic-agent dispatch, not a dangling reference — left untouched. Static verification (grep +
full re-read) confirms no dangling references remain in the touched file.
