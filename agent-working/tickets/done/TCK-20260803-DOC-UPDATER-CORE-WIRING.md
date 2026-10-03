---
status: historical
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20260803-DOC-UPDATER-CORE-WIRING
phase: done
date: 2026-08-03
tags: [workflows, documentation]
---

# TCK-20260803-DOC-UPDATER-CORE-WIRING

## Title
doc-updater agent + Document-Update phase — core agent definition and implement-ticket.js wiring

## Status
DONE

## Tier
standard

## Type
feature

## Priority
P2

## Request Summary
First of three child tickets under `TCK-20260803-DOC-UPDATER-EPIC` (scope-only epic, tracking).
Implements exactly the core mechanics from `docs/architecture/doc_updater_agent.md`'s Decision
section (design doc: `Proposed` status, already written and reviewed through a 3-iteration spec
review loop): (1) a new subagent `.claude/agents/doc-updater.md`, modeled on
`.claude/agents/parity-updater.md`'s shape (static per-family rules + orchestrator-injected
dynamic what/why context + structured output contract); (2) a new **Document-Update** pipeline
phase wired into `.claude/workflows/implement-ticket.js`, inserted between Implement's `agent()`
call (ends line 771) and the existing `doc_staleness_check.py` `bash()` call (comment block starts
line 773, actual call lines 794-796) — not after that gate — with the orchestrator merging
doc-updater's own `files_changed` into the list `doc_staleness_check.py` evaluates before that call
runs. `doc_staleness_check.py`'s own internal pass/fail logic (`check_doc_staleness()`) does not
change at all — only its input does. Runs for every tier, including hotfix. The other two children
of the epic (monitoring/vocabulary registration; dashboard phase-palette registration) are separate,
not-yet-created sibling tickets and are explicitly out of this ticket's scope.

## Scope
1. Create `.claude/agents/doc-updater.md`, matching `.claude/agents/parity-updater.md`'s real file
   structure and conventions (frontmatter `name`/`description`, a "Step 0" orchestrator-injected
   context section, a per-family rules section, a "What to Do" section, an "Output" section).
   Transcribe `docs/architecture/doc_updater_agent.md`'s "Data flow — what, how, why" section's
   `Family | Rule` table (`docs/mechanics/`, `docs/engine/`, `docs/guides/*.md`,
   `docs/guidelines/intentional_divergences.md`, `docs/plans/`, `docs/audits/` cite-only, and the
   17-folder catch-all) into real prose agent instructions — not copied verbatim as a markdown
   table inside the agent file, following `parity-updater.md`'s own prose style. Output contract:
   one-sentence summary (≤200 chars) for the monitoring event, `docs_updated`
   (`{path, reason, what_changed}`), `docs_skipped` (with justification — allowed, not a failure),
   `verified_by`.
2. Wire a new `phase('Document-Update')` block into `.claude/workflows/implement-ticket.js`,
   inserted between line 771 (end of Implement's `agent()` call) and line 773 (start of the
   doc-staleness gate comment block) — i.e. strictly before the `docStalenessFilesArgs` construction
   at line 792 and the `bash()` call at lines 794-796. Follow the exact `writeSidecar`/`agent()`/
   `pushEvent` structural pattern the existing Parity phase already uses (lines ~1086-1109 as the
   direct template: `captureTs()` → `writeSidecar()` → `agent()` with a JSON schema → `pushEvent()`).
   Orchestrator computes "what" before spawning doc-updater (never the agent itself), mirroring
   `parity-updater`'s `expected_subsystems_for_files()` precedent:
   - Standard/epic tier: parse `investigation.md`'s `## Docs Requiring Update` bullets
     (`(path, reason)` pairs).
   - Hotfix tier (no `investigation.md`): pass the ticket's own `## Scope` text plus
     `implementation.files_changed`.
   After the agent call returns, merge doc-updater's own `docs_updated`/reported `files_changed`
   into the array `docStalenessFilesArgs` is built from (currently just
   `implementation.files_changed`, line 792) so the doc-staleness gate's existing check sees both
   Implement's diff and doc-updater's diff combined, before that `bash()` call runs.
3. No changes to `tools/gate_checks/doc_staleness_check.py`'s internal logic
   (`check_doc_staleness()`) — read-only reference for this ticket, confirm zero diff.
