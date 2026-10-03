---
status: historical
layer: ai
authority: P2
audience: agent
ticket_id: TCK-20260803-DOC-UPDATER-CORE-WIRING
artifact_type: test_plan
tags: [workflows, documentation]
---

# Test Plan — TCK-20260803-DOC-UPDATER-CORE-WIRING

## Regression Surface

Static, raw-source-text tests against `.claude/workflows/implement-ticket.js` (no JS test runner exists in this repo for `.claude/workflows/*.js` — all of these read the file as text via `Path.read_text()`, per `test_doc_staleness_gate_wiring.py`'s own header comment):

**unit / static-source (must all still pass after the edit):**
- `tests/tools/test_doc_staleness_gate_wiring.py` — all 6 tests. Most load-bearing:
  - `test_doc_staleness_check_is_invoked_between_implement_and_architecture_verify` — asserts `implement_agent_idx < check_idx < arch_verify_idx` using `text.find("doc_staleness_check.py")` as the anchor for `check_idx`. Inserting Document-Update strictly between the Implement `agent()` call end (line 771) and the doc-staleness comment block (line 773) keeps `check_idx` unchanged in relative order — this test's ordering invariant is exactly what the ticket's required insertion point preserves.
  - `test_doc_staleness_failure_folds_into_the_single_implement_event_not_a_second_one` — counts `pushEvent(` occurrences strictly between `check_idx` and `phase('Architecture-Verify')`; Document-Update's own `pushEvent()` call must land *before* `check_idx` (i.e., before the first appearance of the literal string `doc_staleness_check.py` in the file) or this count goes from 1 to 2 and the test fails.
  - `test_doc_staleness_check_passes_behavior_changed_and_files_changed` and `test_docs_to_update_wired_into_doc_staleness_invocation` — both anchor off `"python3 tools/gate_checks/doc_staleness_check.py"` (a longer, more specific string than the check above) and inspect a narrow window (a single line, or the last 1500 chars before the invoke line) — unaffected by anything inserted upstream of line 773, as long as the merge of doc-updater's own reported files happens by mutating the array `docStalenessFilesArgs` is built from (line 792) rather than by editing the invocation line's shape itself.
  - `test_doc_staleness_blocked_status_has_no_reason_code`, `test_doc_staleness_blocked_writes_monitoring_before_returning` — both scoped to the block between `check_idx` and `phase('Architecture-Verify')`, i.e. entirely below the new phase's insertion point. Unaffected.
- `tests/tools/test_doc_staleness_check.py` — all 18 tests. Pure-function tests against `check_doc_staleness()` itself; this ticket makes zero changes to `tools/gate_checks/doc_staleness_check.py` (Scope item 3 / AC bullet 3), so these must pass completely unmodified. Use `git diff -- tools/gate_checks/doc_staleness_check.py` (must be empty) as a pre-flight confirmation before even running this file.
- `tests/tools/test_workflow_meta_conformance.py` — **at risk, not automatically safe.** `test_parses_meta_phases_from_implement_ticket_js` (lines 64-69) asserts the literal 11-item phase list from `meta.phases`. If the implementer adds `Document-Update` to `meta.phases` (see investigation.md Risk 2 — recommended for consistency), this test's expected list **must** be updated in the same diff to insert `"Document-Update"` between `"Implement"` and `"Architecture-Verify"`, or it fails. If `meta.phases` is deliberately left unchanged instead, this test passes unmodified but the gap noted in investigation.md Risk 2 persists — Implementation Notes must record which choice was made.
- `tests/tools/test_validate_agent_monitoring.py::test_canonical_vocabulary_single_sourced` — confirmed NOT count-based (only asserts `record_events.WORKFLOW_PHASES is validate.WORKFLOW_PHASES` object identity and `infer_workflow` identity) — unaffected by a new phase name existing in real event data, since `vocabulary.py` itself is untouched (out of scope, sibling ticket 2). No change expected/needed.
- `tests/tools/test_step0_ts_orchestrator.py`, `tests/tools/test_current_run_sidecar_orchestrator.py` — assert `writeSidecar(...)`-to-`agent()` adjacency conventions elsewhere in the file (e.g. the shadow-packet call site note at implement-ticket.js:527-533 explicitly calls out one of these guards). Re-run as a precaution since the new phase adds another `writeSidecar()`/`agent()` pair using the identical established pattern — should pass unmodified if the new phase follows the Parity-phase template exactly (`captureTs()` → `writeSidecar()` → `agent()`), but worth confirming no adjacency regex in these tests is anchored to a fixed line number rather than a pattern match.

**integration:**
- None specific to this change — no `src/` runtime behavior is touched. `implement-ticket.js` is orchestration-only and has no `src/` test counterpart.

**arena-combat:**
- Not applicable — this ticket touches no combat/simulation code.

## New Tests Required

1. **Test name:** `test_document_update_phase_between_implement_and_doc_staleness_check`
   **Category:** unit / static-source (new file: `tests/tools/test_document_update_phase_wiring.py`, following `test_doc_staleness_gate_wiring.py`'s exact established pattern for this un-executable `.js` file)
   **Verifies:** `text.find("phase('Document-Update')")` lands strictly between the Implement `agent()` call's closing text and `text.find("doc_staleness_check.py")` — the AC's core ordering requirement, machine-checked rather than eyeballed.
   **Where:** `tests/tools/test_document_update_phase_wiring.py`

2. **Test name:** `test_document_update_files_changed_merged_into_doc_staleness_args`
   **Category:** unit / static-source
   **Verifies:** the array feeding `docStalenessFilesArgs` (line 792 today) includes both `implementation.files_changed` and the new phase's own reported files-changed variable — grep the constructed-array line's text for both source references, mirroring `test_docs_to_update_wired_into_doc_staleness_invocation`'s "reference found within N chars of the invoke line" style.
   **Where:** `tests/tools/test_document_update_phase_wiring.py`

3. **Test name:** `test_document_update_runs_unconditionally_no_hotfix_guard`
   **Category:** unit / static-source
   **Verifies:** no `if (tier !== 'hotfix')` (or equivalent) wraps the new `phase('Document-Update')` block — confirms AC's "runs for every tier, including hotfix" requirement by checking the new phase's `phase(...)` call and its `agent()` call are not nested inside any tier-conditional block (e.g. assert the block's byte range doesn't fall inside the `if (tier !== 'hotfix') { ... Investigate/Plan/Review ... }` span that closes at line 724, and isn't wrapped in a new conditional of its own).
   **Where:** `tests/tools/test_document_update_phase_wiring.py`

4. **Test name:** `test_document_update_failure_does_not_return_blocking_status`
   **Category:** unit / static-source
   **Verifies:** no `return { status: ... }` appears between `phase('Document-Update')` and the doc-staleness gate's own `bash()` call — confirms AC's "does not introduce a new blocking workflow-level status" requirement, mirroring how `test_doc_staleness_blocked_writes_monitoring_before_returning` checks for presence of a return; this test checks for *absence* in the new phase's own span specifically (the existing `DOC_STALENESS_BLOCKED` return further down is out of this test's window).
   **Where:** `tests/tools/test_document_update_phase_wiring.py`

5. **Test name:** `test_doc_updater_agent_file_has_required_sections`
   **Category:** unit / architecture guard
   **Verifies:** `.claude/agents/doc-updater.md` exists, has valid frontmatter (`name: doc-updater`, one-line `description:`), and contains all of: a Step-0-equivalent orchestrator-context section, prose per-family rules (not a bare copied markdown table — assert the `Family | Rule` table header string from `docs/architecture/doc_updater_agent.md` does NOT appear verbatim, per Scope item 1's "not copied verbatim as a markdown table" requirement), a "What to Do" section, and an "Output" section mentioning `docs_updated`/`docs_skipped`/`verified_by`.
   **Where:** `tests/tools/test_doc_updater_agent_file.py` (new file, mirrors any existing `.claude/agents/*.md` structure-guard test if one exists — check for precedent before assuming this is the first)

6. **Test name:** `test_doc_updater_never_edits_parity_ledger_or_audits_scope`
   **Category:** architecture guard
   **Verifies:** `.claude/agents/doc-updater.md`'s prose explicitly excludes `docs/parity_ledger/` and states `docs/audits/` is cite-only/never-edited — a text-presence check against the agent file's content (best-effort; the real enforcement is the agent following its own instructions, but this at least confirms the exclusion is written down, catching an authoring regression where the "everything else" catch-all swallows these paths).
   **Where:** `tests/tools/test_doc_updater_agent_file.py`

7. **Test name:** `test_document_update_phase_appears_in_workflows_md_table` and `test_document_update_appears_in_system_overview_hotfix_line`
   **Category:** unit / doc-sync guard
   **Verifies:** `docs/ai/workflows.md`'s implement-ticket phase table contains a `Document-Update` row; `docs/ai/system_overview.md`'s hotfix pipeline summary line contains `Document-Update` — direct AC checks 7 and 8, machine-verified rather than only human-reviewed.
   **Where:** could live in `tests/tools/test_document_update_phase_wiring.py` alongside the others, or as a small addition to an existing doc-sync test file if one already asserts `docs/ai/workflows.md`'s phase table shape (check for one before creating a new file for just two assertions).

## Scoped Pytest Commands

```
pytest tests/tools/test_doc_staleness_gate_wiring.py tests/tools/test_doc_staleness_check.py tests/tools/test_workflow_meta_conformance.py tests/tools/test_validate_agent_monitoring.py -v

pytest tests/tools/test_document_update_phase_wiring.py tests/tools/test_doc_updater_agent_file.py -v
```

Never `pytest tests/` — scope stays within `tests/tools/` (the only directory with tests for `.claude/workflows/*.js`-adjacent tooling and `.claude/agents/*.md` structure; no `src/` behavior is touched by this ticket).

## Anti-Drift Test Guards

- **`test_doc_staleness_check_passes_behavior_changed_and_files_changed` and the other 4 non-ordering tests in `test_doc_staleness_gate_wiring.py`** already guard against the temptation to "simplify" by editing `doc_staleness_check.py`'s own call signature or the shape of its CLI args — any accidental change there fails these tests immediately, independent of the new `test_doc_updater_agent_file.py` guards.
- **`test_doc_staleness_check.py`'s full 18-test suite, re-run with zero diff on `doc_staleness_check.py` itself**, is the concrete proof AC bullet 3 ("`git diff -- tools/gate_checks/doc_staleness_check.py` is empty") holds — run `git diff --stat -- tools/gate_checks/doc_staleness_check.py` as a companion check alongside the pytest run, not instead of it (a passing test suite alone doesn't prove the file is byte-identical, only that its behavior is; the git diff check is the actual AC).
- **New test 4 (`test_document_update_failure_does_not_return_blocking_status`)** is the guard against Document-Update's blocker case quietly growing into a second `DOC_STALENESS_BLOCKED`-style hard gate later — exactly the scope-creep the ticket's own Scope item 4 and Out of Scope section warn against ("No new blocking workflow-level status").
- **New test 6 (`test_doc_updater_never_edits_parity_ledger_or_audits_scope`)** is the guard against the single most-flagged anti-drift hazard in this ticket (investigation.md's Anti-Drift Hazards #1/#2) — doc-updater's own instructions silently drifting into parity-updater's or the audits programme's territory.
- **`test_workflow_meta_conformance.py`'s existing `test_reuses_vocabulary_infer_workflow_not_a_reimplementation`** (unaffected by this ticket, but worth re-running) guards against a future temptation to hand-roll a second phase/agent vocabulary check inside the new Document-Update phase instead of reusing `vocabulary.py` — relevant because the sibling monitoring/vocabulary registration ticket (out of scope here) is exactly where that reuse eventually gets wired for `Document-Update`/`doc-updater` specifically; this ticket must not pre-empt that by inventing its own local check.
