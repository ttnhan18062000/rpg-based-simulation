---
status: historical
layer: ai
authority: P2
audience: agent
ticket_id: TCK-20260803-DOC-UPDATER-CORE-WIRING
artifact_type: plan
tags: [workflows, documentation]
---

# Implementation Plan — TCK-20260803-DOC-UPDATER-CORE-WIRING

## Summary

Add a new `doc-updater` subagent and a new `Document-Update` pipeline phase, inserted between
Implement's `agent()` call (ends `.claude/workflows/implement-ticket.js:771`) and the existing
`doc_staleness_check.py` gate (comment block starts line 773, `bash()` call lines 794-796), with
the orchestrator merging doc-updater's own reported files into the list that gate evaluates before
it runs — exactly the structural fix `docs/architecture/doc_updater_agent.md`'s Decision section
specifies, with zero changes to `check_doc_staleness()`'s internal pass/fail logic. Both Plan-level
decisions flagged by investigation.md are resolved here rather than left open: (1) `meta.phases`
gains a `Document-Update` entry, with `test_workflow_meta_conformance.py`'s literal expected-list
assertion updated in lockstep — consistency with the other 11 self-declared phases outweighs the
cost of one test-list edit; (2) hotfix tier's "what" reaches doc-updater by having the agent read
`${ticketInfo.ticket_path}` directly in-prompt, tier-branched exactly the way Implement's own
existing hotfix branch (line 750) already does — zero new orchestrator-side parsing. The plan also
folds in two doc-update targets investigation.md confirmed but the ticket's own Scope text
under-named: `docs/ai/ticket-lifecycle.md` (Tier Routing table, mermaid diagram, new prose
subsection) and `docs/ai/agents.md` (new `### doc-updater` section + Agent Summary Table row) —
both confirmed required by the ticket's own Assumptions/Open Questions section, which asked
Investigate to fold agents.md into Plan if confirmed, and it was.

## Steps

