---
status: historical
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20260805-SKILLS-DOC-STALENESS-FIX
phase: done
date: 2026-08-05
tags: [skills, workflows, process-improvement]
---

# TCK-20260805-SKILLS-DOC-STALENESS-FIX

## Title
Fix docs/ai/skills.md's stale "Tag-Based Skill Suggestions" section (predates the security hard-gate and mapping dedup)

## Status
DONE

## Tier
hotfix

## Type
bug

## Priority
P1

## Request Summary
Child ticket #3 of `TCK-20260804-SKILL-CATALOG-MODERNIZATION-EPIC`'s child-ticket breakdown
(`stored_artifacts/TCK-20260804-SKILL-CATALOG-MODERNIZATION-EPIC/plan.md` Step 3). The epic's own
Investigate phase found `docs/ai/skills.md:39-47`'s "Tag-Based Skill Suggestions" section still
describes the `suggested_skills` mechanism as purely advisory, with no mention of:
1. The `security` tag's hard-gate exception (`TCK-20260705-WORKFLOW-SECURITY-GATE`) — `security` is
   no longer purely advisory; it's a binding `implement-ticket.js` `Security-Review` phase gate.
2. The live single-source mapping mechanism (`TCK-20260720-SKILL-MAPPING-DEDUP`) — the tag→skill
   mapping is no longer a hand-copied table; it's a `triggers_skill` field on `tag_registry.jsonl`
   rows, read live via `tools/tag_registry.py::get_skill_mapping()` / the `skill-mapping` CLI
   subcommand.

Both mechanisms postdate this doc's last edit and are unreflected. Filed and fixed now (ahead of a
broader documentation-plus-graphify refresh and a subsequent domain-coverage sweep) specifically so
the upcoming sweep doesn't rely on a doc describing a mechanism that no longer matches reality.

## Scope
- Correct `docs/ai/skills.md:39-47`'s "Tag-Based Skill Suggestions" section to state: (a) `security`
  is now a binding gate, not advisory, citing `WORKFLOW-SECURITY-GATE`; (b) the mapping is
  single-sourced via `tag_registry.jsonl`'s `triggers_skill` field, read via
  `tools/tag_registry.py::get_skill_mapping()`, citing `SKILL-MAPPING-DEDUP` — not a hand-copied
  table.
- This is a factual correction of current state only — no change to the actual mechanism.

## Out of Scope
- Any change to `tools/tag_registry.py`, `implement-ticket.js`'s gate logic, or
  `docs/guides/ticket_tagging.md` — those already exist and are correct; this ticket only fixes
  `docs/ai/skills.md`'s description of them.
- Any decision from epic child ticket #4 (gate-conversion for api-design/debugging/performance) —
  unrelated, not yet decided.

## Acceptance Criteria
- [ ] `docs/ai/skills.md`'s "Tag-Based Skill Suggestions" section accurately describes the
      `security` hard-gate exception, citing `WORKFLOW-SECURITY-GATE`.
- [ ] The same section accurately describes the single-source `tag_registry.jsonl` mapping
      mechanism, citing `SKILL-MAPPING-DEDUP`, rather than implying a hand-copied table.
- [ ] No other content in `docs/ai/skills.md` is modified.

## Related Tickets
- TCK-20260804-SKILL-CATALOG-MODERNIZATION-EPIC (parent epic)
- TCK-20260705-WORKFLOW-SECURITY-GATE (the mechanism this fix describes)
- TCK-20260720-SKILL-MAPPING-DEDUP (the mechanism this fix describes)

## Related Docs
- `docs/ai/skills.md` (edit target)
- `docs/guides/ticket_tagging.md` (read-only reference — already accurate)

## Related Stored Artifacts
None (hotfix tier).

## Related Code Areas
- `docs/ai/skills.md`

## Assumptions / Open Questions
None — self-evident fix, source of truth (the two cited prior tickets' shipped mechanisms) is unambiguous.

## Implementation Notes
Added two new paragraphs to `docs/ai/skills.md`'s "Tag-Based Skill Suggestions" section (after the
existing paragraph, unchanged): (1) states the mapping is single-sourced via `tag_registry.jsonl`'s
`triggers_skill` field, read via `tools/tag_registry.py::get_skill_mapping()`/the `skill-mapping`
CLI, citing `SKILL-MAPPING-DEDUP`, listing all 4 real consumers; (2) states `security` is the one
tag that's no longer advisory-only — it's a mandatory `implement-ticket.js` `Security-Review` gate
that can produce `SECURITY_BLOCKED`, citing `WORKFLOW-SECURITY-GATE`. Verified both citations
directly against `tools/tag_registry.py:199-238` (`add_tag(..., triggers_skill=...)`) and
`implement-ticket.js:1233-1234` (`tags.includes('security') || suggested_skills.includes(...)`)
before writing. No other content in the file was touched.

## Test Summary
No pytest applies (pure prose doc change). Verified via direct grep that both cited API names
(`get_skill_mapping`, `triggers_skill`, `add_tag`) and the gate trigger condition match the real,
current source exactly — not paraphrased/assumed. Ran
`python3 tools/validate_frontmatter.py docs/ai/skills.md` — passes.

## Files Changed
- `docs/ai/skills.md` — added 2 paragraphs to "Tag-Based Skill Suggestions" section.

## Completion Summary
Fixed `docs/ai/skills.md`'s "Tag-Based Skill Suggestions" section, stale since before the
`security` hard-gate and the tag-registry mapping dedup shipped in July. Added 2 accurate
paragraphs: the mapping is single-sourced via `tag_registry.jsonl`'s `triggers_skill` field, and
`security` (unlike the other 3 mapped tags) is now a binding `Security-Review` gate, not advisory.
Filed and fixed specifically as prep work — child ticket #3 of
`TCK-20260804-SKILL-CATALOG-MODERNIZATION-EPIC` — ahead of a documentation-and-graphify refresh and
a broader domain-coverage sweep, so that sweep doesn't rely on a doc describing a mechanism that no
longer matches reality. Both new paragraphs independently re-verified against real source
(`tools/tag_registry.py:199-260`, `implement-ticket.js:1227-1272`) twice — once during Implement,
once during Verify. Hotfix pipeline: Scope → Implement → doc-staleness gate (PASS) → Test
(validate_frontmatter PASS) → Verify (READY TO CLOSE, 13/13) → Finalize.
