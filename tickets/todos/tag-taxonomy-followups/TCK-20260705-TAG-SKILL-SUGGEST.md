---
status: active
layer: guidelines
authority: P1
audience: agent
ticket_id: TCK-20260705-TAG-SKILL-SUGGEST
phase: open
date: 2026-07-05
tags: [tagging, taxonomy, ticket-scoper, skills]
---

# TCK-20260705-TAG-SKILL-SUGGEST

## Title
Wire Process/Skill-signal tags into ticket-scoper's skill suggestion output

## Status
OPEN

## Tier
standard

## Type
feature

## Priority
P2

## Request Summary
`docs/guidelines/tag_taxonomy.md`'s `Process/Skill-signal` category was designed specifically to serve "Scenario 1: Tag-driven skill suggestion" — its canonical tag names (`api-design`, `performance`, `debugging`, `security`, ...) are chosen to line up 1:1 with an existing skill so a routing table is a lookup, not a re-mapping exercise. That routing logic was explicitly deferred when the taxonomy shipped (`TCK-20260704-TAG-TAXONOMY`) — the category existed, but nothing read it. This ticket builds the consumption side: when `ticket-scoper` assigns a `Process/Skill-signal` tag to a new ticket, it should surface the matching skill as a suggestion in its output, complementing `TCK-20260704-SKILL-TRIGGER-COVERAGE`'s file-path-based `CLAUDE.md` triggers (which fire *during* editing) with a signal that fires *before* implementation work starts, at scope time.

## Scope
- Define a small, explicit `tag → skill` mapping covering the `Process/Skill-signal` tags already named as examples in `tag_taxonomy.md` and already present in `CLAUDE.md`'s auto-invoke table: `api-design` → `/api-design-principles`, `debugging` → `/debugging-strategies` (or `Agent(subagent_type: "world-debugger")` if the ticket's `Related Code Areas` overlap `src/worldassembly/`/`src/worldbuilding/`/`src/worldmodules/`/`src/content/`/`src/core/registries.py`, mirroring the existing carve-out), `performance` → `/python-performance-optimization`, `security` → `/security-review`. This mapping should live in a location `ticket-scoper` can read (a small table inside `.claude/agents/ticket-scoper.md` itself is the simplest option — confirm during Investigate whether a shared location is warranted instead, e.g. if `planner`/`architecture-reviewer` would also want to read it).
- Update `.claude/agents/ticket-scoper.md`'s Output section: when a produced ticket's `tags` include one or more `Process/Skill-signal` tags with a mapped skill, add a `suggested_skills` note to the scoper's returned summary/conflict-report output (not to the ticket file itself — this is a runtime suggestion, not durable ticket content).
- Ensure the orchestrating session (whoever runs `implement-ticket`'s Scope phase) surfaces this suggestion via `log(...)`, matching how conflict reports are already surfaced today.
- Add the same mapping awareness to `create-tickets.js`'s Structure phase (where tags are assigned for batch-created tickets) so multi-ticket proposals get the same suggestion behavior ticket-scoper gets for single tickets.

## Out of Scope
- Auto-invoking a skill without a suggestion step — this ticket surfaces a suggestion for the orchestrating session/human to act on, it does not make `ticket-scoper` (a subagent) invoke another skill directly. Actually triggering a suggested skill remains a decision made by whoever is running the pipeline.
- Extending the mapping beyond the tags already named as canonical examples in `tag_taxonomy.md` and already present in `CLAUDE.md`'s auto-invoke table — adding new `Process/Skill-signal` tags for skills not yet wired into `CLAUDE.md` (e.g. `architecture`, `test-driven-development`) is a separate decision, tracked as an open question below, not decided or built here.
- Changing `CLAUDE.md`'s file-path-based auto-invoke table itself — this ticket adds a complementary, tag-based signal; it does not modify or replace the existing mechanism.

## Acceptance Criteria
- [ ] A `tag → skill` mapping exists for at least the 4 tags named above, readable by `ticket-scoper`.
- [ ] `ticket-scoper`'s output includes a `suggested_skills` note whenever a produced ticket's tags include a mapped `Process/Skill-signal` tag.
- [ ] The `debugging` → skill mapping correctly branches to `world-debugger` when the ticket's Related Code Areas overlap the world-assembly file set, matching the existing `CLAUDE.md` carve-out logic.
- [ ] `create-tickets.js`'s Structure phase produces the same suggestion behavior for batch-created tickets.
- [ ] A new `docs/guides/ticket_tagging.md` practical guide exists (see Related Docs) explaining, for a developer authoring or reviewing a ticket: what the 4 tag categories are, concrete examples of each, and — the new behavior this ticket adds — which tags now trigger a skill suggestion and why. Links to `docs/guidelines/tag_taxonomy.md` for the full formal rules rather than duplicating them.
- [ ] `docs/guides/README.md`'s guide index table has a new row for `ticket_tagging.md`.
- [ ] `docs/ai/agents.md`'s `ticket-scoper` section describes the new `suggested_skills` output field.

## Related Tickets
- TCK-20260704-TAG-TAXONOMY (defined the Process/Skill-signal category this ticket consumes)
- TCK-20260704-SKILL-TRIGGER-COVERAGE (the file-path-based `CLAUDE.md` mechanism this ticket complements, not replaces)

## Related Docs
- docs/guidelines/tag_taxonomy.md (Process/Skill-signal category definition, Scenario 1)
- docs/ai/agents.md (`ticket-scoper` section — update to describe the new output field)
- docs/ai/skills.md (cross-reference if useful — the skill catalog now has two trigger mechanisms: file-path via CLAUDE.md, tag-based via ticket-scoper)
- docs/guides/README.md (add new guide to the index)
- **New:** docs/guides/ticket_tagging.md (practical, developer-facing companion to the formal taxonomy doc — required by this ticket's scope, not optional)

## Related Stored Artifacts
None yet.

## Related Code Areas
- .claude/agents/ticket-scoper.md
- .claude/workflows/create-tickets.js (Structure phase)
- .claude/agents/world-debugger.md (reference for the existing debugging carve-out pattern)
- CLAUDE.md (read-only reference — the existing tag→skill candidates already live in its auto-invoke table)

## Assumptions / Open Questions
- Whether the mapping table should also cover skills not yet in `CLAUDE.md`'s auto-invoke table (e.g. `architecture` → `/architecture`, `test-driven-development` → `/test-driven-development`) is an open design question — the four in Scope are the ones with confirmed, already-established precedent; expanding further should be a deliberate Plan-phase decision with its own evidence, not assumed here.
- Whether `planner` (which also reads the ticket) should re-surface the suggestion, or whether once at Scope time is sufficient, is left for Plan to decide.

## Implementation Notes
(not yet implemented — ticket filed for review before proceeding)

## Test Summary
(not yet implemented)

## Files Changed
(not yet implemented)

## Completion Summary
(not yet implemented)