### Step 1 — Create `.claude/agents/doc-updater.md`
**Files:** `.claude/agents/doc-updater.md` [new], `tests/tools/test_doc_updater_agent_file.py` [new]
**Change:** Create the new subagent file following `.claude/agents/parity-updater.md`'s exact
section skeleton (confirmed shape: frontmatter → one-paragraph role intro → `## Step 0` orchestrator-
context section → per-family rules section → `## What to Do` → `## Output`):
- Frontmatter: `name: doc-updater`, one-line `description:` in the same style as
  `parity-updater`'s (`After a behavior change is implemented, updates the relevant YAML entries in
  docs/parity_ledger/ to reflect the new state.`) — e.g. something like "After a behavior change is
  implemented, updates the relevant docs/ files (outside parity_ledger/, audits/, archive/,
  scenarios/, entity/) to reflect the new state."
- `## Step 0 — Orchestrator-Injected Context`: describe that the orchestrator computes "what" before
  spawning this agent (mirrors `parity-updater`'s `expected_subsystems_for_files()` precedent, per
  design doc's Data-flow section) — standard/epic tier gets `investigation.md`'s `## Docs Requiring
  Update` bullets (`(path, reason)` pairs) injected into the prompt preamble; hotfix tier has no
  `investigation.md`, so the agent is told to read `${ticketInfo.ticket_path}`'s own `## Scope`
  section directly plus the real `files_changed` diff, and use its own judgment for whether a
  `docs/` update is warranted.
- Per-family rules section (transcribe `docs/architecture/doc_updater_agent.md`'s Data-flow "Family |
  Rule" table into prose instructions, NOT a copied markdown table — per Scope item 1 and test 5's
  explicit "table header string must not appear verbatim" guard): cover `docs/mechanics/` (bit-
  identical parity, Certified Level 1, cite chapter+section), `docs/engine/` (cite contract ID,
  `project_lawbook_m10.md` is the index), `docs/guides/*.md` (match existing terse per-row table
  convention), `docs/guidelines/intentional_divergences.md` (rationale class + description +
  `Verification:` test path, all three required — use the real filename, no `v2_` prefix, see
  Anti-Drift Notes), `docs/plans/` (update in place if still live, never move to `docs/plans/archive/`
  — a separate whole-epic human decision), `docs/audits/` (never edited — cite-only, dated point-in-
  time snapshots; any staleness claim from an audit finding must be independently re-verified before
  being trusted, never taken as current fact), and the 17-folder catch-all (`agent-monitoring`, `ai`,
  `architecture`, `cognition`, `combat`, `compliance`, `content`, `core`, `guidelines`,
  `observability`, `performance`, `simulation`, `simulation_quality`, `strategy`, `systems`,
  `testing`, `world` — read the target doc's frontmatter plus 2-3 sibling docs before editing, match
  existing structure, any `status: authoritative` doc gets full Mechanics-Bible-level rigor
  regardless of folder). Explicitly state `docs/parity_ledger/*.yaml` is out of scope (parity-
  updater's exclusive territory) and `docs/archive/`, `docs/scenarios/`, `docs/entity/` are out of
  scope for everyone (matches `_SKIP_DOC_SUBDIRS`).
- `## What to Do`: numbered steps — identify target doc(s) from the injected what/why, read the
  doc's current content, apply the per-family rule, record what changed.
- `## Output`: one-sentence summary (≤200 chars) for the monitoring event; `docs_updated` (list of
  `{path, reason, what_changed}`); `docs_skipped` (list of flagged-but-not-touched paths with
  justification — allowed, not a failure); `blocker` (a short description, ONLY set when the agent
  hit genuine ambiguity or could not resolve how to update a flagged doc — distinct from a skip;
  omitted/null in the normal case); `verified_by` field (mirrors `parity-updater`'s shape: which
  findings came from injected context vs. independent judgment).
- Create `tests/tools/test_doc_updater_agent_file.py` with:
  - `test_doc_updater_agent_file_has_required_sections` (test 5 from test_plan.md): asserts the file
    exists, has valid frontmatter (`name: doc-updater`, one-line `description:`), and contains a
    Step-0-equivalent section, prose per-family rules (assert the literal `Family | Rule` table
    header string from `docs/architecture/doc_updater_agent.md` does NOT appear verbatim), a
    "What to Do" section, and an "Output" section mentioning `docs_updated`/`docs_skipped`/
    `blocker`/`verified_by`.
  - `test_doc_updater_never_edits_parity_ledger_or_audits_scope` (test 6): text-presence check that
    the agent file's prose explicitly excludes `docs/parity_ledger/` and states `docs/audits/` is
    cite-only/never-edited.

**Do NOT touch:** `.claude/agents/parity-updater.md` (read-only template — including its
`v2_intentional_divergences.md` typo at line 65; do not carry that typo into the new file, but do
not fix it in `parity-updater.md` either), `.claude/agents/implementer.md`, `.claude/agents/
finalizer` (does not exist as a separate file — Finalize is inline in `implement-ticket.js`, not
touched here), `.claude/agents/planner.md`.

**Verify:** `pytest tests/tools/test_doc_updater_agent_file.py -v` (both new tests pass).

---

### Step 2 — Wire the `Document-Update` phase block into `implement-ticket.js`
**Files:** `.claude/workflows/implement-ticket.js`, `tests/tools/test_document_update_phase_wiring.py` [new]
**Change:** Insert a new phase block strictly between line 771 (`)` closing Implement's `agent()`
call) and line 773 (start of the `// ─── Doc-staleness gate ...` comment block) — i.e. before the
`docsToUpdate`/`docStalenessFilesArgs` construction and before the `bash()` call. Follow the Parity
phase's exact structural template (lines 1086-1109: `captureTs()` → `writeSidecar()` → `agent()`
with a JSON schema → later `pushEvent()`), adapted:
- `phase('Document-Update')`
- A `DOC_UPDATE_SCHEMA` object: `required: ['docs_updated', 'docs_skipped', 'summary']`,
  `docs_updated`: array of `{path, reason, what_changed}` objects, `docs_skipped`: array of
  `{path, justification}` objects, `verified_by`: array of strings, `summary`: one-sentence string
  (≤200 chars), `blocker`: string or null, optional (default null) — the agent sets this to a
  non-null, non-empty description ONLY when it hit genuine ambiguity or could not resolve how to
  update a flagged doc (design doc's Error handling case 2: "doc-updater fails outright"). This is
  distinct from `docs_skipped`, which stays the correct place for "this flagged doc genuinely
  didn't need touching" — `blocker` is reserved for "I could not determine what to do," never used
  interchangeably with a skip.
- `const docUpdateTs = await captureTs()`
- `await writeSidecar(events.length + 1 + seqOffset, 'Document-Update', 'doc-updater')`
- `const docUpdate = await agent(...)` with `{ label: 'doc-update', schema: DOC_UPDATE_SCHEMA,
  agentType: 'doc-updater' }`. Prompt content, tier-branched exactly like Implement's own prompt at
  line 749-750:
  - Standard/epic: inject `investigation.docs_to_update` (already a real JS array, populated at
    line 456 for hotfix and by the Investigate phase for standard/epic) as the "what/why" — each
    entry is a `(path, reason)` pair per `investigation.md`'s `## Docs Requiring Update` format.
  - Hotfix: instruct the agent to read `${ticketInfo.ticket_path}` directly and use its own `##
    Scope` section plus `implementation.files_changed` — mirrors line 750's existing hotfix branch
    verbatim in shape, no new orchestrator-side text extraction.
  - Include architecture constraints reference to the per-family rules living in the agent file
    itself (do not re-embed the rules table in the prompt — the agent file already carries them).
- After the agent call returns: `pushEvent('Document-Update', 'doc-updater', docUpdate.blocker ?
  'failed' : 'ok', docUpdate.blocker || docUpdate.summary || 'Document update complete',
  docUpdateTs)` — the status check reads the schema's own `blocker` field directly (non-null/
  non-empty string means the agent hit case 2), never an undefined or inferred condition. Mirrors
  Parity's non-fatal `pushEvent(..., 'failed', ...)`-without-early-return shape: a `blocker`
  produces a `failed` event but **no `return { status: ... }`** for this phase under any
  circumstance (see Step 2's Anti-Drift Notes below) — the pipeline always continues to the
  doc-staleness gate and, later, Verify's `check_docs_to_update_coverage`, which remain the only
  real backstops per the design doc's Error handling section.
- Create `tests/tools/test_document_update_phase_wiring.py` with:
  - `test_document_update_phase_between_implement_and_doc_staleness_check` (test 1): asserts
    `text.find("phase('Document-Update')")` lands strictly between the Implement `agent()` call's
    closing text and `text.find("doc_staleness_check.py")`.
  - `test_document_update_runs_unconditionally_no_hotfix_guard` (test 3): asserts no `if (tier !==
    'hotfix')` (or equivalent) wraps the new phase block; the block's byte range does not fall
    inside the tier-conditional span closing at line 724, and is not wrapped in a new conditional of
    its own.
  - `test_document_update_failure_does_not_return_blocking_status` (test 4): asserts no `return {
    status: ... }` appears between `phase('Document-Update')` and the doc-staleness gate's `bash()`
    call.
  - `test_document_update_pushevent_status_reads_blocker_field` (test 4b): asserts the `pushEvent`
    call for this phase's status argument is literally `docUpdate.blocker ? 'failed' : 'ok'` (or
    byte-equivalent) — not a placeholder, not an inferred/undefined condition, and not derived from
    `docs_skipped`'s length or contents (a non-empty `docs_skipped` must never itself produce
    `'failed'` — only a set `blocker` may).

