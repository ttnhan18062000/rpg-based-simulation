---
status: historical
layer: guidelines
authority: P2
audience: agent
ticket_id: TCK-20260705-TAG-SKILL-SUGGEST
artifact_type: plan
tags: [tagging, taxonomy, ticket-scoper, skills]
---

# Plan — TCK-20260705-TAG-SKILL-SUGGEST

## Summary
Add a local 4-tag→skill mapping to `ticket-scoper.md`'s Output section and duplicate it inline in `create-tickets.js`'s Structure phase (which must first gain a `tags` field it doesn't have today), thread `suggested_skills` through both workflows' schemas/logs, and add the two required doc updates plus the new practical guide.

## Steps

### Step 1 — Add the tag→skill mapping table to `ticket-scoper.md`'s Output section
**Files:** `.claude/agents/ticket-scoper.md`
**Change:** In the `## Output` section (currently lines 75-81, four numbered items), add a new item 5 containing the mapping table and a new item 6 describing the `suggested_skills` return field. Do not touch the `## Ticket Format` block (lines 15-73) — the mapping is Output-only, never durable ticket content.

Insert after item 4 (the `summary` field):
```
5. A `suggested_skills` list: check the ticket's `tags` field against this mapping —
   any tag not listed below produces no suggestion.

   | Tag | Suggested skill |
   |---|---|
   | `api-design` | `/api-design-principles` |
   | `debugging` | `/debugging-strategies` — unless `Related Code Areas` includes a path under `src/worldassembly/`, `src/worldbuilding/`, `src/worldmodules/`, `src/content/`, or `src/core/registries.py`, in which case suggest `Agent(subagent_type: "world-debugger")` instead (mirrors CLAUDE.md's existing debugging carve-out; note `src/worldgeneration/` is intentionally excluded — that path only appears in `world-debugger.md`'s own broader scope list, not CLAUDE.md's, and this mapping follows CLAUDE.md) |
   | `performance` | `/python-performance-optimization` |
   | `security` | `/security-review` (first codification of this mapping in the repo — no existing CLAUDE.md auto-invoke row for it yet) |

   If none of the ticket's tags match, `suggested_skills` is an empty array — never omit the field (mirrors the existing `conflicts: []` empty-array convention).
```
Renumber the existing item 4 remains item 4; the new content is items 5-6, or fold into a single item 5 with two sentences (either is acceptable — keep it inside `## Output`, not a new top-level section).

**Do NOT touch:** `## Ticket Format` (lines 15-73), `## Mandatory Scan` (lines 5-13).
**Verify:** Re-read `.claude/agents/ticket-scoper.md` after the edit; confirm the Ticket Format block is byte-identical to before, and exactly 4 tags appear in the new table (no `architecture`, no `test-driven-development`).

---

### Step 2 — `create-tickets.js`: add `tags` to `TASK_SCHEMA`, scoped strictly to canonical-form + Process/Skill-signal detection
**Files:** `.claude/workflows/create-tickets.js`
**Change:** In `TASK_SCHEMA` (lines 441-478), add a new property:
```js
tags: {
  type: 'array',
  items: { type: 'string' },
  description: 'Canonical-form tags (lowercase, hyphen-separated, never p0/p1/p2) limited to Process/Skill-signal detection for this ticket — see prompt rule below. Broader Subsystem/Topic/Phase/Quality-attribute tagging is deferred to TCK-20260705-TAG-REGISTRY-QUERY, not assigned here.',
},
```
Add it to the `required` array (line 443) alongside the existing fields, so the Structure agent cannot omit it.

In the Structure agent's prompt (the `Step 4 — produce ticket tasks using these strict rules:` block, lines 536-579), add a new rule block (place it near `related_docs`/`assumptions`, before `tier`):
```
  tags:
  - Canonical form only: lowercase, hyphen-separated. Never emit p0/p1/p2 as tags.
  - Include a Process/Skill-signal tag from this closed list ONLY when it applies: api-design, debugging, performance, security
  - Do NOT assign Subsystem/Topic, Phase/Milestone, or Quality-attribute tags (per docs/guidelines/tag_taxonomy.md's other 3 categories) — that broader tagging is explicitly out of scope for this workflow today (deferred to a separate ticket, TCK-20260705-TAG-REGISTRY-QUERY). If none of the 4 Process/Skill-signal tags apply, tags may be an empty array.
```
**Do NOT touch:** `STRUCTURE_SCHEMA` (lines 480-497), the Merge/Split rules (Step 3, lines 530-534), `short_scope`/`related_code_areas`/`acceptance_criteria` rule blocks.
**Verify:** Confirm `TASK_SCHEMA.required` includes `'tags'`, the prompt text contains the new `tags:` rule block (positioned as an addition, not a replacement of an existing rule), and the rule block explicitly excludes the other 3 taxonomy categories rather than inviting general-purpose tagging.

---

### Step 3 — `create-tickets.js`: add `suggested_skills` to `TASK_SCHEMA` and the same mapping lookup to the Structure prompt
**Files:** `.claude/workflows/create-tickets.js`
**Change:** In `TASK_SCHEMA` (same block as Step 2), add:
```js
suggested_skills: {
  type: 'array',
  items: { type: 'string' },
  description: 'Mapped skill(s) from the tag->skill table below; empty array if no tag matches.',
},
```
Add `'suggested_skills'` to `required` as well (default to empty array, matching the ticket-scoper convention decided in Step 1).

Add a second new rule block in the Step 4 prompt, immediately after the `tags:` block added in Step 2:
```
  suggested_skills:
  - Map each assigned tag against this table; empty array if nothing matches:
      api-design  -> /api-design-principles
      debugging   -> /debugging-strategies (or Agent(subagent_type: "world-debugger") if
                     related_code_areas includes a path under src/worldassembly/,
                     src/worldbuilding/, src/worldmodules/, src/content/, or
                     src/core/registries.py)
      performance -> /python-performance-optimization
      security    -> /security-review
  - Do not invent mappings for tags outside this 4-entry table
```
This is a deliberate, ticket-scoped duplication of the Step 1 table (per investigation.md Risk 1 — no shared-location mechanism exists between an agent `.md` file and a workflow's inline prompt string; a 4-entry table does not warrant building one). Keep both copies textually identical when edited going forward — that is a documentation-hygiene note, not new code.

**Do NOT touch:** anything in Step 2's own diff other than adding this second block adjacent to it.
**Verify:** `TASK_SCHEMA.required` includes `'suggested_skills'`; the prompt's mapping table matches Step 1's table entry-for-entry (same 4 tags, same skills, same world-debugger branch condition and file-set).

---

### Step 4 — `create-tickets.js`: make the Write-phase frontmatter template use real tags instead of hardcoded `tags: []`
**Files:** `.claude/workflows/create-tickets.js`
**Change:** At the frontmatter template inside the Write-phase agent prompt (line 681, currently literally `tags: []`), replace with an instruction that substitutes `task.tags` (already present in the JSON blob passed at line 664, since Step 2 added it to `TASK_SCHEMA`):
```
   tags: <substitute task.tags as a YAML flow-sequence, e.g. [tagging, skills]; use [] only if task.tags is empty>
```
**Do NOT touch:** the rest of the frontmatter template (`status`, `authority`, `audience`, `ticket_id`, `phase`, `date` lines 673-680) or the "Map task data to markdown sections" bullet list (lines 684-699) — `tags` lives in frontmatter, not in that body-section list, and must not be duplicated into it.
**Verify:** Confirm the only frontmatter line touched is `tags: []` → the new substitution instruction; `layer` line (already dynamic) is untouched.

---

### Step 5 — `create-tickets.js`: surface `suggested_skills` via `log(...)` for the batch
**Files:** `.claude/workflows/create-tickets.js`
**Change:** After the existing "Enforce short_scope uniqueness" block and before `const outputFolder = ...` (i.e., right after line 619's `droppedScopes` warning block, using `dedupedTasks`), add:
```js
const tasksWithSkills = dedupedTasks.filter(t => t.suggested_skills && t.suggested_skills.length > 0)
if (tasksWithSkills.length > 0) {
  log(`Suggested skills: ${tasksWithSkills.map(t => `${t.short_scope}: ${t.suggested_skills.join(', ')}`).join(' | ')}`)
}
```
This mirrors the existing `log(\`WARNING: duplicate short_scope...\`)` and `log(\`Skipped: ...\`)` patterns already in this phase (lines 590-592, 617-619) — same file, same log-after-compute style, no new logging mechanism introduced.
**Do NOT touch:** the SEQUENCE.md dependency-detection block that follows (lines 720+) — it is unrelated and must not be reordered or merged with this new block.
**Verify:** Trace a synthetic batch with at least one task carrying `tags: ['debugging']` and confirm the log line fires with the expected skill; a batch with no mapped tags produces no such log line (not an empty one — matches the `Skipped` block's own conditional-log convention).

---

### Step 6 — `implement-ticket.js`: add `suggested_skills` to `TICKET_SCHEMA` and both Scope-phase prompt branches
**Files:** `.claude/workflows/implement-ticket.js`
**Change:**
1. In `TICKET_SCHEMA` (lines 29-42), add:
   ```js
   suggested_skills: { type: 'array', items: { type: 'string' }, description: 'Mapped skill(s) for Process/Skill-signal tags on this ticket; empty array if none.' },
   ```
   Do not add it to `required` (lines 31) — the "Load existing ticket" branch (line 46) is a simpler prompt that should still work if an older ticket predates this field; default to `[]` when absent, same tolerance pattern already used for `todos_source_path`.
2. In the "Load the existing ticket" prompt branch (lines 46-62), add a step after Step 2 (read the ticket, extract Tier) instructing the agent to also read the ticket's `tags` frontmatter field and compute `suggested_skills` using the same 4-entry mapping table as `ticket-scoper.md` (embed the table inline in this prompt string, identical to Step 1's/Step 3's table). Add `suggested_skills` to the `Return:` line (currently ending `..., ts=TS.`) as `..., suggested_skills=(computed list, [] if none), ts=TS.`
3. In the "Create a new ticket" prompt branch (lines 63-105), this already invokes `agentType: 'ticket-scoper'` (line 106), so `ticket-scoper.md`'s own Output contract (Step 1 of this plan) already instructs it to compute `suggested_skills`. Just add `suggested_skills` to this branch's `Return:` line (line 101-104) so the schema-driven call surfaces the field: `..., tier (the tier value written into the ticket), suggested_skills (from the mapping table in your Output contract, [] if none), summary (...), ts=TS.`
**Do NOT touch:** the epic-tier short-circuit logic, the monitoring-write agent block (lines 131-181), or any phase after Scope.
**Verify:** For a ticket carrying `tags: [debugging]` with a Related Code Areas entry under `src/content/`, confirm `ticketInfo.suggested_skills` would resolve to the world-debugger suggestion, not `/debugging-strategies`.

---

### Step 7 — `implement-ticket.js`: add the `log(...)` surfacing block
**Files:** `.claude/workflows/implement-ticket.js`
**Change:** Immediately after the existing conflicts block (lines 186-188:
```js
if (ticketInfo.conflicts && ticketInfo.conflicts.length > 0) {
  log(`Conflicts detected: ${ticketInfo.conflicts.join(' | ')}`)
  log('Review conflicts before proceeding. Re-run with ticket_id to continue from existing ticket.')
}
```
) and before the CONFLICTS_DETECTED early-return block, add a new, independent block (does not gate on conflicts — a ticket can have both conflicts and suggested skills):
```js
if (ticketInfo.suggested_skills && ticketInfo.suggested_skills.length > 0) {
  log(`Suggested skill(s): ${ticketInfo.suggested_skills.join(', ')}`)
}
```
Place this after the conflicts block completes (i.e., after line 188, still before the `if (ticketInfo.conflicts...)` early-return at line 189-196, OR after that whole conflict-handling if-block closes — either position is correct since the conflict branch `return`s early only when conflicts exist; put the new block right before that early-return `if`, so it always logs regardless of whether the CONFLICTS_DETECTED path is taken).
**Do NOT touch:** `pushEvent('Scope', ...)` call at line 184 — do not fold `suggested_skills` into the event summary string; keep the event schema as-is (out of scope — the ticket's AC only requires `log(...)` surfacing, not a monitoring-schema change).
**Verify:** Trace the Scope phase for a ticket with `suggested_skills: ['/debugging-strategies']` and confirm the log line appears exactly once, independent of whether conflicts exist.

---

### Step 8 — Write `docs/guides/ticket_tagging.md`
**Files:** `docs/guides/ticket_tagging.md` (new)
**Change:** A thin, developer-facing guide, structured per the ticket's Acceptance Criteria:
- Brief intro: what tags are for, one sentence.
- The 4 categories (Subsystem/Topic, Phase/Milestone, Process/Skill-signal, Quality-attribute), one concrete example tag per category — pull examples directly from `docs/guidelines/tag_taxonomy.md`, do not invent new ones.
- A section: "Skill suggestions from tags" — describe that `Process/Skill-signal` tags (`api-design`, `debugging`, `performance`, `security`) now trigger a `suggested_skills` note from `ticket-scoper` (and from `create-tickets.js` for batch tickets) at ticket-scoping time, complementing `CLAUDE.md`'s file-path-based auto-invoke triggers which fire during editing. Reproduce the same 4-row table as Step 1 (keep all three copies — this doc, `ticket-scoper.md`, `create-tickets.js` — in sync by construction; note explicitly that `security` has no `CLAUDE.md` precedent row, only a `docs/ai/skills.md` catalog entry).
- Closing line: link to `docs/guidelines/tag_taxonomy.md` for canonical-form rules, forbidden tags, and the full (non-closed) category definitions — do not restate them here.
- Frontmatter: `title`, `layer: guidelines`, `authority: P2`, `audience: developer` (match the style of other `docs/guides/*.md` files — check `docs/guides/observability.md`'s frontmatter for the exact key set before writing, since this is a new file and must pass `tools/validate_frontmatter.py`).
**Do NOT touch:** any existing file under `docs/guidelines/` — this is a new, separate guide, not an edit to `tag_taxonomy.md`.
**Verify:** `python3 -m pytest tests/tools/test_validate_frontmatter.py -q` passes with this new file present; manual read confirms all 4 categories + 1 example each + the skill-suggestion section + the tag_taxonomy.md link are present, and no canonical-form/forbidden-tag rules are duplicated.

---

### Step 9 — Add a row to `docs/guides/README.md`'s index table
**Files:** `docs/guides/README.md`
**Change:** Add one row to the table (currently 7 rows, lines 14-20), after the `agent_monitoring.md` row:
```
| [ticket_tagging.md](ticket_tagging.md) | Tag categories, canonical examples, and which tags trigger a skill suggestion |
```
**Do NOT touch:** the existing 7 rows (do not reorder, reword, or remove any), the closing paragraph (lines 22-24).
**Verify:** `git diff docs/guides/README.md` shows exactly one added line inside the table, nothing else changed.

---

### Step 10 — Update `docs/ai/agents.md`'s `ticket-scoper` section
**Files:** `docs/ai/agents.md`
**Change:** In the `### ticket-scoper` section's `**Outputs:**` bullet list (lines 39-42, currently 3 bullets: ticket file, staging directory, conflict report), add a 4th bullet:
```
- `suggested_skills` list (skill/agent invocations mapped from the ticket's `Process/Skill-signal` tags — e.g. `debugging` -> `/debugging-strategies` or `world-debugger`; empty if no tag maps)
```
**Do NOT touch:** the `**What it does:**`, `**Inputs:**`, or `**When to invoke directly:**` subsections of this same block, or the `investigator` section that immediately follows (line 48+), or the summary table at lines 275-285 (adding a column there is out of scope — the table only lists output artifact *types*, one cell per agent, and `suggested_skills` is additive to the existing `tickets/inprogress/{id}.md` cell's meaning, not a new row).
**Verify:** `git diff docs/ai/agents.md` shows exactly one new bullet line under `ticket-scoper`'s Outputs; no other section touched.

---

### Step 11 — Regression check
**Files:** none (verification only)
**Change:** none.
**Do NOT touch:** anything.
**Verify:** Run `python3 -m pytest tests/tools/test_validate_frontmatter.py -q` — must pass. This confirms this ticket's own artifacts (investigation.md, test_plan.md, plan.md, the eventual ticket file, and the new `docs/guides/ticket_tagging.md`) all satisfy taxonomy/canonical-form validation post-2026-07-04 cutoff. No new test cases are added (per test_plan.md — no executable surface exists for agent-prompt or workflow-script text).

## Scope Guards

- Exactly 4 tags in every copy of the mapping table (`ticket-scoper.md`, `create-tickets.js`'s Structure prompt, `implement-ticket.js`'s "Load existing" prompt, `docs/guides/ticket_tagging.md`): `api-design`, `debugging`, `performance`, `security`. Do not add `architecture`, `test-driven-development`, or any other tag — those are explicitly deferred (ticket Out of Scope + Assumptions).
- Do not modify `CLAUDE.md` at all — `git diff CLAUDE.md` must be empty at completion.
- Do not modify `tools/validate_frontmatter.py` — no category-aware enumeration is being added there; the mapping stays local to the 4 prompt/doc locations named above.
- Do not modify `world-debugger.md` — it is a read-only reference for this ticket (confirms the carve-out pattern); its own broader 5-path scope list (including `src/worldgeneration/`) is not imported into the new mapping.
- The world-debugger branch condition's file-set is exactly: `src/worldassembly/`, `src/worldbuilding/`, `src/worldmodules/`, `src/content/`, `src/core/registries.py` — CLAUDE.md's list, verbatim, in all four copies (ticket-scoper.md, create-tickets.js, implement-ticket.js, ticket_tagging.md). Never `src/worldgeneration/`.
- `suggested_skills` is Output/runtime data only — never written into a ticket's frontmatter or body by any of the three prompt edits (Steps 1, 2-3, 6-7). Ticket Format / TASK_SCHEMA's *ticket-file-writing* fields (Step 4's frontmatter template) must not gain a `suggested_skills` line — only `tags` does.
- `create-tickets.js`'s Structure-phase `tags` addition (Step 2) is scoped to Process/Skill-signal-aware tagging sufficient for this ticket's mapping; broader Subsystem/Topic tag-quality work is TCK-20260705-TAG-REGISTRY-QUERY's concern, not this ticket's — do not expand Step 2's prompt rule beyond what's written above.

## Dependency Map

- Step 1 has no dependency; it is the canonical copy the other mapping copies (Steps 3, 6, 8) must match.
- Step 2 must land before Step 3 (suggested_skills in create-tickets.js is meaningless without tags existing first) and before Step 4 (the frontmatter substitution needs `task.tags` to exist on the schema).
- Step 3 depends on Step 2 (same `TASK_SCHEMA` edit region) — implement together in one pass over the file, but keep them as two logically separate diffs per this plan's step split for review clarity.
- Step 5 depends on Step 3 (needs `dedupedTasks[i].suggested_skills` to exist).
- Step 6 depends on Step 1 (the "Create new ticket" branch relies on `ticket-scoper.md`'s Output contract already producing the field; the "Load existing" branch embeds its own copy of the same table).
- Step 7 depends on Step 6 (needs `ticketInfo.suggested_skills` to exist on the schema before it can be logged).
- Steps 8, 9, 10 are independent of each other and of Steps 1-7's code edits, but Step 8's content must textually match Step 1's table (final content dependency, not an ordering dependency — write Step 8 last so it reflects whatever the final Step 1 table looks like after review).
- Step 11 runs last, after all other steps.

## Acceptance Criteria Map

| Acceptance Criterion | Step(s) |
|---|---|
| A tag→skill mapping exists for the 4 tags, readable by `ticket-scoper` | Step 1 |
| `ticket-scoper`'s output includes `suggested_skills` whenever tags include a mapped tag | Step 1, Step 6 |
| `debugging` branches to `world-debugger` matching the CLAUDE.md carve-out | Step 1, Step 3, Step 6 |
| `create-tickets.js`'s Structure phase produces the same suggestion behavior for batch tickets | Step 2, Step 3, Step 4, Step 5 |
| `docs/guides/ticket_tagging.md` exists, covers 4 categories + skill-suggestion behavior, links to `tag_taxonomy.md` | Step 8 |
| `docs/guides/README.md` index table has a new row | Step 9 |
| `docs/ai/agents.md`'s `ticket-scoper` section describes `suggested_skills` | Step 10 |
| (Scope bullet 3, non-checklist) orchestrating session surfaces suggestion via `log(...)` | Step 7 |
| Regression: taxonomy validator still passes | Step 11 |

## Anti-Drift Notes

- All four copies of the tag→skill table (Steps 1, 3, 6, 8) are independent text — there is no shared import mechanism (investigation.md Risk 1, confirmed no clean extension point in `tools/validate_frontmatter.py`). Keeping them in sync is a manual-diff discipline for this ticket and any future edit to the mapping, not a code guarantee. State this explicitly in the ticket's Implementation Notes when done, so a future editor knows to update all four together.
- `security` → `/security-review` has no `CLAUDE.md` precedent row (investigation.md Risk 4) — Implementation Notes should say this plainly rather than imply uniform precedent across all 4 tags, per the ticket's own precedent-wording correction.
- Empty-array convention: `suggested_skills: []` (never omitted, never `null`) when no tag maps — matches the existing `conflicts: []` convention in `implement-ticket.js`'s `TICKET_SCHEMA` and resolves test_plan.md item 2's open "absent vs. empty" question in favor of empty array.
- Do not let Step 2's `tags` field turn into a general tag-quality improvement pass over `create-tickets.js` — it exists solely to unblock Step 3's `suggested_skills` computation for batch tickets. Broader batch-tagging quality is out of this ticket's scope.

## Unresolved Questions

None. All open items from investigation.md's Risks 1-5 are adopted as stated (see Context section above); no placeholder steps are needed.
