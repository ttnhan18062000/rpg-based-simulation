---
status: active
layer: strategy
authority: P1
audience: agent
ticket_id: TCK-20260810-COGNITION-STRATEGY-SKILL-BYPASS-SYNC
phase: open
date: 2026-08-10
tags: [cognition, strategy]
---

# TCK-20260810-COGNITION-STRATEGY-SKILL-BYPASS-SYNC

## Title
Sync `.claude/skills/cognition-strategy/SKILL.md` (and its `.agents/` mirror) with the
generalized interruption-bypass rule landed in `docs/mechanics/04_strategic_cognition.md` §2

## Status
OPEN

## Tier
hotfix

## Type
chore

## Priority
P2

## Request Summary
`TCK-20260810-COGNITION-ELIGIBILITY-BYPASS-DOCS` rewrote `docs/mechanics/04_strategic_cognition.md`
§2's stale "Emergency Bypass: High-urgency 'Danger' concerns (score > 80) ignore the interruption
margin" line to describe the real, generalized dual-condition bypass rule landed in
`TCK-20260810-PROJECT-SWITCH-BYPASS-GENERALIZATION` (`src/systems/strategic_systems/
intelligence.py:978-1004`: `"detour"` is the sole candidate exempt from the lock's added
normalized floor/percentage gate; every other candidate must additionally clear a normalized
score/urgency-floor check while a lock is active, on top of the base
`effective_current_score` comparison that has always applied to every candidate including detour).

That doc-parity ticket's own investigation confirmed `.claude/skills/cognition-strategy/SKILL.md`
and its `.agents/skills/cognition-strategy/SKILL.md` mirror both still contain the same stale
"Danger concerns scoring > 80 ignore the interruption margin entirely" sentence (near line 70-73 in
both files) — deliberately left untouched by that ticket (undeclared scope expansion; neither file
was named in that ticket's own Scope/Related Docs). `tests/tools/test_cognition_strategy_skill_content.py`
does not pin this specific sentence, so nothing currently forces the fix, but the two skill docs and
the Mechanics Bible now describe different bypass rules — a real residual documentation-parity gap.

## Scope
- Update `.claude/skills/cognition-strategy/SKILL.md`'s stale bypass sentence (near line 70-73) to
  describe the generalized rule, matching `docs/mechanics/04_strategic_cognition.md` §2's landed
  prose (read directly at Implement time — do not paraphrase from this ticket's own summary above,
  which may drift from the doc by the time this ticket is picked up)
- Apply the identical fix to `.agents/skills/cognition-strategy/SKILL.md` (confirm at Implement time
  whether it is a literal mirror of the `.claude/` copy or has diverged; if diverged, sync content
  intent, not necessarily byte-identical text)
- Confirm `tests/tools/test_cognition_strategy_skill_content.py` still passes after the edit (it does
  not currently pin the bypass sentence, so this should be a no-op verification, not a required
  code change to the test)

## Out of Scope
- Any further code change to `src/systems/strategic_systems/intelligence.py` or
  `src/domains/adventure/` — this is a pure doc-mirror sync, downstream of already-landed code
- Re-litigating or rewriting any other part of either SKILL.md file

## Acceptance Criteria
- [ ] `.claude/skills/cognition-strategy/SKILL.md`'s bypass-rule sentence matches the real landed
      rule (detour = sole exemption from the lock's added floor/percentage gate; base
      `effective_current_score` comparison still applies to detour too), not the stale "score > 80"
      framing
- [ ] `.agents/skills/cognition-strategy/SKILL.md` receives the same fix
- [ ] `tests/tools/test_cognition_strategy_skill_content.py` still passes

## Related Tickets
- TCK-20260810-COGNITION-ELIGIBILITY-BYPASS-DOCS (the ticket that found and deliberately deferred
  this gap, rather than silently dropping it)
- TCK-20260810-PROJECT-SWITCH-BYPASS-GENERALIZATION (the ticket that landed the real bypass rule)

## Related Docs
- docs/mechanics/04_strategic_cognition.md (§2 — the authoritative source this sync must match)
- .claude/skills/cognition-strategy/SKILL.md
- .agents/skills/cognition-strategy/SKILL.md

## Related Stored Artifacts
- stored_artifacts/TCK-20260810-COGNITION-ELIGIBILITY-BYPASS-DOCS/investigation.md (documents the
  original finding of this gap in its Risks and Open Questions section)

## Related Code Areas
- src/systems/strategic_systems/intelligence.py (the rule this doc must accurately describe)

## Assumptions / Open Questions
- Whether `.claude/skills/` and `.agents/skills/` are meant to always stay byte-identical mirrors or
  can diverge in wording while matching in substance — not assumed; confirm repo convention at
  Implement time by diffing a few other skill files across both directories

## Implementation Notes
(filled during Implement)

## Test Summary
(filled during Test)

## Files Changed
(filled during Finalize)

## Completion Summary
(filled during Finalize)
