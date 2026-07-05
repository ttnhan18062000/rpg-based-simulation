---
status: active
layer: guidelines
authority: P1
audience: agent
ticket_id: TCK-20260705-SIX-SKILLS-INVESTIGATION
phase: open
date: 2026-07-05
tags: [skills, process-improvement, investigation]
---

# TCK-20260705-SIX-SKILLS-INVESTIGATION

## Title
Investigate whether the 6 deferred zero-invocation skills are genuine gaps or correctly redundant

## Status
OPEN

## Tier
standard

## Type
chore

## Priority
P2

## Request Summary
`TCK-20260704-SKILL-TRIGGER-COVERAGE` wired 3 skills (`api-design-principles`, `debugging-strategies`/`world-debugger`, `python-performance-optimization`) into `CLAUDE.md`'s auto-invoke table based on confirmed applicable-work-but-zero-invocation evidence. It explicitly left 6 more skills as an open, undecided question: `test-driven-development`, `python-testing-patterns`, `backend-testing`, `architecture` (ADR workflow), `brainstorming`, `doc-coauthoring` — all show zero invocations despite real applicable-looking activity (281 test-file edits, 9 `docs/architecture/` edits, 659 `docs/` edits overall at the time), but `CLAUDE.md` already has its own "Testing Rule" and "Architecture Rule" sections that may substantively cover the same ground, and most `docs/` writes are ticket-workflow-internal rather than the free-form proposal/spec writing `doc-coauthoring` targets. That ticket's own words: "Whether these six represent a genuine additional gap or correct-by-design redundancy is an open question, not decided here — left for a follow-on investigation rather than assumed."

**Important sequencing note (user decision, 2026-07-05):** `tickets/todos/tag-taxonomy-followups/TCK-20260705-TAG-SKILL-SUGGEST.md` is building a *tag-based* skill-suggestion mechanism (a ticket tagged `performance`/`debugging`/`api-design` surfaces the matching skill at scope time), as a second, complementary lane to `SKILL-TRIGGER-COVERAGE`'s *file-path-based* `CLAUDE.md` table mechanism. If this investigation confirms any of the 6 skills are genuine gaps, **the actual wiring/implementation should wait until `TCK-20260705-TAG-SKILL-SUGGEST` lands**, so newly-confirmed gaps get wired through the more general, reusable tag-based mechanism rather than a third, redundant one-off `CLAUDE.md` table addition that duplicates work `TAG-SKILL-SUGGEST` will already do more generally.

## Scope
- Repeat `SKILL-TRIGGER-COVERAGE`'s original investigation methodology (grep recent session transcripts for actual file/command activity matching each of the 6 skills' domain; cross-reference against `Skill` tool invocation counts) with a **fresh, current sample** — more sessions and more work have happened since the original count.
- For each of the 6 skills, produce a verdict: **genuine gap** (real applicable work found, zero invocation, not covered by an existing `CLAUDE.md` rule) or **correctly redundant** (covered by an existing rule/section, or no applicable work actually occurred).
- Specifically resolve the two open ambiguities the original ticket flagged: (a) whether `CLAUDE.md`'s "Testing Rule" and "Architecture Rule" sections substantively cover what `test-driven-development`/`python-testing-patterns`/`backend-testing`/`architecture` would add, or whether they're a different kind of guidance (e.g. rules-as-constraints vs. skills-as-workflow-scaffolding) that doesn't actually overlap; (b) whether the 659 `docs/` edits are genuinely ticket-workflow-internal (as assumed) or whether some meaningful fraction is free-form proposal/spec writing that `doc-coauthoring` would actually help with.
- **Do not wire any confirmed gap into `CLAUDE.md` or any other mechanism in this ticket.** This ticket's deliverable is the verdict per skill, with supporting evidence — not an implementation. See the sequencing note above for why.

## Out of Scope
- Implementing any wiring for a confirmed-gap skill — deferred until `TCK-20260705-TAG-SKILL-SUGGEST` lands (see sequencing note). If that ticket is not yet done when this investigation concludes, file a small follow-on ticket for the wiring itself, explicitly blocked on `TAG-SKILL-SUGGEST`, rather than implementing a file-path-based `CLAUDE.md` row here.
- Removing, archiving, or modifying any `.claude/skills/*/SKILL.md` file — this ticket only investigates usage, it doesn't touch the skills themselves.
- Re-litigating the 3 skills `SKILL-TRIGGER-COVERAGE` already wired — settled, not in scope here.

## Acceptance Criteria
- [ ] Each of the 6 skills has a documented verdict (genuine gap / correctly redundant) with cited evidence (session-transcript activity counts, cross-referenced against `CLAUDE.md`'s existing rule sections).
- [ ] The `CLAUDE.md` Testing Rule / Architecture Rule overlap question is explicitly resolved with reasoning, not left as an assumption.
- [ ] The 659-`docs/`-edits composition question is explicitly resolved (what fraction, if any, is free-form proposal/spec writing vs. ticket-workflow-internal).
- [ ] No skill wiring is implemented in this ticket — confirmed gaps are handed off as a note for `TCK-20260705-TAG-SKILL-SUGGEST`'s eventual scope, or a small explicitly-blocked follow-on ticket if that ticket isn't done yet.

## Related Tickets
- TCK-20260704-SKILL-TRIGGER-COVERAGE (raised this exact open question, wired the other 3 skills)
- tickets/todos/tag-taxonomy-followups/TCK-20260705-TAG-SKILL-SUGGEST.md (the mechanism any confirmed gap should be wired through — this ticket should sequence after or alongside it, not before)

## Related Docs
- CLAUDE.md ("Proactive Tool Use" table, "Testing Rule" and "Architecture Rule" sections)
- docs/ai/skills.md

## Related Stored Artifacts
None yet — staging artifacts to be created under `staging_artifacts/TCK-20260705-SIX-SKILLS-INVESTIGATION/` when implementation begins (standard tier).

## Related Code Areas
- CLAUDE.md
- .claude/skills/test-driven-development/, python-testing-patterns/, backend-testing/, architecture/, brainstorming/, doc-coauthoring/ (read-only — investigating usage, not modifying)

## Assumptions / Open Questions
- Whether a fresh session-transcript sample (more sessions than the original count) changes any of the 6 verdicts is exactly what this investigation exists to determine — not assumed here.
- Whether the tag-based mechanism (`TAG-SKILL-SUGGEST`) will actually cover all 6 skills' domains, or whether some would still need a `CLAUDE.md`-table-style trigger regardless (e.g. a skill whose trigger condition isn't naturally tag-shaped) is a question for whoever eventually wires a confirmed gap, not resolved here.

## Implementation Notes
(not yet implemented — ticket filed for review before proceeding)

## Test Summary
(not yet implemented)

## Files Changed
(not yet implemented)

## Completion Summary
(not yet implemented)