4. No new blocking workflow-level status for Document-Update phase failures. A doc-updater blocker
   (can't resolve how to update a flagged doc, genuine ambiguity) is reported in the phase's
   structured output and via `pushEvent(..., 'failed', ...)`, mirroring `parity-updater`'s pattern,
   but does not `return { status: ... }` to stop the pipeline — Verify's existing
   `check_docs_to_update_coverage` gate remains the actual backstop for standard/epic tier. Hotfix
   tier has no equivalent backstop (`check_docs_to_update_coverage` already returns `NA`
   unconditionally for hotfix) — accepted, pre-existing gap per the design doc, not addressed here.
5. Add a `Document-Update` row to `docs/ai/workflows.md`'s `implement-ticket` phase table
   (currently ~lines 81-93, does not list it) and add `Document-Update` to
   `docs/ai/system_overview.md`'s hotfix-tier pipeline summary line (currently
   `Scope → Implement → Test → Parity → Verify → Finalize`, ~line 117) — both flagged by the epic's
   scoping pass as needing this addition once the phase exists; this ticket is the one that adds
   the phase, so it is the one that updates both docs.

## Out of Scope
- `tools/agent-monitoring/vocabulary.py` (`WORKFLOW_PHASES`/`WORKFLOW_AGENTS` registration) and
  `registries/glossary_registry.jsonl` (new `phase` category entry) — separate sibling child
  ticket 2 (monitoring/vocabulary registration), not yet created.
- `dashboard-frontend/src/lib/phasePalette.ts` (`WorkflowPhase` union, `PHASE_FAMILY`,
  `PHASE_PALETTE` hex value) and `dashboard-frontend/src/test/phasePalette.test.ts`'s completeness
  assertion — separate sibling child ticket 3 (dashboard phase-palette registration), not yet
  created.
- Any change to `doc_staleness_check.py`'s internal `check_doc_staleness()` pass/fail logic — only
  what is fed into it (the merged files-changed list) changes, per the design doc's Decision
  section.
- Any change to `.claude/agents/parity-updater.md`, `finalizer`, `planner`, or `plan.md`'s shape —
  the design doc states no change to any of these.
- Promoting `docs_skipped` into a second Verify-time cross-reference against
  `check_docs_to_update_coverage` — explicitly deferred in the design doc's own Revisit Trigger
  section, not this ticket's job.
- Editing `docs/parity_ledger/*.yaml`, `docs/archive/`, `docs/scenarios/`, `docs/entity/`, or
  `docs/audits/` content — all five stay outside doc-updater's scope per the design's scope-boundary
  table (the last two of this ticket's own deliverables — `docs/ai/workflows.md` and
  `docs/ai/system_overview.md` — are ordinary living docs, not in any excluded category).
- Fixing `.claude/agents/implementer.md`'s stale `src/data/` reference — noted as a follow-up in
  the design doc's Consequences section, explicitly not in scope for any child ticket.
