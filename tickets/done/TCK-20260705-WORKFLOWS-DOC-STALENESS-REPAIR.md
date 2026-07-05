---
status: historical
layer: ai
authority: P2
audience: agent
ticket_id: TCK-20260705-WORKFLOWS-DOC-STALENESS-REPAIR
phase: done
date: 2026-07-05
tags: [ai, documentation, workflows]
---

# TCK-20260705-WORKFLOWS-DOC-STALENESS-REPAIR

## Title
Fix docs/ai/workflows.md's stale phase lists and add the undocumented simq-audit workflow/skill

## Status
DONE

## Tier
standard

## Type
chore

## Priority
P2

## Request Summary
This staleness has been independently confirmed and disclosed (never fixed) across 3 separate tickets
this session: `TCK-20260705-AI-AGENT-OVERVIEW-DOC`, `TCK-20260705-WORKFLOW-TAG-TUNING-INVESTIGATION`,
and `TCK-20260705-WORKFLOW-SECURITY-GATE`/`TCK-20260705-WORKFLOW-PARITY-SKIP` (which had to cite the
`.js` files directly instead of `docs/ai/workflows.md` for 4 workflows' phase lists). Confirmed facts
(re-verify at Investigate time in case anything shifted since):
- `docs/ai/workflows.md` documents `create-tickets` as 3 phases (`Parse`/`Write`/`Link`); the actual
  `.claude/workflows/create-tickets.js` has 5 (`Comprehend`/`Investigate`/`Structure`/`Write`/`Link`).
- `generate-simulation-setup`: docs say `Spec Draft → Validation → Promotion`; code has
  `Scan → Draft → Validate`.
- `investigate-simulation-result`: docs list an extra, nonexistent `Correlate` phase; code has
  `Load → Analyze → Report` (3 phases, not 4).
- `compact-simulation-result`: docs say `Inventory → Compact → Archive`; code has
  `Scan → Compact → Archive`.
- `simq-audit.js` (7 phases: `Recalibrate → Classify Drift → Update Anchors → Sync Docs → Parity Check →
  Verify → Report`) is an 11th workflow file, entirely undocumented in `docs/ai/workflows.md`'s catalog
  and in `docs/ai/skills.md`'s two skill tables.
- `docs/ai/README.md`'s Document Index literally says "All 8 workflows" for `workflows.md` — undercounts
  both the 10 actually documented there and the 11 actual files in `.claude/workflows/`.
- `docs/ai/agent_infrastructure_audit.md`'s inventory counts ("10 files / 8 documented" workflows, "14"
  project skills) are themselves stale relative to `simq-audit.js`'s addition — this is a dated,
  historical snapshot (2026-07-03) and should NOT be edited to "fix" this (see Out of Scope); it is
  correctly a point-in-time artifact.

## Scope
- Fix `docs/ai/workflows.md`'s phase lists for the 4 stale workflows (`create-tickets`,
  `generate-simulation-setup`, `investigate-simulation-result`, `compact-simulation-result`) — re-verify
  each against the live `.claude/workflows/*.js` file directly before writing, per this session's own
  established discipline of never trusting a stale citation without re-checking.
- Add `simq-audit` as an 11th entry to `docs/ai/workflows.md`'s workflow catalog (phase table, args,
  return values), matching the existing per-workflow section format.
- Add `simq-audit` to `docs/ai/skills.md`'s "Project Skills (Workflow Shortcuts)" table and
  "Project-Level Skill Files" table (it has both a workflow and a dedicated skill folder,
  `.claude/skills/simq-audit/SKILL.md` — confirm both need an entry, per the existing dual-table
  pattern for other workflow-backed skills).
- Fix `docs/ai/README.md`'s Document Index row for `workflows.md`: replace "All 8 workflows" with an
  accurate description (recommend mirroring `docs/ai/system_overview.md`'s own established phrasing:
  "10 documented development and simulation workflows, plus `simq-audit` as an 11th").
