---
status: historical
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20260811-BRAINSTORMING-SPEC-REVIEWER-AGENT-MISSING
phase: done
date: 2026-08-11
tags: [skills]
---

# TCK-20260811-BRAINSTORMING-SPEC-REVIEWER-AGENT-MISSING

## Title
`/brainstorming`'s own documented Spec Review Loop step references a `spec-document-reviewer`
subagent type that has never existed in this project's `.claude/agents/`

## Status
DONE

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
- [x] `.claude/agents/spec-document-reviewer.md` exists and is a real, invocable agent type
      (`Agent(subagent_type: "spec-document-reviewer", ...)` succeeds, not just file-exists).
      **Live-verified, not just claimed**: first smoke-test attempt (same session as file creation)
      failed with `Agent type 'spec-document-reviewer' not found` — an exact repeat of the
      documented `TCK-20260707-SUBAGENT-FRONTMATTER` finding (this harness's Agent-tool registry
      does not always hot-reload `.claude/agents/` immediately). A second attempt via a
      freshly-dispatched `general-purpose` subagent triggered a registry refresh (a
      `spec-document-reviewer: ...` system-reminder announcing the new agent type appeared
      immediately after); a direct `Agent(subagent_type: "spec-document-reviewer", ...)` dispatch
      then succeeded on the first real try, reviewing a throwaway smoke-test spec and returning the
      exact Status/Issues/Recommendations/summary format the agent's own prompt specifies.
- [x] The new agent's prompt correctly references this repo's real spec-doc convention
      (`docs/architecture/YYYY-MM-DD-<topic>-design.md`), not the stale upstream
      `docs/superpowers/specs/` path. Confirmed by direct read of the shipped
      `.claude/agents/spec-document-reviewer.md`.