**Do NOT touch:** the doc-staleness gate comment block's own text (lines 773-791) beyond what Step 3
requires; do not reference the literal substring `doc_staleness_check.py` anywhere in the new
phase's own comments or prompt text (test 1's ordering anchor uses `text.find("doc_staleness_check.py")`
first-occurrence — referencing it early would break the anchor). Do not add a new `if (tier !==
'hotfix')` guard around this phase — it must run unconditionally for every tier per AC. Do not
conflate `docs_skipped` (expected, not a failure) with `blocker` (case-2 failure signal) anywhere
in the pushEvent status logic — this exact conflation was the architecture-review finding this
revision resolves.

**Verify:** `pytest tests/tools/test_document_update_phase_wiring.py::test_document_update_phase_between_implement_and_doc_staleness_check tests/tools/test_document_update_phase_wiring.py::test_document_update_runs_unconditionally_no_hotfix_guard tests/tools/test_document_update_phase_wiring.py::test_document_update_failure_does_not_return_blocking_status tests/tools/test_document_update_phase_wiring.py::test_document_update_pushevent_status_reads_blocker_field -v`

---

### Step 3 — Merge doc-updater's reported files into the doc-staleness gate's input
**Files:** `.claude/workflows/implement-ticket.js` (the `docStalenessFilesArgs` construction, today
at line 792), `tests/tools/test_document_update_phase_wiring.py`
**Change:** Change the source array `docStalenessFilesArgs` is built from. Today:
`implementation.files_changed.map(f => \`"${f}"\`).join(' ')`. New: merge doc-updater's own
`docs_updated` paths (mapped to their `path` field) into a combined, de-duplicated array before the
`.map()`/`.join()` — e.g. construct `const combinedFilesChanged = Array.from(new Set([
...implementation.files_changed, ...(docUpdate.docs_updated || []).map(d => d.path) ]))` and use
`combinedFilesChanged` in place of `implementation.files_changed` at that line. This is a pure JS-
side change — `doc_staleness_check.py`'s own CLI invocation shape (lines 794-796) does not change.
- Add `test_document_update_files_changed_merged_into_doc_staleness_args` (test 2) to
  `tests/tools/test_document_update_phase_wiring.py`: greps the constructed-array line's text for
  both `implementation.files_changed` and the new doc-updater-derived variable reference, mirroring
  `test_docs_to_update_wired_into_doc_staleness_invocation`'s "reference found within N chars of the
  invoke line" style.

