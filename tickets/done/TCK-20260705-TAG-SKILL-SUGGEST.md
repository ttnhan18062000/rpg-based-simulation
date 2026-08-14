---
status: historical
layer: guidelines
authority: P1
audience: agent
ticket_id: TCK-20260705-TAG-SKILL-SUGGEST
phase: done
date: 2026-07-05
tags: [tagging, taxonomy, ticket-scoper, skills]
---

# TCK-20260705-TAG-SKILL-SUGGEST

## Title
Wire Process/Skill-signal tags into ticket-scoper's skill suggestion output

## Status
DONE

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
- .claude/workflows/implement-ticket.js (Scope phase `TICKET_SCHEMA` + `log(...)` block — added post-investigation: Scope bullet 3 requires the orchestrating session to surface `suggested_skills` via `log(...)`, which requires this file's schema and log block, not just `ticket-scoper.md`'s Output contract)
- .claude/agents/world-debugger.md (reference for the existing debugging carve-out pattern)
- CLAUDE.md (read-only reference — the existing tag→skill candidates already live in its auto-invoke table)

## Assumptions / Open Questions
- Whether the mapping table should also cover skills not yet in `CLAUDE.md`'s auto-invoke table (e.g. `architecture` → `/architecture`, `test-driven-development` → `/test-driven-development`) is an open design question — the four in Scope are the ones with confirmed, already-established precedent; expanding further should be a deliberate Plan-phase decision with its own evidence, not assumed here.
- Whether `planner` (which also reads the ticket) should re-surface the suggestion, or whether once at Scope time is sufficient, is left for Plan to decide.
- **Scope-sizing correction (post-investigation, 2026-07-05):** Scope bullet 4 assumed `create-tickets.js`'s Structure phase already assigns tags to batch tickets — investigation found it does not (`TASK_SCHEMA` has no `tags` field; the Write-phase frontmatter template hardcodes `tags: []`). Satisfying AC4 requires first making Structure phase assign tags, then adding the skill lookup on top — a larger, two-part change than the original wording implied. See `investigation.md`'s Current Behavior section for full detail; Plan must size this explicitly.
- **Precedent correction:** the ticket's "mirroring the existing carve-out"/"already-established precedent" framing holds for 3 of the 4 tags (`api-design`, `debugging`, `performance` each mirror an existing `CLAUDE.md` row). `security` → `/security-review` has no `CLAUDE.md` precedent row — the skill is real and documented in `docs/ai/skills.md` but this ticket's mapping is the first place it's codified as a routing rule anywhere in the repo. Not a blocker, just a wording correction for Plan/Implementation Notes.

## Implementation Notes
Implemented all 11 steps of `staging_artifacts/TCK-20260705-TAG-SKILL-SUGGEST/plan.md` with no deviations:

