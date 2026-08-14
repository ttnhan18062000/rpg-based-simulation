---
status: historical
layer: ai
authority: P2
audience: agent
ticket_id: TCK-20260705-WORKFLOWS-DOC-STALENESS-REPAIR
artifact_type: plan
tags: [ai, documentation, workflows]
---

# Implementation Plan — TCK-20260705-WORKFLOWS-DOC-STALENESS-REPAIR

## Summary

This is a pure prose/table correction across four `docs/ai/` files — zero code changes, zero tests. The
plan breaks the ticket's scope into 8 narrow, independently-verifiable doc-edit steps: four phase-list
corrections in `docs/ai/workflows.md` (one per stale workflow), one new catalog section for the
previously-undocumented `simq-audit` workflow, one new table row in `docs/ai/skills.md` (a single table,
per the investigation's Risk #1 correction — not both tables as the ticket's own text originally
claimed), one line fix in `docs/ai/README.md`, and one deletion in `docs/ai/system_overview.md` §6. Every
step re-verifies its source-of-truth against the live `.claude/workflows/*.js` file (or
`docs/simulation_quality/audit_workflow.md` §2/§3 for `simq-audit`, already confirmed accurate) rather
than trusting the ticket's or investigation's own citations, per this session's established discipline.
Since there is no code path and no automated doc/code parity checker for `docs/ai/`, every step's
"Verify" is the matching manual-review checklist item from `test_plan.md`, not a pytest command.

## Steps

