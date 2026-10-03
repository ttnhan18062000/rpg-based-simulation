---
status: historical
layer: guidelines
authority: P2
audience: agent
ticket_id: TCK-20260705-TAG-SKILL-SUGGEST
artifact_type: test_plan
tags: [tagging, taxonomy, ticket-scoper, skills]
---

# Test Plan — TCK-20260705-TAG-SKILL-SUGGEST

## Regression Surface

This ticket touches four artifact classes, none of which have an existing automated test harness:

- `.claude/agents/ticket-scoper.md` — an agent prompt (markdown), not executable code. No test
  file references `ticket-scoper` (confirmed: `grep -rli "ticket.scoper" tests/` returned nothing
  outside `tests/tools/test_validate_frontmatter.py`, which matches on unrelated frontmatter
  content, not on the agent prompt itself).
- `.claude/workflows/create-tickets.js` and `.claude/workflows/implement-ticket.js` — Claude-internal
  workflow scripts executed via the `Workflow` tool, not standalone Node modules. Confirmed no
  `package.json`-driven JS test runner covers `.claude/workflows/` (repo has a `package.json` but
  no `*.test.js` files exist outside `node_modules`, and no pytest file imports or exercises these
  workflow scripts).
- `docs/guides/ticket_tagging.md` (new), `docs/guides/README.md`, `docs/ai/agents.md` — plain docs.
  No test enforces guide-index completeness or `docs/ai/agents.md` section content (confirmed via
  `grep -rl "guides/README\|docs/guides" tests/` → no matches).
- `CLAUDE.md` — read-only in this ticket (per Out of Scope); no edit, so no regression surface here.