- (Resolved during Investigate/Plan, no longer deferred: `docs/ai/agents.md` and
  `docs/ai/ticket-lifecycle.md` were both confirmed to need a `Document-Update`/`doc-updater`
  addition and are now in this ticket's own Files Changed — see Implementation Notes.)

## Acceptance Criteria
- [x] `.claude/agents/doc-updater.md` exists with frontmatter (`name: doc-updater`,
      `description:` one-liner matching the style of other `.claude/agents/*.md` files) and
      contains: an orchestrator-injected-context section (Step-0-equivalent), the per-family rules
      transcribed as prose instructions (not a bare copied table), a "What to Do" section, and an
      "Output" section describing `docs_updated`/`docs_skipped`/`verified_by`/one-sentence summary.
- [x] `.claude/workflows/implement-ticket.js` contains a `phase('Document-Update')` block located
      strictly between the line that ends Implement's `agent()` call and the line that begins the
      doc-staleness gate's `docStalenessFilesArgs` construction — verified by reading the file
      after the edit and confirming source order.
- [x] `git diff -- tools/gate_checks/doc_staleness_check.py` is empty after implementation (file
      untouched).
- [x] The array passed into `doc_staleness_check.py`'s `bash()` call includes both
      `implementation.files_changed` and doc-updater's own reported files — verified by reading the
      constructed argument list in the diff.
- [x] The new phase executes unconditionally for hotfix and for standard/epic tier (no
      `tier !== 'hotfix'` guard skipping it) — verified by reading the code.
- [x] A doc-updater blocker/failure does not introduce a new `return { status: ... }` workflow-level
      blocking status for this phase (mirrors Parity's non-fatal-failure shape, not
      `DOC_STALENESS_BLOCKED`'s fatal shape) — verified by reading the code.
- [x] `docs/ai/workflows.md`'s `implement-ticket` phase table includes a `Document-Update` row.
- [x] `docs/ai/system_overview.md`'s hotfix-tier pipeline summary includes `Document-Update`.
- [x] Existing tests covering `implement-ticket.js` phase structure and
      `tools/gate_checks/doc_staleness_check.py` still pass (scope determined by `test-scoper` at
      implementation time).

## Related Tickets
- TCK-20260803-DOC-UPDATER-EPIC (in progress, epic, parent) — scope-only epic tracking this and
  two sibling child tickets.
- (sibling, not yet created) Monitoring/vocabulary registration child ticket —
  `tools/agent-monitoring/vocabulary.py` + `registries/glossary_registry.jsonl`.
- (sibling, not yet created) Dashboard phase-palette registration child ticket —
  `dashboard-frontend/src/lib/phasePalette.ts` + `dashboard-frontend/src/test/phasePalette.test.ts`.
- TCK-20260803-DOCS-STRUCTURE-AUDIT (done) — prerequisite structure audit the design doc's
  per-family rule table depends on.
- TCK-20260802-DOC-UPDATE-DISCIPLINE (done) — built the three-layer enforcement
  (`## Docs Requiring Update`, `doc_staleness_check.py`, `check_docs_to_update_coverage`) this
  design's Document-Update phase is a new consumer of, not a replacement for.
- TCK-20260711-DOC-STALENESS-GATE-CHECK / TCK-20260720-GATE-CHECK-WIRING-DECISIONS (done) — shipped
  and wired `doc_staleness_check.py`, the gate whose input this ticket corrects.

## Related Docs
- `docs/architecture/doc_updater_agent.md` — authoritative design doc this ticket implements
  (Decision, Scope boundary, Data flow, Error handling sections).
- `docs/ai/workflows.md` — `implement-ticket` phase table; this ticket adds the missing
  `Document-Update` row (confirmed missing by direct read during scoping).
- `docs/ai/system_overview.md` — hotfix-tier pipeline summary line; this ticket adds
  `Document-Update` to it (confirmed missing by direct read during scoping).
- `.claude/agents/parity-updater.md` — direct structural template for `doc-updater.md`'s shape.

## Related Stored Artifacts
- `stored_artifacts/TCK-20260803-DOCS-STRUCTURE-AUDIT/` — prerequisite investigation the design
  doc's per-family rule table was built from.
- None found specifically covering doc-updater agent implementation beyond the design doc and
  its prerequisite audit.

## Related Code Areas
- `.claude/agents/doc-updater.md` [new]
- `.claude/workflows/implement-ticket.js` [modified — new Document-Update phase]
- `tools/gate_checks/doc_staleness_check.py` [read-only reference — input changes, logic does not]
- `.claude/agents/parity-updater.md` [read-only reference/template]
- `docs/ai/workflows.md` [modified — new phase table row]
- `docs/ai/system_overview.md` [modified — hotfix pipeline summary]

## Assumptions / Open Questions
- `layer: ai` chosen to match the parent epic and CLAUDE.md's explicit note that this repo's
  `layer: ai` means "the Claude agent/orchestration system," not gameplay AI/cognition — this
  ticket is entirely `implement-ticket.js` pipeline tooling.
- Assumes `docs/architecture/doc_updater_agent.md` is committed/stable before implementation
  begins — inherited from the epic's own stated assumption; if the design doc changes materially
  first, this ticket's scope needs re-verification against the updated doc.
- Line numbers cited here (Implement's `agent()` call ending at line 771, the doc-staleness gate
  comment block starting line 773, the `bash()` call at lines 794-796, Parity phase's
  `writeSidecar`/`agent()`/`pushEvent` template at lines ~1086-1109) were confirmed accurate by
  direct read of `.claude/workflows/implement-ticket.js` on 2026-08-03 during scoping — Investigate
  should re-confirm at implementation time in case of intervening drift.
- `docs/ai/agents.md` needing a new `doc-updater` section is unconfirmed (the epic's scoping pass
  flagged it as "likely, not confirmed") — left out of this ticket's committed Scope; Investigate
  should check whether the established per-agent-section pattern (`parity-updater`,
  `mechanics-auditor`, etc.) makes it effectively required, and if so fold it into Plan rather than
  leaving it for a later ticket, since this is the ticket that introduces the agent.
- New `Document-Update`/`doc-updater` monitoring events will render as vocabulary drift in
  `agent-monitoring/retro` reports and the dashboard's drift-detection view until the sibling
  monitoring/vocabulary registration ticket lands — expected and accepted per the epic's
  Consequences section, not a defect to fix in this ticket.
- Tags (`workflows`, `documentation`) chosen from the already-registered set
  (`python3 tools/tag_registry.py list`); no new tag registration needed.
- No `docs/parity_ledger/*.yaml` overlap found (grepped for doc-updater/Document-Update references
  — zero hits) — this is agent-orchestration tooling, not a simulation-mechanics change.

## Implementation Notes
Implemented plan.md's 8 steps exactly, in order:

1. Created `.claude/agents/doc-updater.md` modeled on `.claude/agents/parity-updater.md`'s section
   skeleton (frontmatter → role intro → `## Step 0 — Orchestrator-Injected Context` →
   `## Per-Family Rules` (prose, no copied `Family | Rule` table header) → `## What to Do` →
   `## Output` describing `docs_updated`/`docs_skipped`/`blocker`/`verified_by`). Added
   `tests/tools/test_doc_updater_agent_file.py` with the 2 specified tests.
2. Wired `phase('Document-Update')` into `.claude/workflows/implement-ticket.js` strictly between
   Implement's `agent()` call close and the doc-staleness gate's comment block. Added
   `DOC_UPDATE_SCHEMA` (with `blocker: string|null`), `captureTs()`/`writeSidecar()`/tier-branched
   `agent()` call (standard/epic reads `investigation.docs_to_update` — confirmed by direct read to
   be an array of path strings, not `(path, reason)` objects, so the prompt also points the agent
   at `investigation.md` itself for the reason text; hotfix reads `${ticketInfo.ticket_path}`
   directly), then `pushEvent('Document-Update', 'doc-updater', docUpdate.blocker ? 'failed' : 'ok',
   docUpdate.blocker || docUpdate.summary || 'Document update complete', docUpdateTs)` with no
   `return { status }`. Added `tests/tools/test_document_update_phase_wiring.py` with all 4
   specified tests (1, 3, 4, 4b).
3. Merged `docUpdate.docs_updated`'s paths into the array feeding `docStalenessFilesArgs` via a new
   `combinedFilesChanged = Array.from(new Set([...implementation.files_changed,
   ...(docUpdate.docs_updated || []).map(d => d.path)]))`, replacing `implementation.files_changed`
   at that one line only. Added test 2
   (`test_document_update_files_changed_merged_into_doc_staleness_args`).
4. Added `{ title: 'Document-Update', detail: '...' }` to `meta.phases` between `Implement` and
   `Architecture-Verify`; updated
   `test_workflow_meta_conformance.py::test_parses_meta_phases_from_implement_ticket_js`'s literal
   expected list in the same diff.
5. Added a `Document-Update` row to `docs/ai/workflows.md`'s `implement-ticket` phase table,
   between `Implement` and `Test`.
6. Fixed all 4 stale spots in `docs/ai/system_overview.md` (10→11-phase lead sentence + inserted
   Document-Update clause, Security-Review 11th→12th / 10→11 standing phases, hotfix summary line,
   standard-tier table row).
7. Updated `docs/ai/ticket-lifecycle.md`: Tier Routing table (hotfix row, standard row), mermaid
   diagram (`Implement --> DocUpdate` + new `DocUpdate` node `--> ArchVerify`, per plan.md's exact
   instruction to leave both existing "hotfix skips to" dotted edges — including
   `Implement -. "hotfix skips to" .-> Test` — untouched), and a new `### Document-Update` prose
   subsection between `### Implement` and `### Architecture Verify`, matching the `### Parity`
   subsection's Agent/Step 0/What the agent does/Gate behavior shape.
8. Added a `### doc-updater` section to `docs/ai/agents.md` under `## Quality and Compliance
   Agents` (after `### parity-updater`), plus a row in the Agent Summary Table between
   `parity-updater` and `done-checker`.

Deviation (documented in plan.md's new "Deviations" section): implementing Step 2 legitimately
added a 10th two-line `writeSidecar()`+`agent()` site (Document-Update), which broke two
regression-surface assertions in `tests/tools/test_current_run_sidecar_orchestrator.py` that
plan.md's own step-by-step text did not name (its Anti-Drift Notes only called out
`test_doc_staleness_gate_wiring.py`/`test_doc_staleness_check.py`/`test_workflow_meta_conformance.py`/
`test_validate_agent_monitoring.py` as the regression suite to re-run). That file hard-codes
"exactly 10 writeSidecar() calls" and an exhaustive 9-label two-line-site list — both mechanically
stale the moment a legitimate 10th site is added via the exact same template Step 2 specifies.
Updated in the same diff: `_COVERED_SITE_ADJACENCY` gained the Document-Update adjacency string,
the count assertion moved from 10 to 11, `_NINE_TWO_LINE_SITE_LABELS` was renamed
`_TEN_TWO_LINE_SITE_LABELS` with `'doc-update'` added, and
`test_all_nine_two_line_site_labels_present` was renamed `test_all_ten_two_line_site_labels_present`
to match. This is a mechanical count/list correction, not a design change — no assertion's meaning
changed, only the enumerated total.

## Test Summary
Ran and confirmed passing:
- `pytest tests/tools/test_doc_updater_agent_file.py tests/tools/test_document_update_phase_wiring.py tests/tools/test_workflow_meta_conformance.py -v` — 21 passed, 1 xfailed (pre-existing unrelated xfail).
- `pytest tests/tools/test_doc_staleness_gate_wiring.py tests/tools/test_doc_staleness_check.py tests/tools/test_validate_agent_monitoring.py -v` — all passed (regression surface named by plan.md's Acceptance Criteria Map).
- `pytest tests/tools/test_current_run_sidecar_orchestrator.py tests/tools/test_step0_ts_orchestrator.py -v` — all passed after the count/label fix described above (discovered regression, not named by plan.md).
- `git diff --stat -- tools/gate_checks/doc_staleness_check.py` — empty (confirmed at every step boundary).
- `git status --porcelain .claude/agents/parity-updater.md .claude/agents/implementer.md .claude/agents/planner.md` — empty (read-only references untouched).
- Broader sweep `pytest tests/tools/ -k "not gate_a_readpath"` run for regression confirmation; `tests/tools/test_gate_a_readpath_review.py` failures confirmed pre-existing (identical failure on a stashed/clean tree before this ticket's changes — missing `staging_artifacts/TCK-20260731-PARITY-READPATH-GATE/gate_a_corpus.json` fixture, unrelated to this ticket).
- Steps 7-8 (`docs/ai/ticket-lifecycle.md`, `docs/ai/agents.md`) verified by direct read against the ticket's own Acceptance Criteria evidence style, per plan.md — no dedicated automated test exists in test_plan.md for these two files (acknowledged gap, not invented around).

## Files Changed
- `.claude/agents/doc-updater.md` [new]
- `.claude/workflows/implement-ticket.js` [modified — new Document-Update phase, meta.phases entry]
- `tests/tools/test_doc_updater_agent_file.py` [new]
- `tests/tools/test_document_update_phase_wiring.py` [new]
- `tests/tools/test_workflow_meta_conformance.py` [modified — expected phase list]
- `tests/tools/test_current_run_sidecar_orchestrator.py` [modified — sidecar count/label fix, deviation]
- `docs/ai/workflows.md` [modified — Document-Update phase table row]
- `docs/ai/system_overview.md` [modified — 4 stale phase-count/pipeline spots]
- `docs/ai/ticket-lifecycle.md` [modified — Tier Routing table, mermaid diagram, new ### Document-Update subsection]
- `docs/ai/agents.md` [modified — new ### doc-updater section + Agent Summary Table row]

## Completion Summary
Added the doc-updater subagent and Document-Update pipeline phase exactly per
`docs/architecture/doc_updater_agent.md`'s Decision section: inserted between Implement's agent()
call and the existing `doc_staleness_check.py` gate, with doc-updater's own reported files merged
into that gate's input before it runs, and zero changes to `check_doc_staleness()`'s internal
logic. Runs unconditionally for every tier including hotfix; a doc-updater blocker produces a
`failed`-status event but never a blocking workflow-level `return { status }` — Verify's
`check_docs_to_update_coverage` remains the actual backstop for standard/epic tier. `meta.phases`
and all 4 phase-count-bearing docs (`workflows.md`, `system_overview.md`, `ticket-lifecycle.md`,
`agents.md`) were updated in the same diff so the pipeline is self-consistently described as
11-phase (standard) / +Document-Update (hotfix) everywhere. All named and discovered regression
tests pass; `doc_staleness_check.py` and the three explicitly-read-only agent files are untouched.