- Cross-check `docs/ai/system_overview.md`'s own Section 6 dated note (2026-07-05) against this ticket's
  actual fixes once complete — that note currently says these docs "do not yet" match code; once this
  ticket lands, either remove the note (if `system_overview.md` is in this ticket's edit scope) or leave
  it and flag the now-stale disclosure as a fast-follow one-liner (Investigate/Plan should decide which,
  since `system_overview.md` wasn't originally listed as this ticket's own edit target).

## Out of Scope
- `docs/ai/agent_infrastructure_audit.md` — a dated, historical point-in-time snapshot; do not edit its
  counts to match current reality, that would falsify its own "as of 2026-07-03" framing.
- Any code change — this is pure documentation repair, zero `.claude/workflows/*.js` or `.claude/agents/*.md`
  edits.
- The 4 gate-determinism tickets (`tickets/todos/gate-determinism-followups/`) — unrelated initiative,
  same session, do not conflate.

## Acceptance Criteria
- [ ] All 4 previously-stale phase lists in `docs/ai/workflows.md` match their live `.claude/workflows/*.js`
      files exactly, re-verified at Investigate/Implement time, not copied from this ticket's own citations.
- [ ] `simq-audit` is documented in `docs/ai/workflows.md`'s catalog and both of `docs/ai/skills.md`'s
      skill tables.
- [ ] `docs/ai/README.md`'s "All 8 workflows" line is corrected.
- [ ] `docs/ai/system_overview.md`'s Section 6 dated staleness note is either removed (if this ticket's
      fixes make it obsolete and the file is in scope) or explicitly left with a note explaining why,
      not silently forgotten.
- [ ] No other content in any touched file is modified.

## Related Tickets
- TCK-20260705-AI-AGENT-OVERVIEW-DOC (first disclosed this staleness)
- TCK-20260705-WORKFLOW-TAG-TUNING-INVESTIGATION (re-disclosed it, recommended this exact follow-up)
- TCK-20260705-WORKFLOW-SECURITY-GATE, TCK-20260705-WORKFLOW-PARITY-SKIP (had to work around the
  staleness by citing `.js` files directly instead of this doc)