**Do NOT touch:** `tools/gate_checks/doc_staleness_check.py` itself — `git diff --stat -- tools/
gate_checks/doc_staleness_check.py` must be empty after this step and every subsequent step. Do not
change the shape of the `bash()` invocation line (794-796) itself, only the array feeding
`docStalenessFilesArgs`.

**Verify:** `pytest tests/tools/test_document_update_phase_wiring.py::test_document_update_files_changed_merged_into_doc_staleness_args -v`, plus `git diff --stat -- tools/gate_checks/doc_staleness_check.py` (must be empty).

---

### Step 4 — Resolve the `meta.phases` decision: add `Document-Update`, update the conformance test in lockstep
**Files:** `.claude/workflows/implement-ticket.js` (lines 4-16, the `meta.phases` array),
`tests/tools/test_workflow_meta_conformance.py` (lines 64-69)
**Change:** Investigation's Risk 2 flagged this as a Plan-level decision — resolved here as YES, add
it, for consistency with the other 11 self-declared phases and because leaving it stale is exactly
the class of self-inconsistency `workflow_meta_conformance.py` exists to catch elsewhere in the
pipeline. In `meta.phases` (currently 11 entries, `Scope` through `Finalize`), insert a new entry
between `Implement` and `Architecture-Verify` (matching real execution order from Steps 2-3):
`{ title: 'Document-Update', detail: 'Specialist doc-updater agent applies docs/ updates for this
ticket (outside parity_ledger/, audits/, archive/, scenarios/, entity/); its files merge into the
doc-staleness gate\'s input before that gate runs' }`. In the same diff, update
`test_parses_meta_phases_from_implement_ticket_js` (lines 66-69) to insert `"Document-Update"`
between `"Implement"` and `"Architecture-Verify"` in the literal expected list.

**Do NOT touch:** `test_parses_meta_phases_from_create_tickets_js` or
`test_parses_meta_phases_from_implement_epic_js` — unrelated workflow files, unaffected.

**Verify:** `pytest tests/tools/test_workflow_meta_conformance.py::test_parses_meta_phases_from_implement_ticket_js -v`

---

### Step 5 — Add `Document-Update` row to `docs/ai/workflows.md`'s `implement-ticket` phase table
**Files:** `docs/ai/workflows.md`, `tests/tools/test_document_update_phase_wiring.py`
**Change:** In the `implement-ticket` phase table (header at line 81, `Implement` row at 87, `Test`
row at 89), insert a new row between `Implement` and `Test` (matching real execution order):
`| Document-Update | \`doc-updater\` | Runs unconditionally, every tier; its \`docs_updated\` paths
merge into \`implementation.files_changed\` before the doc-staleness gate evaluates them; a
doc-updater blocker is reported via a \`failed\`-status event but does not stop the pipeline — Verify's
\`check_docs_to_update_coverage\` remains the actual backstop for standard/epic tier |`.
- Add `test_document_update_phase_appears_in_workflows_md_table` (part of test 7) to
  `tests/tools/test_document_update_phase_wiring.py`: asserts `docs/ai/workflows.md`'s
  implement-ticket phase table contains a `Document-Update` row.

**Do NOT touch:** the `create-tickets`/`implement-epic` phase tables elsewhere in the same file, or
any other row in the `implement-ticket` table beyond inserting the new one.

