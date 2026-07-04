---
status: historical
layer: guidelines
authority: P1
audience: agent
ticket_id: TCK-20260704-SKILL-TRIGGER-COVERAGE
phase: done
date: 2026-07-04
tags: [claude-md, skills, process-improvement]
---

# TCK-20260704-SKILL-TRIGGER-COVERAGE

## Title
Add CLAUDE.md proactive-invocation triggers for skills with confirmed applicable-but-unsurfaced work

## Status
DONE

## Tier
hotfix

## Type
chore

## Priority
P2

## Request Summary
Investigation across the last 30 session transcripts found 11 of 14 project skills in `.claude/skills/` have never been invoked. Cross-referencing against actual file/command activity shows this is not universally "no need arose" — for several skills, clearly applicable work happened repeatedly with zero corresponding skill invocation:

| Skill / agent | Applicable work observed | Invocations |
|---|---|---|
| `api-design-principles` | 12 edits to `src/api/` | 0 |
| `debugging-strategies` + `world-debugger` agent | ~100 traceback/pytest-failure-flavored bash commands | 0 |
| `python-performance-optimization` | 4 profiling commands (cProfile/memray) | 0 |

By contrast, `graphify` (21 invocations) and `mcp__knowledge-search__search_docs` (302 invocations) — the two tools that *are* listed in `CLAUDE.md`'s "Proactive Tool Use" table — are used heavily. The most likely cause: a skill's own "use when X" description (in its `SKILL.md` frontmatter and in `docs/ai/skills.md`) is not sufficient signal for proactive mid-session invocation; only entries in `CLAUDE.md`'s own auto-invoke table reliably drive that behavior in this repo.

This ticket is a process/documentation change, not a code change: add rows to `CLAUDE.md`'s "Proactive Tool Use" table for the three skills/agent above, where evidence is unambiguous.

## Scope
- Add rows to `CLAUDE.md`'s "Always auto-invoke" table:
  - Editing or investigating `src/api/` → `/api-design-principles` (review shape/boundaries before or after the change)
  - Investigating a traceback, test failure, or unexpected runtime error → `/debugging-strategies`; if the failure is specifically in world assembly/content resolution (`src/worldassembly/`, `src/worldbuilding/`, `src/worldmodules/`, `src/content/`, `src/core/registries.py`) → `Agent(subagent_type: "world-debugger")` instead (already documented in `docs/ai/skills.md` as the narrower, more specific tool for that case)
  - Profiling or investigating a slow simulation tick / high-memory world assembly → `/python-performance-optimization`
- Do not add rows for `frontend-design` (zero evidence of any frontend/ work in this repo to date — correctly dormant, not a gap) or `prompt-builder` (niche, Copilot-prompt-specific, not this project's concern).

## Out of Scope
- `test-driven-development`, `python-testing-patterns`, `backend-testing`, `architecture` (ADR workflow), `brainstorming`, `doc-coauthoring` — all also show zero invocations despite real applicable-looking activity (281 test-file edits, 9 `docs/architecture/` edits, 659 `docs/` edits overall), but `CLAUDE.md` already has its own "Testing Rule" and "Architecture Rule" sections that may substantively cover the same ground for this project, and most `docs/` writes are ticket-workflow-internal (`investigation.md`/`plan.md`/ticket files) rather than the free-form proposal/spec writing `doc-coauthoring` targets. Whether these six represent a genuine additional gap or correct-by-design redundancy is an open question, not decided here — left for a follow-on investigation rather than assumed.
- Removing or archiving any `.claude/skills/` files — this ticket is additive (wiring existing skills into the trigger table), not a prune.
- Changing anything in `.claude/skills/*/SKILL.md` themselves.

## Acceptance Criteria
- [ ] `CLAUDE.md`'s "Always auto-invoke (no user prompt required)" table has three new rows matching the Scope section above, in the same format as existing rows (Trigger | Action).
- [ ] No existing row in that table is modified, reordered, or removed.
- [ ] The six "Out of Scope" skills are explicitly not touched in this ticket.

## Related Tickets
None.

## Related Docs
- CLAUDE.md ("Proactive Tool Use" section)
- docs/ai/skills.md (already documents `debugging-strategies` "Complements `world-debugger` (agent) for world assembly failures" — this ticket promotes that relationship into the actual auto-invoke table, not just a descriptive doc)
- docs/ai/agent_infrastructure_audit.md (originally flagged "skill catalog shows signs of not being curated" as a maintenance risk; this investigation found the more specific and more actionable form of that gap)

## Related Stored Artifacts
None — hotfix tier, no staging artifacts required.

## Related Code Areas
- CLAUDE.md
- .claude/skills/api-design-principles/
- .claude/skills/debugging-strategies/
- .claude/skills/python-performance-optimization/
- .claude/agents/world-debugger.md

## Assumptions / Open Questions
- Whether the six "out of scope" skills need the same treatment is an open question for a follow-on investigation, not resolved by this ticket.
- This ticket assumes the CLAUDE.md table is in fact the effective proactive-invocation signal (supported by graphify/search_docs's heavy usage vs. everything else's near-zero usage) rather than some other unmeasured factor — worth revisiting if these three skills still don't get used after this change lands.

## Implementation Notes
Added exactly three rows to `CLAUDE.md`'s "Always auto-invoke (no user prompt required)" table, appended after the existing last row (no reordering of existing rows): (1) editing/investigating `src/api/` → `/api-design-principles`; (2) traceback/test-failure/runtime-error investigation → `/debugging-strategies`, with a carve-out to `Agent(subagent_type: "world-debugger")` for failures specifically in `src/worldassembly/`, `src/worldbuilding/`, `src/worldmodules/`, `src/content/`, `src/core/registries.py`; (3) slow-tick/high-memory profiling → `/python-performance-optimization`. No other row in the table was touched. `frontend-design` and `prompt-builder` were not added, per the ticket's explicit exclusion.

## Test Summary
Not applicable in the automated-test sense — this is a documentation/process change. Verification performed: re-read `CLAUDE.md`'s "Always auto-invoke" table after the edit to confirm exactly 3 new rows were added, none of the 8 pre-existing rows were modified/reordered/removed, and none of the 6 explicitly out-of-scope skills appear in the new rows.

## Files Changed
- `CLAUDE.md`

## Completion Summary
Added CLAUDE.md auto-invoke triggers for the three skills/agent with confirmed applicable-but-unsurfaced work (`api-design-principles`, `debugging-strategies`/`world-debugger`, `python-performance-optimization`). The six other zero-invocation skills and the redundancy question with CLAUDE.md's existing Testing/Architecture Rule sections remain an explicitly open, deferred follow-on (not resolved by this ticket).