## Related Docs
- docs/ai/workflows.md (primary edit target)
- docs/ai/skills.md (edit target — simq-audit entries)
- docs/ai/README.md (edit target — workflow count line)
- docs/ai/system_overview.md (conditional edit target — dated staleness note)
- docs/ai/agent_infrastructure_audit.md (read-only reference, do not edit)
- docs/simulation_quality/audit_workflow.md (source of truth for simq-audit's own phase list — already
  confirmed accurate against code, per this session's own investigation)

## Related Stored Artifacts
None yet.

## Related Code Areas
- .claude/workflows/create-tickets.js, generate-simulation-setup.js, investigate-simulation-result.js,
  compact-simulation-result.js, simq-audit.js (read-only reference — source of truth for phase names)
- .claude/skills/simq-audit/SKILL.md (read-only reference)

## Assumptions / Open Questions
- Whether `docs/ai/system_overview.md`'s dated staleness note should be removed or left/annotated once
  this ticket lands — left for Investigate/Plan, since that file wasn't originally in this ticket's own
  scope until this cross-check was added.

## Implementation Notes
Implemented all 8 steps from the approved plan exactly, in order. Pure documentation edit — zero code
changes. Re-verified every phase-name citation directly against the live `.claude/workflows/*.js` files
(`grep -n "phase("`) before writing, per this session's established discipline; all matched the plan's
and investigation's citations exactly, nothing had shifted since 2026-07-06.

1. `docs/ai/workflows.md` `create-tickets` Phases table: expanded 3 rows (`Parse`/`Write`/`Link`) to 5
   (`Comprehend`/`Investigate`/`Structure`/`Write`/`Link`), condensing descriptive language from
   `system_overview.md` §3 to the table's terse one-line style, cross-checked against
   `create-tickets.js`'s `phase()` call sites (lines 39, 204, 446, 672, 847).
2. `generate-simulation-setup` Phases line: `Spec Draft → Validation → Promotion` → `Scan → Draft →
   Validate`.
3. `investigate-simulation-result` Phases line: dropped the phantom `Correlate` phase — `Load → Analyze
   → Correlate → Report` → `Load → Analyze → Report`.
4. `compact-simulation-result` Phases line: `Inventory → Compact → Archive` → `Scan → Compact →
   Archive` (phase 1's `phase()` marker and `meta.phases` title are both `Scan`; `Inventory` only
   appears in that phase's task-description text).
5. Added a new `### \`simq-audit\`` catalog section to `workflows.md`, inserted after
   `update-knowledge-store` and before `## Simulation Workflow Order`, using the plain
   Purpose/Phases/Args/Outputs/When-to-use shape (matching `compact-simulation-result`/
   `update-knowledge-store`, not the `implement-ticket`-style Agent/Gate table), plus a small 2-row
   Return Values table for the `DONE_NO_TICKET`/`NEEDS_TICKET` branch — content sourced from
   `docs/simulation_quality/audit_workflow.md` §2-§4. Did not add it to the `## Simulation Workflow
   Order` diagram (standalone quality lane, not part of that 7-workflow chain).
6. Added exactly one row (`/simq-audit`) to `docs/ai/skills.md`'s "Project Skills (Workflow Shortcuts)"
   table only, after the `/update-knowledge-store` row. Did not add it to "Project-Level Skill Files"
   per investigation.md Risk #1 (that table is scoped to non-workflow-triggered skills by its own
   header text; `create-tickets`/`implement-ticket`/`implement-epic` are precedent for
   workflow+SKILL.md skills appearing only in the Workflow Shortcuts table).
7. `docs/ai/README.md` line 40: `All 8 workflows...` → `10 documented development and simulation
   workflows, plus \`simq-audit\` as an 11th — phases, args, return values, when to use`.
8. `docs/ai/system_overview.md`: deleted the entire `**Note (as of 2026-07-05):**` paragraph (Section 6)
   with no double-blank-line artifact left behind, and struck the 4 dangling "see Section 6"
   parentheticals at the sentences referencing `create-tickets` (line ~62), `generate-simulation-setup`,
   `investigate-simulation-result`, and `compact-simulation-result` (the three consecutive bullets under
   §4) — each parenthetical removed entirely, leaving the main clause (phase names sourced directly from
   the `.js` file) intact and accurate, per architecture review round 1's expanded Step 8.

No deviations from the approved plan — all 8 steps implemented exactly as specified.

## Test Summary
No pytest applies (zero code changes). Ran the plan's/test_plan's manual verification commands instead:
- `grep -n "Section 6" docs/ai/system_overview.md` → zero matches (confirmed).
- `grep -c simq-audit docs/ai/skills.md` → `1` (confirmed, single row in the single correct table).
- `git diff --name-only | grep -vE '^(docs/ai/workflows\.md|docs/ai/skills\.md|docs/ai/README\.md|docs/ai/system_overview\.md|tickets/|staging_artifacts/|stored_artifacts/|agent-monitoring/)'` →
  empty output (confirmed, no scope creep).
- `git diff --stat -- docs/ai/agent_infrastructure_audit.md` → empty (confirmed untouched).
- `git diff --stat -- '.claude/workflows/*.js' '.claude/agents/*.md'` → empty (confirmed zero code
  changes).
- Full diff review of all 4 touched files (`git diff`) confirmed no line changed beyond what each step
  specified.

## Files Changed
- `docs/ai/workflows.md` — 4 phase-line fixes + new `simq-audit` catalog section
- `docs/ai/skills.md` — 1 new row in Workflow Shortcuts table
- `docs/ai/README.md` — 1 line fix (Document Index row)
- `docs/ai/system_overview.md` — Section 6 note removed + 4 dangling parentheticals struck

## Completion Summary
All 8 plan steps implemented exactly as specified; zero deviations. Pure documentation repair —
`docs/ai/workflows.md`'s 4 stale phase lists now match their live `.claude/workflows/*.js` files exactly,
`simq-audit` is now documented as the 11th workflow (in `workflows.md`'s catalog and `skills.md`'s
Workflow Shortcuts table only, per the corrected single-table scope), `README.md`'s workflow count is
accurate, and `system_overview.md`'s now-obsolete Section 6 disclosure and its 4 dependent
cross-references are gone. No code changed; no parity ledger entries affected.

Verify-phase done-checker caught that this was the sole occupant of `tickets/todos/ai-docs-followups/`,
which was left as an empty skeleton folder rather than archived per CLAUDE.md's rule ("Never leave a
completed folder's skeleton in `tickets/todos/`"). Fixed: `mv tickets/todos/ai-docs-followups
tickets/done/ai-docs-followups`.