**Verify:** `pytest tests/tools/test_document_update_phase_wiring.py::test_document_update_phase_appears_in_workflows_md_table -v`

---

### Step 6 — Update `docs/ai/system_overview.md`'s four stale phase-count/pipeline spots
**Files:** `docs/ai/system_overview.md`, `tests/tools/test_document_update_phase_wiring.py`
**Change:** Four separate edits inside the same prose walkthrough (all four confirmed by
investigation.md, not just the one line the ticket originally named):
1. Line 82: `"**The 10-phase \`implement-ticket\` pipeline** (standard tier): ..."` → `"**The 11-phase
   \`implement-ticket\` pipeline** (standard tier): ..."`, and insert `→ **Document-Update
   (\`doc-updater\`, runs unconditionally; \`docs_updated\` paths merge into the doc-staleness gate's
   input)**` into the walkthrough sequence between the `Implement` clause and the
   `**Architecture-Verify (...)** →` clause.
2. Lines 100-105: update the self-referential cross-doc consistency claim — "Security-Review is an
   11th, conditional phase" becomes "Security-Review is a 12th, conditional phase"; "the pipeline is
   still described as 10 standing phases plus this one conditional gate" becomes "11 standing phases
   plus this one conditional gate"; keep the "This matches `docs/ai/workflows.md` and
   `docs/ai/ticket-lifecycle.md`, both of which match `.claude/workflows/implement-ticket.js`
   exactly" sentence intact (it becomes true again once Steps 5 and 7 land).
3. Line 117: hotfix pipeline summary — `Scope → Implement → Test → Parity → Verify → Finalize` →
   `Scope → Implement → Document-Update → Test → Parity → Verify → Finalize`.
4. Line 118: `| standard | Full 10-phase pipeline | ... |` → `| standard | Full 11-phase pipeline |
   ... |`.
- Add `test_document_update_appears_in_system_overview_hotfix_line` (part of test 7) to
  `tests/tools/test_document_update_phase_wiring.py`: asserts `docs/ai/system_overview.md`'s hotfix
  pipeline summary line contains `Document-Update`.

**Do NOT touch:** the `create-tickets`/`implement-epic` sections of the same file (lines 75-80,
107-124's `implement-epic` paragraph), or the "Self-reference note" paragraph (lines 107-111) beyond
what's covered above.

**Verify:** `pytest tests/tools/test_document_update_phase_wiring.py::test_document_update_appears_in_system_overview_hotfix_line -v`, plus direct read confirming all four spots (only the hotfix line has an automated test — items 1, 2, and 4 are prose-consistency edits verified by direct read, per test_plan.md not naming dedicated tests for them).

---

### Step 7 — Update `docs/ai/ticket-lifecycle.md`'s three spots (confirmed by investigation, not named in ticket's original Scope)
**Files:** `docs/ai/ticket-lifecycle.md`
**Change:** Three edits, confirmed required by investigation.md (this doc is the one
`system_overview.md` line 104 explicitly cites as "matching" — leaving it stale breaks that
cross-reference claim even after Step 6):
1. Tier Routing table (lines 20-24): hotfix row `Scope → Implement → Test → Parity → Verify →
   Finalize` → `Scope → Implement → Document-Update → Test → Parity → Verify → Finalize`; standard
   row `| standard | Full 10-phase pipeline (default) | ... |` → `| standard | Full 11-phase
   pipeline (default) | ... |`.
2. Mermaid flowchart (lines 36-88): insert a new `Document-Update` node between the `Implement` node
   (line 58, which already branches to `DocStalenessFix` on `DOC_STALENESS_BLOCKED`) and the
   doc-staleness-gate edge — real orchestrator position is Implement → Document-Update →
   doc-staleness gate → Architecture-Verify. Concretely: change `Implement --> ArchVerify` (line 60)
   to `Implement --> DocUpdate` and add `DocUpdate["Document-Update<br/><i>doc-updater</i><br/>→
   docs/ updates applied<br/><small>files merge into doc-staleness gate's input</small>"] -->
   ArchVerify`; keep `Implement -- DOC_STALENESS_BLOCKED --> DocStalenessFix` and the `"hotfix skips
   to" .-> Implement` edges unchanged (Document-Update runs unconditionally right after Implement for
   every tier, so no new hotfix-skip edge is needed around it).
3. New `### Document-Update` prose subsection, inserted between `### Implement` (ends line 296,
   `---` separator) and `### Architecture Verify` (starts line 298) — same shape as the existing
   `### Parity` subsection (Agent / Step 0 / What the agent does / Gate-or-non-gate behavior):
   `**Agent:** \`doc-updater\``; a Step 0 paragraph describing the tier-branched what/why injection
   from Step 2; a "What the agent does" paragraph summarizing the per-family rules from
   `.claude/agents/doc-updater.md`; a "Gate behavior" paragraph stating this phase never returns a
   blocking `status` — any blocker is reported via a `failed`-status event, and Verify's
   `check_docs_to_update_coverage` remains the actual backstop for standard/epic tier (hotfix has no
   equivalent backstop, an accepted pre-existing gap per the design doc).
- Line 538 ("Hotfix runs push three `skipped` events...") does NOT need editing — confirmed by
  investigation.md; Document-Update runs unconditionally for hotfix, never a fourth skipped event.

**Do NOT touch:** line 538 or any other part of the mermaid diagram/prose beyond the three spots
above; do not add a hotfix-skip edge around the new `DocUpdate` node.

**Verify:** Direct read confirming all three edits — no dedicated automated test names this file in
test_plan.md's "New Tests Required" section (a coverage gap noted in Anti-Drift Notes below, not
something this plan invents a new test for since test_plan.md is the authoritative source of
required tests).

