---
status: historical
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20260705-GATE-DET-PARITY-UPDATER
phase: done
date: 2026-07-05
tags: [ai, workflows, determinism]
---

# TCK-20260705-GATE-DET-PARITY-UPDATER

## Title
Add a deterministic diff-cross-reference check backing parity-updater's ledger updates

## Status
DONE

## Tier
standard

## Type
feature

## Priority
P1

## Request Summary
Second of 4 gate-determinism tickets (see `tickets/todos/gate-determinism-followups/SEQUENCE.md` for
shared design decisions and full context). Per `docs/plans/agent_infrastructure/idea_agent_gate_determinism.md`'s
table: "Git-diff cross-reference: every `src/` file touched in the commit that maps to a
`docs/parity_ledger/*.yaml` subsystem must have a corresponding entry touched in the same commit." What
stays LLM-judged: whether the chosen `status` (`verified`/`divergent`) is the correct one.

## Scope
- Build a `src/` path → parity-ledger-subsystem mapping. Investigate whether one already exists
  implicitly (check `parity-updater.md`'s own prompt/instructions and `implement-ticket.js`'s Parity
  phase for how it currently decides which of the 8 canonical YAML files to touch) or must be derived
  fresh — likely from `docs/parity_ledger/*.yaml`'s own entries' `v2_evidence` path citations (reusing
  `TCK-20260705-WORKFLOW-PARITY-SKIP`'s `tools/parity_ledger_scan.py` module/pattern where sensible,
  without assuming its exact function signatures fit this different purpose without adaptation).
- `tools/gate_checks/parity_updater_static.py`: given `implementation.files_changed` (post-Implement,
  authoritative) and the set of parity-ledger files actually touched/modified in the same Implement
  pass, flag any `src/` file that maps to a subsystem YAML but whose corresponding YAML file was NOT
  touched — a static FAIL signal parity-updater's own LLM judgment must then explain or override with a
  citation.
- Add a `verified_by` field to whatever schema captures parity-updater's return (there is currently no
  formal schema for this call in `implement-ticket.js` — the Parity phase call uses only `{ label,
  agentType }` with no `schema:` property; Investigate should confirm this and decide whether adding a
  minimal schema is now warranted to carry `verified_by`, or whether the static check's result surfaces
  purely via `log(...)`/prose instead).
- Coordinate explicitly with the already-shipped `TCK-20260705-WORKFLOW-PARITY-SKIP` ticket's skip logic:
  this new static check only applies when the Parity phase's full `agent(...)` call actually runs (i.e.,
  it is not skip-eligible) — confirm during Investigate that the skip condition and this new check
  cannot conflict or double-count.
- At least one coverage-honesty test (a fixture `src/` change with a matching but untouched ledger
  subsystem must be flagged; a fixture where the ledger was correctly touched must not be).

## Out of Scope
- The other 3 gates' static verifiers — see SEQUENCE.md.
- Re-deciding `status: verified` vs `status: divergent` — remains LLM-judged.
- Modifying `TCK-20260705-WORKFLOW-PARITY-SKIP`'s skip condition itself.
- Token/cost telemetry.

## Acceptance Criteria
- [ ] `tools/gate_checks/parity_updater_static.py` exists with a documented `src/` → subsystem mapping
      derivation and a diff-cross-reference function.
- [ ] The Parity phase's prompt (when not skip-eligible) instructs parity-updater to run this check
      first and address any flagged file.
- [ ] Confirmed no conflict with the Parity-skip logic from `TCK-20260705-WORKFLOW-PARITY-SKIP`.
- [ ] At least one coverage-honesty test per check function.
- [ ] `docs/ai/agents.md`'s `parity-updater` section and the other 3 shared docs updated.

## Related Tickets
- TCK-20260705-GATE-DET-DONE-CHECKER (sibling, first in sequence)
- TCK-20260705-GATE-DET-MECHANICS-AUDITOR (sibling, should reuse this ticket's src/-to-subsystem mapping
  if built)
- TCK-20260705-WORKFLOW-PARITY-SKIP (the skip logic this check must coexist with)

## Related Docs
- docs/plans/agent_infrastructure/idea_agent_gate_determinism.md
- tickets/todos/gate-determinism-followups/SEQUENCE.md
- docs/ai/agents.md, docs/ai/workflows.md, docs/ai/system_overview.md, docs/ai/ticket-lifecycle.md

## Related Stored Artifacts
None yet.