1. `.claude/agents/ticket-scoper.md` — added item 5 to `## Output` (the 4-tag mapping table + `suggested_skills` field). `## Ticket Format` and `## Mandatory Scan` left byte-identical.
2-3. `.claude/workflows/create-tickets.js` — added `tags` and `suggested_skills` to `TASK_SCHEMA` (both now `required`), added matching `tags:`/`suggested_skills:` rule blocks to the Structure-phase prompt (placed before the `tier:` block, after `assumptions:`). `STRUCTURE_SCHEMA`, `WRITE_SCHEMA`, and the Merge/Split rules were not touched.
4. Same file — Write-phase frontmatter template's `tags: []` replaced with a substitution instruction for `task.tags`.
5. Same file — added a `log('Suggested skills: ...')` block after the `droppedScopes` warning, before `outputFolder` is computed. SEQUENCE.md generation logic untouched.
6-7. `.claude/workflows/implement-ticket.js` — added `suggested_skills` to `TICKET_SCHEMA` (not required, defaults to `[]` for older tickets). "Load existing ticket" prompt branch gained a Step 3 that embeds the same 4-tag mapping table and computes `suggested_skills` from ticket frontmatter `tags`; "Create new ticket" branch's Return line now asks for `suggested_skills` (relies on `ticket-scoper.md`'s own Output contract). Added an unconditional `log('Suggested skill(s): ...')` block right before the conflicts early-return, so it fires regardless of whether conflicts exist. The epic-tier short-circuit and monitoring-write block were not touched.
8. Wrote `docs/guides/ticket_tagging.md` — thin guide covering the 4 tag categories (1 example each, pulled from `tag_taxonomy.md`), the skill-suggestion table (identical to Step 1's), and a closing link to `tag_taxonomy.md`. Frontmatter uses `status: active, layer: guidelines, authority: P2, audience: developer, tags: [...]` — the doc-type validator (`tools/validate_frontmatter.py::_validate_doc`) requires `status`/`layer`/`authority`/`audience`; note `docs/guides/observability.md`, used as the "check its frontmatter" reference in the plan, is itself currently missing `status` and fails validation if run directly — did not copy that gap into the new file.
9. `docs/guides/README.md` — added one row for `ticket_tagging.md`; other 7 rows and closing paragraph untouched.
10. `docs/ai/agents.md` — added one bullet under `ticket-scoper`'s `**Outputs:**`; other subsections and the `investigator` section untouched.
11. Regression: `python3 -m pytest tests/tools/test_validate_frontmatter.py -q` — 64 passed.

**Hazards for future editors (per plan's Anti-Drift Notes):**
- The 4-tag mapping table now exists in **4 separate copies** with no shared import mechanism: `.claude/agents/ticket-scoper.md`, `.claude/workflows/create-tickets.js` (Structure prompt), `.claude/workflows/implement-ticket.js` ("Load existing ticket" prompt), and `docs/guides/ticket_tagging.md`. Keeping them in sync is a manual-diff discipline, not a code guarantee — any future change to the mapping must touch all 4.
- `security` → `/security-review` has no `CLAUDE.md` precedent row, unlike the other 3 tags (`api-design`, `debugging`, `performance`), each of which mirrors an existing `CLAUDE.md` auto-invoke row. This mapping is the first place `security` → `/security-review` is codified as a routing rule anywhere in the repo.
- `suggested_skills` is Output/runtime data only — never written into ticket frontmatter or body; only `tags` is durable ticket content.
- Not moved to `tickets/done/`, staging artifacts not moved to `stored_artifacts/`, `tickets/working_log.csv` and `CLAUDE.md` not touched — those are Finalize-phase/out-of-scope actions per this ticket's scoping instructions, left for the pipeline's later phases.

## Test Summary
No automated pytest surface exists for any of the changed files (agent-prompt markdown, Claude-internal
workflow scripts, and docs — none have a test harness in this repo, confirmed by grep). Verification:
- Regression: `python3 -m pytest tests/tools/test_validate_frontmatter.py -q` → 64 passed (run
  independently twice, by implementer and by test-scoper — confirms the new `docs/guides/ticket_tagging.md`
  and this ticket's own staging-artifact frontmatter pass tag-taxonomy validation post-2026-07-04 cutoff).
- Manual dry-run traces (5 constructed scenarios, per `test_plan.md`), all confirmed correct by tracing
  the actual modified prompt text in all 3 files:
  1. `[debugging]`, Related Code Areas outside world-assembly set → `/debugging-strategies`. Confirmed.
  2. `[debugging]`, Related Code Areas includes `src/content/repository.py` → `Agent(subagent_type: "world-debugger")`. Confirmed.
  3. `[api-design]`, `[performance]`, `[security]` independently → each mapped skill. Confirmed.
  4. `[combat, calibration]` (no mapped tag) → `suggested_skills: []`. Confirmed.
  5. `[debugging]`, Related Code Areas touching only `src/worldgeneration/` (not in CLAUDE.md's 4-path
     carve-out, only in world-debugger.md's broader list) → `/debugging-strategies`, NOT world-debugger.
     Confirms CLAUDE.md's narrower carve-out was wired in, not world-debugger.md's broader one.
- Parity: confirmed no `docs/parity_ledger/` entry needs updating. The one keyword hit (`INFRA-180`,
  `infrastructure.yaml`) covers `tools/validate_frontmatter.py`'s taxonomy-enforcement behavior, which
  this ticket does not touch (zero diff); its own test (`tests/tools/test_validate_frontmatter.py`)
  still passes. This ticket's new tag→skill suggestion capability is agent-orchestration tooling, not a
  parity-ledger-tracked simulation/infrastructure behavior — no new entry warranted, consistent with
  investigation.md's and architecture review's independent "no overlap" conclusions.

## Files Changed
- `.claude/agents/ticket-scoper.md` — added item 5 to Output section (4-tag mapping table + `suggested_skills` field).
- `.claude/workflows/create-tickets.js` — `tags`/`suggested_skills` added to `TASK_SCHEMA`, Structure-prompt rule blocks, frontmatter template substitution, batch `log(...)` surfacing.
- `.claude/workflows/implement-ticket.js` — `suggested_skills` added to `TICKET_SCHEMA`, both Scope-phase prompt branches, unconditional `log(...)` block.
- `docs/guides/ticket_tagging.md` (new) — practical developer guide.
- `docs/guides/README.md` — one index row added.
- `docs/ai/agents.md` — one bullet added under `ticket-scoper` Outputs.
- `tickets/todos/tag-taxonomy-followups/TCK-20260705-TAG-SKILL-SUGGEST.md` — deleted (routine Scope-phase move: content was copied forward to `tickets/inprogress/TCK-20260705-TAG-SKILL-SUGGEST.md` at the start of this pipeline run, nothing lost).
- No diff to `CLAUDE.md`, `tools/validate_frontmatter.py`, or `tickets/working_log.csv` (all explicitly out of scope, confirmed empty).

## Completion Summary
Wired the tag taxonomy's `Process/Skill-signal` category into a `tag -> skill` suggestion mechanism:
`ticket-scoper` and `create-tickets.js`'s Structure phase now compute a `suggested_skills` list from a
4-entry mapping (`api-design`, `debugging` with a world-debugger branch, `performance`, `security`),
surfaced via `log(...)` at Scope time in `implement-ticket.js` and via a batch log line in
`create-tickets.js`. `create-tickets.js`'s Structure phase also gained `tags` assignment for batch
tickets (previously always empty), scoped strictly to canonical-form + the 4-tag Process/Skill-signal
list per an architecture-review correction (broader Subsystem/Topic/Phase/Quality-attribute tagging
remains explicitly deferred to `TCK-20260705-TAG-REGISTRY-QUERY`). Added a new developer guide
(`docs/guides/ticket_tagging.md`) and 2 small doc updates. The mapping now exists in 4 independent
copies with no shared import mechanism (a disclosed, accepted hazard, not a defect) — any future
change to the mapping must update all 4 by hand. `security` -> `/security-review` is the first place
that route is codified anywhere in the repo (no CLAUDE.md precedent, unlike the other 3 tags). No
`src/` code, simulation behavior, or parity ledger entry was touched.