---

### Step 8 — Add `docs/ai/agents.md`'s `### doc-updater` section and Agent Summary Table row
**Files:** `docs/ai/agents.md`
**Change:** Confirmed required by investigation.md (every other pipeline agent has both a
`### agent-name` subsection and a summary-table row; omitting doc-updater leaves the canonical
"what does each agent do" reference silently incomplete for a real, wired agent). Two edits:
1. New `### doc-updater` subsection under `## Quality and Compliance Agents`, immediately after
   `### parity-updater` (ends line 271, before the `---` at 271/272), in the same shape as that
   section (Role / Step 0 static-or-orchestrator-injected-context / a rules-summary list mirroring
   the ledger-files table shape / "When to invoke directly"): **Role:** "Applies `docs/` updates for
   a behavior change, outside `parity_ledger/`, `audits/`, `archive/`, `scenarios/`, `entity/`."
   **Step 0:** describes the tier-branched what/why injection (standard/epic: `investigation.md`'s
   `## Docs Requiring Update` bullets; hotfix: agent reads `${ticketInfo.ticket_path}` directly) from
   Step 2 above. A short per-family rules summary list (mechanics/engine/guides/intentional_divergences/
   plans/audits/catch-all, condensed from the agent file's own prose). **When to invoke directly:**
   "After any manual doc-relevant change — mirrors `parity-updater`'s own guidance."
2. New row in the Agent Summary Table (lines 405-422), between the `parity-updater` row (line 416)
   and `done-checker` row (line 417), matching post-Implement ordering: `| \`doc-updater\` |
   Post-implementation | Updated \`docs/\` files (\`docs_updated\`/\`docs_skipped\`) |`.

**Do NOT touch:** the `### parity-updater` section's own content, or any other agent's section/row.

**Verify:** Direct read confirming both edits — no dedicated automated test names this file in
test_plan.md either (same gap as Step 7, noted in Anti-Drift Notes).

---

## Scope Guards

- **`tools/gate_checks/doc_staleness_check.py`**: zero internal logic changes. `check_doc_staleness()`
  is untouched — only its input (the merged files array) changes, via Step 3. `git diff --stat --
  tools/gate_checks/doc_staleness_check.py` must be empty at every step boundary.
- **`.claude/agents/parity-updater.md`**: read-only reference/template. Do not fix its
  `v2_intentional_divergences.md` typo (line 65) — out of this ticket's scope; `doc-updater.md` must
  simply not copy the typo.
- **`docs/parity_ledger/*.yaml`**: no edits anywhere in this ticket. `doc-updater.md`'s per-family
  rules must explicitly exclude this path (Step 1); parity-updater remains its exclusive owner.
- **`docs/audits/` content**: cite-only, never edited by doc-updater. `doc-updater.md`'s per-family
  rules must state this explicitly (Step 1, verified by test 6).
- **`tools/agent-monitoring/vocabulary.py`** (`WORKFLOW_PHASES`/`WORKFLOW_AGENTS`) and
  **`registries/glossary_registry.jsonl`**: not touched — separate sibling child ticket 2's job. New
  `Document-Update`/`doc-updater` events will render as vocabulary drift in retro/dashboard views
  until that sibling ticket lands — expected, not a defect here.
- **`dashboard-frontend/src/lib/phasePalette.ts`** and **`dashboard-frontend/src/test/
  phasePalette.test.ts`**: not touched — separate sibling child ticket 3's job.
- **`.claude/agents/finalizer`, `.claude/agents/planner.md`, `plan.md`'s own shape**: unchanged, per
  the design doc's Consequences section.
- **`check_docs_to_update_coverage`**: not modified, not given any new coupling to doc-updater's
  `docs_skipped` output — the design doc's Error handling section requires it stay fully decoupled,
  re-deriving ground truth from `investigation.md` + real `git status` only.
- **`.claude/agents/implementer.md`'s stale `src/data/` reference**: not fixed here — noted follow-up,
  explicitly out of scope per the design doc's Consequences section.
- **`CLAUDE.md`**: not edited, even though it has the identical stale phase-count claim (line 108) —
  outside every agent's designed scope in this repo; a known, unaddressed residual gap per
  investigation.md, not this ticket's job.
- **No new blocking `return { status: ... }`** for Document-Update phase failures, at any step —
  AC explicitly forbids it; mirror Parity's non-fatal shape.

## Dependency Map

- Step 1 (agent file) has no code dependency on any other step, but should land before Step 2 so the
  `agentType: 'doc-updater'` referenced by the new `agent()` call corresponds to a real file.
- Step 2 (phase wiring) depends on Step 1 conceptually (agent must exist to be meaningfully invoked)
  but is not blocked by it mechanically — both can be verified independently.
- Step 3 (merge into gate input) depends on Step 2 — it edits the same code region and needs the
  `docUpdate` variable Step 2 introduces.
- Step 4 (`meta.phases` + conformance test) depends on Step 2 — it names the same phase title Step 2
  introduces, and its own AC ("existing tests still pass") only holds once both are updated together.
- Step 5, Step 6, Step 7, Step 8 (the four docs) are independent of each other and of Steps 1-4
  mechanically (pure prose edits), but should land after Step 2-3 conceptually so the docs describe
  real, landed code — do them last as a batch.
- All steps are independently verifiable in the order listed; no step requires a later step to be
  complete first.

## Acceptance Criteria Map

| AC from ticket | Implemented by step(s) | Verified by test |
|---|---|---|
| `.claude/agents/doc-updater.md` exists with required sections | Step 1 | `test_doc_updater_agent_file_has_required_sections` |
| `phase('Document-Update')` block strictly between Implement's `agent()` close and the doc-staleness gate's `docStalenessFilesArgs` construction | Step 2 | `test_document_update_phase_between_implement_and_doc_staleness_check` |
| `git diff -- tools/gate_checks/doc_staleness_check.py` empty | Steps 2-3 (scope guard, all steps) | `git diff --stat -- tools/gate_checks/doc_staleness_check.py` (manual check, plus full `test_doc_staleness_check.py` suite passing unmodified) |
| Merged array (implementation + doc-updater files) feeds the gate's `bash()` call | Step 3 | `test_document_update_files_changed_merged_into_doc_staleness_args` |
| Phase runs unconditionally, every tier including hotfix | Step 2 | `test_document_update_runs_unconditionally_no_hotfix_guard` |
| No new blocking `return { status: ... }` for Document-Update failures | Step 2 | `test_document_update_failure_does_not_return_blocking_status` |
| `docs/ai/workflows.md` phase table includes `Document-Update` row | Step 5 | `test_document_update_phase_appears_in_workflows_md_table` |
| `docs/ai/system_overview.md` hotfix pipeline summary includes `Document-Update` | Step 6 | `test_document_update_appears_in_system_overview_hotfix_line` |
| Existing tests covering `implement-ticket.js` phase structure and `doc_staleness_check.py` still pass | Steps 2-4 | `pytest tests/tools/test_doc_staleness_gate_wiring.py tests/tools/test_doc_staleness_check.py tests/tools/test_workflow_meta_conformance.py tests/tools/test_validate_agent_monitoring.py -v` |
| (newly-discovered, not a literal ticket AC) `docs/ai/ticket-lifecycle.md` gets Tier Routing/mermaid/prose updates | Step 7 | Direct read only — no dedicated automated test in test_plan.md |
| (newly-discovered, not a literal ticket AC) `docs/ai/agents.md` gets new `### doc-updater` section + summary-table row | Step 8 | Direct read only — no dedicated automated test in test_plan.md |

## Anti-Drift Notes

- **Ordering anchor fragility**: `test_doc_staleness_gate_wiring.py`'s tests anchor on
  `text.find("doc_staleness_check.py")` (first occurrence). The new phase's own comments/prompt text
  (Steps 2-3) must never reference that literal substring before the real gate comment block — keep
  all Document-Update-phase prose generic ("the doc-staleness gate" is fine; the literal filename is
  not, until after its first real occurrence at line 773 today).
- **`meta.phases` and the conformance test must land together** (Step 4) — do not add one without the
  other; a half-updated state is explicitly called out as unacceptable in investigation.md's
  Anti-Drift Hazards.
- **`docs/audits/` staleness claims are not current fact** — if implementing Step 1 or any doc step
  surfaces a claim sourced from `docs/audits/`, independently re-verify it against current code before
  treating it as true (the design doc's own review caught exactly this trap once already with a D17
  finding that had already been fixed by unrelated work).
- **Steps 7 and 8 have no automated test coverage named in test_plan.md**, unlike Steps 5 and 6. This
  is a real, acknowledged gap in test_plan.md's own coverage (it was written before investigation.md
  confirmed these two docs also needed updates) — not something this plan silently papers over, and
  not something this plan unilaterally fixes by inventing new tests outside test_plan.md's authority.
  Verify these two steps by direct read as specified; if a future ticket wants machine verification
  for `docs/ai/ticket-lifecycle.md`/`docs/ai/agents.md` doc-sync, that is a test_plan.md update, not
  an implementer-invented test.