## Related Code Areas
- .claude/agents/parity-updater.md
- .claude/workflows/implement-ticket.js (Parity phase)
- tools/parity_ledger_scan.py (reference — reuse pattern, do not assume signature fit without checking)
- docs/parity_ledger/*.yaml (read-only reference)

## Assumptions / Open Questions
- Whether a `src/`-to-subsystem mapping already exists implicitly somewhere, or must be derived fresh —
  left for Investigate.
- Whether the Parity phase call needs a formal `schema:` added for the first time to carry
  `verified_by` — left for Investigate/Plan.

## Implementation Notes
Implemented all 7 steps from the approved `staging_artifacts/TCK-20260705-GATE-DET-PARITY-UPDATER/plan.md`
exactly as specified, in Dependency Map order.

- **Step 1** — `tools/gate_checks/parity_updater_static.py` (new): `derive_mapping(ledger_dir)` imports
  `CANONICAL_LEDGER_FILES` from `tools/parity_ledger_scan.py` (never redefined), regex-extracts every
  `src/....py` substring from each canonical file's `v2_evidence` field, and accumulates a `{src_path:
  {ledger_filename, ...}}` set-valued mapping (never collapses multi-subsystem files to a single value).
  Wrapped per-file in `try/except Exception: continue` for legacy-data tolerance — a malformed YAML file
  is skipped, never raises. `expected_subsystems_for_files(files_changed, ledger_dir)` filters to `src/`
  paths only (non-`src/` excluded entirely from the dict) and returns `sorted(candidates)` or `None`
  (never omits a key). `cross_reference_touched(files_changed, touched_ledger_files, ledger_dir)`
  normalizes `touched_ledger_files` entries to basenames (tolerates raw `git status --porcelain` lines)
  and returns `PASS`/`FAIL`/`NA` per file using ANY-of-candidates semantics — a multi-mapped file only
  needs one candidate touched to clear.
- **Step 2** — `tests/tools/test_parity_updater_static.py` (new, 10 tests): all 9 tests named in
  `test_plan.md` plus one extra (`test_derive_mapping_skips_malformed_yaml_file`) exercising the
  legacy-data-tolerance guard called out in plan.md's Anti-Drift Notes. Mirrors
  `test_parity_ledger_scan.py`'s `_write_ledger` fixture-helper and `sys.path` shim pattern. Unmarked
  (no `pytest.mark.architecture`).
- **Step 3** — `.claude/workflows/implement-ticket.js` Parity phase (full-call `else` branch only):
  added `PARITY_SCHEMA` (mirrors `DONE_SCHEMA`'s shape: `entries_updated`, `p0_missing_test_path`,
  `summary`, `ts`, `verified_by`), wired it into the `agent(...)` call's options
  (`{ label: 'parity-update', schema: PARITY_SCHEMA, agentType: 'parity-updater' }`), replaced the
  `PHASE_TS:`-line regex hack with the standard `ts`-field `Step 0` wording, and deleted the
  `parityTs`/`parityText` regex-extraction lines in favor of direct schema field reads
  (`parity.summary`, `parity.ts`). Added an orchestrator-run `bash()` call *before* `agent()`
  (`expected_subsystems_for_files`, mirroring the existing `p0ScanOutput` shape) injecting its output
  into the shared preamble (outside/before the `implementation.behavior_changed` ternary, so it's
  present regardless of which branch renders). Added an orchestrator-run `bash()` call *after*
  `agent()` returns (`cross_reference_touched` against `git status --porcelain -- docs/parity_ledger/`),
  parsed via the same `PARITY_CHECK_JSON:`-marker-prefix + try/catch pattern as
  `run_finalize_selfcheck`. Any unparseable result or `FAIL` entry is folded into the `pushEvent`
  evidence text (visibility only — no new blocking status, no early return, per the ticket's scope
  guard). Did not touch the `paritySkipEligible`/`parityForceFullRun`/`find_p0_intersection` skip branch.
- **Step 4** — `.claude/agents/parity-updater.md`: added a `## Step 0 — Expected-Subsystem Context`
  section (after the intro paragraph, before `## Parity Ledger Files`) explaining the injected preamble
  context and the post-turn orchestrator re-check. Added a `verified_by` sentence to the existing
  `## Output` section.
- **Step 5** — `docs/ai/agents.md`'s `parity-updater` section: added a "Step 0 — static pre-check"
  paragraph naming both functions and the `verified_by` field, mirroring the `done-checker` section's
  own paragraph.
- **Step 6** — `docs/ai/workflows.md` (Parity table row), `docs/ai/system_overview.md` (Parity pipeline
  clause), `docs/ai/ticket-lifecycle.md` (`### Parity` section, new "Step 0:" paragraph mirroring
  `### Verify`'s own Step 0 paragraph structurally): each extended with one clause naming the new
  static module's two functions, inline in existing prose (no new subsection, consistent with the
  done-checker precedent).
- **Step 7** — this section.

No deviations from `plan.md` — Step 3's code blocks were implemented verbatim as the plan's authoritative,
orchestrator-run design (bash() before agent(), bash() after agent() returns), and `parity.summary` is
used directly (no `parityText` variable, which no longer exists post-edit).

## Test Summary
- `pytest tests/tools/test_parity_updater_static.py -v` — 10/10 passed.
- `pytest tests/tools/ -v` — 486 passed, 30 failed. All 30 failures are in `test_knowledge_search.py`
  and `test_search_mcp.py` (embedding-index build subprocess failure and a `.mcp.json` command-shape
  mismatch — `bash` wrapper vs. expected `python3`), pre-existing and unrelated to this ticket; confirmed
  via `git diff HEAD -- .mcp.json tools/knowledge_search.py` showing no changes from this session's work.
  `test_parity_ledger_scan.py` (3/3), `test_done_checker_static.py` (30/30), and
  `test_done_checker_audit.py` (6/6) — the full regression surface named in test_plan.md — all pass.
- `node --check .claude/workflows/implement-ticket.js` — syntax OK, no regression from the Step 3 edits.

## Files Changed
- `tools/gate_checks/parity_updater_static.py` (new)
- `tests/tools/test_parity_updater_static.py` (new)
- `.claude/workflows/implement-ticket.js` (Parity phase)
- `.claude/agents/parity-updater.md`
- `docs/ai/agents.md`
- `docs/ai/workflows.md`
- `docs/ai/system_overview.md`
- `docs/ai/ticket-lifecycle.md`
- `tickets/inprogress/TCK-20260705-GATE-DET-PARITY-UPDATER.md` (this file)

## Completion Summary
Implemented an orchestrator-run diff-cross-reference backstop for parity-updater's ledger updates:
`tools/gate_checks/parity_updater_static.py` derives a general-purpose `src/` → parity-ledger-subsystem
mapping from the 8 canonical YAML files' `v2_evidence` citations (`derive_mapping`), exposes
`expected_subsystems_for_files` (run via `bash()` before the Parity agent call, injected into the shared
preamble) and `cross_reference_touched` (run via `bash()` after the agent returns, diffed against
`git status --porcelain -- docs/parity_ledger/`) — both orchestrator-run, not LLM-judged, per the
architecture review's corrected design. Non-blocking: any untouched-mapped-subsystem miss is folded into
the pushed event's evidence text only, with no new blocking status and no early return, matching this
ticket's scope guard. `PARITY_SCHEMA` was added (first formal schema for the Parity phase's `agent()`
call) carrying a `verified_by` field, matching the `done-checker` precedent, and the prior
`PHASE_TS:`-regex hack was replaced with the standard `ts`-field `Step 0` wording. Confirmed no conflict
with `TCK-20260705-WORKFLOW-PARITY-SKIP`'s skip branch — the new check only runs inside the full-call
`else` branch and the skip branch itself was untouched. The `derive_mapping`/mapping-derivation approach
is general-purpose (keyed off `v2_evidence` path citations in the 8 canonical ledger files, not specific
to any one gate) and is intended for reuse by the sibling `TCK-20260705-GATE-DET-MECHANICS-AUDITOR`
ticket per this ticket's own Related Tickets note.

Tests added: `tests/tools/test_parity_updater_static.py` (new, 10 tests — all 9 named in `test_plan.md`
plus one extra malformed-YAML-tolerance test) — 10/10 passed. Full regression run across
`tests/tools/` — 486/516 passed; the 30 failures are pre-existing `test_knowledge_search.py`/
`test_search_mcp.py` failures unrelated to and unaffected by this session's changes (confirmed via
`git diff` showing no changes to those files' dependencies).

Files changed: `tools/gate_checks/parity_updater_static.py` (new), `tests/tools/test_parity_updater_static.py`
(new), `.claude/workflows/implement-ticket.js` (Parity phase), `.claude/agents/parity-updater.md`,
`docs/ai/agents.md`, `docs/ai/workflows.md`, `docs/ai/system_overview.md`, `docs/ai/ticket-lifecycle.md`,
plus this ticket file. No `src/` files were touched (tooling/workflow change only, no behavior change),
so no parity-ledger entries required updates for this ticket itself.