**Sole existing automated test surface adjacent to this ticket**:
`tests/tools/test_validate_frontmatter.py` (validates `tools/validate_frontmatter.py`, which
enforces `docs/guidelines/tag_taxonomy.md`'s canonical-form rules on ticket/artifact `tags`).
This ticket does not modify `tools/validate_frontmatter.py` or the taxonomy doc itself, but the
new `staging_artifacts/{ticket_id}/investigation.md` and `test_plan.md` files (this pair) and the
eventual ticket's own frontmatter `tags: [tagging, taxonomy, ticket-scoper, skills]` must still
pass validation, since `TCK-20260705-...` is on/after the `2026-07-04` enforcement cutoff. This is
a regression check, not a new test to write.

**Precedent for a prompt/doc-only change's test treatment**: `tickets/done/
TCK-20260704-SKILL-TRIGGER-COVERAGE.md`'s Test Summary establishes that a CLAUDE.md-only prompt
change in this repo is verified by manual before/after diff inspection, not automated tests
("Not applicable in the automated-test sense... Verification performed: re-read CLAUDE.md's table
after the edit to confirm exactly N new rows were added, none of the pre-existing rows were
modified/reordered/removed"). This ticket's `ticket-scoper.md`/`create-tickets.js`/
`implement-ticket.js` edits are the same class of change (agent-prompt / workflow-prompt text, no
`src/` behavior), so the same verification pattern applies, with one addition: this ticket's
acceptance criteria are specific enough (map correctly, branch correctly, produce the field) that
a manual dry-run trace is warranted in addition to a diff read (see below).

## New Tests Required

No new automated (pytest) tests are required — there is no test harness that exercises agent
prompt text or workflow script behavior in this repo (confirmed above). Required verification is
manual, traced against each Acceptance Criterion:

1. **AC: mapping exists for the 4 tags, readable by `ticket-scoper`.**
   Manual check: open `.claude/agents/ticket-scoper.md` after the edit, confirm a table/mapping
   listing exactly `api-design` → `/api-design-principles`, `debugging` → `/debugging-strategies`
   (with the world-debugger branch condition), `performance` → `/python-performance-optimization`,
   `security` → `/security-review` exists in the Output section (not the Ticket Format template —
   see Anti-Drift Test Guards).

2. **AC: `ticket-scoper`'s output includes `suggested_skills` whenever tags include a mapped
   Process/Skill-signal tag.**
   Dry-run trace (no pytest, since `ticket-scoper` is an LLM-invoked agent, not a pure function):
   construct one worked example per mapped tag —
   - a ticket tagged `[debugging]` with `Related Code Areas` outside the world-assembly file set →
     expect `suggested_skills` mentions `/debugging-strategies` only.
   - a ticket tagged `[debugging]` with `Related Code Areas` including e.g.
     `src/content/repository.py` → expect `suggested_skills` mentions
     `Agent(subagent_type: "world-debugger")` instead of `/debugging-strategies`.
   - a ticket tagged `[api-design]`, `[performance]`, `[security]` each independently →
     expect the corresponding single mapped skill.
   - a ticket tagged `[combat, calibration]` (no mapped tag) → expect no `suggested_skills` field
     or an explicitly empty one (Plan should pin down which — absent vs. empty array — for a
     deterministic contract; recommend empty array for consistency with `conflicts: []`'s existing
     empty-array convention in `implement-ticket.js`'s `TICKET_SCHEMA`).
   Record these traces in the ticket's own Test Summary / Implementation Notes once implemented.

3. **AC: `debugging` branches to `world-debugger` correctly (world-assembly file-set overlap).**
   Covered by the second bullet in item 2. Confirm the exact file-set used matches CLAUDE.md's
   four-path list (`src/worldassembly/`, `src/worldbuilding/`, `src/worldmodules/`,
   `src/content/`, `src/core/registries.py`) per Investigation's Risk 3 recommendation — not
   `world-debugger.md`'s six-path list (which additionally includes `src/worldgeneration/`).
   Negative check: a ticket tagged `[debugging]` with Related Code Areas touching only
   `src/worldgeneration/` and nothing else in the four-path list should get `/debugging-strategies`,
   not `world-debugger` — a concrete test of which list was actually wired in.

4. **AC: `create-tickets.js`'s Structure phase produces the same suggestion behavior for batch
   tickets.**
   Since Investigation found `TASK_SCHEMA` (`create-tickets.js:441-478`) has no `tags` field at
   all today (batch tickets ship `tags: []` unconditionally), this AC cannot be satisfied by only
   adding a mapping lookup — it requires the Structure phase to first assign tags. Verification:
   trace a synthetic proposal through Comprehend → Investigate → Structure (or inspect the
   Structure agent's prompt/schema after the edit) and confirm: (a) `TASK_SCHEMA` gains a `tags`
   property, (b) the Write-phase frontmatter template (`:673-682`) substitutes real tags instead of
   the hardcoded `tags: []`, (c) a `suggested_skills` equivalent is threaded through to the
   workflow's `log(...)` output (mirroring item 5 below) for at least one batch ticket carrying a
   mapped tag.

5. **Implicit requirement (Scope bullet 3, not in the AC checklist but stated in ticket body):
   the orchestrating session surfaces the suggestion via `log(...)`.**
   Per Investigation, `implement-ticket.js`'s `TICKET_SCHEMA` (`:31-39`) has no `suggested_skills`
   field and its Scope-phase block (`:184-188`) has no corresponding `log(...)` call. Verification:
   after the edit, trace the Scope phase of `implement-ticket.js` for a ticket carrying a mapped
   tag and confirm a `log('Suggested skill(s): ...')`-style line is emitted, analogous to the
   existing `log('Conflicts detected: ...')` pattern at `:186-188`. If Plan decides this
   requirement is out of scope for this ticket (since `implement-ticket.js` isn't in the ticket's
   current Related Code Areas), this must be an explicit, stated decision — not a silent gap — per
   CLAUDE.md's "no known material gap is left unstated" Definition of Done clause.

6. **AC: `docs/guides/ticket_tagging.md` exists, covers the 4 categories + skill-suggestion
   behavior, links out to `tag_taxonomy.md`.**
   Manual read-through: confirm all 4 tag categories (Subsystem/Topic, Phase/Milestone,
   Process/Skill-signal, Quality-attribute) are named with at least one concrete example each, the
   skill-suggestion behavior is described with the same 4-tag mapping as `ticket-scoper.md` (no
   drift between the two), and the doc does not re-state the canonical-form rules or Forbidden
   Tags list verbatim (those stay solely in `tag_taxonomy.md`, per AC's own instruction not to
   duplicate).

7. **AC: `docs/guides/README.md` index table has a new row.**
   Manual diff check: exactly one new row added (`ticket_tagging.md`), no existing 7 rows
   modified, removed, or reordered — same verification style as the SKILL-TRIGGER-COVERAGE
   precedent.

8. **AC: `docs/ai/agents.md`'s `ticket-scoper` section describes `suggested_skills`.**
   Manual diff check: the "Outputs" bullet list gains one line describing `suggested_skills`;
   no other section content changes.

## Scoped Pytest Commands

```
python3 -m pytest tests/tools/test_validate_frontmatter.py -q
```
Run this as a regression check only — confirms the taxonomy validator still passes after this
ticket's own frontmatter (investigation.md, test_plan.md, plan.md, and the eventual ticket file)
is written with `tags: [tagging, taxonomy, ticket-scoper, skills]`, since all of it postdates the
`2026-07-04` enforcement cutoff. No new pytest cases are added by this ticket — see "New Tests
Required" above for why (no executable surface exists for agent-prompt or workflow-script logic).

If Plan decides to also touch `tools/validate_frontmatter.py` (e.g. to add a machine-readable
`Process/Skill-signal` tag list as a shared source of truth, contrary to this investigation's
recommendation to keep the mapping local to `ticket-scoper.md` — see investigation.md Risk 1),
that decision would introduce new testable surface and should add cases to
`tests/tools/test_validate_frontmatter.py` following its existing `TestEnumAntiDrift` pattern
(`:456-479`). Not required under the current recommendation.

## Anti-Drift Test Guards

- The 4-tag mapping table must appear in `ticket-scoper.md`'s **Output** section (or a clearly
  Output-adjacent section), not inside the **Ticket Format** template block (`:15-73`) — a
  reviewer should be able to confirm by diff that the Ticket Format YAML/section list is
  byte-identical before and after this ticket, since `suggested_skills` is explicitly a
  runtime/output-only field, never durable ticket content (ticket's Out of Scope).
- The mapping table's 4 entries must exactly match the ticket's Scope wording — no 5th tag added,
  no `architecture` or `test-driven-development` entries, even though both are named as tempting
  candidates in the ticket's own Assumptions section (they're explicitly deferred).
- The world-debugger branch condition's file-set list must be diffed against CLAUDE.md's four
  paths, not world-debugger.md's five/six paths (Investigation Risk 3) — a test-by-inspection
  should explicitly enumerate which list ended up wired in, since the two source-of-truth
  documents disagree and this ticket does not have license to silently pick the broader one.
- Confirm `CLAUDE.md` has zero diff after this ticket (Out of Scope: "Changing CLAUDE.md's
  file-path-based auto-invoke table itself... this ticket does not modify or replace the existing
  mechanism") — `git diff CLAUDE.md` should be empty when this ticket is done.
- Confirm `tools/validate_frontmatter.py` has zero diff unless Plan explicitly decides otherwise
  (see Scoped Pytest Commands note above) — this ticket's Related Code Areas does not list it, and
  Investigation found no clean extension point that would justify touching it for a 4-entry map.