- **This ticket's own diff will trip the doc-staleness gate on itself** — `implement-ticket.js` is a
  `.claude/workflows/*.js` file, so `behavior_changed=true` with no `docs/` path in `files_changed`
  would fail the gate. This is already handled: Steps 5-8 put real `docs/` paths in this ticket's own
  `files_changed`, satisfying the gate on this ticket's own run — a good sanity check that the
  mechanism still works post-change, not something requiring extra action.

## Deviations

- **Step 2's regression surface was incomplete: `tests/tools/test_current_run_sidecar_orchestrator.py`
  was not named anywhere in this plan (its Anti-Drift Notes list only
  `test_doc_staleness_gate_wiring.py`/`test_doc_staleness_check.py`/`test_workflow_meta_conformance.py`/
  `test_validate_agent_monitoring.py` as the suite to re-run), but adding Document-Update's
  `writeSidecar()`-then-`agent()` call site — exactly as Step 2 specifies, mirroring Parity's
  template — legitimately creates a 10th two-line sidecar-tracked site.
  `test_current_run_sidecar_orchestrator.py::test_sidecar_bash_write_precedes_each_covered_agent_call`
  hard-codes "exactly 10 `writeSidecar()` calls total (9 two-line sites + Finalize)", and a separate
  test (`test_all_nine_two_line_site_labels_present`) enumerates exactly 9 two-line-site labels.
  Both assertions are mechanically stale the instant a real 10th site is added correctly — this is
  not a design conflict, just an unnamed regression-surface gap in this plan's own Anti-Drift Notes
  (discovered the same way `meta.phases`/its conformance test were discovered — a self-declared
  count/list that must move in lockstep with a real new call site). Fixed in the same diff as Step
  2: `_COVERED_SITE_ADJACENCY` gained the Document-Update adjacency string (between Implement and
  Architecture-Verify, matching real order), the total-count assertion moved from 10 to 11, and
  `_NINE_TWO_LINE_SITE_LABELS`/`test_all_nine_two_line_site_labels_present` were renamed to
  `_TEN_TWO_LINE_SITE_LABELS`/`test_all_ten_two_line_site_labels_present` with `'doc-update'` added
  to the list. No assertion's *meaning* changed — only the enumerated total, the same class of
  lockstep update this plan's Step 4 already required for `meta.phases`.
- No other deviations. All 8 steps landed as specified, including the mermaid diagram's explicit
  instruction to leave both existing "hotfix skips to" dotted edges (`Scope -. "hotfix skips to"
  .-> Implement` and `Implement -. "hotfix skips to" .-> Test`) untouched even though Document-Update
  now runs unconditionally between Implement and the doc-staleness gate for every tier.
