---
status: historical
layer: strategy
authority: P1
audience: agent
ticket_id: TCK-20260810-COGNITION-STRATEGY-SKILL-BYPASS-SYNC
phase: done
date: 2026-08-10
tags: [cognition, strategy]
---

# TCK-20260810-COGNITION-STRATEGY-SKILL-BYPASS-SYNC

## Title
Sync `.claude/skills/cognition-strategy/SKILL.md` (and its `.agents/` mirror) with the
generalized interruption-bypass rule landed in `docs/mechanics/04_strategic_cognition.md` §2

## Status
DONE

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
- [x] `.claude/skills/cognition-strategy/SKILL.md`'s bypass-rule sentence matches the real landed
      rule (detour = sole exemption from the lock's added floor/percentage gate; base
      `effective_current_score` comparison still applies to detour too), not the stale "score > 80"
      framing
- [x] `.agents/skills/cognition-strategy/SKILL.md` receives the same fix
- [x] `tests/tools/test_cognition_strategy_skill_content.py` still passes — 8/8 passed, including
      `test_agents_mirror_body_matches_claude_source` (confirms both files' bodies stayed identical
      after the edit)

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

Read `docs/mechanics/04_strategic_cognition.md` §2 directly at Implement time rather than
paraphrasing this ticket's own Request Summary (per the ticket's own explicit instruction) — the
doc has evolved further since this ticket was filed, now also covering
`TCK-20260811-INTERRUPTION-BYPASS-RETENTION-MARGIN-SCALE-BUG`,
`TCK-20260811-SOCIAL-CONTRACT-GOAL-SCORER`, and `TCK-20260811-THREAT-RESOLVED-ARBITER-RELOCATION`.
The corrected SKILL.md sentence paraphrases only the core Generalized Bypass rule (detour's sole
exemption + the dual-condition gate for every other candidate), matching this ticket's own AC
wording, and cross-references the doc for the fuller derivation rather than inlining the doc's
entire, now-longer explanation into the skill file's terse style.

Confirmed `.claude/skills/cognition-strategy/SKILL.md` and `.agents/skills/cognition-strategy/
SKILL.md` are byte-identical in body (only frontmatter legitimately differs — `.claude/` uses
`description`/`source`/`date_added`, `.agents/` uses a single `description` field, a pre-existing,
out-of-scope convention difference per this ticket's own Out of Scope) before editing, confirmed
via direct diff. Applied the identical corrected sentence to both files' bodies.

Grepped the full repo (`docs/`, `.claude/`, `.agents/`, excluding `docs/archive/`) for any other
citation of the stale "Danger concerns scoring > 80" / "Emergency Bypass" framing — zero hits
remain anywhere outside the frozen archive copy.

## Test Summary

`pytest tests/tools/test_cognition_strategy_skill_content.py -v -m "not slow"` → 8 passed, including
`test_agents_mirror_body_matches_claude_source` (confirms the two files' bodies are still identical
post-edit).

## Files Changed

- `.claude/skills/cognition-strategy/SKILL.md` — replaced the stale "Emergency bypass: Danger
  concerns scoring > 80 ignore the interruption margin entirely" sentence with the real, generalized
  bypass rule (detour's sole exemption from the added floor/percentage gate; every other candidate's
  dual-condition gate), cross-referencing `docs/mechanics/04_strategic_cognition.md` §2.
- `.agents/skills/cognition-strategy/SKILL.md` — identical body fix.

## Completion Summary

Synced both `cognition-strategy` SKILL.md copies with the real, generalized interruption-bypass rule
already landed in `docs/mechanics/04_strategic_cognition.md` §2, closing a documentation-parity gap
deliberately deferred by `TCK-20260810-COGNITION-ELIGIBILITY-BYPASS-DOCS`. Both files' bodies
confirmed byte-identical before and after the edit (frontmatter difference is pre-existing and
out of scope). No source code touched — pure doc-mirror sync, per the ticket's own Out of Scope.
