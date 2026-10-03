---
status: historical
layer: guidelines
authority: P2
audience: agent
ticket_id: TCK-20260705-SIX-SKILLS-INVESTIGATION
phase: done
date: 2026-07-05
tags: [skills, process-improvement, investigation]
---

# TCK-20260705-SIX-SKILLS-INVESTIGATION

## Title
Investigate whether the 6 deferred zero-invocation skills are genuine gaps or correctly redundant

## Status
DONE

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
- [x] Each of the 6 skills has a documented verdict (genuine gap / correctly redundant) with cited evidence (session-transcript activity counts, cross-referenced against `CLAUDE.md`'s existing rule sections). — Satisfied: `investigation.md`'s Per-Skill Verdict Table; all counts independently re-verified in this session by re-running every script in `test_plan.md` verbatim (41 total Skill invocations / 6 target skills at 0, 281 `tests/` edits, 9 `docs/architecture/` edits, 669 `docs/` edits, 5 `conftest.py`, 303 precedent files, 36 `AskUserQuestion` calls — all matched exactly, zero drift).
- [x] The `CLAUDE.md` Testing Rule / Architecture Rule overlap question is explicitly resolved with reasoning, not left as an assumption. — Satisfied, per-skill (not blanket): Testing Rule is outcome-based and doesn't overlap TDD's Iron Law — worse, the repo's own `implement-ticket.js` pipeline runs Implement *before* Test, actively diverging from TDD rather than merely duplicating it; `python-testing-patterns`/`backend-testing` redundancy is precedent-driven (5 `conftest.py` + 303 files already using fixtures/mocking/parametrize), not rule-text-driven; Architecture Rule covers runtime code-boundary concerns, a different subject than ADR-authoring — the real redundancy source is that all 6 `docs/architecture/*.md` files already follow ADR structure by precedent.
- [x] The 659-`docs/`-edits composition question is explicitly resolved (what fraction, if any, is free-form proposal/spec writing vs. ticket-workflow-internal). — Satisfied: fresh count is 669 (verified), of which ≈86% (575) is mandated/ticket-workflow-internal (parity ledger, engine contracts, mechanics bible, audits, subsystem contracts) and ≈13% (85: `docs/plans/` + `docs/architecture/` + `docs/guides/`) is free-form/proposal-shaped — sampled 3 `docs/plans/` files and 1 `docs/architecture/` file directly to confirm the categorization, not just inferred from directory names.
- [x] No skill wiring is implemented in this ticket — confirmed gaps are handed off as a note for `TCK-20260705-TAG-SKILL-SUGGEST`'s eventual scope, or a small explicitly-blocked follow-on ticket if that ticket isn't done yet. — Satisfied trivially: zero of the 6 skills scored as a genuine/confirmed gap (closest was `doc-coauthoring`, scored "correctly redundant, narrow soft-gap noted" — explicitly not a clean gap), so there is nothing requiring wiring hand-off. The `doc-coauthoring` soft-gap is recorded as a named watch item in Related Tickets below (not a ticket, not a CLAUDE.md/SKILL.md edit).

## Related Tickets
- TCK-20260704-SKILL-TRIGGER-COVERAGE (raised this exact open question, wired the other 3 skills)
- tickets/todos/tag-taxonomy-followups/TCK-20260705-TAG-SKILL-SUGGEST.md (the mechanism any confirmed gap should be wired through — this ticket should sequence after or alongside it, not before)
- Watch item (named only, not a ticket): `doc-coauthoring` soft-gap — ~13% of `docs/` edits (`docs/plans/`, `docs/architecture/`) are free-form/proposal-shaped but produced via single-pass agent-autonomous authorship, not the skill's assumed human-interactive co-writing mode. Revisit only if `docs/plans/` reader-quality issues surface, and only via the tag-based mechanism once `TCK-20260705-TAG-SKILL-SUGGEST` lands — not as a standalone `CLAUDE.md` row.

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
Per-skill verdict table (full evidence and reasoning in `staging_artifacts/TCK-20260705-SIX-SKILLS-INVESTIGATION/investigation.md`):

| Skill | Invocations | Verdict |
|---|---|---|
| `test-driven-development` | 0/41 | Correctly redundant by deliberate divergence — this repo's `implement-ticket.js` pipeline runs Implement before Test (opposite of TDD's Iron Law), so the skill would actively conflict with codified pipeline sequencing, not merely duplicate it. |
| `python-testing-patterns` | 0/41 | Correctly redundant — softest of the six; CLAUDE.md's Testing Rule text is thin here, but 5 `conftest.py` + 303 existing fixture/mock/parametrize files already establish the same craft by precedent. |
| `backend-testing` | 0/41 | Correctly redundant — near-zero domain fit (only 1/281 test edits touch `tests/api/`; skill is Jest/Mocha/auth-flow-oriented, this is a simulation engine). |
| `architecture` | 0/41 | Correctly redundant, but not via CLAUDE.md's Architecture Rule (different subject — runtime code boundaries, not ADR-authoring); redundancy is precedent-driven — all 6 `docs/architecture/*.md` files already follow ADR structure. |
| `brainstorming` | 0/41 | Correctly redundant — the repo's own mandatory investigation.md/plan.md staging-artifact gate already serves brainstorming's core function (no implementation before a reviewed design), in a repo-native form; sampled all 36 `AskUserQuestion` calls, none matched brainstorming's actual trigger shape. |
| `doc-coauthoring` | 0/41 | Correctly redundant, narrow soft-gap noted — ~87% of `docs/` edits are mandated parity/contract/audit updates outside its scope; the remaining ~13% is topically close but agent-authored in a single pass, not the skill's assumed human-interactive co-writing mode. Recorded as a watch item (see Related Tickets), not scored as a genuine gap. |

