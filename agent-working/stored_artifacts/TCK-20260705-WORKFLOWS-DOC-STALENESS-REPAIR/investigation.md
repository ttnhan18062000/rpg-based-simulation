---
status: historical
layer: ai
authority: P2
audience: agent
ticket_id: TCK-20260705-WORKFLOWS-DOC-STALENESS-REPAIR
artifact_type: investigation
tags: [ai, documentation, workflows]
---

# Investigation — TCK-20260705-WORKFLOWS-DOC-STALENESS-REPAIR

## Current Behavior

All six of the ticket's cited discrepancies were re-verified directly against live files today
(2026-07-06, one day after the ticket's own investigation). **All six are still present, unchanged.**
Nothing shifted. One new fact was found that the ticket got wrong (see Risks section — the
"dual-table pattern" claim for `skills.md`).

### 1. `create-tickets` — confirmed stale, 3 documented vs. 5 actual

- `docs/ai/workflows.md:34-40` (table): `Parse | Write | Link` — 3 rows.
- `.claude/workflows/create-tickets.js` — `phase()` call sites at lines 39 (`Comprehend`), 204
  (`Investigate`), 446 (`Structure`), 672 (`Write`), 847 (`Link`, conditional on `epicId`) — 5 phases.
  The file's own `meta.phases` array (lines 4-9) declares the same 5 titles.
- Ticket's claim is accurate: docs need `Comprehend → Investigate → Structure → Write → Link`.

### 2. `generate-simulation-setup` — confirmed stale

- `docs/ai/workflows.md:190`: `**Phases:** Spec Draft → Validation → Promotion`.
- `.claude/workflows/generate-simulation-setup.js:4-7` (`meta.phases`) and `phase()` calls at lines 15
  (`Scan`), 39 (`Draft`), 83 (`Validate`) — 3 phases: `Scan → Draft → Validate`.
- Ticket's claim is accurate.

### 3. `investigate-simulation-result` — confirmed stale (phantom phase)

- `docs/ai/workflows.md:256`: `**Phases:** Load → Analyze → Correlate → Report` — 4 phases.
- `.claude/workflows/investigate-simulation-result.js:4-7` (`meta.phases`) and `phase()` calls at
  lines 18 (`Load`), 40 (`Analyze`), 77 (`Report`) — only 3 phases. No `Correlate` phase exists
  anywhere in the file (grep for `Correlate` in the `.js` returns nothing).
- Ticket's claim is accurate: `Correlate` must be dropped from the docs table.

### 4. `compact-simulation-result` — confirmed stale

- `docs/ai/workflows.md:300`: `**Phases:** Inventory → Compact → Archive`.
- `.claude/workflows/compact-simulation-result.js:4-7` (`meta.phases`) and `phase()` calls at lines 14
  (`Scan`), 32 (`Compact`), 66 (`Archive`) — phase 1 is titled `Scan`, not `Inventory` (the phase 1
  agent's *task description* says "Inventory the simulation log files," which is likely the source of
  the ticket-writer's confusion, but the `phase()` marker and `meta.phases` title are both `Scan`).
- Ticket's claim is accurate.

### 5. `simq-audit` — confirmed fully undocumented as an 11th workflow

- `.claude/workflows/*.js` listing: 11 files total — `compact-simulation-result.js`,
  `create-tickets.js`, `generate-simulation-setup.js`, `implement-epic.js`, `implement-ticket.js`,
  `investigate-simulation-result.js`, `prepare-simulation-execution.js`,
  `propose-simulation-enhancements.js`, `register-simulation-result.js`, `simq-audit.js`,
  `update-knowledge-store.js`.
- `docs/ai/workflows.md` `### \`...\`` section headers: 10 total (all of the above except
  `simq-audit`). Confirmed via `grep -n "^### \`" docs/ai/workflows.md`.
- `simq-audit.js` phases confirmed via `phase()` call sites (lines 97, 131, 190, 254, 293, 327, 396):
  `Recalibrate → Classify Drift → Update Anchors → Sync Docs → Parity Check → Verify → Report` — 7
  phases, matching the ticket's claim exactly, and matching `docs/simulation_quality/audit_workflow.md`
  section 2 (`## 2. The 7-phase pipeline`, same 7 names in the same order) — that doc **is** accurate
  against code, confirming the ticket's claim that it can be used as the copy source.
- `docs/ai/skills.md`: no `simq-audit` row in either table (grepped for `-i "simq"`, zero hits before
  this ticket's edits).
- `docs/ai/system_overview.md` §5 ("Quality Lanes") **already documents** `simq-audit`'s 7 phases
  correctly, in the same order, with the same names — this file is NOT stale on this point. Only
  `workflows.md` and `skills.md` are missing simq-audit entirely.

### 6. `docs/ai/README.md` Document Index — confirmed stale

- Line 40: `| [workflows.md](workflows.md) | All 8 workflows — phases, args, return values, when to
  use |`.
- Actual: 10 documented in `workflows.md`, 11 real `.js` files. Ticket's claim is accurate. Ticket's
  suggested replacement text ("10 documented development and simulation workflows, plus `simq-audit`
  as an 11th") mirrors `system_overview.md`'s own established phrasing style and is a reasonable target
  string, though the exact wording is Plan/Implement's call, not fixed by this investigation.

### `docs/ai/system_overview.md` §6 dated note — confirmed still present, verbatim

Lines 226-231 (Section 6, "Observability and Where to Go Deeper"):

> **Note (as of 2026-07-05):** `docs/ai/workflows.md` does not yet document `simq-audit` as an 11th
> workflow, and its phase lists for `create-tickets`, `generate-simulation-setup`,
> `investigate-simulation-result`, and `compact-simulation-result` do not match the current
> `.claude/workflows/*.js` phase arrays (this document cites the `.js` files directly for those four).
> `docs/ai/skills.md` similarly does not yet list a `/simq-audit` skill entry. These are candidates for
> a future documentation-maintenance ticket; this document does not modify those files.

This note is currently **accurate** (nothing has fixed the staleness yet). Once this ticket's Scope
items land, the note becomes **stale itself** — it will assert "does not yet" about things that now do.
`system_overview.md` is already listed in this ticket's own Related Docs as a conditional edit target,
so leaving the note untouched after landing the fix would immediately reintroduce a documentation
staleness bug of the same species this ticket exists to repair. See Acceptance Criteria — the AC
already anticipates this and defers the remove-vs-annotate decision to Investigate/Plan.

**Recommendation:** remove the note. It was explicitly framed as a temporary disclosure ("candidates
for a future documentation-maintenance ticket") pointing at exactly this ticket's scope; once the scope
lands, the disclosure has no remaining referent and keeping it (even annotated) adds a stale-note
mention for no reader benefit. This is a plan-decision, not a hard fact — flagging as open question
below in case Plan disagrees (e.g. wants an audit-trail breadcrumb instead of a clean delete).

## Effect of the 4 Sibling Gate-Determinism Tickets (Landed After This Ticket Was Filed)

`TCK-20260705-WORKFLOW-SECURITY-GATE`, `TCK-20260705-WORKFLOW-PARITY-SKIP`, and
`TCK-20260705-MONITORING-SCHEMA-GATE-SYNC` all touched `docs/ai/workflows.md` /
`docs/ai/system_overview.md` / `docs/ai/ticket-lifecycle.md` for their own gate documentation
(`Security-Review` row, `Parity` row/skip-logic, monitoring schema notes). Checked each done ticket's
`## Files Changed` section directly:

- `WORKFLOW-SECURITY-GATE`: edited `implement-ticket.js`'s own phase table entry only (added
  `Security-Review` row + `SECURITY_BLOCKED` return value).
- `WORKFLOW-PARITY-SKIP`: edited `implement-ticket.js`'s `Parity` row only.
- `WORKFLOW-TAG-TUNING-INVESTIGATION`: confirmed **zero** doc/code files changed — investigation-only
  ticket, no edits at all.
- `MONITORING-SCHEMA-GATE-SYNC`: per its own working-log summary, corrected monitoring-schema
  references, not workflow phase tables.

None of these four touched the `create-tickets`, `generate-simulation-setup`,
`investigate-simulation-result`, or `compact-simulation-result` sections of `workflows.md`, nor added a
`simq-audit` row, nor changed the `README.md` count line, nor removed the `system_overview.md` §6 note.
All edits were scoped to `implement-ticket.js`'s own phase table (which lives in the *same* file,
`workflows.md`, but a different section than the four this ticket targets). **Confirmed: none of this
ticket's target content was incidentally fixed.** The re-verification above (reading the live files,
not trusting any prior citation) is the actual proof, not an inference from the sibling tickets' scope
statements.

## Mechanics / Engine Constraints

None. This is `docs/ai/` process/tooling documentation, not simulation mechanics. No
`docs/mechanics/` chapter or `docs/engine/` contract applies. No behavior changes — pure prose/table
correction to match already-existing code.

## Parity Ledger Overlap

None. Searched `docs/parity_ledger/*.yaml` for any reference to `docs/ai/` — only
`infrastructure.yaml` mentions `docs/ai/` (an unrelated entry about `docs/ai/skills.md` /
`docs/guides/README.md` RAG mechanisms, not phase-table content). No P0/P1 parity entry is affected by
this ticket; nothing here changes runtime behavior, only documentation of already-existing behavior.

## Prior Work

- `TCK-20260705-AI-AGENT-OVERVIEW-DOC` (done) — created `system_overview.md`, first disclosed the
  staleness (as the §6 note now documents), added README.md's Document Index row for
  `system_overview.md` itself (not the `workflows.md` row this ticket fixes).
- `TCK-20260705-WORKFLOW-TAG-TUNING-INVESTIGATION` (done) — investigation-only, re-disclosed the same
  staleness and explicitly recommended this ticket as the fix; made zero file edits.
- `TCK-20260705-WORKFLOW-SECURITY-GATE` (done) and `TCK-20260705-WORKFLOW-PARITY-SKIP` (done) — both
  had to cite `.claude/workflows/implement-ticket.js` directly in their own doc edits instead of
  trusting `workflows.md`, because of this same staleness (though for a different workflow section
  than this ticket's 4 targets).
- Registry query (`docs/REGISTRY.yaml`, filtered by `tags` containing `workflows`) surfaced no other
  open or done ticket targeting the 4 stale phase lists or the `simq-audit` documentation gap beyond
  the three already cited above.
- No `stored_artifacts/` precedent exists for "add a workflow's catalog entry retroactively" — the
  closest analog is `WORKFLOW-SECURITY-GATE`'s addition of the `Security-Review` row to the
  `implement-ticket` phase table, which is a same-file, same-pattern precedent for the format to follow
  (table row per phase, `Gate condition` / `What happens` column depending on which table format the
  target workflow's section already uses).

## Risks and Open Questions

1. **The ticket's "dual-table pattern for other workflow-backed skills" claim is FALSE — this is a
   real correction, not a re-confirmation.** The ticket asserts `simq-audit` needs a row in *both*
   `skills.md` tables "per the existing dual-table pattern for other workflow-backed skills." Checked
   directly: `create-tickets`, `implement-ticket`, and `implement-epic` all have **both** a live
   workflow (`.claude/workflows/*.js`) **and** a dedicated `.claude/skills/*/SKILL.md` folder — the
   exact same shape as `simq-audit` — yet **none of them appear in the "Project-Level Skill Files"
   table.** They appear *only* in "Project Skills (Workflow Shortcuts)". The "Project-Level Skill
   Files" table's own header text (`docs/ai/skills.md:146`) defines its scope explicitly: "Python and
   engineering patterns adapted for this project" — i.e., skills with **no** workflow trigger
   (`python-testing-patterns`, `debugging-strategies`, `brainstorming`, etc.). The two tables are
   mutually exclusive by category (workflow-triggered vs. standalone-pattern), not overlapping by
   "has a SKILL.md file." **Recommendation: add `simq-audit` to the "Project Skills (Workflow
   Shortcuts)" table only** (one row, matching `create-tickets`/`implement-ticket`/`implement-epic`'s
   precedent), and do **not** add it to "Project-Level Skill Files" — doing so would introduce a new
   inconsistency the ticket did not intend. This directly affects the ticket's stated Scope bullet and
   its Acceptance Criteria bullet ("both of `docs/ai/skills.md`'s skill tables") — flagging as a
   decision point for Plan since it narrows the AC from "both tables" to "one table, correctly", which
   is a change in what "done" means here.
2. **`system_overview.md` §6 note: remove vs. annotate.** As detailed above, recommend removal since
   the note explicitly frames itself as pointing at exactly this ticket's scope. Low risk either way —
   flagging per the ticket's own open-question framing, not because evidence is ambiguous.
3. **No other content in any touched file may be modified** (ticket's own AC). The four `workflows.md`
   sections and the README line are short, well-isolated edits; `skills.md`'s one new row is additive.
   Risk is low but Implement should diff-review after editing to confirm no adjacent row/section was
   accidentally touched (e.g. table column alignment in markdown could visually shift if care isn't
   taken with cell widths — cosmetic only, not a content risk).

## Anti-Drift Hazards

- Do not touch `docs/ai/agent_infrastructure_audit.md` — it is explicitly out of scope, a dated
  point-in-time snapshot (2026-07-03) that should NOT be updated to reflect current counts.
- Do not touch any `.claude/workflows/*.js` or `.claude/agents/*.md` file — zero code changes, this is
  documentation-only.
- Do not touch the `tickets/todos/gate-determinism-followups/` initiative — unrelated, same session.
- Do not add `simq-audit` to `skills.md`'s "Project-Level Skill Files" table — see Risk #1 above; this
  would be a new mistake, not a fix.
- Do not alter `implement-ticket.js`'s or `implement-epic.js`'s existing sections/rows in
  `workflows.md` — those are already correct/current (per `WORKFLOW-SECURITY-GATE` and
  `WORKFLOW-PARITY-SKIP`'s recent edits) and are not part of this ticket's 4 named targets.
- When adding the `simq-audit` catalog section to `workflows.md`, match the existing per-workflow
  section format used by other "Simulation Workflows" entries (Purpose / Phases / Args / Outputs /
  When to use), not the `implement-ticket`-style Agent/Gate-condition table — `simq-audit` has no
  agent-per-phase gate table precedent in `docs/ai/workflows.md`'s existing simulation-workflow
  sections; it should follow `compact-simulation-result`'s or `update-knowledge-store`'s section shape
  (closest siblings: single-session workflow, Purpose/Phases/Args/Outputs/When-to-use, no dedicated
  Return Values table unless one is warranted — `simq-audit.js`'s Report phase returns
  `DONE_NO_TICKET` / `NEEDS_TICKET`, which is a return-value distinction worth a small table similar to
  `implement-epic`'s, per `docs/simulation_quality/audit_workflow.md` §3).