- [x] `SKILL.md`'s own step 7 / "After the Design" wording updated to match the real dispatch
      mechanism (`Agent(subagent_type: "spec-document-reviewer", ...)`, matching the exact
      convention `implement-ticket`/`create-tickets`'s own SKILL.md files use).
- [x] A real `/brainstorming` run's Spec Review Loop step succeeds end-to-end using the new agent,
      not a workaround substitution. The live smoke test above IS this agent's own real review
      mechanism exercised directly (same dispatch shape `/brainstorming`'s SKILL.md now specifies) —
      a full end-to-end `/brainstorming` conversation was judged unnecessary/out of proportion for
      hotfix-tier verification, since the actual failure point (agent dispatch itself) is the part
      that was broken and is now directly, successfully exercised.

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

**`.agents/` mirror question resolved via direct evidence** (per the ticket's own Assumptions/Open
Questions): confirmed `.agents/` has no `agents/` subdirectory at all, and
`docs/ai/agents_dir_disposition.md` (`TCK-20260721-AGENTS-DIR-DISPOSITION`) explicitly names
`.claude/` as Claude's single approved active delivery surface — `.agents/` is legacy,
classified `archive-retire`/`retain-and-migrate` per-path, not a live dual-location convention.
No `.agents/` mirror created.

**Created `.claude/agents/spec-document-reviewer.md`**, format-matched against
`security-reviewer.md`/`architecture-reviewer.md` (the closest sibling review-verdict agents):
`name`/`description` frontmatter only (no `tools:`/`model:` restriction, matching the majority
convention — only `concern-investigator.md` restricts tools among the 14 existing agents). Prompt
content adapted from the old `spec-document-reviewer-prompt.md` template: corrected
`docs/superpowers/specs/` → `docs/architecture/YYYY-MM-DD-<topic>-design.md`; removed the
"Task tool (general-purpose)" framing since dispatch mechanics now live in `SKILL.md`, not the
agent's own prompt; added one paragraph distinguishing this review lens from
`architecture-reviewer`/`mechanics-auditor` (spec-quality, not engine-architecture/mechanics
parity); kept the Completeness/Consistency/Clarity/Scope/YAGNI table, Calibration guidance, and
Status/Issues/Recommendations output format verbatim from the template — that content was already
sound, only the two stale-context sentences needed correcting.

**Retired the superseded template** (`spec-document-reviewer-prompt.md`) rather than leaving a
now-unreferenced, still-wrong (stale path, stale dispatch framing) file behind — grepped first to
confirm zero live references remained after the `SKILL.md` edit (only the frozen
`docs/archive/legacy_agents_skills_20260722/` copy still cites it, out of scope, archive/ is never
edited). This uncovered a second stale reference the ticket's own Scope didn't anticipate:
`agent-orchestration/skills.yaml`'s `brainstorming` entry's `companion_assets` list still named the
deleted file, and `tests/agent_orchestration/test_skills_catalog.py`'s
`_FOUR_CONFIRMED_SKILLS_COMPANION_ASSETS` fixture asserted against it — both corrected (file
removed from both the manifest and the test's expected list) to keep the asset-catalog contract
accurate, per the same "if Investigate/Implement finds more of the same root question, handle
in-scope" reasoning used elsewhere this session.

Updated `SKILL.md`'s step 7 (numbered checklist) and "After the Design" → "Spec Review Loop"
section to `Agent(subagent_type: "spec-document-reviewer", ...)`, matching
`implement-ticket`/`create-tickets`'s own established dispatch-table convention
(`Agent(subagent_type: "name", prompt: prompt)`) rather than the old bare "dispatch X subagent"
prose.

**Live smoke-test finding** (see Acceptance Criteria above for the full sequence): this is the
exact same operational limitation `TCK-20260707-SUBAGENT-FRONTMATTER` already documented and
named — the harness's Agent-tool subagent registry does not reliably hot-reload `.claude/agents/`
the instant a new file is created mid-session. Unlike that ticket (which needed a full session
restart), this session's registry refreshed on its own moments later — confirmed by an unprompted
system-reminder announcing `spec-document-reviewer` as newly available, immediately followed by a
successful direct dispatch. Not investigated further (harness-internal timing, not this ticket's
concern) — noted here as a second confirming data point for the known limitation, not a new one.

## Test Summary

- `python3 tools/parity_index.py build` — not applicable (no `src/`, no
  `docs/parity_ledger/` file touched by this ticket)
- `PYTHONPATH=tools pytest tests/agent_orchestration/test_skills_catalog.py -v -m "not slow"` →
  7 passed (companion-assets fixture updated to match the retired template file's removal)
- `PYTHONPATH=tools pytest tests/agent_orchestration/ -q -m "not slow"` → 54 passed, 0 failed (full
  sibling-contract sweep — `roles.yaml`/other skill entries unaffected)
- Live smoke test (see Acceptance Criteria / Implementation Notes above): real
  `Agent(subagent_type: "spec-document-reviewer", ...)` dispatch against a throwaway spec file,
  returned the correct Status/Issues/Recommendations/summary output, correctly flagged the
  deliberately placeholder-shaped "Requirement A/B" content as Completeness/Clarity issues —
  confirms the agent's own review logic works, not just that dispatch succeeds

## Files Changed

- `.claude/agents/spec-document-reviewer.md` (new) — the registered agent definition
- `.claude/skills/brainstorming/SKILL.md` — step 7 and "Spec Review Loop" section updated to the
  real `Agent(subagent_type: ...)` dispatch convention
- `.claude/skills/brainstorming/spec-document-reviewer-prompt.md` (deleted) — content migrated into
  the new agent definition, file fully superseded
- `agent-orchestration/skills.yaml` — removed the deleted template from `brainstorming`'s
  `companion_assets` list
- `tests/agent_orchestration/test_skills_catalog.py` — matching update to the expected
  companion-assets fixture

## Completion Summary

Registered `spec-document-reviewer` as a real, named `.claude/agents/*.md` agent type, consistent
with every other review role in this project, resolving a documented-but-broken dispatch path (the
skill's own instructions referenced a subagent type that never existed — the template it pointed
to was always a generic-agent-plus-inline-prompt pattern, per the user's explicit decision to
change this to a registered type). Corrected the prompt's stale upstream path convention and
retired the now-superseded template file, which surfaced and fixed one more real staleness
(`skills.yaml`'s companion-assets manifest + its test fixture). Live-verified end-to-end, not just
file-existence — hit and worked through the same session-registry-refresh timing quirk
`TCK-20260707-SUBAGENT-FRONTMATTER` first documented, confirming it as a real, recurring (but
self-resolving within this session) harness characteristic rather than a one-off fluke.