All numeric claims above were independently re-verified in this session (not just trusted from the investigation subagent's report) by re-running every script in `test_plan.md` against the live transcript directory — every count matched exactly with zero drift.

## Test Summary
- Re-ran `count_skills.py` (script in `test_plan.md`): 41 total Skill invocations, all 6 target skills at exactly 0 — matched investigation.md exactly.
- Re-ran the path-normalized Edit/Write counter: `tests/` = 281, `docs/architecture/` = 9, `docs/` (all) = 669 — matched exactly.
- Re-ran precedent checks: `find tests -iname conftest.py` = 5, fixture/mock/parametrize grep = 303 — matched exactly.
- Re-ran the `AskUserQuestion` counter: 36 — matched exactly.
- No pytest suite applies (no code changed); this is the correct verification form for a transcript-analysis investigation, per `test_plan.md`'s own Regression Surface = N/A section.

## Files Changed
- `tickets/inprogress/TCK-20260705-SIX-SKILLS-INVESTIGATION.md` (this file).
- `stored_artifacts/TCK-20260705-SIX-SKILLS-INVESTIGATION/{investigation.md,plan.md,test_plan.md}` (migrated from staging at Finalize).
- No `CLAUDE.md`, `.claude/skills/*/SKILL.md`, or other ticket file touched.

## Completion Summary
Investigated whether the 6 zero-invocation skills (`test-driven-development`, `python-testing-patterns`, `backend-testing`, `architecture`, `brainstorming`, `doc-coauthoring`) represent genuine CLAUDE.md auto-invoke gaps or correct-by-design redundancy, using a fresh 27-session-transcript sample (up from the original ticket's assumed 30). All 6 scored **correctly redundant** — none is a clean genuine gap. Reasoning differs per skill: TDD actively diverges from the repo's own implement-before-test pipeline ordering rather than merely duplicating it; the two other testing skills are redundant via mature in-repo precedent (conftest.py, 303 fixture/mock/parametrize files) rather than CLAUDE.md rule text; `architecture` is redundant via ADR-structure precedent in `docs/architecture/*.md`, not via CLAUDE.md's (differently-scoped) Architecture Rule; `brainstorming` is redundant via the repo's own mandatory investigation/plan staging-artifact gate; `doc-coauthoring` is the closest soft gap (~13% of `docs/` edits are free-form-shaped) but not scored as genuine since that slice is agent-authored, not human-co-written as the skill assumes. Zero skill wiring was implemented — the `doc-coauthoring` soft-gap is recorded as a named watch item only, deferred to the tag-based mechanism `TCK-20260705-TAG-SKILL-SUGGEST` will build.