### Step 1 — Fix `create-tickets` phase table
**Files:** `docs/ai/workflows.md` (lines 34-40, the `### \`create-tickets\`` section's Phases table)
**Change:** Replace the 3-row table (`Parse | Write | Link`) with 5 rows: `Comprehend`, `Investigate`,
`Structure`, `Write`, `Link`. Re-derive each row's "What happens" text directly from
`.claude/workflows/create-tickets.js`'s `phase()` call sites (lines 39, 204, 446, 672, 847) and the
task descriptions passed at each call site — do not invent prose. `docs/ai/system_overview.md` §3
(lines 63-71, itself already independently confirmed accurate for phase names via
`docs/agent-monitoring/schema.md`'s `events.jsonl` phase list) has usable descriptive language for each
of the 5 phases that may be condensed into the table's terse one-line style; cross-check it but pull
the authoritative phase names and order from the `.js` file, not from `system_overview.md`.
**Do NOT touch:** The `Args`, `Usage`, `Typical full flow`, or `Artifacts produced` subsections
immediately below the table — only the Phases table itself changes.
**Verify:** test_plan.md manual checklist item 1 ("`create-tickets` phase table lists exactly:
Comprehend, Investigate, Structure, Write, Link (5 rows)").

### Step 2 — Fix `generate-simulation-setup` phase line
**Files:** `docs/ai/workflows.md` (line 190, `### \`generate-simulation-setup\`` section)
**Change:** Replace `**Phases:** Spec Draft → Validation → Promotion` with
`**Phases:** Scan → Draft → Validate`, matching `.claude/workflows/generate-simulation-setup.js`'s
`meta.phases` array and `phase()` call sites (lines 15, 39, 83).
**Do NOT touch:** The Args table, Outputs line, or When-to-use line in the same section.
**Verify:** test_plan.md manual checklist item 2.

### Step 3 — Fix `investigate-simulation-result` phase line
**Files:** `docs/ai/workflows.md` (line 256, `### \`investigate-simulation-result\`` section)
**Change:** Replace `**Phases:** Load → Analyze → Correlate → Report` (4 phases) with
`**Phases:** Load → Analyze → Report` (3 phases) — drop the phantom `Correlate` phase entirely, per
`.claude/workflows/investigate-simulation-result.js`'s `meta.phases` array and `phase()` call sites
(lines 18, 40, 77); no `Correlate` phase exists anywhere in that file.
**Do NOT touch:** The Args table, Outputs bullets, or When-to-use line in the same section.
**Verify:** test_plan.md manual checklist item 3.

### Step 4 — Fix `compact-simulation-result` phase line
**Files:** `docs/ai/workflows.md` (line 300, `### \`compact-simulation-result\`` section)
**Change:** Replace `**Phases:** Inventory → Compact → Archive` with
`**Phases:** Scan → Compact → Archive` — the first phase's `phase()` marker and `meta.phases` title in
`.claude/workflows/compact-simulation-result.js` are both `Scan`, not `Inventory` (the phase 1 agent's
task description says "Inventory the simulation log files," which is the likely source of the original
mislabeling, but the phase name itself is `Scan`).
**Do NOT touch:** The Args table or When-to-use line in the same section (this section has no separate
`Outputs` line in the current doc — leave that as-is, it is not part of this ticket's scope).
**Verify:** test_plan.md manual checklist item 4.

### Step 5 — Add the `simq-audit` catalog section to `docs/ai/workflows.md`
**Files:** `docs/ai/workflows.md` (insert a new `### \`simq-audit\`` section immediately after the
`### \`update-knowledge-store\`` section ends, i.e. after line 347's content and its trailing `---`
separator, and before the `## Simulation Workflow Order` heading at line 351)
**Change:** Add one new section following the same Purpose/Phases/Args/Outputs/When-to-use shape used
by sibling "Simulation Workflows" entries (e.g. `compact-simulation-result`, `update-knowledge-store`)
— explicitly NOT the `implement-ticket`-style Agent/Gate-condition table format, since `simq-audit` has
no per-phase agent/gate table precedent among the existing simulation-workflow sections. Content,
sourced from `docs/simulation_quality/audit_workflow.md` §2 (confirmed accurate against
`.claude/workflows/simq-audit.js`'s 7 `phase()` call sites at lines 97, 131, 190, 254, 293, 327, 396)
and §3/§4 of the same doc:
  - **Purpose:** a narrow calibration and anchor-drift maintenance lane for the 10-pillar SimQ grading
    system — recalibrates against `grade_anchors.json`, classifies drift, and either closes out cleanly
    or spawns a follow-up ticket. Never changes SimQ scoring formulas or pillar logic
    (`src/simulation_quality/*` is out of scope for every phase).
  - **Phases:** Recalibrate → Classify Drift → Update Anchors → Sync Docs → Parity Check → Verify →
    Report (7 phases, one line each summarizing what each phase does — pull the one-line summaries from
    `audit_workflow.md` §2's numbered list, condensed to table-row length to match sibling sections'
    density).
  - **Args:** `mode` (`fast` default / `full` / `slow`), `worlds` (optional comma-separated scope, only
    meaningful with `mode=full`) — per `audit_workflow.md` §4.
  - **Outputs:** updated `grade_anchors.json` / `FAST_ANCHOR_KEYS` / `SLOW_ANCHOR_KEYS` (Update Anchors
    phase, `EXPECTED_DRIFT` items only); updated `docs/simulation_quality/eval_matrix_results.md` and
    `docs/audits/D20_simq_integration.md`, conditionally `event_type_coverage.md` and
    `v2_intentional_divergences.md` (Sync Docs phase); updated `docs/parity_ledger/*.yaml` entries
    (Parity Check phase); either a suggested no-ticket chore-commit message or one spawned follow-up
    ticket (Report phase, see Return values below).
  - **When to use:** After a SimQ-related uplift ticket lands, or on a recalibration cadence, to check
    anchor/grade drift without re-deriving the manual process by hand (see
    `audit_workflow.md` §1 for the manual sequence this replaces).
  - **Return values (small table, mirroring `implement-epic`'s Return-values table style):**
    `DONE_NO_TICKET` (verdict was `no_regression` — no ticket created, suggested chore-commit message
    emitted) and `NEEDS_TICKET` (verdict was `regression` or `needs_da_decision` — one ticket spawned via
    `ticket-scoper`, hand off with `/implement-ticket ticket_id=<new-id>`), per `audit_workflow.md` §3.
**Do NOT touch:** The `## Simulation Workflow Order` diagram immediately below (lines 351-373) —
`simq-audit` is a standalone-invocable quality lane, not part of the 7-workflow generation-to-cleanup
chain that diagram depicts (confirmed by `system_overview.md` §5: "It is standalone-invocable and does
not require or by default create a ticket"). Do not add it to that diagram.
**Verify:** test_plan.md manual checklist item 5.

### Step 6 — Add `simq-audit` to `docs/ai/skills.md`'s Workflow Shortcuts table only
**Files:** `docs/ai/skills.md` (the "Project Skills (Workflow Shortcuts)" table, lines 46-57)
**Change:** Add exactly one new row: `| \`/simq-audit\` | \`simq-audit\` | <when-to-use text> |`,
placed after the `/update-knowledge-store` row (line 57), matching the existing row format and
column widths. Suggested when-to-use text: "Check SimQ grade/anchor drift after a calibration corpus
change; closes cleanly or spawns a follow-up ticket."
**Do NOT touch:** The "Project-Level Skill Files" table (lines 146-164). Per investigation.md Risk #1,
that table's own header (line 148: "Python and engineering patterns adapted for this project") scopes it
to non-workflow-triggered skills only. `create-tickets`, `implement-ticket`, and `implement-epic` are
the existing precedent of workflow-triggered skills that also have a dedicated `SKILL.md` file yet
correctly appear in only the Workflow Shortcuts table — never in Project-Level Skill Files. Adding
`simq-audit` there would introduce a new inconsistency, not fix one. This is a narrowing of the
ticket's original AC text ("both of skills.md's skill tables") to "one table, correctly" — already
resolved by the orchestrating session, not an open question for this plan.
**Do NOT touch:** The "Choosing the Right Tool" table (lines 167-182) or any other section of
`skills.md` — out of scope; the ticket only calls for the one workflow-shortcuts row.
**Verify:** test_plan.md manual checklist item 6, plus the anti-drift guard
`grep -c simq-audit docs/ai/skills.md` equals 1 (one occurrence, one row, one table).

### Step 7 — Fix `docs/ai/README.md`'s workflow count line
**Files:** `docs/ai/README.md` (line 40, Document Index table row for `workflows.md`)
**Change:** Replace `All 8 workflows — phases, args, return values, when to use` with accurate text
reflecting 10 documented + `simq-audit` as an 11th, e.g.: `10 documented development and simulation
workflows, plus simq-audit as an 11th — phases, args, return values, when to use` (mirrors
`system_overview.md` §2's own established phrasing style: "10 of them are documented... The 11th,
simq-audit.js... "). Exact wording is Implement's call as long as it accurately states 10 documented +
the 11th, not a bare recount to "11".
**Do NOT touch:** Any other row in the Document Index table (lines 36-44), including the `agents.md` row
(line 39, "All 11 subagents" — already accurate, not part of this ticket) or the
`agent_infrastructure_audit.md` row (line 43) — that row's own description ("2026-07-03") is correct as
a dated-snapshot label and must not be touched.
**Verify:** test_plan.md manual checklist item 7.

### Step 8 — Remove `docs/ai/system_overview.md` §6's dated staleness note, and its 4 dangling in-file cross-references
**Files:** `docs/ai/system_overview.md` (Section 6 note, lines 243-248; plus 4 cross-referencing
parentheticals at lines 62, 152-153, 156, and 158-159)
**Change (expanded per architecture review round 1, CONFIRMED finding):**
1. Delete the entire paragraph beginning `**Note (as of 2026-07-05):**` and ending `...this
   document does not modify those files.` (lines 243-248), including its surrounding blank line so no
   double-blank-line artifact is left between the preceding paragraph (ending `...this overview does not
   re-derive or re-score it.`, line 241) and the following `### Where to go deeper` heading (line 250).
2. **Also strike the 4 parentheticals elsewhere in this same file that cross-reference the note being
   deleted in sub-step 1 — this is a direct, mechanical, same-cause consequence of sub-step 1, not new
   scope**, since removing Section 6 would otherwise leave 4 dangling "see Section 6" pointers to a
   section that no longer exists, which is strictly worse than today's state (an accurate, if
   stale-flagged, note):
   - Line 62: change `...docs/ai/workflows.md's prose (which documents only 3 phases there — see
     Section 6's dated note).` → `...docs/ai/workflows.md's prose.` (drop the parenthetical entirely —
     once Steps 1-4 land, `workflows.md` documents all 5 phases correctly, so the parenthetical's claim
     is no longer true either, not just its "see Section 6" pointer).
   - Lines 152-153: change `...(not workflows.md, whose prose here is stale — see Section 6).` →
     delete the parenthetical entirely (the preceding sentence, "sourced directly from
     `.claude/workflows/generate-simulation-setup.js`", stands complete without it).
   - Line 156: change `...(not workflows.md, which lists an extra, nonexistent 4th phase — see Section
     6).` → delete the parenthetical entirely, same reasoning.
   - Lines 158-159: change `...(not workflows.md, whose first phase name is stale there — see Section
     6).` → delete the parenthetical entirely, same reasoning.
   In each of the 4 cases, deleting the parenthetical clause is sufficient — the sentence's main claim
   (phase names sourced directly from the `.js` file) remains accurate and complete on its own; no
   sentence needs restructuring beyond removing the trailing parenthetical.
Rationale for sub-step 1 (already resolved by the orchestrating session, not an open question here): the
note explicitly frames itself as pointing at "candidates for a future documentation-maintenance ticket" —
exactly this ticket's scope. Once Steps 1-7 land, the note has no remaining referent and would itself
become a stale artifact if left in place, even annotated. Rationale for sub-step 2: these 4 parentheticals
assert current facts ("documents only 3 phases," "is stale," "nonexistent 4th phase," "first phase name is
stale") that Steps 1-4 make false, and each also points at a section (6) that sub-step 1 deletes — leaving
either the false claim or the dangling pointer would be a new, self-inflicted defect this exact ticket
created, not a pre-existing one being deferred.
**Do NOT touch:** Any other content in `system_overview.md` beyond the note (sub-step 1) and the 4 named
parentheticals (sub-step 2) — in particular, do not touch the surrounding sentences' main clauses (only
the trailing parenthetical is removed in each case), and do not touch Sections 2/3/4's other content.
**Verify:** test_plan.md manual checklist item 8 (updated — see below) plus a fresh
`grep -n "Section 6" docs/ai/system_overview.md` returning zero matches after this step.

## Scope Guards

- Do not touch `docs/ai/agent_infrastructure_audit.md` under any circumstances — dated point-in-time
  snapshot (2026-07-03), explicitly out of scope; its stale counts must not be "corrected."
- Do not touch any `.claude/workflows/*.js` or `.claude/agents/*.md` file — zero code changes, this
  entire ticket is documentation-only.
- Do not touch `tickets/todos/gate-determinism-followups/` — unrelated initiative, same session.
- Do not add `simq-audit` to `skills.md`'s "Project-Level Skill Files" table (Step 6).
- Do not alter `implement-ticket.js`'s or `implement-epic.js`'s existing sections/rows in
  `workflows.md` — already correct/current per recent sibling tickets, not part of this ticket's 4 named
  targets (Steps 1-4) or the new addition (Step 5).
- Do not add `simq-audit` to the `## Simulation Workflow Order` diagram in `workflows.md` (Step 5) — it
  is a standalone quality lane, not part of that 7-workflow chain.
- Step 8 DOES include striking the 4 "see Section 6" parentheticals in Sections 2-4 (revised per
  architecture review round 1) — this is a direct, same-cause consequence of deleting Section 6, not
  scope creep. Do not go further and rewrite/restructure the sentences those parentheticals sit in
  beyond removing the trailing parenthetical clause itself.
- No other line in any of the five touched files (`docs/ai/workflows.md`, `docs/ai/skills.md`,
  `docs/ai/README.md`, `docs/ai/system_overview.md`) may change — confirm via
  `git diff --name-only | grep -vE '^(docs/ai/workflows\.md|docs/ai/skills\.md|docs/ai/README\.md|docs/ai/system_overview\.md|tickets/|staging_artifacts/|stored_artifacts/|agent-monitoring/)'`
  returning empty output.

## Dependency Map

All 8 steps are independent — each touches a distinct file/section and can be completed and verified in
any order. Recommended execution order (1-8 as listed) only groups the four `workflows.md` phase-line
fixes (Steps 1-4) before the new `workflows.md` section addition (Step 5) for easier diff review of that
one file, but this is a convenience ordering, not a hard dependency.

## Acceptance Criteria Map

| AC from ticket | Implemented by step(s) | Verified by test |
|---|---|---|
| All 4 previously-stale phase lists in `workflows.md` match live `.js` files exactly | Steps 1, 2, 3, 4 | test_plan.md checklist items 1-4 |
| `simq-audit` documented in `workflows.md`'s catalog and in `skills.md`'s tables (narrowed to the one correct table per investigation Risk #1) | Steps 5, 6 | test_plan.md checklist items 5, 6 |
| `docs/ai/README.md`'s "All 8 workflows" line corrected | Step 7 | test_plan.md checklist item 7 |
| `system_overview.md` §6's dated note removed (resolved: remove, not annotate) | Step 8 | test_plan.md checklist item 8 |
| No other content in any touched file is modified | All steps' "Do NOT touch" clauses + Scope Guards | test_plan.md's `git diff --name-only` guard and full-diff manual review |

## Anti-Drift Notes

- **`skills.md` table placement (Step 6) is a correction, not a re-confirmation.** The ticket's own text
  claimed a "dual-table pattern" requiring both tables; investigation.md Risk #1 disproved this by
  checking `create-tickets`/`implement-ticket`/`implement-epic` directly — none of them appear in
  "Project-Level Skill Files" despite each having a dedicated `SKILL.md` folder. The two tables are
  mutually exclusive by category (workflow-triggered vs. standalone pattern), not by "has a SKILL.md
  file." Implementer must add exactly one row, in Workflow Shortcuts only.
- **`compact-simulation-result`'s Step 4 fix is a one-word change with a subtle root cause.** The docs
  said `Inventory`; the code's `phase()` marker and `meta.phases` title both say `Scan`. The word
  "Inventory" does appear in that phase's *task description* text passed to the agent — that is likely
  why the ticket-writer originally mislabeled it. Do not "split the difference" by keeping `Inventory` in
  the doc; the phase name is `Scan`, full stop.
- **Step 5's format choice is deliberate.** `simq-audit` must use the plain Purpose/Phases/Args/Outputs/
  When-to-use shape (matching `compact-simulation-result`/`update-knowledge-store`), not the
  `implement-ticket`-style Agent/Gate-condition table — there is no per-phase agent/gate precedent for it
  among the existing simulation-workflow sections. Only the Return Values sub-part (a small 2-row table)
  deviates from the plainest sibling sections, justified because `simq-audit.js`'s Report phase has a
  genuine binary branch (`DONE_NO_TICKET` / `NEEDS_TICKET`) worth surfacing, per
  `docs/simulation_quality/audit_workflow.md` §3.
- **Corrected per architecture review round 1 (CONFIRMED finding): the 4 "see Section 6" cross-references
  in Sections 2-4 are fixed IN this ticket, not deferred.** An earlier draft of this plan treated these as
  a residual inconsistency to leave for a fast-follow ticket, reasoning that the ticket's AC restricts the
  `system_overview.md` edit to "Section 6's dated staleness note" plus "no other content... modified."
  Architecture review correctly rejected this: unlike the ticket's original pre-existing staleness (which
  this ticket didn't create), these 4 dangling pointers would be manufactured by Step 8's own deletion, in
  the same file, in the same edit — deferring a defect you are about to create yourself is not the same as
  deferring one you merely found. Step 8 now strikes all 4 parentheticals as part of the same causal edit
  (see Step 8 above) — this is the minimum necessary consequence of removing Section 6, not scope
  expansion beyond it.
- No mechanics/engine-contract constraints apply (per investigation.md) — this is `docs/ai/` process
  documentation, not simulation law; no `docs/mechanics/` or `docs/engine/` cross-check is needed.
